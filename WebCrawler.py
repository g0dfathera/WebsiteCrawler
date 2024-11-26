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
    print(f"{GREEN} _  _  _ _______ ______     _______ ______  _______ _  _  _ _       _______ ______")
    print(f"(_)(_)(_|_______|____  \\   (_______|_____ \\(_______|_)(_)(_|_)     (_______|_____ \\ ")
    print(f" _  _  _ _____   ____)  )   _       _____) )_______ _  _  _ _       _____   _____) )")
    print(f"| || || |  ___) |  __  (   | |     |  __  /|  ___  | || || | |     |  ___) |  __  / ")
    print(f"| || || | |_____| |__)  )  | |_____| |  \\ \\| |   | | || || | |_____| |_____| |  \\ \\ ")
    print(f" \\_____/|_______)______/    \\______)_|   |_|_|   |_|\\_____/|_______)_______)_|   |_|")
    print(f"  ")
    print(f"{RESET}{GREEN}Welcome to Website Link Crawler!{RESET}")
    print(f"{WHITE}--------------------------------\n{RESET}")

async def fetch(url, session, retries=3):
    for attempt in range(retries):
        async with semaphore:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response.raise_for_status()
                    return await response.text()
            except aiohttp.ClientError as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
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
        print(f"Error getting IP address for {url}: {e}")
        return "IP not found"

async def save_links_to_file(links, filename):
    try:
        with open(filename, 'w') as file:
            for link, ip_address in links.items():
                file.write(f"{link},{ip_address}\n")
        print(f"\n{GREEN}Links saved to{RESET} {WHITE}{filename}{RESET}")
    except Exception as e:
        print(f"Error saving links to file: {e}")

async def analyze_website_structure(collected_links, filename):
    try:
        structure = {}
        for link in collected_links.keys():
            parts = urlparse(link).path.strip('/').split('/')
            current = structure
            for part in parts:
                current = current.setdefault(part, {})
        
        with open(filename, 'w') as file:
            _write_structure_to_file(structure, file)
        
        print(f"\n{GREEN}Website structure saved to{RESET} {WHITE}{filename}{RESET}")
    except Exception as e:
        print(f"Error analyzing website structure: {e}")

def _write_structure_to_file(structure, file, indent=0):
    for key, value in structure.items():
        file.write(" " * indent + f"- {key}\n")
        if isinstance(value, dict):
            _write_structure_to_file(value, file, indent + 4)

def is_valid_url(url, base_domain):
    parsed_url = urlparse(url)
    return parsed_url.netloc.endswith(base_domain)

async def crawl_website(url, session, printed=set(), collected_links={}, depth=0, max_depth=None, max_urls=None):
    try:
        if stop_event.is_set():
            return  # Exit if stopped

        if max_depth is not None and depth >= max_depth:
            return

        html = await fetch(url, session)
        if html:
            links = get_links(html, url)

            for link in links:
                if stop_event.is_set():
                    return  # Exit if stopped

                if max_urls is not None and len(collected_links) >= max_urls:
                    return

                if link not in printed and urlparse(link).scheme in {'http', 'https'}:
                    if is_valid_url(link, urlparse(url).netloc):
                        ip_address = get_ip_address(link)
                        print(f"   - URL: {WHITE}{link}{RESET} (IP: {GREEN}{ip_address}{RESET})")
                        printed.add(link)
                        collected_links[link] = ip_address

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
    print(f"1. Fast, But Small Amount Of URLs.")
    print(f"2. Slow, But Big Amount Of URLs.")

    option = input("\nEnter the Option Number: ")

    if option == "1":
        clear_console()
        print(f"{MAGENTA}Selected: Fast, But Small Amount Of URLs.{RESET}")
        await fast_small_urls()
    elif option == "2":
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

    save_option = input("\nDo You Want to Save the Links to a File? (yes/no): ").lower()
    if save_option == 'yes':
        filename = input("Enter the Filename to Save the Links (e.g., links.txt): ")
        await save_links_to_file(collected_links, filename)
    else:
        print("\nLinks Not Saved.")
    
    analyze_option = input("\nDo You Want to Analyze the Website Structure? (yes/no): ").lower()
    if analyze_option == 'yes':
        structure_filename = input("Enter the Filename to Save the Structure (e.g., structure.txt): ")
        await analyze_website_structure(collected_links, structure_filename)

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
        structure_filename = input("Enter the Filename to Save the Structure (e.g., structure.txt): ")
        await analyze_website_structure(collected_links, structure_filename)

if __name__ == "__main__":
    asyncio.run(main())
