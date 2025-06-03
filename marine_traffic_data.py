import os
import cloudscraper
from bs4 import BeautifulSoup

# Config
base_url = "https://www.vesselfinder.com/vessels/details/"

# REGNOS is optional/visible, so fallback is safe
vessel_list_raw = os.environ.get("VESSELS", "")
vessel_list = [i.strip() for i in vessel_list_raw.split(",") if i.strip()]

print(f"Vessel list: {vessel_list}")

if not vessel_list:
    print("No vessels found in the list environment variable.")
    exit(1)

# Initialize session
scarper = cloudscraper.create_scraper()

for i, imonr in enumerate(vessel_list, 1):
    print(f"Processing vessel {i}: {imonr}")

    # Fetch the vessel page
    vessel_url = f"{base_url}/{imonr}"
    response = scarper.get(vessel_url)
    if response.status_code != 200:
        print(f"Failed to fetch data for {imonr}")
        continue

    # Parse the page content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the required data
    try:
        # Find the destination label section
        vessel_name = soup.find('h1', class_= 'title').get_text(strip=True) if soup.find('h1', class_='title') else "Vessel info. not found."

        print(f"Vessel: {vessel_name}")

        # Find the destination section of the HTML
        if soup.find('div', class_='vi__r1 vi__sbt'):
            # Destination name
            destination = soup.find('a', class_='_npNa').get_text(strip=True) if soup.find('a', class_='_npNa') else "Destination not found."

            # ETA
            eta = soup.find('span', class_='_mcol12ext').get_text(strip=True) if soup.find('span', class_='_mcol12ext') else "ETA not found."

            print(f"Destination: {destination}")
            print(f"{eta}")
        else:
            print("Destination section not found.")
    except AttributeError:
        print("Vessel name not found.")
    