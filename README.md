# Water Bill Checker

Checks the xpress-pay portal daily and sends a Home Assistant push notification when a bill is due. Silent when no bill is found.

## Setup

### 1. Build the Docker image

On your Linux server, from this directory:

```bash
docker build -t water-bill-checker .
```

### 2. Test it manually

```bash
docker run --rm water-bill-checker
# Prints NO_BILL (exit 0) or BILL_FOUND (exit 1)
```

### 3. Add to Home Assistant

Copy the contents of `ha_config.yaml` into your HA config:

- The `shell_command` block goes under `shell_command:` in `configuration.yaml`
- The `automation` block goes in `automations.yaml` or paste into the UI automation editor

**Important:** Replace `mobile_app_your_phone` with your actual HA mobile device name. Find it under:
`Settings → Companion App → your device name`

It'll look something like `mobile_app_connors_pixel` or similar.

### 4. Reload HA

```bash
# In HA developer tools, or:
ha core reload
```

### 5. Test the automation

Trigger it manually from HA's automation page to confirm the notification fires correctly.

## How it works

1. HA automation fires at 8am daily
2. Shells out to `docker run water-bill-checker`
3. Script loads the xpress-pay page, grabs the CSRF token, submits your name + address
4. If redirected to a payment page → exits with code 1 → HA sends push notification
5. If "No bills match your criteria" appears → exits with code 0 → HA does nothing

## Adjusting the time

Change `08:00:00` in the automation trigger to whatever time you prefer.

## Troubleshooting

- **Notification not firing:** Check HA logs for shell_command errors. Run the Docker container manually to confirm it's working.
- **Docker not found by HA:** HA may need the full Docker path. Try `/usr/bin/docker` instead of `docker` in the shell_command.
- **Form fields changed:** xpress-pay occasionally updates their portal. If it breaks, inspect the Network tab again and update the field names in `check_bill.py`.
