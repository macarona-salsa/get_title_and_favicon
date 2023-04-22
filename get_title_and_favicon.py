"""Get page title and favicon"""
import base64
import mimetypes
from urllib.parse import urljoin

import magic
import requests
from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager

REQUESTS_ADAPTER = HTTPAdapter(max_retries=3)


class ErrorElementNotFound(Exception):
    """Raised when an HTML element couldn't be found"""


class ErrorDataNotFound(Exception):
    """Raised when an HTML element doesn't contain the required data"""


def get_title_and_favicon(url):
    """
    Download title and favicon of the URL and return them as a
    tuple. Favicon is encoded as text using base64.
    """
    using_webdriver = False
    parse_only = SoupStrainer(["link", "title"])

    # Request page
    try:
        with requests.Session() as session:
            session.mount(url, REQUESTS_ADAPTER)
            page = session.get(url, timeout=5)
            page.raise_for_status()
            page_source = page.content
    except HTTPError as exc1:
        if exc1.response.status_code == 403:
            # Request again using a webdriver
            try:
                using_webdriver = True
                page_source = _get_page_webdriver(
                    "title",
                    'link[rel="icon"]',
                    url=url,
                )
            except TimeoutException as exc2:
                raise ErrorElementNotFound(
                    f"Title or favicon not found! url: {url}"
                ) from exc2
        else:
            raise exc1

    # Get elements
    while True:
        soup = bs(page_source, "lxml", parse_only=parse_only)
        icon_element = soup.find("link", rel="icon")
        title_element = soup.find("title")
        # Elements found
        if icon_element and title_element:
            break

        # Try launching a webdriver to load javascript and check again
        if not using_webdriver and soup.find("script"):
            using_webdriver = True
            page_source = _get_page_webdriver(
                "title",
                'link[rel="icon"]',
                url=url,
            )
            continue

        # Raise appropriate error
        raise ErrorElementNotFound(f"Favicon or title not found! url: {url}")

    # Get icon url
    try:
        icon_url = icon_element["href"]
    except KeyError as exc:
        raise ErrorDataNotFound(
            f"Favicon source URL not found! url: {url}"
        ) from exc
    icon_url = urljoin(url, icon_url)

    # Get favicon and title
    icon_encoded = _get_favicon_source(icon_url)
    try:
        title = str(title_element.string.strip())
    except AttributeError as exc:
        raise ErrorDataNotFound(f"Page title not found! url: {url}") from exc

    return icon_encoded, title


def _get_favicon_source(icon_url):
    """Get base64 source of favicon at url"""
    try:
        with requests.Session() as session:
            session.mount(icon_url, REQUESTS_ADAPTER)
            icon_response = session.get(icon_url, timeout=5)
            icon_response.raise_for_status()
            icon_source = icon_response.content
            icon_encoded = base64.b64encode(icon_source)
    except HTTPError as exc1:
        if exc1.response.status_code == 403:
            # Screenshot favicon using a webdriver
            try:
                icon_encoded = _screenshot_element(
                    "img",
                    url=icon_url,
                    page_load_strategy="normal",
                )
            except TimeoutException as exc2:
                raise ErrorElementNotFound(
                    f"Favicon element not found! url: {icon_url}"
                ) from exc2
        else:
            raise exc1

    return icon_encoded


def save_favicon(icon_encoded):
    """
    Decode a base64 encoded favicon and saves it to disk. File extension
    is guessed from magic bytes. File will have no extension if mime type
    couldn't be guessed.
    """
    icon = base64.b64decode(icon_encoded)

    # Guess file extension
    file_magic = magic.from_buffer(icon, mime=True)
    file_extension = mimetypes.guess_extension(file_magic)
    if file_extension is None:
        file_extension = ""

    with open(f"favicon{file_extension}", "wb") as file:
        file.write(icon)


def _get_page_webdriver(
    *css_selectors,
    url,
    page_load_strategy="none",
    timeout=10,
    poll_frequency=1,
):
    """
    Get page source after elements specified by css_selectors are
    finished loading
    """
    driver = _start_webdriver(url, page_load_strategy=page_load_strategy)

    # Check for existence of elements
    driver_wait = WebDriverWait(
        driver, timeout=timeout, poll_frequency=poll_frequency
    )
    for selector in css_selectors:
        driver_wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    page_source = driver.page_source
    driver.quit()
    return page_source


def _screenshot_element(
    css_selector, url, page_load_strategy="none", timeout=10, poll_frequency=1
):
    """
    Get value of src attribute of element specified by css_selector after
    element has finished loading
    """
    driver = _start_webdriver(url, page_load_strategy=page_load_strategy)
    driver_wait = WebDriverWait(
        driver, timeout=timeout, poll_frequency=poll_frequency
    )
    element = driver_wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )
    element_source = element.screenshot_as_base64
    driver.quit()
    return element_source


def _start_webdriver(url, page_load_strategy="none"):
    """Start a headless firefox webdriver"""
    service = Service(GeckoDriverManager().install())
    options = Options()
    options.add_argument("--headless")
    options.page_load_strategy = page_load_strategy
    options.unhandled_prompt_behavior = "ignore"
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)
    return driver
