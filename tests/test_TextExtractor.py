import unittest
from unittest.mock import patch, MagicMock
from markdownExtractor import extract_from_url, get_filemime, extract


class TestmarkdownExtractor(unittest.TestCase):

    @patch('requests.get')
    @patch('markdownExtractor.extract')
    def test_extract_from_url(self, mock_extract, mock_get):
        mock_get.return_value.headers = {'content-type': 'text/html'}
        mock_get.return_value.content = b'<html><body><h1>Hello World</h1></body></html>'
        mock_extract.return_value = 'Hello World'
        result = extract_from_url('http://example.com')
        self.assertEqual(result, 'Hello World')

    def test_get_filemime(self):
        result = get_filemime('tests/resources/test.html')
        self.assertEqual(result, 'text/html')

    @patch('markdownExtractor.md_from_html')
    def test_extract_html(self, mock_md_from_html):
        mock_md_from_html.return_value = 'Hello World'
        result = extract('tests/resources/test.html', 'text/html')
        self.assertEqual(result, 'Hello World')

    @patch('markdownExtractor.extract_text_to_fp')
    @patch('markdownExtractor.extract')
    def test_extract_pdf(self, mock_extract, mock_extract_text_to_fp):
        mock_extract.return_value = 'Hello World'
        result = extract('tests/resources/test.pdf', 'application/pdf')
        self.assertEqual(result, 'Hello World')

    @patch('mammoth.convert_to_markdown')
    def test_extract_docx(self, mock_convert_to_markdown):
        mock_convert_to_markdown.return_value = MagicMock(value='Hello World')
        result = extract('tests/resources/test.docx',
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        self.assertEqual(result, 'Hello World')

    @patch('markdownExtractor.extract_image_md')
    def test_extract_image(self, mock_extract_image_md):
        mock_extract_image_md.return_value = 'Hello World'
        result = extract('test.png', 'image/png')
        self.assertEqual(result, 'Hello World')

    def test_extract_unsupported_mimetype(self):
        result = extract('test.txt', 'text/plain')
        self.assertEqual(result, '')


if __name__ == '__main__':
    unittest.main()
