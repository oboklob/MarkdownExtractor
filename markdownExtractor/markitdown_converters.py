import html
import logging
import mimetypes
import os
import tempfile
from typing import Any, BinaryIO, Optional

from markitdown import StreamInfo
from markitdown.converters import DocxConverter, PptxConverter

from .image import extract_image_text

logger = logging.getLogger(__name__)


def _guess_extension(stream_info: StreamInfo) -> str:
    if stream_info.extension:
        return stream_info.extension
    if stream_info.mimetype:
        guessed = mimetypes.guess_extension(stream_info.mimetype)
        if guessed:
            return guessed
    return '.png'


class _OcrImageMixin:
    """
    Shared _image_to_html override for markitdown's DocxConverter/PptxConverter: OCR embedded
    images instead of leaving them as an unreadable base64 data-URI placeholder. Returning None
    keeps markitdown's default (native) representation for images with nothing to OCR (logos, etc).
    """

    def _image_to_html(
        self,
        image_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> Optional[str]:
        suffix = _guess_extension(stream_info)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_img:
            tmp_img.write(image_stream.read())
            tmp_img_path = tmp_img.name

        try:
            text = extract_image_text(tmp_img_path, enhance_level=2)
        except Exception as e:
            logger.debug(f"OCR of embedded image failed: {e}")
            text = ''
        finally:
            os.remove(tmp_img_path)

        if not text:
            return None

        return f"<p>{html.escape(text)}</p>"


class OcrDocxConverter(_OcrImageMixin, DocxConverter):
    pass


class OcrPptxConverter(_OcrImageMixin, PptxConverter):
    pass
