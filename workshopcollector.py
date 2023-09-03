import requests
from bs4 import BeautifulSoup
import concurrent.futures
import time

# Replace with the URL of the Garry's Mod Workshop collection you want to scrape
COLLECTION_URL = 'https://steamcommunity.com/sharedfiles/filedetails/?id=2812780898'

# Output file name
OUTPUT_FILE = 'map_addons.txt'

# Create a session for reusing connections
session = requests.Session()

# Create a dictionary to store addon data (link and name)
addon_data = {}

def scrape_workshop_collection(collection_url):
    response = session.get(collection_url)
    if response.status_code != 200:
        print(f'Failed to retrieve the collection page.')
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    addon_links = []

    # Find all the links to individual addons in the collection
    addon_elements = soup.find_all('div', class_='workshopItem')
    for addon_element in addon_elements:
        link = addon_element.find('a')['href']
        if link:
            addon_links.append(link)

    return addon_links

def check_for_map_tag(addon_url):
    response = session.get(addon_url)
    if response.status_code != 200:
        print(f'Failed to retrieve addon page: {addon_url}')
        return False

    soup = BeautifulSoup(response.text, 'html.parser')
    # Check if any <a> element's 'href' attribute contains "=Map"
    anchor_elements = soup.find_all('a', href=True)
    for anchor in anchor_elements:
        if '=Map' in anchor['href']:
            return True

    return False

def process_addon(i, addon_link):
    response = session.get(addon_link)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        title_element = soup.find('div', class_='workshopItemTitle')
        if title_element:
            addon_title = title_element.get_text().strip()
            if check_for_map_tag(addon_link):
                print(f'{i}. Addon found with "=Map" in href: {addon_title} {addon_link}')
                addon_data[addon_title] = addon_link

def main():
    addon_links = scrape_workshop_collection(COLLECTION_URL)

    if not addon_links:
        print(f'No addons found in the collection.')
        return

    print(f'Checking addons in the collection:')
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed
        future_to_link = {executor.submit(process_addon, i, addon_link): addon_link for i, addon_link in enumerate(addon_links, start=1)}
        for future in concurrent.futures.as_completed(future_to_link):
            addon_link = future_to_link[future]
            try:
                future.result()
            except Exception as exc:
                print(f'Error processing addon: {addon_link} - {exc}')
            # Introduce a small delay to avoid overwhelming the server

    # Sort the addon data by addon name
    sorted_data = dict(sorted(addon_data.items()))

    # Write the sorted data to the output file
    with open(OUTPUT_FILE, 'w') as file:
        for addon_name, addon_link in sorted_data.items():
            file.write(f'{addon_name} | {addon_link}\n')

if __name__ == "__main__":
    main()
