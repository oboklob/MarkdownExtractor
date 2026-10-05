import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup, Comment
from markdownExtractor import html as html_module
from markdownExtractor.html import md_from_html, convert_links_to_markdown, convert_headings_to_markdown, \
    convert_emphasis_to_markdown, convert_lists_to_markdown, convert_images_to_text, tag_visible, \
    _extract_text_from_markdown_images


def test_md_from_html_with_valid_html():
    result = md_from_html('<p>Hello, World!</p>')
    assert result == 'Hello, World!'


def test_tag_visible_filters_comment_and_hidden_elements():
    soup = BeautifulSoup('<style>body{}</style><div><!-- Hidden --></div><p>Visible</p>', 'html.parser')
    hidden_text = next(soup.find('style').strings)
    comment = soup.find_all(string=lambda text: isinstance(text, Comment))[0]
    visible_text = soup.find('p').string

    assert not tag_visible(hidden_text)
    assert not tag_visible(comment)
    assert tag_visible(visible_text)

def test_md_from_html_with_relative_links():
    result = md_from_html('<p>Hello, <a href="world.html">World!</a></p>', url='http://example.com')
    assert result == 'Hello,\n[World!](http://example.com/world.html)'


def test_md_from_html_with_large_navigation():
    """A large, realistic site-wide nav (no semantic <nav> tag, just classed divs/uls) alongside a
    genuine article body should have the nav stripped and the article content kept. This needs a
    real article paragraph (not a one-liner) since trafilatura's extraction needs enough body text
    to distinguish the article from the surrounding chrome."""
    article = (
        'ACME Ltd is a global company dedicated to producing high quality goods for households '
        'everywhere. This page contains our latest announcements and news updates for shareholders '
        'and customers alike, spanning several sentences of real substantive content that should be '
        'retained by any reasonable content extractor.'
    )
    result = md_from_html("""<div class="wd_mobile-nav-wrapper">
    						<ul class="wd_mobile-nav">
    	<li class=""><a href="/welcome">ACME's Better Days Home</a></li>

    <li class="wd_has-children">
    	<a href="/about-us" target="_self">
    		About Us	</a><span class="wd_indicator"></span>	<ul class="wd_mobile-submenu">
    <li class="wd_submenu-item">
    	<a href="/kellogg-company-overview" target="_self" class="">ACME Company Overview</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/message-from-our-ceo" target="_self" class="">Message from our CEO</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/message-from-our-senior-vice-president" target="_self" class="">Message from the Sr. VP, Chief Global Corporate Affairs Officer</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/esg-oversight-and-management" target="_self" class="">ESG Oversight &amp; Management</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/wkkellogg-foundation" target="_self" class="">Relationship to W.K. ACME Foundation</a>
    </li>
    </ul>
    </li>
    <li class="wd_has-children">
    	<a href="/wellbeing" target="_self">
    		Wellbeing	</a><span class="wd_indicator"></span>	<ul class="wd_mobile-submenu">
    <li class="wd_submenu-item">
    	<a href="/our-approach-to-wellbeing" target="_self" class="">Our Approach to Wellbeing</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/responsible-marketing" target="_self" class="">Responsible Marketing</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/childhood-wellbeing-promise" target="_self" class="">Childhood Wellbeing Promise</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/food-safety" target="_self" class="">Food Safety</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/our-culinary-culture" target="_self" class="">Our Culinary Culture</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/healthier-lifestyles" target="_self" class="">Healthier Lifestyles</a>
    </li>
    </ul>
    </li>
    <li class="wd_has-children">
    	<a href="/hunger" target="_self">
    		Hunger	</a><span class="wd_indicator"></span>	<ul class="wd_mobile-submenu">
    <li class="wd_submenu-item">
    	<a href="/food-bank-partnerships" target="_self" class="">Food Bank Partnerships/Food Drives</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/child-feeding-programs" target="_self" class="">Child Feeding Programs</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/summer-hunger-programs" target="_self" class="">Summer Hunger Programs</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/disaster-relief" target="_self" class="">Disaster Relief</a>
    </li>
    </ul>
    </li>
    <li class="wd_has-children">
    	<a href="/sustainability" target="_self">
    		Sustainability	</a><span class="wd_indicator"></span>	<ul class="wd_mobile-submenu">
    <li class="wd_submenu-item">
    	<a href="/climate-action" target="_self" class="">Climate Action</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/renewable-electricity" target="_self" class="">Renewable Electricity</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/responsible-sourcing" target="_self" class="">Responsible Sourcing</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/sustainable-packaging" target="_self" class="">Sustainable Packaging</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/food-waste-reduction" target="_self" class="">Food Waste Reduction</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/water-efficiency" target="_self" class="">Water Efficiency</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/palm-oil" target="_self" class="">Palm Oil</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/deforestation" target="_self" class="">Deforestation</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/biodiversity" target="_self" class="">Biodiversity</a>
    </li>
    </ul>
    </li>
    <li class="wd_has-children">
    	<a href="/equity-diversity-inclusion" target="_self">
    		ED&amp;I	</a><span class="wd_indicator"></span>	<ul class="wd_mobile-submenu">
    <li class="wd_submenu-item">
    	<a href="/our-approach-to-edi" target="_self" class="">Our Approach to ED&amp;I</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/workforce" target="_self" class="">Workforce</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/business-employee-resource-groups" target="_self" class="">Business Employee Resource Groups</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/marketplace" target="_self" class="">Marketplace </a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/supplier-diversity" target="_self" class="">Supplier Diversity</a>
    </li>
    </ul>
    </li>
    <li class="wd_has-children">
    	<a href="/people" target="_self">
    		People	</a><span class="wd_indicator"></span>	<ul class="wd_mobile-submenu">
    <li class="wd_submenu-item">
    	<a href="/volunteerism" target="_self" class="">Volunteerism</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/supporting-our-hometown" target="_self" class="">Supporting Our Hometown</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/partnering-with-others" target="_self" class="">Partnering With Others</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/operating-ethically" target="_self" class="">Operating Ethically</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/human-rights" target="_self" class="">Human Rights</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/employee-safety" target="_self" class="">Employee Safety</a>
    </li>
    </ul>
    </li>
    <li class="wd_has-children active">
    	<a href="/reporting" target="_self">
    		Reporting	</a><span class="wd_indicator"></span>	<ul class="wd_mobile-submenu">
    <li class="wd_submenu-item">
    	<a href="/current-progress" target="_self" class="">Current Progress</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/materiality-united-nations-sustainable-development-goals" target="_self" class="">Materiality/U.N. SDGs</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/esg-a-to-z" target="_self" class="active">ESG A to Z</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/sasb" target="_self" class="">SASB</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/gri" target="_self" class="">GRI</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/tcfd" target="_self" class="">TCFD</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/cdp" target="_self" class="">CDP</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/stakeholder-engagement" target="_self" class="">Stakeholder Engagement</a>
    </li>
    <li class="wd_submenu-item">
    	<a href="/archives" target="_self" class="">Archives</a>
    </li>
    </ul>
    </li>
    </ul>

    					</div><p>{article}</p><p>Hello, <a href="world.html">World!</a></p>""".format(article=article), url='http://example.com')
    assert 'ACME Company Overview' not in result
    assert 'Message from our CEO' not in result
    assert article in result
    assert 'Hello, [World!](http://example.com/world.html)' in result


def test_md_from_html_does_not_include_yaml_frontmatter():
    """Regression guard: the title-recovery lookup must not switch the main extraction call over
    to trafilatura's with_metadata mode, which would prepend a YAML frontmatter block (title/url/
    hostname/date/...) to every result instead of just restoring the title as a heading."""
    article = (
        'ACME Ltd is a global company dedicated to producing high quality goods for households '
        'everywhere. This page contains our latest announcements and news updates for shareholders '
        'and customers alike, spanning several sentences of real substantive content that should be '
        'retained by any reasonable content extractor.'
    )
    html = f'<html><head><title>ACME News</title></head><body><h1>ACME News</h1><p>{article}</p></body></html>'

    result = md_from_html(html, url='http://example.com')

    assert not result.startswith('---')
    assert 'hostname:' not in result


def test_complex_situation():
    """Deeply-nested WordPress-style wrapper divs, plus a real <nav>, around a genuine article
    body: the nav should be stripped and the nested article content kept."""
    article = (
        'ACME Ltd is a global company dedicated to producing high quality goods for households '
        'everywhere. This page contains our latest announcements and news updates for shareholders '
        'and customers alike, spanning enough real substantive sentences to pass extraction '
        'thresholds reliably every time we run this test.'
    )
    nav_links = ''.join(f'<a href="/{i}">Nav {i}</a> ' for i in range(10))
    result = md_from_html(f"""
    <body class="page-template page-template-page-sidebar page-template-page-sidebar-php page page-id-15347" data-template="base.twig">
        <nav class="site-nav">{nav_links}</nav>
        <main id="content" role="main" class="site-main">
            <div class="wrap wrap--relative background-sidebar background-sidebar--overlap">
                <div class="grid grid--1-12--ng">
                    <section id="modules" class="modules-content page-content grid__item grid__item--span-8 switched ">
                        <div class="content-wrap content-wrap--right">
                            <div class="grid grid--1-8--cm">
                                <div class="grid__item grid__item--span-8 module-text">
                                    <div class="modules-content__text">
                                        <div class="wysiwyg">
                                            <p>{article}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>
                </div>
            </div>
        </main>
    </body>
    """, 'http://example.com')
    assert article in result
    assert 'Nav 0' not in result


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


def test_convert_lists_to_markdown_with_ordered_list():
    soup = BeautifulSoup('<ol><li>First</li><li>Second</li></ol>', 'html.parser')

    convert_lists_to_markdown(soup)

    assert str(soup) == '1. First\n2. Second\n'


@patch('markdownExtractor.html.download_and_extract_image_to_md')
def test_convert_images_to_text_with_valid_image(mock_download_and_extract_image_to_md):
    mock_download_and_extract_image_to_md.return_value = 'Image Text'
    soup = BeautifulSoup('<img src="http://example.com/image.jpg" alt="Example Image">', 'html.parser')
    convert_images_to_text(soup)
    texts = soup.find_all(string=True)
    stripped = u"\n".join(t.strip() for t in texts)
    assert stripped == 'Image Text'


@patch('markdownExtractor.html.download_and_extract_image_to_md')
def test_convert_images_to_text_skips_missing_src(mock_download_and_extract_image_to_md):
    soup = BeautifulSoup('<img alt="Example Image">', 'html.parser')

    convert_images_to_text(soup)

    mock_download_and_extract_image_to_md.assert_not_called()


def test_md_from_html_with_possible_full_removal():
    """A body whose class matches a 'nav-ish' token (e.g. 'clear-nav') must not wipe out a genuine
    article body just because of that class name."""
    article = (
        'ACME Ltd is a global company dedicated to producing high quality goods for households '
        'everywhere. This page contains our latest announcements and news updates for shareholders '
        'and customers alike, spanning several sentences of real substantive content that should be '
        'retained by any reasonable content extractor.'
    )
    html = f'<html><body class="clear-nav"><p>{article}</p><p>Hello, <a href="world.html">World!</a></p></body></html>'
    result = md_from_html(html, url='http://example.com')
    assert article in result
    assert 'Hello, [World!](http://example.com/world.html)' in result


def test_content_in_form_wrapper_survives_when_page_not_otherwise_empty():
    """Characterization test for the strip_decoration TODO bug: real content wrapped
    in a <form> is deleted (form removal has no per-element keep/undo check, only a
    whole-soup emptiness check), while unrelated content elsewhere on the page keeps
    the soup non-empty so the safety net never fires."""
    html = (
        '<html><body>'
        '<form id="statement-viewer" class="report-form">'
        '<h1>ACME Ltd Modern Slavery Statement 2024</h1>'
        '<p>This statement sets out the steps ACME Ltd has taken to ensure '
        'slavery and human trafficking is not taking place in our supply chains.</p>'
        '</form>'
        '<p>Site last updated January 2024.</p>'
        '</body></html>'
    )
    result = md_from_html(html, 'http://example.com')
    assert 'Modern Slavery Statement' in result
    assert 'slavery and human trafficking' in result


def test_content_in_unwanted_class_wrapper_survives_when_page_not_otherwise_empty():
    """Characterization test: real content wrapped in an element whose class matches
    the 'unwanted' pattern (and has no 'keep' token) is deleted, while unrelated
    content elsewhere on the page keeps the soup non-empty so the safety net never
    fires."""
    html = (
        '<html><body>'
        '<div class="promo social widget">'
        '<h1>Annual Sustainability Report</h1>'
        '<p>Full text of the report body goes here with real substantive content.</p>'
        '</div>'
        '<p>Cookies are used on this site.</p>'
        '</body></html>'
    )
    result = md_from_html(html, 'http://example.com')
    assert 'Sustainability Report' in result
    assert 'real substantive content' in result


@patch('markdownExtractor.html.download_and_extract_image_to_md')
def test_extract_text_from_markdown_images_replaces_image_syntax(mock_download_and_extract_image_to_md):
    mock_download_and_extract_image_to_md.return_value = 'Image Text'
    markdown_text = 'Before\n\n![alt text](http://example.com/image.jpg)\n\nAfter'

    result = _extract_text_from_markdown_images(markdown_text, '/tmp', enhance_image_level=2)

    mock_download_and_extract_image_to_md.assert_called_once_with(
        'http://example.com/image.jpg', '/tmp', alt_text='alt text', enhance_level=2)
    assert result == 'Before\n\nImage Text\n\nAfter'


@patch('trafilatura.extract')
def test_md_from_html_falls_back_when_trafilatura_finds_nothing(mock_extract):
    mock_extract.return_value = None
    article = (
        'ACME Ltd is a global company dedicated to producing high quality goods for households '
        'everywhere. This page contains our latest announcements and news updates for shareholders '
        'and customers alike, spanning several sentences of real substantive content that should be '
        'retained by any reasonable content extractor.'
    )
    html = f'<html><body><p>{article}</p></body></html>'

    result = md_from_html(html, url='http://example.com')

    assert article in result

CATS = 'tests/statement_extraction_fixtures/html_onetrust_preference_centre_cats_protection.html'


def _consent_page(body_attrs='', wrapper_class='page'):
    return f"""<html><body {body_attrs}>
    <div class="{wrapper_class}"><h1>Modern Slavery Statement</h1>
    <p>This statement sets out the steps Acme Widgets Ltd has taken during the financial year to ensure that
    slavery and human trafficking are not taking place in its business or its supply chains.</p></div>
    <div id="onetrust-consent-sdk"><div id="onetrust-pc-sdk"><div class="ot-main-content">
    <h2>Privacy Preference Center</h2><p>You are in control of what we do with your personal data. You can choose
    whether or not to allow certain types of cookies by selecting the different category headings.</p></div></div></div>
    </body></html>"""


def test_consent_dialog_is_removed_from_the_page():
    soup = BeautifulSoup(_consent_page(), 'html.parser')
    html_module._remove_consent_dialogs(soup)
    assert 'Privacy Preference Center' not in soup.get_text()
    assert 'Acme Widgets Ltd' in soup.get_text()


def test_consent_dialog_is_left_out_by_both_conversions():
    for strip_non_content in (True, False):
        result = md_from_html(_consent_page(), extract_images=False, strip_non_content=strip_non_content)
        assert 'Acme Widgets Ltd' in result
        assert 'Privacy Preference Center' not in result


def test_content_is_kept_when_its_wrapper_is_named_like_a_consent_dialog():
    """A <body> or wrapper can carry a class like cookie-consent: it holds the content, so it stays."""
    for page in (_consent_page(body_attrs='class="cookie-consent"'), _consent_page(wrapper_class='cookie-banner')):
        soup = BeautifulSoup(page, 'html.parser')
        html_module._remove_consent_dialogs(soup)
        assert 'Acme Widgets Ltd' in soup.get_text()
        assert 'Privacy Preference Center' not in soup.get_text()


def test_onetrust_preference_centre_is_not_taken_for_the_content():
    with open(CATS, encoding='utf-8', errors='replace') as f:
        result = md_from_html(f.read(), url='https://www.cats.org.uk/terms/modern-slavery-act-statement',
                              extract_images=False)
    assert 'This statement sets out the actions that Cats Protection is taking' in result
    assert 'Privacy Preference Center' not in result
