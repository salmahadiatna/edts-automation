from datetime import datetime
from pathlib import Path

import pytest
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import time
from selenium.common.exceptions import WebDriverException
# ==========================================
# CONFIGURATION
# ==========================================

BASE_URL = "https://www.klikindomaret.com/"
WAIT_SECONDS = 20

SCREENSHOT_DIR = Path(__file__).resolve().parent / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

LOWER = (
    "translate(normalize-space(.),"
    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"
)


# ==========================================
# SCREENSHOT
# ==========================================

def take_screenshot(driver, name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOT_DIR / f"{name}_{timestamp}.png"
    driver.save_screenshot(str(path))
    print(f"\nScreenshot saved: {path.resolve()}")
    return path


# ==========================================
# WAIT FOR PAGE LOAD
# ==========================================

def wait_for_page(driver):
    WebDriverWait(driver, WAIT_SECONDS).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


# ==========================================
# CLOUDFLARE
# ==========================================

CLOUDFLARE_KEYWORDS = [
    # English
    "just a moment",
    "verify you are human",
    "checking your browser",
    "performing security verification",
    # Indonesia (Cloudflare mengikuti bahasa browser)
    "tunggu sebentar",
    "verifikasi bahwa anda",
    "memverifikasi bahwa anda",
]


def is_cloudflare_page(driver):
    try:
        title = driver.title.lower()
        body = driver.find_element(By.TAG_NAME, "body").text.lower()
        combined = title + " " + body
        return any(keyword in combined for keyword in CLOUDFLARE_KEYWORDS)
    except Exception:
        return False


def check_cloudflare(driver, timeout=180):
    if not is_cloudflare_page(driver):
        return

    take_screenshot(driver, "CLOUDFLARE_BLOCKED")

    print("\nCloudflare verification detected.")
    print("Silakan selesaikan verifikasi di jendela Chrome Selenium.")
    print("Sistem akan mengecek otomatis setiap 3 detik...")

    try:
        WebDriverWait(driver, timeout, poll_frequency=3).until(
            lambda d: not is_cloudflare_page(d)
        )
        print("\nCloudflare verification selesai!")
        wait_for_page(driver)

    except TimeoutException:
        print("\nCloudflare belum selesai setelah batas waktu.")
        take_screenshot(driver, "CLOUDFLARE_TIMEOUT")
        pytest.skip("Cloudflare verification was not completed.")


# ==========================================
# CLOSE QR POPUP
# ==========================================

def close_popup(driver):
    """Return True jika popup tertutup atau memang tidak ada."""
    wait = WebDriverWait(driver, 10)

    try:
        modal = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div.modal.modal-open")
            )
        )
    except TimeoutException:
        print("\nModal tidak ditemukan atau sudah tertutup.")
        return True

    candidates = modal.find_elements(
        By.XPATH,
        ".//button | .//a | .//*[@role='button'] | .//span"
    )

    for element in candidates:
        try:
            if not element.is_displayed():
                continue

            text = element.text.strip().lower()
            aria = (element.get_attribute("aria-label") or "").lower()
            title = (element.get_attribute("title") or "").lower()
            classes = (element.get_attribute("class") or "").lower()

            if (
                text in ["×", "✕", "x"]
                or "close" in aria
                or "close" in title
                or "close" in classes
            ):
                try:
                    element.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", element)
                break

        except StaleElementReferenceException:
            continue
    else:
        print("\nTombol close popup belum ditemukan.")
        print(modal.get_attribute("outerHTML")[:1500])
        return False

    try:
        wait.until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "div.modal.modal-open")
            )
        )
    except TimeoutException:
        return False

    print("\nPopup berhasil ditutup!")
    return True


# ==========================================
# FIND ELEMENT BY TEXT
# ==========================================

def find_text_element(driver, text, tags="a|button|span", timeout=WAIT_SECONDS):
    tag_expression = " or ".join(f"self::{tag}" for tag in tags.split("|"))
    xpath = (
        f"//*[({tag_expression})]"
        f"[contains({LOWER},'{text.lower()}')]"
    )

    def find_element(d):
        for element in d.find_elements(By.XPATH, xpath):
            try:
                if element.is_displayed() and element.is_enabled():
                    return element
            except StaleElementReferenceException:
                continue
        return False

    return WebDriverWait(driver, timeout).until(find_element)


# ==========================================
# CLICK ELEMENT
# ==========================================

def click_element(driver, element):
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", element
    )

    WebDriverWait(driver, WAIT_SECONDS).until(
        lambda d: element.is_displayed() and element.is_enabled()
    )

    try:
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)


# ==========================================
# CLICK MENU ITEM
# ==========================================

def click_menu_item(driver, text, tag):
    locator = (
        By.XPATH,
        f"//{tag}[contains(@class, 'menu-list') "
        f"and normalize-space()='{text}']"
    )

    def find_visible_element(d):
        for element in d.find_elements(*locator):
            try:
                if element.is_displayed() and element.is_enabled():
                    return element
            except StaleElementReferenceException:
                continue
        return False

    element = WebDriverWait(driver, WAIT_SECONDS).until(find_visible_element)

    print(f"\nMENU FOUND: {text}")
    click_element(driver, element)
    print(f"SUCCESS CLICK: {text}")

    return element


# ==========================================
# SELECT PRODUCT
# ==========================================

from urllib.parse import urlparse

EXTERNAL_DOMAINS = (
    "apple.com", "google.com", "play.google", "facebook.com",
    "instagram.com", "twitter.com", "x.com", "youtube.com", "tiktok.com",
)


def is_internal_product_link(href):
    if not href:
        return False
    parsed = urlparse(href)
    host = parsed.netloc.lower()
    path = parsed.path.lower()

    if "klikindomaret.com" not in host:
        return False
    if any(domain in host for domain in EXTERNAL_DOMAINS):
        return False
    if "/category/" in path or path.rstrip("/") == "":
        return False
    return True


def select_first_product(driver):
    print("\nSTEP 5: Find honey products")

    take_screenshot(driver, "honey_product_listing")
    listing_url = driver.current_url
    print("LISTING URL:", listing_url)

    def find_product_link(d):
        # Prioritas 1: link yang jelas produk
        for link in d.find_elements(By.CSS_SELECTOR, "a[href*='/product/']"):
            try:
                if link.is_displayed() and is_internal_product_link(link.get_attribute("href")):
                    return link
            except StaleElementReferenceException:
                continue

        # Prioritas 2: link internal ber-gambar di area utama (bukan header/footer/nav)
        for link in d.find_elements(
            By.XPATH,
            "//a[@href][.//img]"
            "[not(ancestor::header) and not(ancestor::footer) and not(ancestor::nav)]",
        ):
            try:
                if link.is_displayed() and is_internal_product_link(link.get_attribute("href")):
                    return link
            except StaleElementReferenceException:
                continue
        return False

    try:
        product_link = WebDriverWait(driver, WAIT_SECONDS).until(find_product_link)
    except TimeoutException:
        take_screenshot(driver, "product_link_not_found")
        print("\nLink internal yang terlihat di halaman:")
        for a in driver.find_elements(By.CSS_SELECTOR, "a[href]")[:40]:
            try:
                if a.is_displayed():
                    print(" ", a.get_attribute("href"))
            except Exception:
                pass
        raise

    href = product_link.get_attribute("href")
    print("PRODUCT HREF:", href)
    take_screenshot(driver, "product_before_click")

    handles_before = driver.window_handles
    click_element(driver, product_link)

    # Kalau ternyata membuka tab baru, pindah ke tab itu
    WebDriverWait(driver, WAIT_SECONDS).until(
        lambda d: d.current_url != listing_url or len(d.window_handles) > len(handles_before)
    )
    if len(driver.window_handles) > len(handles_before):
        driver.switch_to.window(driver.window_handles[-1])

    wait_for_page(driver)
    driver = check_cloudflare(driver) or driver

    print("PRODUCT DETAIL URL:", driver.current_url)
    take_screenshot(driver, "product_detail")
    return driver
# ==========================================
# FIND ADD TO CART BUTTON
# ==========================================

def find_add_to_cart_button(driver):
    print("\nSTEP 6: Find '+ Keranjang' button")

    # Hindari ikon keranjang di header/navbar
    xpath = (
        "//*[self::button or @role='button']"
        f"[contains({LOWER},'keranjang')]"
        "[not(ancestor::header) and not(ancestor::nav)]"
    )

    def find_button(d):
        fallback = None

        for button in d.find_elements(By.XPATH, xpath):
            try:
                if not button.is_displayed() or not button.is_enabled():
                    continue

                # Utamakan yang bertuliskan "+ Keranjang"
                if "+" in button.text:
                    return button
                if fallback is None:
                    fallback = button

            except StaleElementReferenceException:
                continue

        return fallback or False

    button = WebDriverWait(driver, WAIT_SECONDS).until(find_button)

    print("BUTTON TEXT:", button.text)
    return button


# ==========================================
# VERIFY LOGIN POPUP
# ==========================================

LOGIN_KEYWORDS = [
    "login",
    "masuk",
    "nomor handphone",
    "nomor hp",
    "no. handphone",
    "password",
]


def verify_login_popup(driver):
    print("\nSTEP 8: Verify login popup")

    def find_login_popup(d):
        for selector in ["div.modal.modal-open", "[role='dialog']", ".modal"]:
            for modal in d.find_elements(By.CSS_SELECTOR, selector):
                try:
                    if not modal.is_displayed():
                        continue

                    modal_text = modal.text.lower()
                    if any(key in modal_text for key in LOGIN_KEYWORDS):
                        return modal

                except StaleElementReferenceException:
                    continue
        return False

    try:
        popup = WebDriverWait(driver, WAIT_SECONDS).until(find_login_popup)
    except TimeoutException:
        take_screenshot(driver, "login_popup_not_found")
        return None

    print("LOGIN POPUP TEXT:\n", popup.text)
    take_screenshot(driver, "login_popup")
    return popup