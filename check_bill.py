#!/usr/bin/env python3
"""
Water bill checker for xpress-pay portal.
Exits with code 0 and prints 'NO_BILL' if no bill found.
Exits with code 1 and prints 'BILL_FOUND' if a bill is found (redirect occurred).
"""

import sys
from playwright.sync_api import sync_playwright

SEARCH_URL = "https://pay.xpress-pay.com/bill/search/e59f5554733c46658a100aa68b08545b"
LAST_NAME = "MacGregor"
STREET_NAME = "lakeland"


def check_bill():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(SEARCH_URL, wait_until="networkidle")

            page.fill('input[name="Bill[locator1]"]', LAST_NAME)
            page.fill('input[name="Bill[locator2]"]', STREET_NAME)

            # atLeast1Locator is a hidden Yii2 validation flag; set it so the
            # server accepts the POST (bypassing client-side activeForm check)
            page.evaluate('document.getElementById("bill-atleast1locator").value = "1"')

            initial_url = page.url

            # Submit directly to bypass Yii2 activeForm client-side validation
            page.evaluate("""
                var btn = document.querySelector('button[name="submitLocators"]');
                (btn.closest('form') || btn.form).submit();
            """)
            page.wait_for_load_state("networkidle")

            final_url = page.url

            if final_url != initial_url:
                # Redirected to payment page — bill found
                print("BILL_FOUND")
                print(f"Payment URL: {final_url}", file=sys.stderr)
                browser.close()
                sys.exit(1)
            else:
                # Server returned to search form — no bill due
                print("NO_BILL")
                browser.close()
                sys.exit(0)

        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            browser.close()
            sys.exit(2)


if __name__ == "__main__":
    check_bill()
