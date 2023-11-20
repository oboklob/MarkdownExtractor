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

        if not text:
            alt_mimetype = get_filemime(filepath)
            if alt_mimetype != filemime:
                logging.debug(f"Trying alternative mimetype: {alt_mimetype}")
                text = extract(filepath, filemime=alt_mimetype, extract_images=extract_images,
                               strip_non_content=strip_non_content, enhance_image_level=enhance_images, url=url)

    return text


def get_filemime(filepath: str) -> str:
    """
    Get the mimetype of a file
    :param filepath: The filepath including filename and extension
    :return: The mimetype of the file
    """
    return mimetypes.guess_type(filepath)[0]


def extract(
        filepath: str,
        filemime: str = None,
        _trying_again: bool = False,
        alt_ext: str = None,
        url: str = None,
        extract_images: bool = True,
        strip_non_content: bool = True,
        enhance_image_level: int = 2
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
    TODO: use tempfile for downloads rather than tmp
    TODO: Replace textract for PDF, DOCX, PPTX with pdfminer, docx2txt, python-pptx
    TODO:
    :return: The text of the document in UTF-8
    """

    if not filemime:
        filemime = get_filemime(filepath)

    if not filemime:
        logging.error(f"Could not determine mimetype for {filepath}")
        return ''

    if filemime == 'text/html':
        # use BS4 directly as it is far better!
        html = open(filepath, 'rb').read()
        text = md_from_html(html, url=url, extract_images=extract_images, strip_non_content=strip_non_content,
                            enhance_image_level=enhance_image_level)
        if text:
            logging.debug(f"Got '{text[0:100]}...'")
            return text

    elif filemime == 'application/pdf':
        # Convert to html then call extract
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.html') as tmp:
            # extract the text from the pdf
            with open(filepath, 'rb') as file:
                extract_text_to_fp(io.BytesIO(file.read()), tmp, output_type='html', codec='utf-8')
            # read the text from the temporary file
            tmp.seek(0)
            html = tmp.read()
            return extract(html, filemime='text/html', url=url, extract_images=extract_images,
                           strip_non_content=strip_non_content, enhance_image_level=enhance_image_level)

    elif filemime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        result = mammoth.convert_to_markdown(filepath)
        return result.value

    elif filemime.startswith('image/'):
        return extract_image_md(url, filepath, enhance_level=enhance_image_level)
    else:
        # raise an error if we don't know how to handle this file type
        logging.error(f"Unsupported mimetype: {filemime}")
        return ''

        # Don't trust the user to give us a valid mimetype, or file extension - so try until we get something
    logging.debug(f'extracting from {filepath} of type {filemime}')

    file_extension = os.path.splitext(filepath)[1]

    if len(text) < 10 and not _trying_again:
        # retry with common mimetypes in case it was incorrectly categorized
        tried = {file_extension, alt_ext}
        possibles = {'.html', '.pdf', '.docx', '.ppt'}

        for retry_ext in (possibles - tried):
            new_result = extract(filepath, '', _trying_again=True, alt_ext=retry_ext, url=url,
                                 extract_images=extract_images, strip_non_content=strip_non_content,
                                 enhance_image_level=enhance_image_level)
            if len(new_result) > 10:
                logging.warning(f'extracted when trying {retry_ext}!')
                return new_result

        logging.error(f"Everything failed!")

    logging.debug('extracted')
    return text


"""
Following functions courtesy of https://stackoverflow.com/a/1983219
"""
