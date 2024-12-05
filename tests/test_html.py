import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from markdownExtractor.html import md_from_html, convert_links_to_markdown, convert_headings_to_markdown, \
    convert_emphasis_to_markdown, convert_lists_to_markdown, strip_decoration, convert_images_to_text
import re


@patch('markdownExtractor.html.BeautifulSoup')
def test_md_from_html_with_valid_html(mock_soup):
    mock_soup.return_value = BeautifulSoup('<p>Hello, World!</p>', 'html.parser')
    result = md_from_html('<p>Hello, World!</p>')
    assert result == 'Hello, World!'

@patch('markdownExtractor.html.BeautifulSoup')
def test_md_from_html_with_relative_links(mock_soup):
    mock_soup.return_value = BeautifulSoup('<p>Hello, <a href="world.html">World!</a></p>', 'html.parser')
    result = md_from_html('<p>Hello, <a href="world.html">World!</a></p>', url='http://example.com')
    assert result == 'Hello,\n[World!](http://example.com/world.html)'

def test_md_from_html_with_large_navigation():
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

    					</div><p>Hello, <a href="world.html">World!</a></p>""", url='http://example.com')
    assert result == 'Hello,\n[World!](http://example.com/world.html)'


def test_divs_not_removed_for_having_near_excude_classes():
    result = md_from_html('<html><body class="sidebar"><div class="main-sidebar"><div id="not-a-popup">Hello World!</div></div></body></html>', 'http://example.com')

    assert result == 'Hello World!'

def test_item_not_removed_because_empty_result():
    result = md_from_html('<html><body class="sidebar"><div class="main-sidebar"><div role="navigation">Hello World!</div></div></body></html>', 'http://example.com')

    assert result == 'Hello World!'

def test_roles_removed():
    result = md_from_html('<html><body class="sidebar"><div class="main-sidebar">Hello World!<div role="navigation"> Goodbye World!</div></div></body></html>', 'http://example.com')

    assert result == 'Hello World!'

def test_complex_situation():
    result = md_from_html("""
    <body class="page-template page-template-page-sidebar page-template-page-sidebar-php page page-id-15347" data-template="base.twig">
        <main id="content" role="main" class="site-main">	                  
            <div class="wrap wrap--relative background-sidebar background-sidebar--overlap">
                <div class="grid grid--1-12--ng">
                    <section id="modules" class="modules-content page-content grid__item grid__item--span-8 switched ">
                        <div class="content-wrap content-wrap--right">
                            <div class="grid grid--1-8--cm">
                                <div class="grid__item grid__item--span-8 module-text">
                                    <div class="modules-content__text">
                                        <div class="wysiwyg">
                                            <p>Hello</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>    
                </div>
            </div>
        </main>
         World!
    </body>
    """, 'http://example.com')
    assert result == 'Hello\n\nWorld!'


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


@patch('markdownExtractor.html.download_and_extract_image_to_md')
def test_convert_images_to_text_with_valid_image(mock_download_and_extract_image_to_md):
    mock_download_and_extract_image_to_md.return_value = 'Image Text'
    soup = BeautifulSoup('<img src="http://example.com/image.jpg" alt="Example Image">', 'html.parser')
    convert_images_to_text(soup)
    texts = soup.findAll(string=True)
    stripped = u"\n".join(t.strip() for t in texts)
    assert stripped == 'Image Text'


@patch('markdownExtractor.html.BeautifulSoup')
def test_md_from_html_with_possible_full_removal(mock_soup):
    mock_soup.return_value = BeautifulSoup('<html><body class="clear-nav"><p>Hello, <a href="world.html">World!</a></p></body></html>', 'html.parser')
    result = md_from_html('<html><body class="clear-nav"><p>Hello, <a href="world.html">World!</a></p></body></html>', url='http://example.com')
    assert result == 'Hello,\n[World!](http://example.com/world.html)'

@patch('markdownExtractor.html.BeautifulSoup')
def test_md_from_html_with_less_agressive_strip_needed(mock_soup):
    mock_soup.return_value = BeautifulSoup(
        '<html><body class="clear-nav"><ul class="nav"><li>This is a nav item</li></ul><p class="not-nav">Hello, <a href="world.html" class="random">World!</a></p></body></html>', 'html.parser')
    result = md_from_html(
        '<html><body class="clear-nav"><ul class="nav"><li>This is a nav item</li></ul><p class="not-nav">Hello, <a href="world.html" class="random">World!</a></p></body></html>',
        url='http://example.com')
    assert result == 'Hello,\n[World!](http://example.com/world.html)'

def test_md_from_html_with_less_agressive_strip_needed_2():
    result = md_from_html(
        '<html><body class="clear-nav"><form><ul class="nav"><li>This is a nav item</li></ul><p class="not-nav">Hello, <a href="world.html" class="random">World!</a></p></form></body></html>',
        url='http://example.com')
    assert result == 'Hello,\n[World!](http://example.com/world.html)'