import fitz
import logging
import io
import tempfile
import os
import re
from .image import extract_image_md, extract_image_text

logger = logging.getLogger(__name__)

# statementapi kills extraction after 60s and OCR costs about 1s per page at 300 dpi
OCR_PAGE_BUDGET = 20

# A page rendered at 300 dpi is already the resolution Tesseract wants: the 3x upscale of image
# enhancement doubled the time (8.9s against 4.3s for a scanned page) for the same text.
RENDERED_PAGE_ENHANCE_LEVEL = 0

_CID_RE = re.compile(r'\(cid:\d+\)')
_LATIN_LETTER_RE = re.compile(r'[A-Za-zÀ-˿]')
# BiDi characters to remove: LRM, RLM, LRE, RLE, PDF, LRO, RLO
_BIDI_CHARS = re.compile(r'[‎‏‪‫‬‭‮]')


def is_garbled(text: str) -> bool:
    """
    Detect a text layer whose fonts decoded to the wrong characters.
    Garbled if there are at least 10 (cid:N) tokens, or if there are at least 20 Latin
    letters (U+0041-U+02FF) and 0.3+ of them are in Latin Extended-A/B or IPA (U+0100 and above).
    Control characters are deliberately not used: dot leaders can come out as \\x08.
    """
    if not text:
        return False
    if len(_CID_RE.findall(text)) >= 10:
        return True
    letters = [c for c in text if _LATIN_LETTER_RE.match(c) and c not in '×÷']
    if len(letters) < 20:
        return False
    extended = sum(1 for c in letters if ord(c) >= 0x100)
    return extended / len(letters) >= 0.3


def _images_upright(page) -> bool:
    """
    Whether the page's embedded images appear the way they are stored. A scan is often stored
    sideways or upside down with the page rotated for display, or placed rotated or flipped;
    OCR of the raw image then reads rotated text and returns gibberish, so the rendered page
    (which applies the rotation) must be OCR'd instead.
    """
    if page.rotation:
        return False
    for info in page.get_image_info():
        a, b, c, d = info['transform'][:4]
        if b or c or a <= 0 or d <= 0:
            return False
    return True


def _ocr_page(page, enhance_level: int) -> str:
    """Render the whole page and OCR it, which also catches vector-drawn text and rotated scans."""
    pix = page.get_pixmap(dpi=300)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        pix.save(tmp_path)
        return (extract_image_text(tmp_path, enhance_level) or '').strip()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def extract_pdf_md(filepath: str, url: str = None, extract_images: bool = True,
                   enhance_image_level: int = 2) -> str:
    """
    Extract text from a PDF using PyMuPDF (fitz).
    Pages that are empty or have a garbled text layer are OCR'd (if extract_images is set
    and the OCR page budget allows). Garbled text is never returned.
    :param filepath:
    :param url:
    :param extract_images:
    :param enhance_image_level:
    :return:
    """
    # filetype, as the file's name can't be trusted (a PDF is sometimes saved as .html)
    doc = fitz.open(filepath, filetype='pdf')
    md_content = []
    ocr_pages_used = 0

    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            text = _BIDI_CHARS.sub('', page.get_text().strip())

            if text and not is_garbled(text):
                md_content.append(text)
                continue

            garbled = bool(text)
            if not extract_images:
                if garbled:
                    logger.warning(f"Page {page_index} has a garbled text layer and OCR is disabled, dropping page")
                continue

            # An empty page might be a scan: OCR its embedded images first, unless they're stored
            # rotated (see _images_upright), when only the rendered page reads the right way up
            if not garbled and _images_upright(page):
                logger.debug(f"Page {page_index} has no text, attempting image extraction/OCR")
                found = False
                for img in page.get_images(full=True):
                    base_image = doc.extract_image(img[0])

                    # Save image to temp file for extraction
                    with tempfile.NamedTemporaryFile(suffix=f".{base_image['ext']}", delete=False) as tmp_img:
                        tmp_img.write(base_image["image"])
                        tmp_img_path = tmp_img.name

                    try:
                        # Use existing image extraction logic
                        img_src = url if url else filepath
                        img_md = extract_image_md(img_src, tmp_img_path, enhance_level=enhance_image_level)
                        if img_md:
                            md_content.append(img_md)
                            found = True
                    finally:
                        if os.path.exists(tmp_img_path):
                            os.remove(tmp_img_path)
                if found:
                    continue

            if ocr_pages_used >= OCR_PAGE_BUDGET:
                if garbled:
                    logger.warning(f"Page {page_index} has a garbled text layer and the OCR page budget "
                                   f"({OCR_PAGE_BUDGET}) is used up, dropping page")
                continue
            ocr_pages_used += 1
            logger.debug(f"Page {page_index} is {'garbled' if garbled else 'empty'}, OCR of rendered page")
            ocr_text = _BIDI_CHARS.sub('', _ocr_page(page, RENDERED_PAGE_ENHANCE_LEVEL))
            if ocr_text and not is_garbled(ocr_text):
                md_content.append(ocr_text)
            elif garbled:
                logger.warning(f"Page {page_index} has a garbled text layer and OCR gave no usable text, dropping page")
    finally:
        doc.close()
    return "\n\n".join(md_content)
