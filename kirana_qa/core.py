from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pymupdf as fitz


_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)?", re.IGNORECASE)
_STOP_WORDS = frozenset(
    "a an and are as at be been being by can could did do does for from had has have he her here hers him his how i in into is it its may me might more most much must my of on or our ours she should so than that the their theirs them then there these they this those to was we were what when where which who why will with would you your yours tell show explain state report document according year about based please was were".split()
)
_CORRECTION_RE = re.compile(
    r"\b(errata|correct(?:ed|ion)?|supersed(?:e|es|ed)|restat(?:ed|ement)|revised figure)\b",
    re.IGNORECASE,
)
_ANSWER_NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{2,}(?:\.\d+)?|\d(?:\.\d+)?%)(?:%)?(?![A-Za-z0-9])"
)
_VISUAL_REQUEST_RE = re.compile(
    r"\b(?:chart|graph|plot|infographic|visualization)\b|\bfigure\s+\d+\b",
    re.IGNORECASE,
)
_NUMERIC_REQUEST_RE = re.compile(
    r"\b(?:how many|how much|number|total|count|amount|rate|value|revenue|profit|emissions?|employees?|fleet|trucks?|vehicles?|warehouses?|parcels?|percentage|percent|capex|ebitda)\b|[%$€£]",
    re.IGNORECASE,
)


def _numeric_values(text: str) -> list[str]:
    values = []
    for match in _ANSWER_NUMBER_RE.findall(text):
        value = match.replace(",", "")
        if re.fullmatch(r"(?:19|20)\d{2}", value):
            continue
        values.append(value)
    return values


def _canonical_number(value: str) -> str:
    return value.replace(",", "").rstrip("%")


def _citation_supports_entity_amount(
    entity: str,
    amount: str,
    citation: Mapping[str, Any],
    evidence: Mapping[str, Any] | None,
) -> bool:
    hit = evidence.get(str(citation.get("evidence_id", "")), {}) if evidence else {}
    source = str(citation.get("source") or hit.get("source", ""))
    search_text = " ".join(
        str(value or "")
        for value in (
            hit.get("evidence"),
            hit.get("context"),
            citation.get("quote"),
        )
    )
    target = _canonical_number(amount)
    entity_fold = entity.casefold()

    if source == "table_row" and hit:
        assignments: list[tuple[str, str]] = []
        for piece in re.split(r"\s*\|\s*", str(hit.get("evidence", ""))):
            if "=" in piece:
                key, value = piece.split("=", 1)
                assignments.append((key.strip(), value.strip()))
        # A value in an entity-named column (for example, Indonesia=44) is
        # directly attributable to that entity. Aggregate columns such as Total
        # remain distinct even when they share the same table row.
        aggregate_words = {"total", "overall", "all", "group", "grand total", "global"}
        if any(
            entity_fold in key.casefold()
            and not any(word in key.casefold() for word in aggregate_words)
            and target in {_canonical_number(value) for value in _numeric_values(value)}
            for key, value in assignments
        ):
            return True
        # In record-oriented tables, Country=Indonesia can identify a row whose
        # separately labeled metric value belongs to that country.
        entity_fields = {
            value.casefold()
            for key, value in assignments
            if key.casefold() in {"country", "market", "location", "region", "business unit"}
        }
        if entity_fold in entity_fields:
            return any(
                target in {_canonical_number(value) for value in _numeric_values(field_value)}
                and not any(word in key.casefold() for word in aggregate_words)
                for key, field_value in assignments
            )
        return False

    # Prose and row-based OCR must keep the requested entity near the value in
    # the same sentence/group; a global value elsewhere in the citation is not
    # attributed to the entity by mere co-occurrence.
    for sentence in re.split(r"[.!?;\n]", search_text):
        if entity_fold not in sentence.casefold():
            continue
        for match in _ANSWER_NUMBER_RE.finditer(sentence):
            found = _canonical_number(match.group(0))
            if found != target:
                continue
            entity_pos = sentence.casefold().find(entity_fold)
            if abs(match.start() - entity_pos) <= 48:
                return True
    return False


def validate_answer_constraints(
    question: str,
    response: Mapping[str, Any],
    evidence_by_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Fail closed on answer facts that violate explicit visual/entity scope.

    `evidence_by_id` maps each evidence ID to the same hit dict used to build
    the model prompt. The helper is deterministic and can replay recorded model
    answers without invoking Ollama. It returns a new response dict.
    """
    result = dict(response)
    status = result.get("status")
    answer = str(result.get("answer", "")).strip()
    citations = [citation for citation in result.get("citations", []) if isinstance(citation, Mapping)]
    if status == "abstained":
        result["answer"] = answer or "I could not find enough evidence in the retrieved excerpts to answer."
        result["citations"] = []
        return result
    if status != "answered":
        return result

    reasons: list[str] = []
    answer_numbers = _numeric_values(answer)
    if _VISUAL_REQUEST_RE.search(question):
        visual_citations = [citation for citation in citations if str(citation.get("source", "")).startswith("rapidocr_")]
        visual_quotes = " ".join(str(citation.get("quote", "")) for citation in visual_citations)
        if not visual_citations:
            reasons.append("The question explicitly asks about a visual, but no visual OCR citation supports the answer.")
        elif any(
            _canonical_number(number) not in {_canonical_number(value) for value in _numeric_values(visual_quotes)}
            for number in answer_numbers
        ):
            reasons.append("At least one numeric answer is not present in the cited visual OCR excerpts.")
        requested_quarters = [quarter.upper() for quarter in re.findall(r"\bQ[1-4]\b", question, re.IGNORECASE)]
        if requested_quarters and any(quarter not in visual_quotes.upper() for quarter in requested_quarters):
            reasons.append("The requested quarter label is missing from the visual OCR citations.")

    entity_match = re.search(
        r"^\s*for\s+([A-Z][A-Za-z'’.-]*(?:\s+[A-Z][A-Za-z'’.-]*){0,3})\s*,",
        question,
        re.IGNORECASE,
    )
    if entity_match and _NUMERIC_REQUEST_RE.search(question):
        entity = entity_match.group(1).strip()
        if not answer_numbers:
            reasons.append("The entity-scoped numeric question received no cited numeric answer.")
        else:
            for number in answer_numbers:
                if not any(
                    _citation_supports_entity_amount(entity, number, citation, evidence_by_id)
                    for citation in citations
                ):
                    reasons.append(f"The answer value {number} is not tied to {entity} in its cited evidence.")

    if reasons:
        result["status"] = "abstained"
        result["answer"] = "I could not verify the requested visual or entity-specific value in the cited evidence."
        result["citations"] = []
        result["diagnostics"] = {
            **dict(result.get("diagnostics", {})),
            "post_validation_reasons": reasons,
            "related_candidates": [dict(citation) for citation in citations],
        }
    return result


@dataclass
class EvidenceUnit:
    id: str
    page: int
    text: str
    source: str = "text"
    block: int | None = None
    context: str | None = None
    citation_quote: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    retrieval_text: str | None = None


def _tokens(text: str) -> list[str]:
    result: list[str] = []
    for match in _TOKEN_RE.findall(text.lower()):
        token = match.strip(".,")
        if token in _STOP_WORDS or len(token) < 2:
            continue
        # Small, conservative normalization helps plural and inflected forms
        # meet without depending on a language model or an extra NLP package.
        if token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("ing") and len(token) > 5:
            token = token[:-3]
        elif token.endswith("ed") and len(token) > 4:
            token = token[:-2]
        elif token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
            token = token[:-1]
        result.append(token)
    return result


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _query_aware_ocr_text(query: str, text: str) -> str:
    """Let search terms match words fused together by OCR, without indexing coordinates."""
    base_tokens = _tokens(text)
    base_set = set(base_tokens)
    embedded = {
        term
        for term in _tokens(query)
        if term not in base_set and any(len(token) > len(term) + 1 and term in token for token in base_tokens)
    }
    return f"{text} {' '.join(sorted(embedded))}" if embedded else text


def _bm25(query: str, documents: list[str]) -> list[float]:
    """A small BM25 implementation with no network or model dependency."""
    if not documents:
        return []
    tokenized = [_tokens(doc) for doc in documents]
    qterms = list(dict.fromkeys(_tokens(query)))
    if not qterms:
        return [0.0] * len(documents)
    df: Counter[str] = Counter()
    frequencies = [Counter(doc) for doc in tokenized]
    for term in qterms:
        df[term] = sum(term in freq for freq in frequencies)
    avgdl = sum(map(len, tokenized)) / max(1, len(tokenized))
    k1, b = 1.5, 0.75
    scores: list[float] = []
    for tokens, tf in zip(tokenized, frequencies):
        dl = len(tokens)
        score = 0.0
        for term in qterms:
            count = tf.get(term, 0)
            if not count:
                continue
            # BM25+ style positive IDF keeps rare-term matches rankable.
            idf = math.log(1 + (len(documents) - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * (count * (k1 + 1)) / (count + k1 * (1 - b + b * dl / max(avgdl, 1)))
        scores.append(score)
    return scores


class DocumentQA:
    """Extract and search PDF evidence, then answer with validated citations.

    Ollama generation and visual OCR are optional. Without a configured model,
    answers are intentionally extractive: the cited evidence is also the answer.
    """

    def __init__(
        self,
        pdf_path: str | Path,
        *,
        model_config: dict[str, Any] | None = None,
        ocr_visuals: bool = False,
    ) -> None:
        self.pdf_path = Path(pdf_path)
        self.model_config = dict(model_config or {})
        self.ocr_visuals = ocr_visuals
        self.units: list[EvidenceUnit] = []
        self._ocr_engine: Any = None
        self.pages: list[dict[str, Any]] = []
        self._page_texts: list[str] = []
        self._boilerplate_terms: set[str] = set()
        self._load()

    @classmethod
    def from_pdf(
        cls,
        path: str | Path,
        *,
        model_config: dict[str, Any] | None = None,
        ocr_visuals: bool = False,
    ) -> "DocumentQA":
        return cls(path, model_config=model_config, ocr_visuals=ocr_visuals)

    def _load(self) -> None:
        if not self.pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        footer_pages: list[set[str]] = []
        with fitz.open(self.pdf_path) as doc:
            self.page_count = len(doc)
            for page_index, page in enumerate(doc):
                page_num = page_index + 1
                raw_text = page.get_text("text", sort=True)
                blocks = page.get_text("blocks", sort=True)
                image_rects = self._image_rects(page)
                # Text and image geometry are reported for every physical page.
                # A digital footer alone is not treated as useful body evidence.
                body_blocks: list[tuple[int, str, float]] = []
                footer_tokens: set[str] = set()
                for block_index, block in enumerate(blocks):
                    if len(block) < 5 or not isinstance(block[4], str):
                        continue
                    text = _compact(block[4])
                    if text and float(block[1]) > page.rect.height * 0.92:
                        footer_tokens.update(_tokens(text))
                    if not text or float(block[1]) > page.rect.height * 0.92:
                        continue
                    body_blocks.append((block_index, text, float(block[1])))
                footer_pages.append(footer_tokens)
                body_chars = sum(len(text) for _, text, _ in body_blocks)
                table_headers = self._table_headers(body_blocks)
                page_units_before = len(self.units)
                for block_index, text, _ in body_blocks:
                    # Keep a PDF text block intact: it is the most reliable
                    # citation boundary for nearby labels, paragraphs, and rows.
                    for piece in self._split_block(text):
                        if len(piece) < 2:
                            continue
                        self.units.append(
                            EvidenceUnit(
                                id=f"P{page_num}-B{block_index}-{len(self.units) - page_units_before + 1}",
                                page=page_num,
                                text=piece,
                                source="text",
                                block=block_index,
                                context=table_headers.get(block_index),
                                bbox=tuple(float(x) for x in blocks[block_index][:4]),
                            )
                        )
                self._add_table_units(page, page_num)
                ocr_ok = False
                ocr_error: str | None = None
                if self.ocr_visuals and image_rects:
                    for image_index, rect in enumerate(image_rects, 1):
                        try:
                            ocr_units = self._ocr_image(page, rect, page_num, image_index)
                            self.units.extend(ocr_units)
                            ocr_ok = ocr_ok or bool(ocr_units)
                        except Exception as exc:  # OCR is optional and should not block text QA.
                            ocr_error = str(exc)[:240]
                            break
                visual_area = sum(max(0.0, r.width) * max(0.0, r.height) for r in image_rects)
                visual_ratio = min(1.0, visual_area / max(page.rect.width * page.rect.height, 1.0))
                if ocr_ok:
                    coverage = "text_plus_ocr_visuals_unverified"
                elif image_rects and (visual_ratio >= 0.06 or body_chars < 250):
                    coverage = "text_extracted_visuals_not_ocr"
                elif body_chars:
                    coverage = "text_extracted"
                else:
                    coverage = "no_body_text_detected"
                self.pages.append(
                    {
                        "page": page_num,
                        "status": coverage,
                        "body_chars": body_chars,
                        "image_count": len(image_rects),
                        "visual_area_ratio": round(visual_ratio, 3),
                        "ocr_error": ocr_error,
                        "unit_count": len(self.units) - page_units_before,
                    }
                )
                # Full-page text for baseline ranking includes the physical
                # page's extracted text. It still never merges page numbers.
                self._page_texts.append(_compact(" ".join(text for _, text, _ in body_blocks)))
        footer_term_counts = Counter(term for terms in footer_pages for term in terms)
        repeated_footer_threshold = max(2, math.ceil(self.page_count * 0.4))
        self._boilerplate_terms = {
            term for term, count in footer_term_counts.items() if count >= repeated_footer_threshold
        }
        if not self.pages:
            raise ValueError(f"The PDF has no readable pages: {self.pdf_path}")

    @staticmethod
    def _image_rects(page: fitz.Page) -> list[fitz.Rect]:
        rects: list[fitz.Rect] = []
        seen: set[tuple[int, int, int, int]] = set()
        for image in page.get_images(full=True):
            for rect in page.get_image_rects(image[0]):
                # Round geometry to avoid duplicate placements differing by tiny floats.
                key = tuple(round(value * 2) for value in rect)
                if key in seen or rect.is_empty:
                    continue
                seen.add(key)
                rects.append(rect)
        return sorted(rects, key=lambda r: (r.y0, r.x0))

    @staticmethod
    def _table_headers(blocks: list[tuple[int, str, float]]) -> dict[int, str]:
        """Associate each pipe-delimited row with nearby header blocks."""
        row_indexes = [i for i, (_, text, _) in enumerate(blocks) if text.count("|") >= 2]
        contexts: dict[int, str] = {}
        if not row_indexes:
            return contexts
        groups: list[list[int]] = []
        for index in row_indexes:
            if groups and index == groups[-1][-1] + 1 and blocks[index][2] - blocks[groups[-1][-1]][2] <= 35:
                groups[-1].append(index)
            else:
                groups.append([index])
        for group in groups:
            first = group[0]
            header_indexes = [first]
            # For a single data row, include a preceding table header if it is
            # physically close and contains multiple column separators.
            previous = first - 1
            if previous >= 0 and blocks[first][2] - blocks[previous][2] <= 35:
                previous_text = blocks[previous][1]
                if previous_text.count("|") >= 2:
                    header_indexes.insert(0, previous)
            if len(group) > 1:
                header_indexes = [group[0]]
            header = " | ".join(blocks[i][1] for i in header_indexes)
            for index in group:
                # The citation remains the exact row block; this context helps
                # the model align fields without fabricating a merged quote.
                if index != header_indexes[0]:
                    contexts[blocks[index][0]] = header
        return contexts

    @staticmethod
    def _normalize_cell_text(text: str) -> str:
        text = _compact(text)
        # Correct line-wrap artifacts inside numeric cells without guessing a
        # missing digit or changing the value represented by the PDF text.
        text = re.sub(r"(?<=\d)\s*,\s*(?=\d)", ",", text)
        text = re.sub(r"(?<=\d)\s*,\s*$", "", text)
        return text

    def _add_table_units(self, page: fitz.Page, page_num: int) -> None:
        """Build header-keyed row evidence from native vector table geometry."""
        try:
            tables = page.find_tables(strategy="lines").tables
        except (AttributeError, TypeError, RuntimeError):
            return
        for table_index, table in enumerate(tables, 1):
            rows = list(table.rows)
            if len(rows) < 2:
                continue
            def read_cells(row: Any) -> list[str]:
                cells: list[str] = []
                for cell in row.cells:
                    if not cell:
                        cells.append("")
                        continue
                    try:
                        cell_text = page.get_text("text", clip=fitz.Rect(cell), sort=True)
                    except Exception:
                        cell_text = ""
                    cells.append(self._normalize_cell_text(cell_text))
                return cells

            header_values = read_cells(rows[0])
            if not any(header_values):
                header_values = [self._normalize_cell_text(str(value or "")) for value in getattr(table.header, "names", [])]
            if not header_values:
                continue
            table_title = ""
            table_top = float(table.bbox[1])
            for block in page.get_text("blocks", sort=True):
                if len(block) < 5 or not isinstance(block[4], str):
                    continue
                block_text = _compact(block[4])
                block_bottom = float(block[3])
                if 0 <= table_top - block_bottom <= 32 and 4 <= len(block_text) <= 180:
                    table_title = block_text
            header_excerpt = self._normalize_cell_text(
                page.get_text("text", clip=fitz.Rect(rows[0].bbox), sort=True)
            )
            header_structured = "Table columns: " + " | ".join(
                f"{name or f'column_{index + 1}'}" for index, name in enumerate(header_values)
            )
            if table_title:
                header_structured = f"{table_title} | {header_structured}"
            header_unit = EvidenceUnit(
                id=f"P{page_num}-T{table_index}-H",
                page=page_num,
                text=header_structured,
                source="table_header",
                block=None,
                citation_quote=header_excerpt or " | ".join(header_values),
                bbox=tuple(float(value) for value in rows[0].bbox),
            )
            self.units.append(header_unit)
            for row_index, row in enumerate(rows[1:], 1):
                values = read_cells(row)
                if not any(values):
                    continue
                pairs = []
                for column_index, value in enumerate(values):
                    if not value:
                        continue
                    label = header_values[column_index] if column_index < len(header_values) else ""
                    if label:
                        pairs.append(f"{label}={value}")
                    else:
                        pairs.append(value)
                if not pairs:
                    continue
                native_excerpt = self._normalize_cell_text(
                    page.get_text("text", clip=fitz.Rect(row.bbox), sort=True)
                )
                if not native_excerpt:
                    native_excerpt = " | ".join(values)
                row_text = f"Table row: {' | '.join(pairs)}"
                if table_title:
                    row_text = f"{table_title} | {row_text}"
                self.units.append(
                    EvidenceUnit(
                        id=f"P{page_num}-T{table_index}-R{row_index}",
                        page=page_num,
                        text=row_text,
                        source="table_row",
                        block=None,
                        context=header_structured,
                        citation_quote=native_excerpt,
                        bbox=tuple(float(value) for value in row.bbox),
                    )
                )

    @staticmethod
    def _split_block(text: str, limit: int = 700) -> list[str]:
        if len(text) <= limit:
            return [text]
        # Long text blocks are split on sentence or row boundaries first.
        pieces: list[str] = []
        current = ""
        for fragment in re.split(r"(?<=[.!?])\s+", text):
            if not fragment:
                continue
            candidate = f"{current} {fragment}".strip()
            if current and len(candidate) > limit:
                pieces.append(current)
                current = fragment
            else:
                current = candidate
        if current:
            pieces.append(current)
        # Avoid a single oversized fragment (for example, a scanned OCR table).
        out: list[str] = []
        for piece in pieces:
            while len(piece) > limit:
                cut_at = piece.rfind(" ", 0, limit)
                if cut_at <= 0:
                    cut_at = limit
                out.append(piece[:cut_at])
                piece = piece[cut_at:].lstrip()
            if piece:
                out.append(piece)
        return out

    def _ollama_url(self, endpoint: str) -> str:
        base = str(self.model_config.get("base_url", "http://localhost:11434")).rstrip("/")
        return f"{base}{endpoint}"

    def _ollama_request(self, payload: dict[str, Any], endpoint: str = "/api/generate") -> dict[str, Any]:
        model = self.model_config.get("model")
        if not model:
            raise ValueError("model_config requires an Ollama 'model' value")
        payload = {"model": model, "stream": False, **payload}
        req = urllib.request.Request(
            self._ollama_url(endpoint),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        timeout = float(self.model_config.get("timeout", 90))
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body

    def _ocr_image(self, page: fitz.Page, rect: fitz.Rect, page_num: int, image_index: int) -> list[EvidenceUnit]:
        try:
            from rapidocr_onnxruntime import RapidOCR
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("Optional OCR is unavailable; install with `uv sync --extra ocr`.") from exc
        if self._ocr_engine is None:
            self._ocr_engine = RapidOCR()
        scale = 1.35
        result: Any = None
        last_error: Exception | None = None
        for attempt in range(3):
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
            pixel_count = pix.width * pix.height
            if pixel_count > 900_000:
                adjusted_scale = scale * math.sqrt(900_000 / pixel_count)
                pix = page.get_pixmap(matrix=fitz.Matrix(adjusted_scale, adjusted_scale), clip=rect, alpha=False)
            image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            # RapidOCR expects contiguous BGR input. Bound memory and retry
            # downscaled scans if ONNX Runtime cannot allocate the first image.
            image = np.ascontiguousarray(image[:, :, ::-1])
            try:
                result = self._ocr_engine(image)
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                if attempt == 2:
                    raise RuntimeError(f"OCR failed after downscaled retries: {exc}") from exc
                scale *= 0.68
        if last_error:
            raise RuntimeError(f"OCR failed: {last_error}") from last_error
        if isinstance(result, tuple):
            result = result[0]
        if not result:
            return "", ""
        found: list[dict[str, Any]] = []
        for item in result:
            try:
                polygon, text, confidence = item
                if float(confidence) < 0.2 or not str(text).strip():
                    continue
                xs = [float(point[0]) for point in polygon]
                ys = [float(point[1]) for point in polygon]
                left_y = (ys[0] + ys[3]) / 2
                right_y = (ys[1] + ys[2]) / 2
                left_x = (xs[0] + xs[3]) / 2
                right_x = (xs[1] + xs[2]) / 2
                if abs(right_x - left_x) > 1:
                    slope = (right_y - left_y) / (right_x - left_x)
                else:
                    slope = 0.0
                x0, x1 = min(xs), max(xs)
                y0, y1 = min(ys), max(ys)
                center_x = (x0 + x1) / 2
                center_y = (y0 + y1) / 2
                found.append(
                    {
                        "x0": x0,
                        "x1": x1,
                        "y0": y0,
                        "y1": y1,
                        "cx": center_x,
                        "cy": center_y,
                        "height": max(1.0, y1 - y0),
                        "slope": slope,
                        "text": _compact(str(text)),
                    }
                )
            except (TypeError, ValueError, IndexError):
                continue
        if not found:
            return []

        # Estimate the scan's common baseline slope from OCR quadrilaterals,
        # then cluster by de-skewed vertical centers. This keeps price and
        # service labels on the same physical table row despite a tilted scan.
        slopes = sorted(item["slope"] for item in found if abs(item["slope"]) < 0.15)
        slope = slopes[len(slopes) // 2] if slopes else 0.0
        median_height = sorted(item["height"] for item in found)[len(found) // 2]
        row_tolerance = max(4.0, median_height * 0.65)
        for item in found:
            item["deskew_y"] = item["cy"] - slope * item["cx"]
        found.sort(key=lambda item: (item["deskew_y"], item["x0"]))
        rows: list[dict[str, Any]] = []
        for item in found:
            nearest = min(rows, key=lambda row: abs(row["center"] - item["deskew_y"]), default=None)
            if nearest is None or abs(nearest["center"] - item["deskew_y"]) > row_tolerance:
                rows.append({"center": item["deskew_y"], "items": [item]})
            else:
                nearest["items"].append(item)
                nearest["center"] = sum(value["deskew_y"] for value in nearest["items"]) / len(nearest["items"])
        for row in rows:
            row["items"].sort(key=lambda item: item["x0"])

        def spatial_text(items: list[dict[str, Any]], row_label: str) -> str:
            parts = [
                f"[x={item['x0'] / pix.width:.3f}-{item['x1'] / pix.width:.3f}, "
                f"y={item['y0'] / pix.height:.3f}-{item['y1'] / pix.height:.3f}] {item['text']}"
                for item in items
            ]
            return f"OCR {row_label}; baseline slope={slope:.4f}: " + " | ".join(parts)

        def page_bbox(items: list[dict[str, Any]]) -> tuple[float, float, float, float]:
            x0 = min(item["x0"] for item in items) / pix.width
            x1 = max(item["x1"] for item in items) / pix.width
            y0 = min(item["y0"] for item in items) / pix.height
            y1 = max(item["y1"] for item in items) / pix.height
            return (
                rect.x0 + x0 * rect.width,
                rect.y0 + y0 * rect.height,
                rect.x0 + x1 * rect.width,
                rect.y0 + y1 * rect.height,
            )

        units: list[EvidenceUnit] = []
        for row_index, row in enumerate(rows, 1):
            items = row["items"]
            quote = " | ".join(item["text"] for item in items)
            units.append(
                EvidenceUnit(
                    id=f"P{page_num}-OCR{image_index}-R{row_index}",
                    page=page_num,
                    text=spatial_text(items, f"same-row group {row_index}"),
                    source="rapidocr_row",
                    citation_quote=quote,
                    bbox=page_bbox(items),
                    retrieval_text=quote,
                )
            )

        # Short, grid-like visuals often separate category labels from values
        # vertically (charts and KPI cards). Add column-aligned evidence only
        # for compact layouts; large scans are handled by the de-skewed rows.
        if len(rows) <= 8:
            column_tolerance = max(12.0, pix.width * 0.12)
            columns: list[list[dict[str, Any]]] = []
            for item in sorted(found, key=lambda candidate: candidate["cx"]):
                nearest = min(columns, key=lambda col: abs(sum(x["cx"] for x in col) / len(col) - item["cx"]), default=None)
                if nearest is None or abs(sum(x["cx"] for x in nearest) / len(nearest) - item["cx"]) > column_tolerance:
                    columns.append([item])
                else:
                    nearest.append(item)
            column_index = 0
            for column in columns:
                numbers = [item for item in column if re.fullmatch(r"[\d][\d,]*(?:\.\d+)?%?", item["text"].replace(" ", ""))]
                labels = [item for item in column if re.search(r"[A-Za-z]", item["text"]) and item not in numbers]
                pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
                for label in labels:
                    nearby = [value for value in numbers if abs(value["deskew_y"] - label["deskew_y"]) > row_tolerance]
                    if len(nearby) == 1:
                        pairs.append((label, nearby[0]))
                if not pairs:
                    continue
                # Keep the nearest label/value pair in this x-aligned column.
                label, value = min(pairs, key=lambda pair: abs(pair[0]["deskew_y"] - pair[1]["deskew_y"]))
                column_index += 1
                column_items = sorted((label, value), key=lambda item: (item["deskew_y"], item["x0"]))
                units.append(
                    EvidenceUnit(
                        id=f"P{page_num}-OCR{image_index}-C{column_index}",
                        page=page_num,
                        text=spatial_text(column_items, f"x-aligned value/category group {column_index}"),
                        source="rapidocr_column",
                        citation_quote=f"{value['text']} | {label['text']}",
                        bbox=page_bbox(column_items),
                        retrieval_text=f"{value['text']} {label['text']}",
                    )
                )
        return units

    def _score(self, question: str, strategy: str) -> list[dict[str, Any]]:
        if strategy not in {"baseline", "structured"}:
            raise ValueError("strategy must be 'baseline' or 'structured'")
        if not self.units:
            return []
        if strategy == "baseline":
            scores = _bm25(question, self._page_texts)
            block_scores = _bm25(
                question,
                [
                    _query_aware_ocr_text(question, unit.retrieval_text or unit.text)
                    if unit.source.startswith("rapidocr") else unit.text
                    for unit in self.units
                ],
            )
            best_unit_by_page: dict[int, tuple[float, EvidenceUnit]] = {}
            for unit, unit_score in zip(self.units, block_scores):
                previous = best_unit_by_page.get(unit.page)
                if previous is None or unit_score > previous[0]:
                    best_unit_by_page[unit.page] = (unit_score, unit)
            candidates: list[dict[str, Any]] = []
            for page_index, score in enumerate(scores):
                if score <= 0:
                    continue
                page_num = page_index + 1
                best = best_unit_by_page.get(page_num)
                if best is None:
                    continue
                candidates.append(self._hit(best[1], score, "baseline"))
            return sorted(candidates, key=lambda hit: (-hit["score"], hit["page"]))

        unit_scores = _bm25(
            question,
            [
                _query_aware_ocr_text(question, unit.retrieval_text or unit.text)
                if unit.source.startswith("rapidocr") else unit.text
                for unit in self.units
            ],
        )
        page_scores = _bm25(question, self._page_texts)
        max_page_score = max(page_scores, default=0.0) or 1.0
        candidates = []
        qtokens = set(_tokens(question))
        for unit, unit_score in zip(self.units, unit_scores):
            page_score = page_scores[unit.page - 1] if unit.page <= len(page_scores) else 0.0
            score = unit_score + 0.18 * page_score / max_page_score
            text_tokens = set(_tokens(unit.text))
            # Prefer correction statements only when they concern the query.
            if _CORRECTION_RE.search(unit.text) and qtokens.intersection(text_tokens):
                score += 1.6
            # Prefer a cell-aligned row over the same row's flattened text
            # block when both match. The structured record retains which value
            # belongs to which year, country, or metric column.
            if unit.source == "table_row":
                score += 1.5
            if unit.source.startswith("rapidocr") and qtokens.intersection(
                _tokens(_query_aware_ocr_text(question, unit.retrieval_text or unit.text))
            ):
                score += 1.1
            # A title or table-label block can aid retrieval, but should not
            # displace a matching data row; this is only a small tie-breaker.
            if len(unit.text) < 100 and qtokens.intersection(text_tokens):
                score -= 0.15
            if score <= 0:
                continue
            candidates.append(self._hit(unit, score, "structured"))
        candidates.sort(key=lambda hit: (-hit["score"], hit["page"], hit["id"]))
        # Return no duplicate pages: `top_k` is a page count in the public API.
        unique: list[dict[str, Any]] = []
        seen_pages: set[int] = set()
        for candidate in candidates:
            if candidate["page"] in seen_pages:
                continue
            unique.append(candidate)
            seen_pages.add(candidate["page"])
        return unique

    @staticmethod
    def _hit(unit: EvidenceUnit, score: float, strategy: str) -> dict[str, Any]:
        return {
            "id": unit.id,
            "page": int(unit.page),
            "score": round(float(score), 6),
            "evidence": unit.text,
            "quote": unit.citation_quote or unit.text,
            "source": unit.source,
            "context": unit.context,
            "bbox": unit.bbox,
            "strategy": strategy,
        }

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        strategy: str = "structured",
    ) -> list[dict[str, Any]]:
        if not question.strip():
            return []
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        return self._score(question, strategy)[:top_k]

    def answer_evidence(
        self,
        question: str,
        top_k: int = 5,
        strategy: str = "structured",
    ) -> dict[str, dict[str, Any]]:
        """Return the exact ID-indexed evidence bundle used by model answering.

        This makes `validate_answer_constraints(question, response,
        qa.answer_evidence(question))` reproducible without calling the model.
        """
        hits = self.retrieve(question, top_k=top_k, strategy=strategy)
        return {hit["id"]: hit for hit in self._expanded_evidence(question, hits)}

    def _has_support(self, question: str, hits: list[dict[str, Any]]) -> bool:
        if not hits:
            return False
        qterms = set(_tokens(question))
        qterms.difference_update(self._boilerplate_terms)
        qterms.difference_update({term for term in qterms if re.fullmatch(r"(?:19|20)\d{2}", term)})
        if not qterms:
            return False
        # Require a discriminating term in one evidence unit. A company name,
        # report boilerplate, or year by itself is not enough to answer.
        for hit in hits[:3]:
            overlap = qterms.intersection(_tokens(hit["evidence"]))
            if overlap and len(overlap) / max(1, len(qterms)) >= 0.4:
                return True
        return False

    def _extractive_terms(self, question: str) -> set[str]:
        terms = set(_tokens(question))
        terms.difference_update(self._boilerplate_terms)
        terms.difference_update(
            {
                "full", "year", "many", "number", "amount", "percentage", "percent",
                "figure", "value", "make", "made", "provide", "give", "tell", "show",
            }
        )
        # A date alone does not distinguish a fact from the cover or footer.
        if terms and all(re.fullmatch(r"(?:19|20)\d{2}", term) for term in terms):
            return set()
        if "plann" in terms:
            terms.remove("plann")
            terms.add("plan")
        return terms

    @staticmethod
    def _role_requested(question: str) -> tuple[str, str] | None:
        roles = (
            ("cfo", r"\b(?:CFO|chief financial officer)\b"),
            ("ceo", r"\b(?:CEO|chief executive officer)\b"),
            ("coo", r"\b(?:COO|chief operating officer)\b"),
            ("cto", r"\b(?:CTO|chief technology officer)\b"),
            ("chair", r"\b(?:chair(?:man|person)?|board chair)\b"),
            ("president", r"\bpresident\b"),
            ("director", r"\bdirector\b"),
            ("founder", r"\bfounder\b"),
        )
        for name, pattern in roles:
            if re.search(pattern, question, re.IGNORECASE):
                return name, pattern
        return None

    @staticmethod
    def _role_has_named_association(text: str, role_pattern: str) -> bool:
        for match in re.finditer(role_pattern, text, re.IGNORECASE):
            after = text[match.end() : match.end() + 72]
            before = text[max(0, match.start() - 72) : match.start()]
            after_match = re.search(
                r"^\s*(?:(?:is|was|named|appointed|:|,)\s*)?(?:Mr\.?|Ms\.?|Dr\.?\s+)?"
                r"([A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+){0,2})\b",
                after,
            )
            before_match = re.search(
                r"\b([A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+){0,2})\s*(?:,|is|was|:)?\s*$",
                before,
            )
            candidate = after_match.group(1) if after_match else (before_match.group(1) if before_match else "")
            if candidate and candidate.lower().split()[0] not in {
                "our", "the", "chief", "executive", "financial", "operating", "technology", "board"
            }:
                return True
        return False

    def _direct_extractive_hit(self, question: str, hits: list[dict[str, Any]]) -> dict[str, Any] | None:
        terms = self._extractive_terms(question)
        if not terms or not hits:
            return None
        year_terms = {term for term in terms if re.fullmatch(r"(?:19|20)\d{2}", term)}
        role = self._role_requested(question)
        ignored_number_labels = {
            "which", "what", "how", "many", "number", "top", "first", "last", "only",
            "more", "less", "than", "the", "in", "on", "by", "for", "at", "no", "and", "or",
        }
        requested_numeric_labels = [
            (label, digit)
            for label, digit in re.findall(r"\b([A-Za-z][A-Za-z_-]*)\s+([1-9])\b", question)
            if label.lower() not in ignored_number_labels
        ]
        for hit in hits[:3]:
            # Extractive mode cannot safely resolve spatial alignments. Preserve
            # OCR candidates for inspection and let the local model reason over
            # their normalized coordinates when one is configured.
            if hit.get("source") == "rapidocr_column":
                continue
            support_text = " ".join((hit["evidence"], hit.get("context") or ""))
            evidence_terms = set(_tokens(support_text))
            if "plann" in evidence_terms:
                evidence_terms.remove("plann")
                evidence_terms.add("plan")
            # The shared tokenizer intentionally drops one-digit tokens. Keep
            # compound labels such as Scope 1 / Scope 2 aligned in extractive
            # mode so a neighboring row cannot satisfy the wrong category.
            if any(
                not re.search(rf"\b{re.escape(label)}\s*[- ]?\s*{digit}\b", support_text, re.IGNORECASE)
                for label, digit in requested_numeric_labels
            ):
                continue
            if not terms.issubset(evidence_terms):
                continue
            # Time and reporting-status words are hard constraints: an actual
            # year must not be answered with a plan from another period.
            status_terms = terms.intersection(
                {"actual", "plan", "planned", "forecast", "target", "projected", "budget", "proposed"}
            )
            if not year_terms.issubset(evidence_terms) or not status_terms.issubset(evidence_terms):
                continue
            if role and not self._role_has_named_association(support_text, role[1]):
                continue
            return hit
        return None

    def _has_direct_extractive_match(self, question: str, hits: list[dict[str, Any]]) -> bool:
        return self._direct_extractive_hit(question, hits) is not None

    def ask(
        self,
        question: str,
        top_k: int = 5,
        strategy: str = "structured",
    ) -> dict[str, Any]:
        hits = self.retrieve(question, top_k=top_k, strategy=strategy)
        retrieved_pages = [hit["page"] for hit in hits]
        model_configured = bool(self.model_config.get("model"))
        # A configured model receives any nonempty retrieved evidence and makes
        # the semantic sufficiency decision itself. Offline mode uses the stricter
        # same-excerpt gate because it cannot resolve paraphrase or relationships.
        direct_hit = None if model_configured else self._direct_extractive_hit(question, hits)
        supported = bool(hits) if model_configured else direct_hit is not None
        if not supported:
            return self._refusal(
                hits,
                retrieved_pages,
                reason="No single excerpt contains the requested topic and any explicit time or role constraints.",
                mode="extractive_guard",
            )
        if self.model_config.get("model"):
            try:
                model_hits = self._expanded_evidence(question, hits)
                result = self._ask_ollama(question, model_hits)
                result = validate_answer_constraints(
                    question,
                    result,
                    evidence_by_id={hit["id"]: hit for hit in model_hits},
                )
                result["retrieved_pages"] = retrieved_pages
                result["mode"] = "ollama"
                return result
            except urllib.error.URLError as exc:
                # Keep working offline when Ollama is absent or still downloading.
                if not self._has_direct_extractive_match(question, hits):
                    return self._refusal(
                        hits,
                        retrieved_pages,
                        reason="The local model is unavailable and no direct extractive match was found.",
                        mode="extractive_guard",
                    )
                direct_hit = self._direct_extractive_hit(question, hits)
                result = self._extractive_answer([direct_hit], retrieved_pages, model_error=str(exc))
                return validate_answer_constraints(
                    question,
                    result,
                    evidence_by_id={direct_hit["id"]: direct_hit},
                )
            except (ValueError, json.JSONDecodeError) as exc:
                # A bad or ungrounded model response is a refusal, never a
                # license to return an unrelated lexical hit as an answer.
                return self._refusal(
                    hits,
                    retrieved_pages,
                    reason=f"The model did not return a verifiable answer: {exc}",
                    mode="grounding_guard",
                )
            except Exception as exc:
                return self._refusal(
                    hits,
                    retrieved_pages,
                    reason=f"The local model could not produce a safely validated answer: {exc}",
                    mode="grounding_guard",
                )
        result = self._extractive_answer([direct_hit], retrieved_pages)
        return validate_answer_constraints(
            question,
            result,
            evidence_by_id={direct_hit["id"]: direct_hit},
        )

    @staticmethod
    def _candidate_evidence(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "page": hit["page"],
                "evidence": hit["evidence"],
                "quote": hit["quote"],
                "source": hit["source"],
                "evidence_id": hit["id"],
            }
            for hit in hits[:3]
        ]

    def _refusal(
        self,
        hits: list[dict[str, Any]],
        retrieved_pages: list[int],
        *,
        reason: str,
        mode: str,
    ) -> dict[str, Any]:
        return {
            "status": "abstained",
            "answer": "I could not verify the requested fact in one supporting excerpt. Related passages are listed as candidates.",
            "citations": [],
            "retrieved_pages": retrieved_pages,
            "mode": mode,
            "diagnostics": {"reason": reason, "candidate_evidence": self._candidate_evidence(hits)},
        }

    def _extractive_answer(
        self,
        hits: list[dict[str, Any]],
        retrieved_pages: list[int],
        *,
        model_error: str | None = None,
    ) -> dict[str, Any]:
        best = hits[0]
        quote = best["quote"]
        citations = [
            {
                "page": best["page"],
                "quote": quote,
                "evidence_id": best["id"],
                "source": best["source"],
                "bbox": best.get("bbox"),
            }
        ]
        answer_text = f"The document states: “{best['evidence']}”"
        if best.get("context"):
            header_unit = next(
                (
                    unit for unit in self.units
                    if unit.page == best["page"] and unit.text == best["context"]
                ),
                None,
            )
            if header_unit is not None:
                answer_text += f" Table header: “{header_unit.text}”"
                citations.append(
                    {
                        "page": header_unit.page,
                        "quote": header_unit.citation_quote or header_unit.text,
                        "evidence_id": header_unit.id,
                        "source": header_unit.source,
                        "bbox": header_unit.bbox,
                    }
                )
        result: dict[str, Any] = {
            "status": "answered",
            "answer": answer_text,
            "citations": citations,
            "retrieved_pages": retrieved_pages,
            "mode": "extractive",
        }
        if model_error:
            result["diagnostics"] = {"model_error": model_error}
        return result

    @staticmethod
    def _quote_matches(quote: str, source: str) -> bool:
        normalized_quote = _compact(quote)
        substantial = len(normalized_quote) >= 8
        short_numeric = len(normalized_quote) >= 2 and len(re.findall(r"\d", normalized_quote)) >= 2
        short_chart_label = bool(re.fullmatch(r"[A-Za-z]{1,4}\d{1,2}", normalized_quote))
        return bool(normalized_quote and (substantial or short_numeric or short_chart_label) and normalized_quote in _compact(source))

    def _expanded_evidence(self, question: str, hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Pass multiple same-page blocks, including nearby table headers, to the LLM."""
        page_order = [hit["page"] for hit in hits]
        if not page_order:
            return []
        unit_scores = _bm25(
            question,
            [
                _query_aware_ocr_text(question, unit.retrieval_text or unit.text)
                if unit.source.startswith("rapidocr") else unit.text
                for unit in self.units
            ],
        )
        by_page: dict[int, list[tuple[float, EvidenceUnit]]] = {page: [] for page in page_order}
        for unit, score in zip(self.units, unit_scores):
            if unit.page in by_page and score > 0:
                by_page[unit.page].append((score, unit))
        for rows in by_page.values():
            rows.sort(key=lambda row: (-row[0], row[1].id))

        # First reserve one best-matching unit from every retrieved page. This
        # prevents a late-ranked chart or scanned page from disappearing behind
        # several paragraph fragments from early pages.
        by_id = {unit.id: unit for unit in self.units}
        # The public structured ranking can include layout boosts and table
        # associations. Preserve that selected unit instead of silently
        # replacing it with a raw-BM25 paragraph from the same page.
        primary = [by_id[hit["id"]] for hit in hits if hit.get("id") in by_id]
        primary_pages = {unit.page for unit in primary}
        for page in page_order:
            if page not in primary_pages and by_page[page]:
                primary.append(by_page[page][0][1])
        selected_ids = {unit.id for unit in primary}
        headers: list[EvidenceUnit] = []
        for unit in primary:
            if not unit.context:
                continue
            header = next(
                (other for other in self.units if other.page == unit.page and other.text == unit.context),
                None,
            )
            if header and header.id not in selected_ids:
                headers.append(header)
                selected_ids.add(header.id)
        extras: list[EvidenceUnit] = []
        for page in page_order:
            for _, unit in by_page[page][1:]:
                if unit.id not in selected_ids:
                    extras.append(unit)
                    selected_ids.add(unit.id)
                if len(primary) + len(headers) + len(extras) >= 12:
                    break
            if len(primary) + len(headers) + len(extras) >= 12:
                break
        ordered_units = primary + headers + extras

        expanded: list[dict[str, Any]] = []
        char_budget = max(1200, min(4200, int(self.model_config.get("num_ctx", 3072) * 1.3)))
        used_chars = 0
        for unit_index, unit in enumerate(ordered_units):
            if len(expanded) >= 12 or used_chars >= char_budget:
                break
            hit = self._hit(unit, 0.0, "structured")
            remaining = char_budget - used_chars
            remaining_primary_pages = max(0, len(primary) - unit_index - 1) if unit_index < len(primary) else 0
            reserve = min(500 * remaining_primary_pages, max(0, remaining - 500))
            quote_limit = 1000 if hit["source"] == "rapidocr_onnxruntime" else 600
            quote_reserve = min(len(hit["quote"]), quote_limit)
            evidence_limit = 1300 if hit["source"] == "rapidocr_onnxruntime" else 900
            max_evidence = min(evidence_limit, max(0, remaining - reserve - quote_reserve - 100))
            max_quote = min(quote_reserve, max(0, remaining - max_evidence - reserve - 80))
            if max_evidence < 80:
                continue
            if len(hit["evidence"]) > max_evidence:
                cut_at = hit["evidence"].rfind(" ", 0, max_evidence)
                hit["evidence"] = hit["evidence"][: cut_at if cut_at > 0 else max_evidence]
            if len(hit["quote"]) > max_quote:
                cut_at = hit["quote"].rfind(" ", 0, max_quote)
                hit["quote"] = hit["quote"][: cut_at if cut_at > 0 else max_quote]
            if hit.get("context"):
                hit["context"] = hit["context"][: min(220, max(0, remaining - len(hit["evidence"]) - len(hit["quote"]) - 80))]
            used_chars += len(hit["evidence"]) + len(hit["quote"]) + len(hit.get("context") or "") + 80
            expanded.append(hit)
        return expanded

    def _ask_ollama(self, question: str, hits: list[dict[str, Any]]) -> dict[str, Any]:
        evidence = "\n\n".join(
            f"[{hit['id']} | page {hit['page']} | {hit['source']} | bbox={hit.get('bbox')}] {hit['evidence']}"
            + f"\n  Source excerpt to quote exactly: {hit['quote']}"
            + (f"\n  Table context (cite its own matching block ID if needed): {hit['context']}" if hit.get("context") else "")
            for hit in hits
        )
        prompt = (
            "You answer questions using only the supplied PDF evidence. If it does not establish the answer, "
            "return status=abstained and explain the gap. Answer briefly with only the requested facts; explicit "
            "year, actual-versus-plan, and scope constraints must match. Treat errata, corrections, and later "
            "explicit correction notes as authoritative over earlier conflicting statements. Do not invent facts. "
            "Visual OCR rows are grouped using deskewed baselines; OCR column groups connect vertically aligned "
            "labels and values. Coordinates are normalized within the placed image crop. Use row, column, or card "
            "alignment only when the geometry supports it. If a value-to-label mapping is ambiguous, abstain. "
            "Every factual statement in an answer must be supported by at least one citation. Cite only evidence "
            "IDs below, and copy each quote exactly from the source excerpt for that ID, without coordinate prefixes. "
            "Return valid JSON only with "
            'this schema: {"status":"answered"|"abstained","answer":"...",'
            '"citations":[{"id":"EVIDENCE_ID","quote":"exact excerpt"}]}.\n\n'
            f"Question: {question}\n\nEvidence:\n{evidence}"
        )
        citation_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["answered", "abstained"]},
                "answer": {"type": "string"},
                "citations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "quote": {"type": "string"},
                        },
                        "required": ["id", "quote"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["status", "answer", "citations"],
            "additionalProperties": False,
        }
        options = {
            "temperature": 0,
            "num_ctx": int(self.model_config.get("num_ctx", 3072)),
            "num_predict": int(self.model_config.get("num_predict", 512)),
        }
        if self.model_config.get("num_gpu") is not None:
            options["num_gpu"] = int(self.model_config["num_gpu"])
        if self.model_config.get("num_thread") is not None:
            options["num_thread"] = int(self.model_config["num_thread"])
        result = self._ollama_request(
            {
                "prompt": prompt,
                "format": citation_schema,
                "options": options,
                "think": False,
            }
        )
        raw = str(result.get("response", ""))
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Ollama response was not a JSON object")
        status = parsed.get("status")
        answer = parsed.get("answer")
        if status not in {"answered", "abstained"} or not isinstance(answer, str):
            raise ValueError("Ollama response did not match the required answer schema")
        if status == "abstained":
            return {
                "status": "abstained",
                "answer": answer.strip() or "I could not find enough evidence in the retrieved excerpts to answer.",
                "citations": [],
            }
        allowed = {hit["id"]: hit for hit in hits}
        citations: list[dict[str, Any]] = []
        for citation in parsed.get("citations", []):
            if not isinstance(citation, dict):
                continue
            hit = allowed.get(str(citation.get("id", "")))
            quote = citation.get("quote")
            if hit is None or not isinstance(quote, str) or not self._quote_matches(quote, hit["quote"]):
                continue
            # Expose the normalized source wording only after substring validation.
            normalized_quote = _compact(quote)
            citations.append(
                {
                    "page": hit["page"],
                    "quote": normalized_quote,
                    "source": hit["source"],
                    "evidence_id": hit["id"],
                    "bbox": hit.get("bbox"),
                }
            )
        if not answer.strip() or not citations:
            raise ValueError("Ollama answer had no verifiable evidence citation")
        return {"status": "answered", "answer": answer.strip(), "citations": citations}

    def coverage_report(self) -> dict[str, Any]:
        return {
            "pdf": str(self.pdf_path),
            "page_count": self.page_count,
            "pages_with_evidence": sum(1 for page in self.pages if page["unit_count"] > 0),
            "pages_without_evidence": [page["page"] for page in self.pages if page["unit_count"] == 0],
            "pages": self.pages,
        }
