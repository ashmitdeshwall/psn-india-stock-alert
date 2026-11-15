
import os
import json
import requests
import hashlib
from datetime import datetime, timezone
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Add verified direct product-page URLs here.

PRODUCT_URLS = [
    # 1. Amazon India
    "https://www.amazon.in/dp/B0C1H473H8",

    # 2. E2Z Store - ₹1,000 and ₹2,000 category
    "https://e2zstore.com/product-tag/psn-card-india/",

    # E2Z - individual denominations
    "https://e2zstore.com/product/rs-2000-playstation-network-wallet-top-up/",
    "https://e2zstore.com/product/rs-3000-playstation-network-wallet-top-up/",
    "https://e2zstore.com/product/rs-4000-playstation-network-wallet-top-up/",

    # 3. JioGames - ₹2,000
    "https://www.store.jiogames.com/products/?brand=playstation",

    # 4. Rooter - ₹1,000 to ₹4,000 options
    "https://shop.rooter.gg/product/playstation-gift-cards",

    # 5. GyFTR - ₹1,000, ₹2,000 and ₹5,000
    "https://www.gyftr.com/sony-playstation",

    # 6. StanShop - ₹1,000 to ₹4,000 options
    "https://www.stanshop.co/playstation-psn-gift-card-in-india-4000-inr",
    "https://www.stanshop.co/playstation-psn-gift-card-in-india-3000-inr",

    # 7. GamesTheShop - ₹5,000
    "https://www.gamestheshop.com/product/57ffc696-2241-45b1-af43-736209293710",
    
    # 8. Woohoo
    "https://www.woohoo.in/playstation-e-gift-instant-voucher",
]


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
