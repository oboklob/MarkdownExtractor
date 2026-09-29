import io
from unittest.mock import patch

from markitdown import StreamInfo
from markitdown.converters import DocxConverter, PptxConverter

from markdownExtractor.markitdown_converters import OcrDocxConverter, OcrPptxConverter, _guess_extension


def test_ocr_docx_converter_is_a_docx_converter():
    assert isinstance(OcrDocxConverter(), DocxConverter)


def test_ocr_pptx_converter_is_a_pptx_converter():
    assert isinstance(OcrPptxConverter(), PptxConverter)


@patch('markdownExtractor.markitdown_converters.extract_image_text')
def test_image_to_html_returns_escaped_paragraph_for_ocr_text(mock_extract_image_text):
    mock_extract_image_text.return_value = 'Statement <text> & more'
    converter = OcrDocxConverter()
    stream_info = StreamInfo(mimetype='image/png', extension='.png')

    result = converter._image_to_html(io.BytesIO(b'fake image bytes'), stream_info)

    assert result == '<p>Statement &lt;text&gt; &amp; more</p>'


@patch('markdownExtractor.markitdown_converters.extract_image_text')
def test_image_to_html_returns_none_for_decorative_image(mock_extract_image_text):
    mock_extract_image_text.return_value = ''
    converter = OcrPptxConverter()
    stream_info = StreamInfo(mimetype='image/png', extension='.png')

    result = converter._image_to_html(io.BytesIO(b'fake logo bytes'), stream_info)

    assert result is None


@patch('markdownExtractor.markitdown_converters.extract_image_text')
def test_image_to_html_returns_none_when_ocr_raises(mock_extract_image_text):
    mock_extract_image_text.side_effect = Exception('boom')
    converter = OcrDocxConverter()
    stream_info = StreamInfo(mimetype='image/png', extension='.png')

    result = converter._image_to_html(io.BytesIO(b'fake image bytes'), stream_info)

    assert result is None


def test_guess_extension_prefers_stream_info_extension():
    assert _guess_extension(StreamInfo(extension='.jpg', mimetype='image/png')) == '.jpg'


def test_guess_extension_falls_back_to_mimetype():
    assert _guess_extension(StreamInfo(extension=None, mimetype='image/jpeg')) == '.jpg'


def test_guess_extension_defaults_to_png():
    assert _guess_extension(StreamInfo(extension=None, mimetype=None)) == '.png'
