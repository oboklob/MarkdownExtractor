import unittest
from unittest.mock import patch, MagicMock

import pytest

from markdownExtractor import extract_from_url, get_filemime, extract, _normalize_mime_type
from markdownExtractor.powerpoint import extract_pptx_md
from pdfminer.high_level import extract_text_to_fp

def html_extract_side_effect(html):
    """
    Mocked function for html.md_from_html
    Return nothing if given nothing, or Hello World otherwise
    :param html:
    :return:
    """
    if html == '':
        return ''
    else:
        return 'Hello World'


class TestmarkdownExtractor(unittest.TestCase):
    def setUp(self):
        self.markitdown_patcher = patch('markdownExtractor.MarkItDown')
        self.mock_markitdown = self.markitdown_patcher.start()
        self.mock_markitdown.return_value.convert.side_effect = Exception("Mocked fallback for legacy tests")

    def tearDown(self):
        patch.stopall()


    def test_normalize_mime_type_handles_empty(self):
        self.assertIsNone(_normalize_mime_type(None))
        self.assertEqual(_normalize_mime_type(''), '')

    @patch('markdownExtractor.get_filemime', return_value=None)
    def test_extract_returns_empty_when_mime_unknown(self, mock_get_filemime):
        result = extract('tests/resources/test.html')
        self.assertEqual(result, '')
        mock_get_filemime.assert_called_once_with('tests/resources/test.html')

    @patch('markdownExtractor.extract_image_md', return_value='image text')
    @patch('markdownExtractor.get_file_content', return_value='<html></html>')
    @patch('markdownExtractor.md_from_html', return_value='')
    def test_extract_retries_with_alternate_mimetype(self, mock_md_from_html, mock_get_file_content,
                                                     mock_extract_image_md):
        with patch('markdownExtractor.get_filemime', side_effect=['text/html', 'image/png']):
            result = extract('tests/resources/test.html')

        self.assertEqual(result, 'image text')
        mock_extract_image_md.assert_called_once_with('tests/resources/test.html', 'tests/resources/test.html',
                                                      enhance_level=1)
        mock_get_file_content.assert_called()

    @patch('markdownExtractor.get_file_content', return_value='<html></html>')
    @patch('markdownExtractor.md_from_html', return_value='')
    def test_extract_logs_failure_when_no_text_found(self, mock_md_from_html, mock_get_file_content):
        with patch('markdownExtractor.get_filemime', return_value='text/html'):
            result = extract('tests/resources/test.html')

        self.assertEqual(result, '')
        mock_get_file_content.assert_called_once()

    @patch('requests.get')
    @patch('markdownExtractor.extract')
    def test_extract_html_from_url(self, mock_extract, mock_get):
        mock_get.return_value.headers = {'content-type': 'text/html'}
        mock_get.return_value.content = b'<html><body><h1>Hello World</h1></body></html>'
        mock_extract.return_value = 'Hello World'
        result = extract_from_url('http://example.com')
        self.assertEqual(result, 'Hello World')

    @patch('requests.get')
    @patch('markdownExtractor.md_from_html')
    def test_extract_html_from_url_with_charset(self, mock_md_from_html, mock_get):
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
        mock_response.content = b'<html><body><h1>Hello World</h1></body></html>'
        mock_get.return_value = mock_response
        mock_md_from_html.return_value = 'Hello World'

        result = extract_from_url('http://example.com')

        self.assertEqual(result, 'Hello World')
        mock_md_from_html.assert_called_once()

    def test_get_filemime(self):
        result = get_filemime('tests/resources/test.html')
        self.assertEqual(result, 'text/html')

    @patch('markdownExtractor.md_from_html')
    def test_extract_html(self, mock_md_from_html):
        mock_md_from_html.return_value = 'Hello World'
        result = extract('tests/resources/test.html', 'text/html')
        self.assertEqual(result, 'Hello World')

    @patch('markdownExtractor.get_file_content')
    def test_extract_markdown(self, mock_get_file_content):
        mock_get_file_content.return_value = b'# Hello World'
        result = extract('test.md', 'text/markdown')
        self.assertEqual(result, '# Hello World')

    @patch('markdownExtractor.get_file_content')
    @patch('markdownExtractor.get_filemime')
    def test_extract_markdown_empty(self, mock_get_filemime, mock_get_file_content):
        mock_get_filemime.return_value = 'text/markdown'
        mock_get_file_content.return_value = b''
        result = extract('test.md', 'text/markdown')
        self.assertEqual(result, '')

    @patch('markdownExtractor.requests.get')
    @patch('markdownExtractor.get_file_content')
    def test_extract_html_with_url_fetches_md(self, mock_get_file_content, mock_get):
        mock_get_file_content.return_value = b'<html><body><h1>Hello World</h1></body></html>'
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'text/markdown'}
        mock_response.content = b'# Hello World'
        mock_get.return_value = mock_response

        # _fetch_md is True by default
        result = extract('tests/resources/test.html', 'text/html', url='http://example.com')
        
        self.assertEqual(result, '# Hello World')
        mock_get.assert_called_once()

    @patch('markdownExtractor.md_from_html')
    @patch('markdownExtractor.requests.get')
    @patch('markdownExtractor.get_file_content')
    def test_extract_html_with_url_fallback_to_html(self, mock_get_file_content, mock_get, mock_md_from_html):
        mock_get_file_content.return_value = b'<html><body><h1>Hello World</h1></body></html>'
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.content = b'<html></html>'
        mock_get.return_value = mock_response
        mock_md_from_html.return_value = 'Fallback HTML Text'

        result = extract('tests/resources/test.html', 'text/html', url='http://example.com')
        
        self.assertEqual(result, 'Fallback HTML Text')
        mock_get.assert_called_once()
        mock_md_from_html.assert_called_once()

    @patch('markdownExtractor.md_from_html')
    @patch('requests.get')
    @patch('markdownExtractor.get_file_content')
    def test_extract_html_with_url_no_fetch_md(self, mock_get_file_content, mock_get, mock_md_from_html):
        mock_get_file_content.return_value = b'<html><body><h1>Hello World</h1></body></html>'
        mock_md_from_html.return_value = 'HTML text'
        
        result = extract('tests/resources/test.html', 'text/html', url='http://example.com', _fetch_md=False)
        
        self.assertEqual(result, 'HTML text')
        mock_get.assert_not_called()

    @patch('markdownExtractor.get_filemime')
    @patch('markdownExtractor.html.md_from_html', html=html_extract_side_effect)
    @patch('markdownExtractor.extract_text_to_fp')
    @patch('markdownExtractor.get_file_content')
    def test_extract_type_fail(self, mock_get_file_content, mock_extract_text_to_fp, mock_md_from_html, mock_get_filemime):
        mock_get_filemime.return_value = 'text/html'
        mock_get_file_content.return_value = b'<html><body>Hello World</body></html>'
        mock_extract_text_to_fp.return_value = ''
        mock_md_from_html.return_value = 'Hello World'
        result = extract('tests/resources/test.html', 'application/pdf')
        self.assertEqual(result, 'Hello World')

    @patch('markdownExtractor.extract_text_to_fp')
    @patch('markdownExtractor.md_from_html')
    def test_extract_pdf(self, mock_md_from_html, mock_extract_text_to_fp):
        mock_md_from_html.return_value = 'Hello World'
        result = extract('tests/resources/test.pdf', 'application/pdf')
        self.assertEqual(result, 'Hello World')

    def test_extract_actual_pdf(self):
        result = extract('tests/resources/test.pdf', 'application/pdf')
        self.assertTrue('Test Document' in result)

    @pytest.mark.skip("Skipping scanned PDF test as it requires OCR which may not be available in all environments. Also takes too long")
    def test_extract_actual_pdf_2(self):
        result = extract('tests/resources/scanned.pdf', 'application/pdf', url='https://www.example.com/')
        self.assertTrue('Obligation to Implement All Schindler' in result)

    def test_extract_actual_pdf_3(self):
        result = extract('tests/resources/awkward.pdf', 'application/pdf', url='https://www.example.com/')
        import logging
        logging.warning(result)
        self.assertTrue('KONE must play its part' in result)

    @patch('mammoth.convert_to_html')
    def test_extract_docx(self, mock_convert_to_html):
        mock_convert_to_html.return_value = MagicMock(value='<html><body>Hello World</body></html>')
        result = extract('tests/resources/test.docx',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        self.assertEqual(result, 'Hello World')

    def test_extract_actual_docx(self):
        result = extract('tests/resources/test.docx',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        self.assertEqual(result, 'This is a test\nWoot to the test\n[Does link work?](https://www.example.com)')

    def test_extract_actual_pptx(self):
        result = extract('tests/resources/test.pptx',
                         'application/vnd.openxmlformats-officedocument.presentationml.presentation')
        self.assertEqual(result, 'Title\nsubtitle\nHello World!\n**Bold**\n \n*italic*\n_Underlined_\nAnd a \n[_link_](https://www.example.com/)')

    @patch('markdownExtractor.get_file_content')
    @patch('markdownExtractor.extract_image_md')
    def test_extract_image(self, mock_extract_image_md, mock_get_file_content):
        mock_get_file_content.return_value = b'<html><body><h1>Hello World</h1></body></html>'
        mock_extract_image_md.return_value = 'Hello World'
        result = extract('test.png', 'image/png')
        self.assertEqual(result, 'Hello World')
        mock_extract_image_md.assert_called_once_with('test.png', 'test.png', enhance_level=1)

    def test_extract_actual_local_image(self):
        result = extract('tests/resources/test.jpg', 'image/jpeg')
        self.assertEqual(
            result,
            ('![](tests/resources/test.jpg "JPEG - Least compression - 85K Four score and seven years ago '
             'our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated '
             'to the proposition that all men are created equal.")')
        )


    @patch('markdownExtractor.get_file_content')
    def test_extract_unsupported_mimetype(self, mock_get_file_content):
        mock_get_file_content.return_value = b'<html><body><h1>Hello World</h1></body></html>'
        result = extract('test.txt', 'text/plain')
        self.assertEqual(result, '')


@patch('markdownExtractor.powerpoint.Presentation')
@patch('markdownExtractor.powerpoint.Pt', return_value=24)
def test_extract_pptx_md_marks_large_text_as_heading(mock_pt, mock_presentation):
    run = MagicMock()
    font = MagicMock()
    font.bold = False
    font.italic = False
    font.underline = False
    font.size = 30
    run.font = font
    run.text = 'Heading'
    run.hyperlink = MagicMock(address=None)
    paragraph = MagicMock()
    paragraph.runs = [run]
    shape = MagicMock()
    shape.has_text_frame = True
    text_frame = MagicMock()
    text_frame.paragraphs = [paragraph]
    shape.text_frame = text_frame
    slide = MagicMock()
    slide.shapes = [shape]
    mock_presentation.return_value.slides = [slide]

    result = extract_pptx_md('dummy.pptx')

    assert result == '# Heading'


    def test_extract_markitdown_success(self):
        self.mock_markitdown.return_value.convert.side_effect = None
        mock_result = MagicMock()
        mock_result.text_content = "Markitdown Extracted Content"
        self.mock_markitdown.return_value.convert.return_value = mock_result
        
        result = extract('dummy.pdf', 'application/pdf')
        self.assertEqual(result, "Markitdown Extracted Content")
        
    def test_extract_markitdown_empty_returns_fallback(self):
        self.mock_markitdown.return_value.convert.side_effect = None
        mock_result = MagicMock()
        mock_result.text_content = ""
        self.mock_markitdown.return_value.convert.return_value = mock_result
        
        with patch('markdownExtractor.extract_text_to_fp'):
            with patch('markdownExtractor.md_from_html', return_value="Fallback Content"):
                with patch('markdownExtractor.get_file_content', return_value=b'<html></html>'):
                    result = extract('dummy.pdf', 'application/pdf')
                    self.assertEqual(result, "Fallback Content")

if __name__ == '__main__':
    unittest.main()
