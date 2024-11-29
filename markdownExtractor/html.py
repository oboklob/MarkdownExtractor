import logging
from bs4 import BeautifulSoup, Comment
from .image import download_and_extract_image_to_md
import re
import tempfile
from urllib.parse import urljoin
import copy

logger = logging.getLogger(__name__)

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


def md_from_html(body, url=None, extract_images: bool = True, strip_non_content: bool = True,
                 enhance_image_level: int = 2) -> str:
    """
    Given an HTML document, extract the text from it, and return it as a string.
    :param enhance_image_level:
    :param extract_images:
    :param url:
    :param body:
    :param strip_non_content:
    """
    soup = BeautifulSoup(body, 'html.parser')
    logger.debug(f"Converting HTML to Markdown...")

    # strip headers/footers/navigation etc
    if strip_non_content:
        soup = strip_decoration(soup)
        logger.debug(f"stripped decoration...")

    # convert relative links to absolute using the base_url if we have one
    if url:
        for link in soup.findAll('a', href=True):
            link['href'] = urljoin(url, link['href'])
        for img in soup.findAll('img', src=True):
            img['src'] = urljoin(url, img['src'])

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
        convert_images_to_text(soup, enhance_level=enhance_image_level)
        logger.debug(f"converted images to text...")

    texts = soup.findAll(string=True)
    visible_texts = filter(tag_visible, texts)
    stripped = u"\n".join(t.strip() for t in visible_texts)

    # remove triple newlines or larger and triple spaces or larger (and replace with double)
    stripped = re.sub(r'\n{3,}', '\n\n', stripped)
    stripped = re.sub(r' {3,}', '  ', stripped)

    return stripped.strip()


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


def strip_decoration(original_soup: BeautifulSoup) -> BeautifulSoup:
    """
    Given a BeautifulSoup object, attempt to remove all elements that are not part of the main content
    :param original_soup:
    :return:
    """

    # Remove semantic elements, if they don't contain main content indicators
    for tag_name in ['header', 'footer', 'nav', 'aside']:
        for element in original_soup.find_all(tag_name):
            element.decompose()
    # work on a copy of the soup so that we don't modify the original yet
    # using python's copy module to avoid the "A copy of a bs4.element.Tag is not supported" error
    soup = copy.copy(original_soup)

    for element in soup.find_all('form'):
        element.decompose()

    if not len(soup.get_text(strip=True)):
        # un-decompose the forms and try again
        soup = copy.copy(original_soup)

    # Compile regular expression patterns
    unwanted_class_id_pattern = re.compile(
        r'(?<![\w-])(nav|popup|menu|footer|header|sidebar|advert|modal|form|cookie|social|share|navigation|dialog|banner|menubar|menuitem)(?![\w-])')

    keep_class_id_pattern = re.compile(r'(content|page|wrapper|main)', re.IGNORECASE)  # Pattern to identify main content

    soup = _try_decomposing_elements(soup, unwanted_class_id_pattern, keep_class_id_pattern, ['class', 'id', 'role'])

    # harsher decomposing on unordered lists:

    unwanted_ul_class_pattern = re.compile(r'(nav|menu|menubar|menuitem)')

    soup = _try_decomposing_elements(soup, unwanted_ul_class_pattern, None, ['class'], ['li', 'ul'])

    return soup


def _try_decomposing_elements(soup: BeautifulSoup, unwanted_pattern: re.Pattern, keep_pattern: re.Pattern | None, attr: list = None, elements: list = None) -> BeautifulSoup:

    # TODO: problem items https://tiscreport.org/statement-processing/MSAStatement/587686
    # Find all elements where either the class or the id matches the unwanted pattern
    elements_to_decompose = []

    if attr is None:
        attr = ['class', 'id']

    if elements is None:
        # run it once for All elements
        elements = [True]

    targets = []
    for a in attr:
        for element in elements:
            targets += soup.find_all(element, {a: unwanted_pattern})

    for element in targets:
        # logger.debug(f"Found unwanted element: {element}")
        keep = False
        if keep_pattern is not None:
            for a in attr:
                if a in element.attrs and any(keep_pattern.search(cls) for cls in element[a]):
                    keep = True

        if keep or element.name == 'body':
            # don't remove if it's a keeper or the body tag
            continue

        elements_to_decompose.append(element)

    # Decompose collected elements
    for element in elements_to_decompose:
        backup_soup = copy.copy(soup)
        if element.name is not None:
            logger.debug(f"Decomposing: {element.name} {element.attrs}")
            element.decompose()
            if len(soup.get_text(strip=True)) == 0:
                # restore the soup because stripping this element removed all content
                logger.debug(f"Restoring soup because stripping {element} removed all content")
                soup = backup_soup

    logger.debug(f"Decomposed to:\n{soup.get_text()}")
    return soup


def convert_images_to_text(soup: BeautifulSoup, enhance_level=2):
    """
    Given a BeautifulSoup object, find all images and extract the text from them.
    :param soup:
    :param enhance_level: Enhance the image before extracting the text
    :return:
    """

    with tempfile.TemporaryDirectory() as tempDirectory:
        for img_tag in soup.find_all('img'):
            # Extract the src attribute
            if 'src' not in img_tag.attrs:
                continue

            # Extract the alt attribute if it exists
            alt_text = img_tag.get('alt', '')

            text_content = download_and_extract_image_to_md(img_tag['src'], tempDirectory, alt_text=alt_text,
                                                            enhance_level=enhance_level)

            if not text_content:
                continue

            # replace the img tag with the extracted text
            text_node = soup.new_tag('span')

            text_node.string = text_content
            # Insert the text right after the img tag
            img_tag.insert_after(text_node)
