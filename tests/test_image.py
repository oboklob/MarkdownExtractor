import base64
import pytest
import numpy as np
import requests
from PIL import UnidentifiedImageError
from unittest.mock import patch, MagicMock
from markdownExtractor.image import download_and_extract_image_to_md, extract_image_md, _image_data_to_markdown, \
    download_image, convert_svg_to_png, extract_image_text, _resolve_file_uri
import tempfile
import unittest
from pathlib import Path


@patch('markdownExtractor.image.download_image')
@patch('markdownExtractor.image.extract_image_md')
def test_download_and_extract_image_to_md_with_valid_image(mock_extract_image_md, mock_download_image):
    mock_download_image.return_value = 'tests/resources/test.jpg'
    mock_extract_image_md.return_value = 'markdown'
    with tempfile.TemporaryDirectory() as tempDirectory:
        result = download_and_extract_image_to_md('https://stu.co.uk/test.jpg', tempDirectory)
    assert result == 'markdown'


@patch('markdownExtractor.image.download_image')
def test_download_and_extract_image_to_md_returns_empty_when_download_fails(mock_download_image):
    mock_download_image.return_value = ''
    with tempfile.TemporaryDirectory() as temp_directory:
        result = download_and_extract_image_to_md('https://example.com/image.png', temp_directory)

    assert result == ''


@patch('markdownExtractor.image.extract_image_md')
@patch('markdownExtractor.image.os.path.isfile', return_value=False)
@patch('markdownExtractor.image.download_image')
def test_download_and_extract_image_to_md_missing_file(mock_download_image, mock_isfile, mock_extract_image_md):
    mock_download_image.return_value = 'missing.png'

    with tempfile.TemporaryDirectory() as temp_directory:
        result = download_and_extract_image_to_md('https://example.com/image.png', temp_directory)

    assert result == ''
    mock_extract_image_md.assert_not_called()


@patch('markdownExtractor.image.extract_image_text')
def test_extract_image_md_with_valid_image(mock_extract_image_text):
    mock_extract_image_text.return_value = 'extracted_text'
    result = extract_image_md('https://stu.co.uk/test.jpg', 'tests/resources/test.jpg')
    assert result == '![](https://stu.co.uk/test.jpg "extracted_text")'


@patch('markdownExtractor.image.extract_image_text')
def test_extract_image_md_returns_raw_text_for_large_payload(mock_extract_image_text):
    mock_extract_image_text.return_value = 'a' * 600

    result = extract_image_md('https://example.com/large.png', 'tests/resources/test.jpg')

    assert result == 'a' * 600

def test_extract_image_md_quality_0():
    result = extract_image_md('https://stu.co.uk/test.jpg', 'tests/resources/test.jpg', enhance_level=0)
    assert result == ('![](https://stu.co.uk/test.jpg "JPEG - Least compression - 85K Four score and seven years ago '
                      'our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated '
                      'to the proposition that all men are created equal.")')

def test_extract_image_md_quality_1():
    result = extract_image_md('https://stu.co.uk/test.jpg', 'tests/resources/test.jpg', enhance_level=1)
    assert result == ('![](https://stu.co.uk/test.jpg "JPEG - Least compression - 85K Four score and seven years ago '
                      'our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated '
                      'to the proposition that all men are created equal.")')

def test_extract_image_md_quality_2():
    result = extract_image_md('https://stu.co.uk/test.jpg', 'tests/resources/test.jpg', enhance_level=2)
    assert result == ('![](https://stu.co.uk/test.jpg "JPEG - Least compression - 85K Four score and seven years ago '
                      'our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated '
                      'to the proposition that all men are created equal.")')

def test_extract_image_md_quality_difficult_0():
    """
    This test assumes that the test image is too hard to read.
    IF THIS TEST FAILS, then pytesseract just got better! Adjust the testing, not the code.
    :return:
    """
    result = extract_image_md('https://stu.co.uk/test.jpg', 'tests/resources/test_difficult.jpg', enhance_level=0)
    assert result != ('![](https://stu.co.uk/test.jpg "JPEG - Least compression - 85K Four score and seven years ago '
                      'our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated '
                      'to the proposition that all men are created equal.")')

def test_extract_image_md_quality_difficult_1():
    result = extract_image_md('https://stu.co.uk/test.jpg', 'tests/resources/test_difficult.jpg', enhance_level=1)
    assert result == ('![](https://stu.co.uk/test.jpg "JPEG - Least compression - 85K Four score and seven years ago '
                      'our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated '
                      'to the proposition that all men are created equal.")')

@unittest.skip("Currently enhancement level > 1 is not delivering great results on the difficult image.")
def test_extract_image_md_quality_difficult_2():
    """
    Currently enhancement level > 1 is not delivering great results on the difficult image. So skip this test
    :return:
    """

    result = extract_image_md('https://stu.co.uk/test.jpg', 'tests/resources/test_difficult.jpg', enhance_level=2)
    assert result == ('![](https://stu.co.uk/test.jpg "JPEG - Least compression - 85K Four score and seven years ago '
                      'our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated '
                      'to the proposition that all men are created equal.")')

def test_image_data_to_markdown_with_empty_alt_text_and_extracted_text():
    result = _image_data_to_markdown('src', '', '', False)
    assert result == ''


def test_image_data_to_markdown_remote_without_extracted_text():
    result = _image_data_to_markdown('https://example.com/image.png', 'Alt', '', False)

    assert result == '![Alt](https://example.com/image.png)'


def test_image_data_to_markdown_include_empty_placeholder():
    result = _image_data_to_markdown('src', '', '', True)

    assert result == '![](src)'


def test_image_data_to_markdown_data_uri_with_alt_text_only():
    data_uri = 'data:image/png;base64,abc'
    result = _image_data_to_markdown(data_uri, 'Example alt', '', False)
    assert result == '![Example alt](local.img)'


def test_image_data_to_markdown_data_uri_with_extracted_text():
    data = base64.b64encode(b'something').decode('ascii')
    data_uri = f'data:image/png;base64,{data}'

    result = _image_data_to_markdown(data_uri, 'Alt', 'Quote "here"', False)

    assert result == "![Alt](local.img \"Quote 'here'\")"


def test_image_data_to_markdown_long_extracted_text_uses_code_block():
    long_text = '```' + 'lorem' * 70

    result = _image_data_to_markdown('https://example.com/image.png', 'Alt', long_text, False)

    assert result.startswith('![Alt](https://example.com/image.png)```image-text')
    assert '~~~' in result


@patch('markdownExtractor.image.requests.get')
def test_download_image_with_valid_url(mock_get):
    mock_get.return_value.content = b'image_content'
    result = download_image('https://upload.wikimedia.org/wikipedia/commons/3/3f/JPEG_example_flower.jpg',
                            'temp_directory')
    assert result.endswith('.jpg')


def test_download_image_with_data_url(tmp_path):
    payload = base64.b64encode(b'image-bytes').decode('ascii')
    data_url = f'data:image/png;base64,{payload}'

    result = download_image(data_url, tmp_path.as_posix())

    assert result.endswith('.png')
    assert Path(result).is_file()


def test_download_image_with_data_url_jpeg(tmp_path):
    payload = base64.b64encode(b'image-bytes').decode('ascii')
    data_url = f'data:image/jpeg;base64,{payload}'

    result = download_image(data_url, tmp_path.as_posix())

    assert result.endswith('.jpg')


def test_download_image_with_data_url_svg(tmp_path):
    payload = base64.b64encode(b'<svg></svg>').decode('ascii')
    data_url = f'data:image/svg+xml;base64,{payload}'

    result = download_image(data_url, tmp_path.as_posix())

    assert result.endswith('.svg')


def test_download_image_with_data_url_gif(tmp_path):
    payload = base64.b64encode(b'GIF89a').decode('ascii')
    data_url = f'data:image/gif;base64,{payload}'

    result = download_image(data_url, tmp_path.as_posix())

    assert result.endswith('.gif')


@patch('markdownExtractor.image.requests.get')
def test_download_image_handles_request_exception(mock_get, tmp_path):
    mock_get.side_effect = requests.exceptions.RequestException('boom')

    result = download_image('https://example.com/image.png', tmp_path.as_posix())

    assert result == ''


def test_download_image_with_data_url_unknown_type(tmp_path, monkeypatch):
    payload = base64.b64encode(b'image-bytes').decode('ascii')

    class FakeMatch:
        def group(self, name):
            if name == 'type':
                return 'webp'
            if name == 'data':
                return payload
            raise KeyError(name)

    class FakePattern:
        def match(self, _):
            return FakeMatch()

    monkeypatch.setattr('markdownExtractor.image.re.compile', lambda pattern: FakePattern())

    result = download_image(f'data:image/webp;base64,{payload}', tmp_path.as_posix())

    assert result.endswith('.img')
    assert Path(result).is_file()


@patch('markdownExtractor.image.requests.get')
def test_download_image_without_extension_uses_default(mock_get, tmp_path):
    class DummyResponse:
        content = b'abc'

        def raise_for_status(self):
            return None

    mock_get.return_value = DummyResponse()

    result = download_image('https://example.com/image.', tmp_path.as_posix())

    assert result.endswith('.img')
    assert Path(result).is_file()


def test_download_image_with_unsupported_protocol(tmp_path):
    result = download_image('ftp://example.com/image.png', tmp_path.as_posix())

    assert result == ''


def test_resolve_file_uri_rejects_non_file_scheme():
    with pytest.raises(ValueError):
        _resolve_file_uri('http://example.com/image.svg')


def test_resolve_file_uri_handles_network_path():
    result = _resolve_file_uri('file://server/share/image.svg')

    assert str(result).startswith('//server')


@patch('markdownExtractor.image.cairosvg.svg2png')
@patch('markdownExtractor.image.Image.open')
def test_convert_svg_to_png_with_local_path(mock_open, mock_svg2png):
    mock_svg2png.return_value = b'png_data'
    mock_open.return_value = 'image'

    result = convert_svg_to_png('tests/resources/line_box.svg')

    assert result == 'image'
    _, kwargs = mock_svg2png.call_args
    assert 'file_obj' in kwargs
    assert kwargs['file_obj'].name.endswith('line_box.svg')
    assert 'url' not in kwargs


@patch('markdownExtractor.image.cairosvg.svg2png')
@patch('markdownExtractor.image.Image.open')
def test_convert_svg_to_png_with_remote_url(mock_open, mock_svg2png):
    mock_svg2png.return_value = b'png_data'
    mock_open.return_value = 'image'

    svg_url = 'https://example.com/image.svg'
    result = convert_svg_to_png(svg_url)

    assert result == 'image'
    _, kwargs = mock_svg2png.call_args
    assert kwargs['url'] == svg_url
    assert 'file_obj' not in kwargs


@patch('markdownExtractor.image.cairosvg.svg2png')
@patch('markdownExtractor.image.Image.open')
def test_convert_svg_to_png_with_file_uri(mock_open, mock_svg2png):
    mock_svg2png.return_value = b'png_data'
    mock_open.return_value = 'image'

    svg_uri = Path('tests/resources/line_box.svg').resolve().as_uri()
    result = convert_svg_to_png(svg_uri)

    assert result == 'image'
    _, kwargs = mock_svg2png.call_args
    assert 'file_obj' in kwargs
    assert kwargs['file_obj'].name.endswith('line_box.svg')


def test_convert_svg_to_png_missing_file_raises(tmp_path):
    missing_uri = (tmp_path / 'missing.svg').as_uri()

    with pytest.raises(FileNotFoundError):
        convert_svg_to_png(missing_uri)


@patch('markdownExtractor.image.cairosvg.svg2png', return_value=None)
def test_convert_svg_to_png_raises_when_renderer_returns_none(mock_svg2png):
    with pytest.raises(ValueError):
        convert_svg_to_png('https://example.com/image.svg')


@patch('markdownExtractor.image.pytesseract.image_to_data')
def test_extract_image_text_with_valid_image(mock_image_to_data):
    mock_image_to_data.return_value = {'text': ['extracted', 'text'], 'conf': [100, 100]}
    result = extract_image_text('tests/resources/test.jpg')
    assert result == 'extracted text'


@patch('markdownExtractor.image.pytesseract.image_to_data')
def test_extract_image_text_ignores_blank_confidences(mock_image_to_data):
    mock_image_to_data.return_value = {
        'text': ['valid', 'ignored', 'words'],
        'conf': ['85', ' ', '95']
    }

    result = extract_image_text('tests/resources/test.jpg')

    assert result == 'valid words'


@patch('markdownExtractor.image.pytesseract.image_to_data')
@patch('markdownExtractor.image.ImageEnhance.Contrast')
@patch('markdownExtractor.image.convert_svg_to_png')
def test_extract_image_text_with_svg_source(mock_convert_svg, mock_contrast, mock_image_to_data):
    mock_img = MagicMock()
    mock_img.width = 1
    mock_img.height = 1
    mock_img.resize.return_value = mock_img
    mock_img.mode = 'RGB'
    mock_contrast_instance = MagicMock()
    mock_contrast_instance.enhance.return_value = mock_img
    mock_contrast.return_value = mock_contrast_instance
    mock_convert_svg.return_value = mock_img
    mock_image_to_data.return_value = {'text': ['svg'], 'conf': ['90']}

    result = extract_image_text('diagram.svg')

    assert result == 'svg'
    mock_convert_svg.assert_called_once_with('diagram.svg')


@patch('markdownExtractor.image.Image.open')
def test_extract_image_text_handles_unidentified_image(mock_open, tmp_path):
    mock_open.side_effect = UnidentifiedImageError('bad image')
    temp_file = tmp_path / 'image.png'
    temp_file.write_bytes(b'data')

    result = extract_image_text(temp_file.as_posix())

    assert result == ''


@patch('markdownExtractor.image.Image.open')
def test_extract_image_text_handles_resize_failure(mock_open):
    mock_img = MagicMock()
    mock_img.width = 1
    mock_img.height = 1
    mock_img.resize.side_effect = OSError('boom')
    mock_open.return_value = mock_img

    result = extract_image_text('tests/resources/test.jpg', enhance_level=1)

    assert result == ''


@patch('markdownExtractor.image.pytesseract.image_to_data')
@patch('markdownExtractor.image.ImageEnhance.Contrast')
@patch('markdownExtractor.image.Image.open')
def test_extract_image_text_converts_non_rgb_mode(mock_open, mock_contrast, mock_image_to_data):
    mock_img = MagicMock()
    mock_img.width = 1
    mock_img.height = 1
    mock_img.resize.return_value = mock_img
    mock_img.mode = 'P'
    mock_img.convert.return_value = mock_img
    mock_contrast_instance = MagicMock()
    mock_contrast_instance.enhance.return_value = mock_img
    mock_contrast.return_value = mock_contrast_instance
    mock_open.return_value = mock_img
    mock_image_to_data.return_value = {'text': ['converted'], 'conf': ['80']}

    result = extract_image_text('tests/resources/test.jpg', enhance_level=1)

    assert result == 'converted'
    mock_img.convert.assert_any_call('RGB')


@patch('markdownExtractor.image.pytesseract.image_to_data')
@patch('markdownExtractor.image.Image.fromarray')
@patch('markdownExtractor.image.cv2.threshold')
@patch('markdownExtractor.image.cv2.GaussianBlur')
@patch('markdownExtractor.image.cv2.cvtColor')
@patch('markdownExtractor.image.np.array')
@patch('markdownExtractor.image.ImageEnhance.Contrast')
@patch('markdownExtractor.image.Image.open')
def test_extract_image_text_high_enhance_level_uses_opencv(mock_open, mock_contrast, mock_np_array, mock_cvtcolor,
                                                           mock_blur, mock_threshold, mock_fromarray, mock_image_to_data):
    mock_img = MagicMock()
    mock_img.width = 2
    mock_img.height = 2
    mock_img.resize.return_value = mock_img
    mock_img.mode = 'RGB'
    mock_contrast_instance = MagicMock()
    mock_contrast_instance.enhance.return_value = mock_img
    mock_contrast.return_value = mock_contrast_instance
    mock_open.return_value = mock_img
    mock_np_array.return_value = np.zeros((1, 1, 3), dtype=np.uint8)
    mock_cvtcolor.return_value = 'gray'
    mock_blur.return_value = 'blurred'
    mock_threshold.return_value = (None, 'thresh')
    mock_fromarray.return_value = mock_img
    mock_image_to_data.return_value = {'text': ['opencv'], 'conf': ['99']}

    result = extract_image_text('tests/resources/test.jpg', enhance_level=2)

    assert result == 'opencv'
    mock_cvtcolor.assert_called_once()
    mock_fromarray.assert_called_once_with('thresh')


@patch('markdownExtractor.image.pytesseract.image_to_data')
@patch('markdownExtractor.image.Image.fromarray')
@patch('markdownExtractor.image.cv2.threshold')
@patch('markdownExtractor.image.cv2.GaussianBlur')
@patch('markdownExtractor.image.cv2.cvtColor')
@patch('markdownExtractor.image.np.array')
@patch('markdownExtractor.image.ImageEnhance.Contrast')
@patch('markdownExtractor.image.Image.open')
def test_extract_image_text_high_enhance_level_with_grayscale_array(mock_open, mock_contrast, mock_np_array, mock_cvtcolor,
                                                                    mock_blur, mock_threshold, mock_fromarray, mock_image_to_data):
    mock_img = MagicMock()
    mock_img.width = 2
    mock_img.height = 2
    mock_img.resize.return_value = mock_img
    mock_img.mode = 'RGB'
    mock_contrast_instance = MagicMock()
    mock_contrast_instance.enhance.return_value = mock_img
    mock_contrast.return_value = mock_contrast_instance
    mock_open.return_value = mock_img
    mock_np_array.return_value = np.zeros((2, 2), dtype=np.uint8)
    mock_blur.return_value = 'blurred'
    mock_threshold.return_value = (None, 'thresh')
    mock_fromarray.return_value = mock_img
    mock_image_to_data.return_value = {'text': ['gray'], 'conf': ['99']}

    result = extract_image_text('tests/resources/test.jpg', enhance_level=2)

    assert result == 'gray'
    mock_cvtcolor.assert_not_called()
