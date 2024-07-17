import logging
import re
import requests
import time
import os
import pytz

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urljoin
from .utils import fetch_page, parse_page, convert_price
from dotenv import dotenv_values


def get_current_time():
    return datetime.now(pytz.timezone("America/Sao_Paulo")).isoformat()


env_path = os.path.join(os.path.dirname(__file__), "../.env")

try:
    config = dotenv_values(env_path)
    MONGO_API = config["MONGO_API"]
    BASE_URL = config["BASE_URL"]
except KeyError as e:
    raise KeyError(f"Missing expected environment variable: {e}")

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_site():
    start_time = time.time()
    try:
        collections = extract_collections(BASE_URL + "?view=cards/edicoes")

    except Exception as e:
        logger.error(f"Error scraping site: {e}")
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"Total execution time: {elapsed_time:.2f} seconds")


def process_collection(row):
    cells = row.find_all("td")
    edition_name = cells[0].find("a").text
    edition_link = urljoin(BASE_URL, cells[0].find("a")["href"]).replace(" ", "%20")
    acronym = cells[1].text
    release_date = datetime.strptime(cells[2].text, "%d/%m/%Y")

    collection_data = {
        "name": edition_name,
        "link": edition_link,
        "acronym": acronym,
        "release_date": release_date.isoformat(),
    }

    # Check if the collection already exists
    response = requests.get(f"{MONGO_API}/collections/{acronym}")
    if response.status_code == 200:
        # Collection exists, update it
        update_response = requests.put(
            f"{MONGO_API}/collections/{acronym}", json=collection_data
        )
        if update_response.status_code == 200:
            logger.info(f"Updated collection: {acronym}")
            collection_data["collection_id"] = update_response.json()["_id"]
        else:
            logger.error(
                f"Failed to update collection: {acronym}, Status Code: {update_response.status_code}"
            )
    else:
        # Collection does not exist, create it
        create_response = requests.post(
            f"{MONGO_API}/collections", json=collection_data
        )
        if create_response.status_code == 201:
            logger.info(f"Created collection: {acronym}")
            collection_data["collection_id"] = create_response.json()["_id"]
        else:
            logger.error(
                f"Failed to create collection: {acronym}, Status Code: {create_response.status_code}"
            )

    return collection_data


def extract_collections(url):
    try:
        html = fetch_page(url, "tab-edc")
        soup = parse_page(html)
        table = soup.find("table", id="tab-edc")
        collections = []

        rows = table.find("tbody").find_all("tr")

        # Use ThreadPoolExecutor to parallelize collection processing
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(process_collection, row) for row in rows]
            for future in as_completed(futures):
                try:
                    collection_data = future.result()
                    collections.append(collection_data)
                except Exception as e:
                    logger.error(f"Error processing collection: {e}")

        collections_data = []

        # Use ThreadPoolExecutor to parallelize card scraping
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(extract_cards, collection): collection
                for collection in collections
            }
            for future in as_completed(futures):
                collection = futures[future]
                try:
                    cards = future.result()
                    collection_data = {
                        "name": collection["name"],
                        "acronym": collection["acronym"],
                        "release_date": collection["release_date"],
                        "link": collection["link"],
                        "cards": cards,
                    }
                    collections_data.append(collection_data)
                except Exception as e:
                    logger.error(
                        f"Error extracting cards from {collection['name']}: {e}"
                    )

        return collections_data
    except Exception as e:
        logger.error(f"Error extracting collections: {e}")
        return []


def extract_cards(collection):
    try:
        url = collection["link"]
        logger.info(f"Scraping collection: {collection['acronym']}")

        # Wait for card-estoque element to render and parse the page
        html = fetch_page(url, "card-estoque")
        soup = parse_page(html)

        cards = []
        card_container = soup.find("div", class_="grid-cardsinput")

        if not card_container:
            logger.warning(
                f"Unable to find 'grid-cardsinput' in collection: {collection['acronym']}"
            )
            return []

        for card in card_container.find_all("div", class_="card-item"):
            card_info = {}
            card_name = card.find("span", class_="invisible-label").b.text
            prices = card.find("div", class_="card-prices")
            if prices:
                low_price = prices.find("div", class_="avgp-minprc").text
                high_price = prices.find("div", class_="avgp-maxprc").text
            else:
                low_price = high_price = "N/A"

            marketplace_link = urljoin(BASE_URL, card.find("a")["href"])
            card_image = None
            image_element = card.find("img", class_="main-card")
            if image_element:
                card_image = image_element.get("src") or image_element.get(
                    "data-src", "N/A"
                )

            match = re.search(r".*\(([^()]*)\)[^(]*$", card_name)
            if match:
                collection_number = match.group(1)
            else:
                collection_number = card_name

            label_collection_number = collection["acronym"] + ": " + collection_number

            card_info = {
                "collection_id": collection["collection_id"],
                "number": collection_number,
                "collection_number": label_collection_number,
                "name": card_name,
                "lowest_price": convert_price(low_price),
                "highest_price": convert_price(high_price),
                "link_marketplace": marketplace_link,
                "image": card_image,
                "last_updated": get_current_time(),
            }

            # Check if the card already exists
            response = requests.get(f"{MONGO_API}/cards/{label_collection_number}")
            if response.status_code == 200:
                # Card exists, update it
                update_response = requests.put(
                    f"{MONGO_API}/cards/{label_collection_number}", json=card_info
                )
                if update_response.status_code == 200:
                    logger.info(f"Updated card: {label_collection_number}")
                else:
                    logger.error(
                        f"Failed to update card: {label_collection_number}, Status Code: {update_response.status_code}"
                    )
            else:
                # Card does not exist, create it
                create_response = requests.post(f"{MONGO_API}/cards", json=card_info)
                if create_response.status_code == 201:
                    logger.info(f"Created card: {label_collection_number}")
                else:
                    logger.error(
                        f"Failed to create card: {label_collection_number}, Status Code: {create_response.status_code}"
                    )

            cards.append(card_info)

        return cards

    except Exception as e:
        logger.error(f"Error extracting cards from {collection['name']}: {e}")
        return []


if __name__ == "__main__":
    scrape_site()
