# Markdown Extract

Markdown Extract is a Python package that extracts markdown from a URL regardless of what is there. It's useful for sending data to an LLM.

## Installation

You can install Markdown currently only from this private repository.
OCR requires Tesseract to be installed on your system.
```bash
sudo apt install tesseract-ocr
```
Or build from sources:
https://tesseract-ocr.github.io/tessdoc/Compiling.html


```bash
pip install git+ssh://git@bitbucket.org/nameless-media/markdown-extract.git
```

## Usage

The `extract_from_url` function is the main function in the Markdown Extract package. It extracts markdown from a given URL.

Here's a basic example of how to use it:

```python
from MarkdownExtractor import extract_from_url

# Extract markdown from a URL
markdown_text = extract_from_url('https://www.example.com')
```

### Parameters

- `url` (str): The URL from which to extract markdown.
- `extract_images` (bool, optional): Whether to extract text from images found at the URL. Defaults to True.
- `strip_non_content` (bool, optional): Whether to strip headers, footers, navigation etc. Defaults to True.
- `enhance_images` (bool, optional): Whether to enhance images before extracting text. Defaults to True.

### Returns

- `str`: The extracted markdown text.

### Raises

- `Exception`: If the URL is not reachable or the content type of the URL is not supported.