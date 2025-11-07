import unittest
from unittest.mock import patch, MagicMock
from markdownExtractor import extract_from_url, get_filemime, extract
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

    @patch('requests.get')
    @patch('markdownExtractor.extract')
    def test_extract_html_from_url(self, mock_extract, mock_get):
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


if __name__ == '__main__':
    unittest.main()
