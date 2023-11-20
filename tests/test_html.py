import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from markdownExtractor.html import md_from_html, convert_links_to_markdown, convert_headings_to_markdown, convert_emphasis_to_markdown, convert_lists_to_markdown, strip_decoration, convert_images_to_text
import re


@patch('TextExtractor.html.BeautifulSoup')
def test_md_from_html_with_valid_html(mock_soup):
    mock_soup.return_value = BeautifulSoup('<p>Hello, World!</p>', 'html.parser')
    result = md_from_html('<p>Hello, World!</p>')
    assert result == 'Hello, World!'

def test_convert_links_to_markdown_with_valid_link():
    soup = BeautifulSoup('<a href="http://example.com">Example</a>', 'html.parser')
    convert_links_to_markdown(soup)
    assert str(soup) == '[Example](http://example.com)'

def test_convert_headings_to_markdown_with_valid_heading():
    soup = BeautifulSoup('<h1>Heading 1</h1>', 'html.parser')
    convert_headings_to_markdown(soup)
    assert str(soup) == '# Heading 1'

def test_convert_emphasis_to_markdown_with_valid_emphasis():
    soup = BeautifulSoup('<b>Bold</b><i>Italic</i>', 'html.parser')
    convert_emphasis_to_markdown(soup)
    assert str(soup) == '**Bold***Italic*'

def test_convert_lists_to_markdown_with_valid_list():
    soup = BeautifulSoup('<ul><li>Item 1</li><li>Item 2</li></ul>', 'html.parser')
    convert_lists_to_markdown(soup)
    assert str(soup) == '* Item 1\n* Item 2\n'

def test_strip_decoration_with_valid_html():
    soup = BeautifulSoup('<div><nav>Navigation</nav><main>Main Content</main></div>', 'html.parser')
    result = strip_decoration(soup)
    assert str(result) == '<div><main>Main Content</main></div>'

@patch('TextExtractor.html.download_and_extract_image_to_md')
def test_convert_images_to_text_with_valid_image(mock_download_and_extract_image_to_md):
    mock_download_and_extract_image_to_md.return_value = 'Image Text'
    soup = BeautifulSoup('<img src="http://example.com/image.jpg" alt="Example Image">', 'html.parser')
    convert_images_to_text(soup)
    texts = soup.findAll(string=True)
    stripped = u"\n".join(t.strip() for t in texts)
    assert stripped == 'Image Text'