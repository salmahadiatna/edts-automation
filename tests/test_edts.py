
import os
import pytest

from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# CONFIGURATION
BASE_URL = "https://www.klikindomaret.com/"
WAIT_SECONDS = 20

SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)


# PYTEST REPORT HOOK
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


# BROWSER FIXTURE
@pytest.fixture
def driver(request):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    if os.getenv("HEADLESS") == "1":
        options.add_argument("--headless=new")

    browser = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    browser.implicitly_wait(0)

    yield browser

    # Screenshot automatically when test fails
    if (
        hasattr(request.node, "rep_call")
        and request.node.rep_call.failed
    ):
        take_screenshot(browser, "FAILED")

    browser.quit()


# SCREENSHOT FUNCTION
def take_screenshot(driver, name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    screenshot_path = (
        SCREENSHOT_DIR / f"{name}_{timestamp}.png"
    )

    driver.save_screenshot(str(screenshot_path))

    print(f"\nScreenshot saved: {screenshot_path}")


# WAIT FOR PAGE LOAD
def wait_for_page(driver):
    WebDriverWait(driver, WAIT_SECONDS).until(
        lambda d: d.execute_script(
            "return document.readyState"
        ) == "complete"
    )


# CLOSE QR POPUP
def close_popup(driver):
    close_selectors = [
        (By.CSS_SELECTOR, "button[aria-label='Close']"),
        (By.CSS_SELECTOR, "button[aria-label='close']"),
        (By.CSS_SELECTOR, "button[title='Close']"),
        (
            By.XPATH,
            "//*[normalize-space(text())='×' "
            "or normalize-space(text())='✕']"
        ),
        (
            By.XPATH,
            "//*[contains(@class,'close') "
            "or contains(@class,'Close')]"
        )
    ]

    for by, selector in close_selectors:
        try:
            elements = driver.find_elements(by, selector)

            for element in elements:
                if element.is_displayed():
                    driver.execute_script(
                        "arguments[0].click();",
                        element
                    )

                    print("Popup berhasil ditutup!")

                    return True

        except Exception:
            continue

    print("Popup tidak ditemukan atau sudah tertutup.")
    return False


# FIND ELEMENT BY TEXT
def find_text_element(
    driver,
    text,
    tags="a|button|span|div",
    timeout=WAIT_SECONDS
):
    tag_expression = " or ".join(
        f"self::{tag}" for tag in tags.split("|")
    )

    xpath = (
        f"//*[({tag_expression})]"
        f"[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),"
        f"'{text.lower()}')]"
    )

    def find_smallest_visible(d):
        elements = d.find_elements(By.XPATH, xpath)

        visible_elements = []

        for element in elements:
            try:
                if element.is_displayed():
                    visible_elements.append(element)
            except StaleElementReferenceException:
                continue

        if visible_elements:
            return min(
                visible_elements,
                key=lambda el: len(el.text.strip())
            )

        return False

    return WebDriverWait(driver, timeout).until(
        find_smallest_visible
    )


# CLICK ELEMENT
def click_element(driver, element):
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        element
    )

    WebDriverWait(driver, WAIT_SECONDS).until(
        lambda d: element.is_displayed() and element.is_enabled()
    )

    try:
        element.click()

    except ElementClickInterceptedException:
        raise Exception(
            "Element terhalang popup atau overlay."
        )


# CLICK BY TEXT
def click_text(driver, text, tags="a|button|span|div"):
    element = find_text_element(
        driver,
        text,
        tags
    )

    click_element(driver, element)

    print(f"Clicked: {text}")

    return element


# MAIN TEST
def test_user_can_add_honey_product_to_cart_without_login(driver):

    # STEP 1: Open website
    print("\nSTEP 1: Open Klik Indomaret")

    driver.get(BASE_URL)
    wait_for_page(driver)

    assert "klikindomaret" in driver.current_url.lower()

    # STEP 2: Close QR popup
    print("\nSTEP 2: Close QR popup")

    close_popup(driver)

    # STEP 3: Select meta category Makanan
    print("\nSTEP 3: Select category Makanan")

    try:
        click_text(driver, "Kategori", tags="a|button|span")
    except TimeoutException:
        print("Menu Kategori sudah terbuka atau tidak diperlukan.")

    click_text(driver, "Makanan")

    # STEP 4: Select category Madu
    print("\nSTEP 4: Select category Madu")

    click_text(driver, "Madu")

    # STEP 5: Select one honey product
    print("\nSTEP 5: Select honey product")

    product_xpath = (
        "//a[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        "'madu')]"
    )

    def find_product(d):
        elements = d.find_elements(By.XPATH, product_xpath)

        for element in elements:
            try:
                if (
                    element.is_displayed()
                    and len(element.text.strip()) > 3
                ):
                    return element
            except StaleElementReferenceException:
                continue

        return False

    product = WebDriverWait(driver, WAIT_SECONDS).until(
        find_product
    )

    print(f"Selected product: {product.text}")

    click_element(driver, product)

    # STEP 6: Verify product detail page
    print("\nSTEP 6: Verify product detail")

    WebDriverWait(driver, WAIT_SECONDS).until(
        lambda d: "madu" in
        d.find_element(By.TAG_NAME, "body").text.lower()
    )

    # STEP 7: Click Add to Cart
    print("\nSTEP 7: Click Add to Cart")

    add_button_xpath = (
        "//button[contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        "'keranjang') or "
        "contains(translate(normalize-space(.),"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
        "'tambah')]"
    )

    add_button = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.element_to_be_clickable(
            (By.XPATH, add_button_xpath)
        )
    )

    click_element(driver, add_button)

    # STEP 8: Verify successful addition
    print("\nSTEP 8: Verify cart result")

    success_keywords = [
        "berhasil ditambahkan",
        "ditambahkan ke keranjang",
        "berhasil ditambahkan ke keranjang"
    ]

    WebDriverWait(driver, WAIT_SECONDS).until(
        lambda d: any(
            keyword in d.find_element(
                By.TAG_NAME, "body"
            ).text.lower()
            for keyword in success_keywords
        )
    )

    print("\nTEST PASSED: Product added to cart!")
