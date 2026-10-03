import glob
import logging
import re
import shutil
from unittest.mock import patch

import fitz
import pytest

from markdownExtractor import extract
from markdownExtractor import pdf
from markdownExtractor.pdf import is_garbled, extract_pdf_md

REGIS = 'tests/statement_extraction_fixtures/pdf_garbled_tounicode_identity_h_regis.pdf'
LATIN_EXTENDED = re.compile(r'[Ā-˿]')

PYMUPDF_GARBLED = 'DŽĚĞƌŶ\x03^ůĂǀĞƌǇ\x03^ƚĂƚĞŵĞŶƚ ' * 5
PDFMINER_GARBLED = ''.join(f'(cid:{n})' for n in (68, 381, 282, 258, 286, 396, 94, 258, 400, 349, 381))


def test_is_garbled_pymupdf_form():
    assert is_garbled(PYMUPDF_GARBLED)


def test_is_garbled_pdfminer_form():
    assert is_garbled(PDFMINER_GARBLED)


@pytest.mark.parametrize('text', [
    "Déclaration sur l'esclavage moderne. Les entreprises doivent être très vigilantes à l'égard "
    "de la chaîne d'approvisionnement, où l'été est généralement la période la plus chargée.",
    'Prohlášení o moderním otroctví. Společnost se zavazuje k etickému chování ve všech svých '
    'činnostech a dodavatelských řetězcích, včetně příležitostných dodavatelů.',
    'Oświadczenie w sprawie nowoczesnego niewolnictwa. Spółka zobowiązuje się do przestrzegania '
    'najwyższych standardów etycznych w łańcuchu dostaw i działalności.',
    'Tuyên bố về chế độ nô lệ hiện đại. Công ty cam kết thực hiện các tiêu chuẩn đạo đức cao nhất '
    'trong chuỗi cung ứng và hoạt động của chúng tôi.',
    '現代奴隷制に関する声明。当社はサプライチェーンおよび事業活動において最高水準の倫理基準を遵守することを約束します。' * 3,
    'Contents' + '.\x08' * 60 + ' 12\nIntroduction' + '.\x08' * 60 + ' 14',
    '',
    'short',
])
def test_is_garbled_false_for_real_text(text):
    assert not is_garbled(text)


def _all_clean_pdfs():
    paths = glob.glob('tests/resources/*.pdf') + glob.glob('tests/statement_extraction_fixtures/*.pdf')
    return [p for p in paths if p != REGIS]


@pytest.mark.parametrize('path', _all_clean_pdfs())
def test_is_garbled_false_on_existing_pdfs(path):
    with fitz.open(path) as doc:
        for page in doc:
            assert not is_garbled(page.get_text()), f'{path} page {page.number}'


def test_clean_pdf_triggers_no_ocr():
    with patch('markdownExtractor.pdf.extract_image_text') as ocr, \
            patch('markdownExtractor.pdf.extract_image_md') as ocr_md:
        result = extract_pdf_md('tests/resources/test.pdf')
    assert 'Test Document' in result
    ocr.assert_not_called()
    ocr_md.assert_not_called()


def test_garbled_fixture_is_detected_on_every_page():
    with fitz.open(REGIS) as doc:
        assert all(is_garbled(page.get_text()) for page in doc)


@pytest.mark.skipif(shutil.which('tesseract') is None, reason='requires tesseract')
def test_garbled_fixture_is_ocrd():
    result = extract(REGIS, 'application/pdf')
    assert 'Modern Slavery Statement' in result
    assert not LATIN_EXTENDED.search(result)


def test_garbled_dropped_when_ocr_disabled(caplog):
    with caplog.at_level(logging.WARNING, logger='markdownExtractor.pdf'):
        result = extract_pdf_md(REGIS, extract_images=False)
    assert result == ''
    assert 'garbled' in caplog.text


def test_garbled_pages_ocrd_within_budget(monkeypatch, caplog):
    monkeypatch.setattr(pdf, 'OCR_PAGE_BUDGET', 1)
    with patch('markdownExtractor.pdf.extract_image_text', return_value='Modern Slavery Statement') as ocr, \
            caplog.at_level(logging.WARNING, logger='markdownExtractor.pdf'):
        result = extract_pdf_md(REGIS)
    assert ocr.call_count == 1
    assert result == 'Modern Slavery Statement'
    assert 'budget' in caplog.text


def test_garbled_ocr_output_is_never_returned():
    with patch('markdownExtractor.pdf.extract_image_text', return_value=PYMUPDF_GARBLED):
        assert extract_pdf_md(REGIS) == ''

