#!/usr/bin/env python3
"""
Water bill checker for xpress-pay portal.
Runs daily at 8am and notifies Home Assistant if a bill is found.
"""

import os
import sys
import time
import schedule
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

SEARCH_URL = "https://pay.xpress-pay.com/bill/search/e59f5554733c46658a100aa68b08545b"
LAST_NAME = "MacGregor"
STREET_NAME = "lakeland"

PAGE_TIMEOUT_MS = 60_000
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 300
DEBUG_SCREENSHOT = "/tmp/water-bill-debug.png"

HA_URL = os.environ.get("HA_URL", "").rstrip("/")
HA_TOKEN = os.environ.get("HA_TOKEN", "")


def notify_ha():
    url = f"{HA_URL}/api/services/notify/mobile_app_d_s24"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "title": "Water Bill Due",
        "message": "Your water bill is ready. Tap to pay.",
        "data": {"url": SEARCH_URL},
    }
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    log("Notification sent.")


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def log_page_state(page):
    """Log what the browser is actually showing, to diagnose failures."""
    try:
        log(f"Page URL: {page.url}")
        log(f"Page title: {page.title()!r}")
        inputs = page.eval_on_selector_all(
            "input, select, button",
            "els => els.map(e => `${e.tagName.toLowerCase()} name=${e.name || ''} id=${e.id || ''} type=${e.type || ''}`)",
        )
        log("Form elements: " + ("; ".join(inputs) if inputs else "none"))
        text = " ".join(page.inner_text("body").split())
        log(f"Page text: {text[:500]}")
        page.screenshot(path=DEBUG_SCREENSHOT, full_page=True)
        log(f"Screenshot saved to {DEBUG_SCREENSHOT}")
    except Exception as e:
        log(f"Could not capture page state: {e}")


def check_bill():
    for attempt in range(1, MAX_ATTEMPTS + 1):
        log("Checking water bill..." + (f" (attempt {attempt}/{MAX_ATTEMPTS})" if attempt > 1 else ""))
        if _check_bill_once():
            return
        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS)
    log("All attempts failed.")


def _check_bill_once():
    """Returns True if the check completed (bill or no bill), False on error."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page()
        page.set_default_timeout(PAGE_TIMEOUT_MS)

        try:
            # Don't wait for "networkidle": background requests (analytics,
            # polling) on the portal can keep the network busy indefinitely.
            # Wait for the form field we actually need instead.
            page.goto(SEARCH_URL, wait_until="domcontentloaded")
            page.wait_for_selector('input[name="Bill[locator1]"]')

            page.fill('input[name="Bill[locator1]"]', LAST_NAME)
            page.fill('input[name="Bill[locator2]"]', STREET_NAME)
            page.evaluate('document.getElementById("bill-atleast1locator").value = "1"')

            initial_url = page.url

            with page.expect_navigation(wait_until="domcontentloaded"):
                page.evaluate("""
                    var btn = document.querySelector('button[name="submitLocators"]');
                    (btn.closest('form') || btn.form).submit();
                """)

            if page.url != initial_url:
                log("BILL_FOUND")
                notify_ha()
            else:
                log("NO_BILL")
            return True

        except Exception as e:
            log(f"ERROR: {e}")
            log_page_state(page)
            return False
        finally:
            browser.close()


if __name__ == "__main__":
    if "--test-notify" in sys.argv:
        log("Sending test notification...")
        notify_ha()
    elif "--once" in sys.argv:
        check_bill()
    else:
        schedule.every().day.at("08:00").do(check_bill)
        log("Water bill checker started. Runs daily at 08:00.")
        while True:
            schedule.run_pending()
            time.sleep(60)
