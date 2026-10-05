import logging
import trafilatura
from bs4 import BeautifulSoup, Comment
from .image import download_and_extract_image_to_md
import re
import tempfile
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

MARKDOWN_IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)')

# The containers that cookie consent managers inject into a page (which a saved, rendered page includes)
CONSENT_DIALOG_SELECTORS = (
    '#onetrust-consent-sdk', '#onetrust-banner-sdk', '#onetrust-pc-sdk', '.optanon-alert-box-wrapper',  # OneTrust
    '#CybotCookiebotDialog', '#CybotCookiebotDialogBodyUnderlay', '#CookiebotWidget',  # Cookiebot
    '.cky-consent-container', '.cky-modal', '.cky-preference-center',  # CookieYes
    '#cookie-law-info-bar', '#cookie-law-info-again', '.cli-modal',  # GDPR Cookie Consent
    '#cmplz-cookiebanner-container', '.cmplz-cookiebanner',  # Complianz
    '#moove_gdpr_cookie_modal', '#moove_gdpr_cookie_info_bar',  # GDPR Cookie Compliance
    '#BorlabsCookieBox', '#iubenda-cs-banner', '#didomi-host', '#usercentrics-root',
    '.qc-cmp2-container', '#qc-cmp2-container',  # Quantcast
    '#truste-consent-track', '#truste-consent-content', '.truste_box_overlay', '.truste_overlay',  # TrustArc
    '.osano-cm-window', '#cookiescript_injected', '#cookiescript_injected_wrapper',
    '.termly-styles-root', '#termly-code-snippet-support', '#hs-eu-cookie-confirmation',
    '#coiOverlay', '#coi-banner-wrapper', '#ccc',  # Cookie Information, Civic Cookie Control
    '.cc-window', '#cookie-notice', '.cookie-notice', '#cookieConsent', '#cookie-consent', '.cookie-consent',
    '#cookie-banner', '.cookie-banner', '#cookiebanner',
)

def tag_visible(element: BeautifulSoup) -> bool:
    """
    Given a BeautifulSoup element, return True if it should be visible in the output, False otherwise
    :param element:
    :return:
    """
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def _resolve_relative_urls(body, url: str = None) -> BeautifulSoup:
    """
    Parse body into a BeautifulSoup object, converting relative links/image srcs to absolute using url as the base
    :param body:
    :param url:
    :return:
    """
    soup = BeautifulSoup(body, 'html.parser')
    if url:
        for link in soup.find_all('a', href=True):
            link['href'] = urljoin(url, link['href'])
        for img in soup.find_all('img', src=True):
            img['src'] = urljoin(url, img['src'])
    return soup


def _remove_consent_dialogs(soup: BeautifulSoup) -> None:
    """
    Remove cookie consent dialogs from the page. They are never the content, and trafilatura can
    mistake one for it: OneTrust's preference centre is marked up as "ot-main-content", so for a
    page with no <main> or <article> the cookie settings were returned instead of the page.

    An element that holds the page's content is left alone, whatever it is called (a wrapper or
    <body> can carry a class like "cookie-consent").
    """
    page_text = len(soup.get_text(strip=True))
    for selector in CONSENT_DIALOG_SELECTORS:
        for element in soup.select(selector):
            if element.decomposed or element.name in ('html', 'body', 'main', 'article'):
                continue
            if element.find(['main', 'article']) or len(element.get_text(strip=True)) > page_text / 2:
                continue
            element.decompose()


def _collapse_whitespace(text: str) -> str:
    # remove triple newlines or larger and triple spaces or larger (and replace with double)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {3,}', '  ', text)
    return text.strip()


def md_from_html(body, url=None, extract_images: bool = True, strip_non_content: bool = True,
                 enhance_image_level: int = 2, temp_directory: str = None) -> str:
    """
    Given an HTML document, extract the text from it, and return it as a string.
    :param temp_directory: Optionally passed temporary directory to use for image extraction
    :param enhance_image_level:
    :param extract_images:
    :param url:
    :param body:
    :param strip_non_content:
    """
    logger.debug(f"Converting HTML to Markdown...")

    if strip_non_content:
        text = _md_from_html_trafilatura(body, url=url, extract_images=extract_images,
                                         enhance_image_level=enhance_image_level, temp_directory=temp_directory)
        if text:
            return text
        logger.debug(f"trafilatura found no content, falling back to full-page conversion...")

    return _md_from_html_legacy(body, url=url, extract_images=extract_images,
                                enhance_image_level=enhance_image_level, temp_directory=temp_directory)


def _md_from_html_trafilatura(body, url=None, extract_images: bool = True, enhance_image_level: int = 2,
                              temp_directory: str = None) -> str:
    """
    Extract the main content from an HTML document as markdown, using trafilatura to discard
    boilerplate (nav/header/footer/ads/etc). Falls back to a less strict pass, and returns '' if
    trafilatura can't find any content at all so the caller can fall back further.
    """
    soup = _resolve_relative_urls(body, url)
    _remove_consent_dialogs(soup)
    html_str = str(soup)

    try:
        text = trafilatura.extract(html_str, url=url, output_format='markdown', include_images=True,
                                   include_links=True, include_comments=False)
        if not text:
            text = trafilatura.extract(html_str, url=url, output_format='markdown', include_images=True,
                                       include_links=True, include_comments=False, favor_recall=True)
    except Exception as e:
        logger.debug(f"trafilatura extraction raised {e}")
        text = None

    if not text:
        return ''

    logger.debug(f"extracted main content with trafilatura...")

    # trafilatura excludes a recognized page title from the body text - restore it as a heading.
    # extensive=False skips htmldate's exhaustive date-guessing pass, which can otherwise take
    # seconds on some pages for metadata (date/author) we don't even use here.
    try:
        title = trafilatura.extract_metadata(html_str, default_url=url, extensive=False).title
    except Exception:
        title = None
    if title and title not in text:
        text = f"# {title}\n\n{text}"

    if extract_images:
        if temp_directory:
            text = _extract_text_from_markdown_images(text, temp_directory, enhance_image_level)
        else:
            with tempfile.TemporaryDirectory() as tmp_directory:
                text = _extract_text_from_markdown_images(text, tmp_directory, enhance_image_level)
        logger.debug(f"converted images to text...")

    return _collapse_whitespace(text)


def _md_from_html_legacy(body, url=None, extract_images: bool = True, enhance_image_level: int = 2,
                         temp_directory: str = None) -> str:
    """
    Convert an entire HTML document to markdown verbatim, without any boilerplate removal
    (other than cookie consent dialogs).
    """
    soup = _resolve_relative_urls(body, url)
    _remove_consent_dialogs(soup)
    logger.debug(f"converted relative links to absolute...")

    # Annotate hyperlinks with their href attribute
    convert_links_to_markdown(soup)
    logger.debug(f"converted links to markdown...")
    convert_headings_to_markdown(soup)
    logger.debug(f"converted headings to markdown...")
    convert_emphasis_to_markdown(soup)
    logger.debug(f"converted emphasis to markdown...")
    convert_lists_to_markdown(soup)
    logger.debug(f"converted lists to markdown...")

    # extract text from any embedded images
    if extract_images:
        convert_images_to_text(soup, enhance_level=enhance_image_level, temp_directory=temp_directory)
        logger.debug(f"converted images to text...")

    texts = soup.find_all(string=True)
    visible_texts = filter(tag_visible, texts)
    stripped = u"\n".join(t.strip() for t in visible_texts)

    return _collapse_whitespace(stripped)


def _extract_text_from_markdown_images(markdown_text: str, temp_directory: str, enhance_image_level: int) -> str:
    """
    Given markdown text containing image references (as produced by trafilatura's include_images=True),
    replace each image reference with OCR'd/extracted text via the existing image pipeline.
    :param markdown_text:
    :param temp_directory:
    :param enhance_image_level:
    :return:
    """
    def _replace(match: re.Match) -> str:
        alt_text, src = match.group(1), match.group(2)
        return download_and_extract_image_to_md(src, temp_directory, alt_text=alt_text,
                                                 enhance_level=enhance_image_level)

    return MARKDOWN_IMAGE_PATTERN.sub(_replace, markdown_text)


def convert_links_to_markdown(soup: BeautifulSoup) -> None:
    """
    Given a BeautifulSoup object, find all links and convert them to markdown
    :param soup:
    :return:
    """
    for a in soup.find_all('a', href=True):
        link_text = a.get_text()
        href = a['href']
        markdown_link = f"[{link_text}]({href})"
        a.replace_with(markdown_link)


def convert_headings_to_markdown(soup: BeautifulSoup) -> None:
    """
    Given a BeautifulSoup object, find all headings and convert them to markdown
    :param soup:
    :return:
    """
    for level in range(1, 7):
        for header in soup.find_all(f'h{level}'):
            header_text = header.get_text()
            markdown_header = f"{'#' * level} {header_text}"
            header.replace_with(markdown_header)


def convert_emphasis_to_markdown(soup: BeautifulSoup) -> None:
    """
    Given a BeautifulSoup object, find all bold and italic tags and convert them to markdown
    :param soup:
    :return:
    """
    for bold in soup.find_all('b'):
        bold_text = bold.get_text()
        bold.replace_with(f"**{bold_text}**")

    for italic in soup.find_all('i'):
        italic_text = italic.get_text()
        italic.replace_with(f"*{italic_text}*")


def convert_lists_to_markdown(soup: BeautifulSoup) -> None:
    """
    Given a BeautifulSoup object, find all lists and convert them to markdown
    :param soup:
    :return:
    """
    # Handle unordered lists
    for ul in soup.find_all('ul'):
        for li in ul.find_all('li'):
            li_text = li.get_text()
            li.replace_with(f"* {li_text}\n")

    # Handle ordered lists
    for ol in soup.find_all('ol'):
        for index, li in enumerate(ol.find_all('li'), start=1):
            li_text = li.get_text()
            li.replace_with(f"{index}. {li_text}\n")

    # Remove the list tags themselves, leaving only the list items
    for list_tag in soup.find_all(['ul', 'ol']):
        list_tag.unwrap()


def convert_images_to_text(soup: BeautifulSoup, enhance_level=2, temp_directory: str = None) -> None:
    """
    Given a BeautifulSoup object, find all images and extract the text from them.
    :param temp_directory:
    :param soup:
    :param enhance_level: Enhance the image before extracting the text
    :return:
    """

    with tempfile.TemporaryDirectory() as tempDirectory:
        preferred_temp_directory = temp_directory or tempDirectory
        for img_tag in soup.find_all('img'):
            # Extract the src attribute
            if 'src' not in img_tag.attrs:
                continue

            # Extract the alt attribute if it exists
            alt_text = img_tag.get('alt', '')

            text_content = download_and_extract_image_to_md(img_tag['src'], preferred_temp_directory, alt_text=alt_text,
                                                            enhance_level=enhance_level)

            if not text_content:
                continue

            # replace the img tag with the extracted text
            text_node = soup.new_tag('span')

            text_node.string = text_content
            # Insert the text right after the img tag
            img_tag.insert_after(text_node)
