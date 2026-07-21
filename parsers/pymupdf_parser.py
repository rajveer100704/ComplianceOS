import time
import unicodedata
import os
import shutil
import re
import io
from datetime import datetime, timezone
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from parsers.base import BaseParser, ParserCapabilities

# Gracefully locate tesseract executable on Windows if not on PATH
if os.name == "nt" and not shutil.which("tesseract"):
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\BIT\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break


class PyMuPDFParser(BaseParser):
    """PDF parsing engine powered by PyMuPDF layout extraction and Tesseract OCR fallback."""

    @property
    def capabilities(self) -> ParserCapabilities:
        return ParserCapabilities(
            tables=True, ocr=True, layout=True, images=False, formulas=False
        )

    @property
    def version(self) -> str:
        return "1.0.0"

    def _extract_tables(self, page, page_num: int, warnings: list) -> list:
        tables_md = []
        try:
            tables = page.find_tables()
            for t in tables:
                bbox = t.bbox  # (x0, y0, x1, y1)
                df = t.to_pandas()

                # Convert pandas DF to clean GitHub style Markdown table manually
                cols = list(df.columns)
                header = "| " + " | ".join(str(c) for c in cols) + " |"
                divider = "| " + " | ".join("---" for _ in cols) + " |"
                rows = []
                for _, row in df.iterrows():
                    rows.append("| " + " | ".join(str(val) for val in row) + " |")
                table_md = "\n".join([header, divider] + rows)
                tables_md.append((bbox, table_md))
        except Exception as e:
            warnings.append(f"Table extraction failed on page {page_num}: {str(e)}")
        return tables_md

    def _extract_blocks(self, page, tables_md: list) -> str:
        blocks = page.get_text("blocks")
        filtered_blocks = []
        for b in blocks:
            # Check if block overlaps table bounding box
            is_inside_table = False
            for bbox, _ in tables_md:
                if (
                    b[0] >= bbox[0] - 2
                    and b[1] >= bbox[1] - 2
                    and b[2] <= bbox[2] + 2
                    and b[3] <= bbox[3] + 2
                ):
                    is_inside_table = True
                    break
            if not is_inside_table:
                filtered_blocks.append(b)

        # Sort blocks vertically, then horizontally with vertical tolerance (5px)
        filtered_blocks.sort(key=lambda b: (round(b[1] / 5) * 5, b[0]))

        page_text_parts = []
        for b in filtered_blocks:
            txt = b[4].strip()
            if txt:
                page_text_parts.append(txt)

        return "\n\n".join(page_text_parts)

    def _run_ocr_if_needed(
        self, page, page_text: str, page_num: int, warnings: list
    ) -> tuple[str, bool]:
        is_ocr = False
        if len(page_text.strip()) < 50:
            try:
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                ocr_text = pytesseract.image_to_string(img).strip()
                if ocr_text:
                    page_text = ocr_text
                    is_ocr = True
                    warnings.append(f"OCR fallback used on page {page_num}")
                else:
                    warnings.append(f"Page {page_num} contained no readable text")
            except Exception as e:
                warnings.append(f"OCR failed on page {page_num}: {str(e)}")
        return page_text, is_ocr

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text)
        lines = normalized.splitlines()
        cleaned_lines = [l.rstrip() for l in lines]
        cleaned_text = "\n".join(cleaned_lines)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
        cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
        return cleaned_text

    def parse(self, data: bytes, doc_name: str) -> tuple[str, dict]:
        start_time = time.perf_counter()
        warnings = []
        pages_content = []

        doc = fitz.open(stream=data, filetype="pdf")
        page_count = doc.page_count

        table_count = 0
        ocr_page_count = 0
        text_page_count = 0

        for page_num in range(page_count):
            page = doc[page_num]

            tables_md = self._extract_tables(page, page_num + 1, warnings)
            table_count += len(tables_md)

            page_text = self._extract_blocks(page, tables_md)

            page_text, is_ocr = self._run_ocr_if_needed(
                page, page_text, page_num + 1, warnings
            )
            if is_ocr:
                ocr_page_count += 1
            elif page_text.strip():
                text_page_count += 1

            if tables_md:
                page_text += "\n\n" + "\n\n".join(t[1] for t in tables_md) + "\n"

            cleaned_text = self._normalize_text(page_text)
            pages_content.append(cleaned_text)

        doc.close()

        full_text = "\n\n--- Page Break ---\n\n".join(pages_content)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        pages_per_second = (
            round(page_count / (elapsed_ms / 1000.0), 1)
            if elapsed_ms > 0
            else page_count
        )

        metadata = {
            "parser_engine": "pymupdf",
            "parser_version": self.version,
            "engine_version": "1.0",
            "ocr_used": ocr_page_count > 0,
            "ocr_enabled": ocr_page_count > 0,
            "table_engine": "PyMuPDF",
            "layout_mode": "blocks",
            "tables_found": table_count,
            "layout": "blocks",
            "pages": page_count,
            "text_pages": text_page_count,
            "ocr_pages": ocr_page_count,
            "tables": table_count,
            "elapsed_ms": elapsed_ms,
            "pages_per_second": pages_per_second,
            "warnings": warnings,
            "processed_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "capabilities": self.capabilities.to_dict(),
        }

        return full_text, metadata
