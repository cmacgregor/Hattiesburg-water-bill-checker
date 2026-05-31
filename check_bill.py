#!/usr/bin/env python3
"""
Water bill checker for xpress-pay portal.
Checks for a due bill and notifies Home Assistant if found.
"""

import os
import sys
import requests
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
        "data": {
            "url": SEARCH_URL,
        },
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print("Notification sent.", file=sys.stderr)


def check_bill():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
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

            final_url = page.url

            if final_url != initial_url:
                print("BILL_FOUND")
                notify_ha()
            else:
                print("NO_BILL")

        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    check_bill()
