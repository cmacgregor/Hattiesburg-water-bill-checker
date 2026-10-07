# Water Bill Checker (retired)

> **This project was retired in October 2026 and the repository is archived.**
> It no longer works and is kept only for reference.

## What it did

A Docker container that loaded the City of Hattiesburg water bill page on the
Xpress-pay portal once a day in headless Chromium (Playwright), searched for the
account by last name and street, and sent a Home Assistant push notification
when a bill was waiting.

## What happened

In early October 2026, every daily check started failing. The investigation went
like this:

1. **Page load timeouts.** `page.goto(..., wait_until="networkidle")` timed out
   after 30 seconds on every run. Switching to `domcontentloaded` plus waiting
   for the form field got the page to load, but the search form never appeared.
2. **Diagnostic logging** (URL, title, form fields, page text, screenshot on
   failure) showed why. The browser was stuck on a Cloudflare
   *"Just a moment… Performing security verification"* page with a Turnstile
   challenge. Xpress-pay had put Cloudflare bot protection in front of the portal.
3. **Decision: retire the scraper.** Getting past the check would mean disguising
   the headless browser or paying a captcha-solving service. That works against
   the site operator's explicit choice to block automated access, and it's an
   arms race that would keep breaking the checker silently.

## Replacement

Home Assistant now watches for the utility's "bill ready" email through the
[IMAP integration](https://www.home-assistant.io/integrations/imap/) and sends
the same push notification with the payment link. Setup and the automation are
in [`ha_config.yaml`](ha_config.yaml).

## Shutting down the old container

On the server:

```bash
docker compose down
docker image rm ghcr.io/cmacgregor/water-bill-checker:latest
```

The original code (`check_bill.py`, `Dockerfile`, `docker-compose.yaml`) is left
in place for reference. The original setup instructions are in the git history.
