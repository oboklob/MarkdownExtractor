import glob
import logging
import re
import shutil
from unittest.mock import patch

import pymupdf
import pytest

from markdownExtractor import extract
from markdownExtractor import pdf
from markdownExtractor.pdf import is_garbled, extract_pdf_md

REGIS = 'tests/statement_extraction_fixtures/pdf_garbled_tounicode_identity_h_regis.pdf'
ROTATED_180 = 'tests/statement_extraction_fixtures/pdf_scanned_rotated_180_crayola.pdf'
ROTATED_270 = 'tests/statement_extraction_fixtures/pdf_scanned_rotated_270_two_pages.pdf'
UPRIGHT_SCAN = 'tests/statement_extraction_fixtures/pdf_scanned_no_text_layer_south_pennine_academies.pdf'
OUTLINED_TEXT = 'tests/statement_extraction_fixtures/pdf_outlined_text_small_signature_images_vmed_o2_holdco_3.pdf'
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
    with pymupdf.open(path) as doc:
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
    with pymupdf.open(REGIS) as doc:
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



def _page_with_image(rotation=0, placement_rotate=0):
    doc = pymupdf.open()
    page = doc.new_page()
    image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 20, 10), False)
    image.clear_with(255)
    page.insert_image(pymupdf.Rect(50, 50, 250, 150), pixmap=image, rotate=placement_rotate)
    page.set_rotation(rotation)
    return doc, page


@pytest.mark.parametrize('rotation, placement_rotate, upright', [
    (0, 0, True),
    (90, 0, False),
    (180, 0, False),
    (270, 0, False),
    (0, 90, False),
    (0, 180, False),
])
def test_images_upright(rotation, placement_rotate, upright):
    doc, page = _page_with_image(rotation, placement_rotate)
    assert pdf._images_upright(page) is upright
    doc.close()


def test_rotated_fixtures_are_rotated_scans():
    for path in (ROTATED_180, ROTATED_270):
        with pymupdf.open(path) as doc:
            assert all(not page.get_text().strip() and page.get_images() and page.rotation for page in doc), path


def test_rotated_scan_ocrs_the_rendered_page_not_the_raw_image():
    with patch('markdownExtractor.pdf.extract_image_md') as raw_image, \
            patch('markdownExtractor.pdf.extract_image_text', return_value='Modern Slavery Statement') as ocr:
        result = extract_pdf_md(ROTATED_270)
    raw_image.assert_not_called()
    assert ocr.call_count == 2  # one rendered page each
    assert ocr.call_args.args[1] == pdf.RENDERED_PAGE_ENHANCE_LEVEL
    assert result == 'Modern Slavery Statement\n\nModern Slavery Statement'


def test_upright_scan_still_ocrs_its_embedded_images():
    with patch('markdownExtractor.pdf.extract_image_md', return_value='Scanned text') as raw_image, \
            patch('markdownExtractor.pdf.extract_image_text') as rendered:
        extract_pdf_md(UPRIGHT_SCAN)
    assert raw_image.called
    rendered.assert_not_called()


@pytest.mark.parametrize('image_rect, is_a_scan', [
    (pymupdf.Rect(50, 50, 250, 150), False),  # a signature or a logo
    (pymupdf.Rect(0, 0, 595, 842), True),     # the whole page
    (pymupdf.Rect(0, 0, 595, 500), True),     # most of it
])
def test_image_coverage_tells_a_scan_from_a_page_with_a_small_image(image_rect, is_a_scan):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 20, 10), False)
    image.clear_with(255)
    page.insert_image(image_rect, pixmap=image, keep_proportion=False)
    assert (pdf._image_coverage(page) >= pdf.SCAN_IMAGE_COVERAGE) is is_a_scan
    doc.close()


def test_image_coverage_of_a_page_without_images_is_nothing():
    doc = pymupdf.open()
    assert pdf._image_coverage(doc.new_page()) == 0
    doc.close()


def test_outlined_text_fixture_has_no_text_layer_and_only_small_images():
    with pymupdf.open(OUTLINED_TEXT) as doc:
        page = doc[0]
        assert not page.get_text().strip() and page.get_images() and pdf._images_upright(page)
        assert pdf._image_coverage(page) < 0.05


def test_page_of_outlined_text_ocrs_the_rendered_page_not_its_signature_images():
    """OCR of the signature gave a stray character, which was taken for the page's text."""
    with patch('markdownExtractor.pdf.extract_image_md', return_value='![](doc.pdf ")")') as raw_image, \
            patch('markdownExtractor.pdf.extract_image_text', return_value='Section 172 Statement') as ocr:
        result = extract_pdf_md(OUTLINED_TEXT)
    raw_image.assert_not_called()
    assert ocr.call_count == 1
    assert result == 'Section 172 Statement'


@pytest.mark.skipif(shutil.which('tesseract') is None, reason='requires tesseract')
def test_outlined_text_is_read():
    text = extract(OUTLINED_TEXT, 'application/pdf')
    assert 'Section 172 Statement' in text
    assert 'section 172 of the Companies Act 2006' in text
    assert len(text.split()) > 300


@pytest.mark.skipif(shutil.which('tesseract') is None, reason='requires tesseract')
@pytest.mark.parametrize('path, expected', [
    (ROTATED_180, 'Modern Slavery Statement - 2019'),
    (ROTATED_270, 'SLAVERY & HUMAN TRAFFICKING STATEMENT'),
])
def test_rotated_scans_are_read_the_right_way_up(path, expected):
    assert expected in extract(path, 'application/pdf')


def test_pdf_saved_as_html_is_extracted_as_a_pdf(tmp_path):
    """A PDF is sometimes saved from a URL that was served as text/html; read as HTML it is gibberish."""
    disguised = tmp_path / 'statement.html'
    shutil.copy('tests/resources/test.pdf', disguised)
    result = extract(str(disguised), 'text/html')
    assert 'Test Document' in result
    assert '%PDF' not in result


def test_html_is_not_mistaken_for_a_pdf():
    from markdownExtractor import _is_pdf
    assert _is_pdf(b'%PDF-1.4\n...')
    assert _is_pdf(b'\xef\xbb\xbf\n%PDF-1.7\n...')
    assert not _is_pdf(b'<html><body>About our %PDF- downloads</body></html>')
    assert not _is_pdf('%PDF-1.4 as text')
