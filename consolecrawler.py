import asyncio
import logging
import os
import socket
import time
from urllib.parse import urlparse, urljoin

import aiohttp
import validators
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(filename='crawler.log', level=logging.ERROR)

# ANSI escape codes for colors
GREEN = '\033[92m'
WHITE = '\033[97m'
RESET = '\033[0m'

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    print(f"{GREEN} _  _  _ _______ ______     _______ ______  _______ _  _  _ _       _______ ______")
    print(f"(_)(_)(_|_______|____  \\   (_______|_____ \\(_______|_)(_)(_|_)     (_______|_____ \\ ")
    print(f" _  _  _ _____   ____)  )   _       _____) )_______ _  _  _ _       _____   _____) )")
    print(f"| || || |  ___) |  __  (   | |     |  __  /|  ___  | || || | |     |  ___) |  __  / ")
    print(f"| || || | |_____| |__)  )  | |_____| |  \\ \\| |   | | || || | |_____| |_____| |  \\ \\ ")
    print(f" \\_____/|_______)______/    \\______)_|   |_|_|   |_|\\_____/|_______)_______)_|   |_|")
    print(f"  ")
    print(f"{RESET}{GREEN}Welcome to Website Link Crawler!{RESET}")
    print(f"{WHITE}--------------------------------\n{RESET}")

async def fetch(url, session):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching {url}: {e}")
        print(f"Error fetching {url}: {e}")
        return None

def get_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    links = [urljoin(base_url, anchor['href']) for anchor in soup.find_all('a', href=True)]
    return links

def get_ip_address(url):
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc.split(':')[0]
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except (socket.gaierror, ValueError) as e:
        logging.error(f"Error getting IP address for {url}: {e}")
        print(f"Error getting IP address for {url}: {e}")
        return "IP not found"

async def save_links_to_file(links, filename):
    try:
        with open(filename, 'w') as file:
            for link, ip_address in links.items():
                file.write(f"{link},{ip_address}\n")
        print(f"\n{GREEN}Links saved to{RESET} {WHITE}{filename}{RESET}")
    except Exception as e:
        logging.error(f"Error saving links to file: {e}")
        print(f"Error saving links to file: {e}")

async def crawl_website(url, session, printed=set(), collected_links={}, depth=0, max_depth=None, max_urls=None):
    try:
        if max_depth is not None and depth >= max_depth:
            return

        html = await fetch(url, session)
        if html:
            links = get_links(html, url)

            for link in links:
                if max_urls is not None and len(collected_links) >= max_urls:
                    return

                if link not in printed and urlparse(link).scheme in {'http', 'https'}:
                    print(f"   - URL: {WHITE}{link}{RESET}")
                    printed.add(link)
                    collected_links[link] = None  # Placeholder for IP address

                    parsed_url = urlparse(link)
                    if parsed_url.netloc == urlparse(url).netloc:
                        await crawl_website(link, session, printed, collected_links, depth + 1, max_depth, max_urls)
    except Exception as e:
        logging.error(f"Error crawling website {url}: {e}")
        print(f"Error crawling website {url}: {e}")

async def analyze_website_structure(collected_links):
    try:
        print(f"\n{GREEN}Website Structure:{RESET}")
        structure = {}
        for link in collected_links.keys():
            parts = urlparse(link).path.strip('/').split('/')
            current = structure
            for part in parts:
                current = current.setdefault(part, {})
        print_structure(structure)
    except Exception as e:
        logging.error(f"Error analyzing website structure: {e}")
        print(f"Error analyzing website structure: {e}")

def print_structure(structure, indent=0):
    for key, value in structure.items():
        print(" " * indent + f"- {key}")
        if isinstance(value, dict):
            print_structure(value, indent + 4)

async def main():
    print_header()

    print("Which Code Do You Want To Use?\n")
    print("1. Fast, But Small Amount Of URLs.")
    print("2. Slow, But Big Amount Of URLs.")

    option = input("\nEnter the Option Number: ")

    if option == "1":
        clear_console()
        await fast_small_urls()
    elif option == "2":
        clear_console()
        await slow_big_urls()
    else:
        print("Invalid option. Please choose either '1' or '2'.")

async def fast_small_urls():
    website_url = input("Enter the Website URL You Want to Crawl: ")
    if not validators.url(website_url):
        print("Invalid URL format.")
        return

    max_depth = 2  # Limit the depth of crawling
    max_urls = 10  # Limit the number of URLs fetched

    async with aiohttp.ClientSession() as session:
        collected_links = {}
        await crawl_website(website_url, session, collected_links=collected_links, max_depth=max_depth, max_urls=max_urls)

    save_option = input("\nDo You Want to Save the Links to a File? (yes/no): ").lower()
    if save_option == 'yes':
        filename = input("Enter the Filename to Save the Links (e.g., links.txt): ")
        await save_links_to_file(collected_links, filename)
    else:
        print("\nLinks Not Saved.")

async def slow_big_urls():
    website_url = input("Enter the Website URL You Want to Crawl: ")
    if not validators.url(website_url):
        print("Invalid URL format.")
        return

    async with aiohttp.ClientSession() as session:
        collected_links = {}
        start_time = time.time()
        await crawl_website(website_url, session, collected_links=collected_links)
        end_time = time.time()

    print(f"\n{GREEN}Crawling completed in {end_time - start_time:.2f} seconds.{RESET}")

    save_option = input("\nDo You Want to Save the Links to a File? (yes/no): ").lower()
    if save_option == 'yes':
        filename = input("Enter the Filename to Save the Links (e.g., links.txt): ")
        await save_links_to_file(collected_links, filename)
    else:
        print("\nLinks Not Saved.")

    analyze_option = input("\nDo You Want to Analyze the Website Structure? (yes/no): ").lower()
    if analyze_option == 'yes':
        await analyze_website_structure(collected_links)

if __name__ == "__main__":
    asyncio.run(main())
