import fitz
import logging
import io
import tempfile
import os
import re
from .image import extract_image_md

logger = logging.getLogger(__name__)

def extract_pdf_md(filepath: str, url: str = None, extract_images: bool = True, 
                   enhance_image_level: int = 2) -> str:
    """
    Extract text from a PDF using PyMuPDF (fitz)
    :param filepath:
    :param url:
    :param extract_images:
    :param enhance_image_level:
    :return:
    """
    doc = fitz.open(filepath)
    md_content = []
    
    # BiDi characters to remove: LRM, RLM, LRE, RLE, PDF, LRO, RLO
    bidi_chars = re.compile(r'[\u200e\u200f\u202a\u202b\u202c\u202d\u202e]')
    
    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text().strip()
        
        # If there is meaningful text, use it
        if text:
            # Sanitize text to remove BiDi markers
            text = bidi_chars.sub('', text)
            md_content.append(text)
        
        # If the page has very little text and we are allowed to extract images, 
        # assume it might be a scan and try to OCR
        elif extract_images:
            logger.debug(f"Page {page_index} has no text, attempting image extraction/OCR")
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Save image to temp file for extraction
                with tempfile.NamedTemporaryFile(suffix=f".{image_ext}", delete=False) as tmp_img:
                    tmp_img.write(image_bytes)
                    tmp_img_path = tmp_img.name
                
                try:
                    # Use existing image extraction logic
                    img_src = url if url else filepath
                    img_md = extract_image_md(img_src, tmp_img_path, enhance_level=enhance_image_level)
                    if img_md:
                        md_content.append(img_md)
                finally:
                    if os.path.exists(tmp_img_path):
                        os.remove(tmp_img_path)
    
    doc.close()
    return "\n\n".join(md_content)
