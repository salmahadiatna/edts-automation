import os
import socket
from pathlib import Path

import pytest
from selenium import webdriver

from helpers import take_screenshot

ROOT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = ROOT_DIR / "chrome_test_profile"

DEBUG_HOST = "127.0.0.1"
DEBUG_PORT = 9222

def debug_port_open():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((DEBUG_HOST, DEBUG_PORT)) == 0



@pytest.fixture
def driver(request):
    # Default: attach. Set ATTACH_CHROME=0 untuk meluncurkan Chrome sendiri.
    attach = os.getenv("ATTACH_CHROME", "1") == "1"
    options = webdriver.ChromeOptions()

    if attach:
        if not debug_port_open():
            pytest.exit(
                f"Chrome dengan --remote-debugging-port={DEBUG_PORT} belum berjalan. "
                "Jalankan Chrome dulu (lihat README), lalu ulangi test.",
                returncode=1,
            )
        options.add_experimental_option(
            "debuggerAddress", f"{DEBUG_HOST}:{DEBUG_PORT}"
        )
        print("\nMODE: ATTACH ke Chrome yang sudah terbuka")
    else:
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={PROFILE_DIR.resolve()}")
        print("\nMODE: LAUNCH Chrome baru oleh Selenium")
    
    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(0)

    yield browser

    try:
        if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
            take_screenshot(browser, "FAILED")
    except Exception as error:
        print(f"\nGagal mengambil screenshot: {error}")
    finally:
        if not attach:
            browser.quit()