import mimetypes
import os
import sys
import zipfile
import logging
from bs4 import BeautifulSoup, Comment
import re
import requests
import tempfile
from pathlib import Path
from urllib.parse import urljoin
from PIL import Image, ImageEnhance, ImageFilter, UnidentifiedImageError
import io
import pytesseract
import base64
import hashlib
import cairosvg
from pdfminer.high_level import extract_text_to_fp
from urllib.parse import urljoin
import mammoth
from .html import md_from_html
from .image import extract_image_md, download_image
from .powerpoint import extract_pptx_md


def extract_from_url(url: str, extract_images: bool = True, strip_non_content: bool = True,
                     enhance_images: bool = True) -> str:
    """
    Extract text from a URL
    :param url:
    :param filemime:
    :param extract_images:
    :param strip_non_content:
    :param enhance_images:
    :return:
    """
    # download the file to a tempfile directory
    with tempfile.TemporaryDirectory() as tempDirectory:
        filepath = os.path.join(tempDirectory, 'file')
        logging.debug(f"Downloading file to: {filepath}")
        r = requests.get(url, allow_redirects=True, timeout=2)

        # try filemime from the headers
        filemime = r.headers.get('content-type')

        open(filepath, 'wb').write(r.content)
        logging.debug(f"Downloaded file to: {filepath}")

        # extract the text from the file
        text = extract(filepath, filemime=filemime, extract_images=extract_images, strip_non_content=strip_non_content,
                       enhance_image_level=enhance_images, url=url)

    return text


def get_filemime(filepath: str) -> str:
    """
    Get the mimetype of a file
    :param filepath: The filepath including filename and extension
    :return: The mimetype of the file
    """
    return mimetypes.guess_type(filepath)[0]


def get_file_content(filepath: str, filemime: str) -> bytes:
    """
    Real simple file open
    Separated as a function so that I can mock it in tests
    :param filepath:
    :param filemime: currently unused.
    :return:
    """
    with open(filepath, 'rb') as file:
        file_content = file.read()

    return file_content


def extract(
        filepath: str,
        filemime: str = None,
        _trying_again: bool = False,
        url: str = None,
        extract_images: bool = True,
        strip_non_content: bool = True,
        enhance_image_level: int = 1
) -> str:
    """

    :param url:
    :param filepath: The filepath including filename and extension
    :param filemime: The mimetype we believe this file should be
    :param _trying_again: Is this a retry of an alternative type
    :param alt_ext: A different extension to try e.g. ".pdf" 0 If specified, this is used instead of filemime
    :param extract_images: Extract text from images
    :param strip_non_content: Strip headers, footers, navigation etc
    :param enhance_image_level: Enhance images before extracting text
    TODO: Add a parameter to specify the language for tesseract
    TODO: Make this more modular, allowing handler files for each mimetype and allowing them to handle the file
      so that new handlers can be easily plugged in by adding a new handler file
    :return: The text of the document in UTF-8
    """

    if not filemime:
        filemime = get_filemime(filepath)

    if not filemime:
        logging.error(f"Could not determine mimetype for {filepath}")
        return ''

    file_content = get_file_content(filepath, filemime)

    if filemime == 'text/html':
        logging.debug(f"Converting HTML to Markdown...")
        text = md_from_html(file_content, url=url, extract_images=extract_images, strip_non_content=strip_non_content,
                            enhance_image_level=enhance_image_level)
        if text:
            logging.debug(f"Got '{text[0:100]}...'")
            return text
        else:
            logging.debug(f"Got nothing from HTML!")

    elif filemime == 'application/pdf':
        # Convert to html then call extract
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.html') as tmp:
            # extract the text from the pdf
            with open(filepath, 'rb') as file:
                extract_text_to_fp(io.BytesIO(file.read()), tmp, output_type='html', codec='utf-8')
            # read the text from the temporary file
            tmp.seek(0)
            content = get_file_content(tmp.name, 'text/html')
            return md_from_html(content, url=url, extract_images=extract_images,
                                strip_non_content=strip_non_content, enhance_image_level=enhance_image_level)

    elif filemime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        result = mammoth.convert_to_html(filepath)
        return md_from_html(result.value, url=url)

    elif filemime.startswith('image/'):
        return extract_image_md(url, filepath, enhance_level=enhance_image_level)

    elif filemime == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
        return extract_pptx_md(filepath)
    else:
        # raise an error if we don't know how to handle this file type
        logging.error(f"Unsupported mimetype: {filemime}")
        return ''

        # Don't trust the user to give us a valid mimetype, or file extension - so try until we get something


    if not text and not _trying_again:
        # retry with common mimetypes in case it was incorrectly categorized
        alt_mimetype = get_filemime(filepath)
        if alt_mimetype != filemime:
            logging.debug(f"Trying alternative mimetype: {alt_mimetype}")
            text = extract(filepath, filemime=alt_mimetype, extract_images=extract_images,
                           strip_non_content=strip_non_content, enhance_image_level=enhance_image_level,
                           _trying_again=True)

        if not text:
            logging.error(f"Everything failed!")

    logging.debug('extracted')
    return text


"""
Following functions courtesy of https://stackoverflow.com/a/1983219
"""
