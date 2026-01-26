import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
from PIL import Image
import logging

# Configure logging to capture output
logging.basicConfig(level=logging.DEBUG)

from markdownExtractor import extract

class TestLargeImageExtraction(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.large_image_path = os.path.join(self.temp_dir.name, 'large.jpg')
        self.small_image_path = os.path.join(self.temp_dir.name, 'small.jpg')

        # Create a large image (> 10MP). 3200x3200 = 10.24MP
        large_img = Image.new('RGB', (3200, 3200), color='red')
        large_img.save(self.large_image_path)

        # Create a small image (< 10MP). 100x100 = 0.01MP
        small_img = Image.new('RGB', (100, 100), color='blue')
        small_img.save(self.small_image_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('markdownExtractor.extract_image_md')
    def test_extract_large_image(self, mock_extract_image_md):
        # calling extract with a large image
        # We need to simulate the mime type being detected as image/jpeg
        # extract_text.py uses mimetypes.guess_type, which works on file extension
        
        extract(self.large_image_path)
        
        # Verify extract_image_md was called
        self.assertTrue(mock_extract_image_md.called)
        
        # Verify enhance_level was set to 0
        call_args = mock_extract_image_md.call_args
        # checking keyword arguments
        self.assertEqual(call_args.kwargs.get('enhance_level'), 0, "enhance_level should be 0 for large images")

    @patch('markdownExtractor.extract_image_md')
    def test_extract_small_image(self, mock_extract_image_md):
        # calling extract with a small image
        
        extract(self.small_image_path)
        
        # Verify extract_image_md was called
        self.assertTrue(mock_extract_image_md.called)
        
        # Verify enhance_level was NOT set to 0 (should be default 1 passed from extract default)
        call_args = mock_extract_image_md.call_args
        
        # extract default enhance_image_level is 1
        self.assertEqual(call_args.kwargs.get('enhance_level'), 1, "enhance_level should be 1 for small images")

if __name__ == '__main__':
    unittest.main()
