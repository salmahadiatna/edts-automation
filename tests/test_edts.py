from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import (
    BASE_URL,
    WAIT_SECONDS,
    check_cloudflare,
    click_element,
    click_menu_item,
    close_popup,
    find_add_to_cart_button,
    find_text_element,
    select_first_product,
    take_screenshot,
    verify_login_popup,
    wait_for_page,
)


def test_guest_is_prompted_to_login_when_adding_honey_to_cart(driver):

    # STEP 1: Open website
    print("\nSTEP 1: Open Klik Indomaret")
    driver.get(BASE_URL)

    wait_for_page(driver)
    check_cloudflare(driver)

    print("CURRENT URL:", driver.current_url)
    print("PAGE TITLE:", driver.title)

    assert "klikindomaret" in driver.current_url.lower()
    take_screenshot(driver, "homepage")

    # STEP 2: Close QR popup
    print("\nSTEP 2: Close QR popup")
    assert close_popup(driver), "QR popup gagal ditutup!"

    # STEP 3: Open category menu
    print("\nSTEP 3: Open category menu")
    category_element = find_text_element(driver, "Kategori", tags="a|button|span")
    click_element(driver, category_element)
    check_cloudflare(driver)

    WebDriverWait(driver, WAIT_SECONDS).until(
        lambda d: "kategori belanja"
        in d.find_element(By.TAG_NAME, "body").text.lower()
    )
    take_screenshot(driver, "category_menu")

    # STEP 4: Select Makanan
    print("\nSTEP 4: Select Makanan")
    click_menu_item(driver, "Makanan", "button")
    take_screenshot(driver, "makanan_submenu")

    # STEP 4.1: Find Madu category
    print("\nSTEP 4.1: Find Madu category")
    honey_link = WebDriverWait(driver, WAIT_SECONDS).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//a[contains(@href, '/category/makanan/sarapan-selai/madu')]")
        )
    )

    # STEP 4.2: Click Madu
    print("\nSTEP 4.2: Open Madu category")
    click_element(driver, honey_link)
    wait_for_page(driver)
    check_cloudflare(driver)
    assert "madu" in driver.current_url.lower(), "Tidak berada di kategori Madu!"
    take_screenshot(driver, "honey_category")

    # STEP 5: Select one honey product
    select_first_product(driver)

    # STEP 6: Find Add to Cart button
    add_button = find_add_to_cart_button(driver)

    # STEP 7: Click + Keranjang
    print("\nSTEP 7: Click + Keranjang")
    click_element(driver, add_button)
    take_screenshot(driver, "after_add_to_cart")

    # STEP 8: Verify login popup (guest)
    popup = verify_login_popup(driver)
    assert popup is not None, (
        "Popup login tidak muncul setelah klik '+ Keranjang' sebagai guest"
    )

    print(
        "\nTEST PASSED: Guest user is prompted to login "
        "when adding honey product to cart!"
    )