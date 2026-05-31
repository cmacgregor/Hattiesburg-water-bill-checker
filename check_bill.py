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


def check_bill():
    log("Checking water bill...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page()

        try:
            page.goto(SEARCH_URL, wait_until="networkidle")

            page.fill('input[name="Bill[locator1]"]', LAST_NAME)
            page.fill('input[name="Bill[locator2]"]', STREET_NAME)
            page.evaluate('document.getElementById("bill-atleast1locator").value = "1"')

            initial_url = page.url

            page.evaluate("""
                var btn = document.querySelector('button[name="submitLocators"]');
                (btn.closest('form') || btn.form).submit();
            """)
            page.wait_for_load_state("networkidle")

            if page.url != initial_url:
                log("BILL_FOUND")
                notify_ha()
            else:
                log("NO_BILL")

        except Exception as e:
            log(f"ERROR: {e}")
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
