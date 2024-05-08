import json

from datetime import datetime
from urllib.parse import urljoin
from .utils import fetch_page, parse_page
from .config import BASE_URL


"""Performs web scraping of the website"""
def scrape_site():
    collections = extract_collections(BASE_URL + "?view=cards/edicoes")

    with open("collections_data.json", "w", encoding="utf-8") as f:
        json.dump(collections, f, ensure_ascii=False, indent=4)

"""Extracts and sorts information from each collection in the table"""
def extract_collections(url):
    html = fetch_page(url, "tab-edc")
    soup = parse_page(html) 
    table = soup.find('table', id='tab-edc')
    collections = []

    for row in table.find('tbody').find_all('tr'):
        cells = row.find_all('td')
        edition_name = cells[0].find('a').text
        edition_link = urljoin(BASE_URL, cells[0].find('a')['href']).replace(" ", "%20")
        acronym = cells[1].text
        release_date = datetime.strptime(cells[2].text, "%d/%m/%Y")

        collections.append({
            'Name': edition_name,
            'Link': edition_link,
            'Acronym': acronym,
            'Release Date': release_date
        })
        
    collections = sorted(collections, key=lambda x: (x['Release Date'], x['Acronym']))

    collections_data = []
    for collection in collections:
        cards = extract_cards(collection)
        
        collection_data = {
            'Name': collection['Name'],
            'Acronym': collection['Acronym'],
            'Release Date': collection['Release Date'].strftime("%d/%m/%Y"),
            'Link': collection['Link'],
            'Cards': cards
        }
        
        collections_data.append(collection_data)

    return collections_data


"""Extract information about the cards."""
def extract_cards(collection):
    url = collection['Link']
    print(f"Scraping collection: {url}")
    html = fetch_page(url, "card-estoque")
    soup = parse_page(html)

    cards = []
    card_container = soup.find("div", class_="grid-cardsinput")
    if not card_container:
        print(f"Unable to find 'grid-cardsinput' in collection: {collection['Name']}")
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

        marketplace_link = urljoin(BASE_URL, card.find("a")['href'])
        card_image = None
        image_element = card.find("img", class_="main-card")
        if image_element:
            card_image = image_element.get('src') or image_element.get('data-src', "N/A")

        card_info = {
            'Name': card_name,
            'Lowest Price': low_price,
            'Highest Price': high_price,
            'Link Marketplace': marketplace_link,
            'Image': card_image
        }

        cards.append(card_info)

    return cards


"""Displays information for each collection"""
def display_collections(collections):
    
    for collection in collections:
        print(f"Name: {collection['Name']}")
        print(f"Link: {collection['Link']}")
        print(f"Acronym: {collection['Acronym']}")
        print(f"Release Date: {collection['Release Date']}")
        print("-" * 50)


"""Displays cards from a specific collection"""
def display_collection_cards(collection, cards):
    
    print(f"Coleção: {collection['Name']}")
    print(f"Acronym: {collection['Acronym']}")
    print(f"Release Date: {collection['Release Date']}")
    print(f"Cards:")

    for card in cards:
        print(f"  - Name: {card['Name']}")
        print(f"    Lowest Price: {card['Lowest Price']}")
        print(f"    Highest Price: {card['Highest Price']}")
        print(f"    Image: {card['Image']}")
        print(f"    Link Marketplace: {card['Link Marketplace']}")
        print("")