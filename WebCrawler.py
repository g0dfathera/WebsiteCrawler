import asyncio
import os
import signal
import sys
import socket
import time
from urllib.parse import urlparse, urljoin
import aiohttp
import validators
from bs4 import BeautifulSoup
import csv

# ANSI escape codes for colors
GREEN = '\033[92m'
WHITE = '\033[97m'
RESET = '\033[0m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'

# Global semaphore for limiting concurrency
semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests

# Global event for stopping
stop_event = asyncio.Event()
stop_event.clear()  # Initially not stopped

# Counter for handling Ctrl+C presses
stop_counter = 0

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print(GREEN + r"""
+============================================================+
| __        __   _      ____                    _            |
| \ \      / /__| |__  / ___|_ __ __ ___      _| | ___ _ __  |
|  \ \ /\ / / _ \ '_ \| |   | '__/ _` \ \ /\ / / |/ _ \ '__| |
|   \ V  V /  __/ |_) | |___| | | (_| |\ V  V /| |  __/ |    |
|    \_/\_/ \___|_.__/ \____|_|  \__,_| \_/\_/ |_|\___|_|    |
+============================================================+
""" + RESET)
    print(GREEN + "Welcome to Website Crawler!")
    print("--------------------------------\n")



async def fetch(url, session, retries=3):
    for attempt in range(retries):
        async with semaphore:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    status_code = response.status  # Get the HTTP status code
                    html = await response.text()
                    return html, status_code  # Return both HTML and status
            except aiohttp.ClientError as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Error fetching {url}: {e}")
                    return None, None  # Return None for both in case of error


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
        print(f"Error getting IP address for {url}: {e}")
        return "IP not found"

def save_links_to_csv(links, filename):
    try:
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['URL', 'Status Code'])
            for link, status_code in links.items():
                writer.writerow([link, status_code])
        print(f"\n{GREEN}Links saved to{RESET} {WHITE}{filename}{RESET}")
    except Exception as e:
        print(f"Error saving links to CSV file: {e}")


def is_valid_url(url, base_domain):
    parsed_url = urlparse(url)
    return parsed_url.netloc.endswith(base_domain)

async def crawl_website(url, session, printed=set(), collected_links={}, depth=0, max_depth=None, max_urls=None):
    try:
        if stop_event.is_set():
            return

        if max_depth is not None and depth >= max_depth:
            return

        html, status_code = await fetch(url, session)  # Get both HTML and status
        if html is not None:
            links = get_links(html, url)

            for link in links:
                if stop_event.is_set():
                    return

                if max_urls is not None and len(collected_links) >= max_urls:
                    return

                if link not in printed and urlparse(link).scheme in {'http', 'https'}:
                    if is_valid_url(link, urlparse(url).netloc):
                        ip_address = get_ip_address(link)
                        print(f"   - URL: {WHITE}{link}{RESET} (Status: {YELLOW}{status_code}{RESET}, IP: {GREEN}{ip_address}{RESET})")

                        printed.add(link)
                        collected_links[link] = status_code  # Store status code instead of depth

                        parsed_url = urlparse(link)
                        if parsed_url.netloc == urlparse(url).netloc:
                            await crawl_website(link, session, printed, collected_links, depth + 1, max_depth, max_urls)
    except Exception as e:
        print(f"Error crawling website {url}: {e}")

def handle_signal(signum, frame):
    global stop_counter
    if stop_counter == 0:
        print("\nStopping the crawling process...")
        stop_event.set()
        stop_counter += 1
        print("Press Ctrl+C again to exit the program.")
    elif stop_counter == 1:
        print("Exiting the program...")
        sys.exit(0)  # Exit the program

async def main():
    clear_console()
    print_header()

    # Setup signal handlers
    signal.signal(signal.SIGINT, handle_signal)  # Handle Ctrl+C

    print(f"{CYAN}Which Code Do You Want To Use?{RESET}\n")
    print(f"1. Slow, But Big Amount Of URLs.")
    print(f"2. Fast, But Small Amount Of URLs.")

    option = input("\nEnter the Option Number: ")

    if option == "2":
        clear_console()
        print(f"{MAGENTA}Selected: Fast, But Small Amount Of URLs.{RESET}")
        await fast_small_urls()
    elif option == "1":
        clear_console()
        print(f"{MAGENTA}Selected: Slow, But Big Amount Of URLs.{RESET}")
        await slow_big_urls()
    else:
        print("Invalid option. Please choose either '1' or '2'.")

async def fast_small_urls():
    website_url = input("Enter the Website URL You Want to Crawl: ")
    if not validators.url(website_url):
        print("Invalid URL format.")
        return

    max_depth = 3  # Increase the depth of crawling to explore more levels
    max_urls = 50  # Increase the number of URLs fetched

    async with aiohttp.ClientSession() as session:
        collected_links = {}
        await crawl_website(website_url, session, collected_links=collected_links, max_depth=max_depth, max_urls=max_urls)

    save_option = input("\nDo You Want to Save the Links to a CSV File? (yes/no): ").lower()
    if save_option == 'yes':
        filename = input("Enter the Filename to Save the Links (e.g., links.csv): ")
        save_links_to_csv(collected_links, filename)
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

    save_option = input("\nDo You Want to Save the Links to a CSV File? (yes/no): ").lower()
    if save_option == 'yes':
        filename = input("Enter the Filename to Save the Links (e.g., links.csv): ")
        save_links_to_csv(collected_links, filename)
    else:
        print("\nLinks Not Saved.")

if __name__ == "__main__":
    asyncio.run(main())
