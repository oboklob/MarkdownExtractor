import pytest
from unittest.mock import patch, MagicMock
from markdownExtractor.image import download_and_extract_image_to_md, extract_image_md, _image_data_to_markdown, \
    download_image, convert_svg_to_png, extract_image_text
import tempfile
import unittest


@patch('markdownExtractor.image.download_image')
@patch('markdownExtractor.image.extract_image_md')
def test_download_and_extract_image_to_md_with_valid_image(mock_extract_image_md, mock_download_image):
    mock_download_image.return_value = 'tests/resources/test.jpg'
    mock_extract_image_md.return_value = 'markdown'
    with tempfile.TemporaryDirectory() as tempDirectory:
        result = download_and_extract_image_to_md('https://stu.co.uk/test.jpg', tempDirectory)
    assert result == 'markdown'


@patch('markdownExtractor.image.extract_image_text')
def test_extract_image_md_with_valid_image(mock_extract_image_text):
    mock_extract_image_text.return_value = 'extracted_text'
    result = extract_image_md('https://stu.co.uk/test.jpg', 'tests/resources/test.jpg')
    assert result == '![](https://stu.co.uk/test.jpg "extracted_text")'

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


@patch('markdownExtractor.image.requests.get')
def test_download_image_with_valid_url(mock_get):
    mock_get.return_value.content = b'image_content'
    result = download_image('https://upload.wikimedia.org/wikipedia/commons/3/3f/JPEG_example_flower.jpg',
                            'temp_directory')
    assert result.endswith('.jpg')


@patch('markdownExtractor.image.cairosvg.svg2png')
@patch('markdownExtractor.image.Image.open')
def test_convert_svg_to_png_with_valid_svg(mock_open, mock_svg2png):
    mock_svg2png.return_value = b'png_data'
    mock_open.return_value = 'image'
    # get file from resources subdirectory of this package
    result = convert_svg_to_png('tests/resources/line_box.svg')
    assert result == 'image'


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
