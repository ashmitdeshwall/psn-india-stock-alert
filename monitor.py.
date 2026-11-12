
import os
import json
import requests
import hashlib
from datetime import datetime, timezone
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Add verified direct product-page URLs here.
PRODUCT_URLS = []

STATE_FILE = "stock_state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PSNStockMonitor/1.0)"
}

def send_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": message},
        timeout=20
    )
    response.raise_for_status()

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def find_products(data):
    if isinstance(data, list):
        for item in data:
            yield from find_products(item)

    elif isinstance(data, dict):
        if data.get("@type") in ("Product", ["Product"]):
            yield data

        for value in data.values():
            if isinstance(value, (dict, list)):
                yield from find_products(value)

def verify_product(product):
    name = str(product.get("name", "")).lower()
    description = str(product.get("description", "")).lower()

    text = name + " " + description

    if not any(x in text for x in ("playstation", "psn")):
        return None

    if any(x in text for x in (
        "ps plus", "subscription", "steam", "xbox"
    )):
        return None

    offers = product.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}

    price = offers.get("price")
    currency = offers.get("priceCurrency")
    availability = str(offers.get("availability", "")).lower()

    if not price or currency != "INR":
        return None

    if not availability.endswith("instock"):
        return None

    return {
        "name": product.get("name", "PSN Gift Card"),
        "price": price
    }

def check_page(url):
    response = requests.get(
        url, headers=HEADERS, timeout=25
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    products = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text())
            products.extend(find_products(data))
        except (json.JSONDecodeError, TypeError):
            continue

    return [p for item in products if (p := verify_product(item))]

def main():
    state = load_state()

    if not PRODUCT_URLS:
        print("No direct product URLs configured.")
        print("No stock alerts will be generated.")
        return

    for url in PRODUCT_URLS:
        try:
            products = check_page(url)

            for product in products:
                key = hashlib.sha256(
                    (url + product["name"]).encode()
                ).hexdigest()

                if key not in state:
                    send_alert(
                        "PSN India stock candidate\n\n"
                        f"Product: {product['name']}\n"
                        f"Price: ₹{product['price']}\n"
                        f"Link: {url}\n"
                        f"Checked: {datetime.now(timezone.utc).isoformat()}\n\n"
                        "Please verify the live product before purchasing."
                    )

                state[key] = True

            print(f"Checked: {url}")

        except Exception as error:
            print(f"SITE_ERROR: {url}: {error}")

    save_state(state)

if __name__ == "__main__":
    main()
