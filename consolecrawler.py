import asyncio
import aiohttp
import requests
import socket
import threading
import os  # Added import
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import time

# ANSI escape codes for colors
GREEN = '\033[92m'
WHITE = '\033[97m'
RESET = '\033[0m'

def clear_console():  # Added function to clear console
    os.system('cls' if os.name == 'nt' else 'clear')

def fast_small_urls():
    def get_links(url):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [urljoin(url, link['href']) for link in soup.find_all('a', href=True)]
            return links
        except requests.RequestException as e:
            print(f"Error fetching links from {url}: {e}")
            return []

    def get_ip_address(url):
        try:
            # Check if the URL starts with 'http://' or 'https://'
            if url.startswith('http://') or url.startswith('https://'):
                # Split the URL into parts
                parts = url.split('//')[1].split('/')
                if len(parts) < 1:
                    raise ValueError("Invalid URL format")
                
                # Get the hostname from the URL
                hostname = parts[0]
                
                # Get the IP address of the hostname
                ip_address = socket.gethostbyname(hostname)
                return ip_address
            else:
                raise ValueError("URL must start with 'http://' or 'https://'")
        except (socket.gaierror, ValueError) as e:
            print(f"Error getting IP address for {url}: {e}")
            return "IP not found"

    def save_links_to_file(links, filename):
        try:
            with open(filename, 'w') as file:
                for link in links:
                    file.write(link + '\n')
            print(f"\n{GREEN}Links saved to{RESET} {WHITE}{filename}{RESET}")
        except Exception as e:
            print(f"Error saving links to file: {e}")

    def crawl_website(website_url):
        links = get_links(website_url)
        print(f"\n{GREEN}Links found on{RESET} {WHITE}{website_url}:{RESET}\n")
        for link in links:
            ip_address = get_ip_address(link)
            print(f"   - URL: {WHITE}{link}{RESET}, IP: {GREEN}{ip_address}{RESET}")
            time.sleep(0.05)  # Introduce a delay of 0.05 seconds
        return links

    def main():
        print(f"{GREEN} _  _  _ _______ ______     _______ ______  _______ _  _  _ _       _______ ______")
        print(f"(_)(_)(_|_______|____  \\   (_______|_____ \\(_______|_)(_)(_|_)     (_______|_____ \\ ")
        print(f" _  _  _ _____   ____)  )   _       _____) )_______ _  _  _ _       _____   _____) )")
        print(f"| || || |  ___) |  __  (   | |     |  __  /|  ___  | || || | |     |  ___) |  __  / ")
        print(f"| || || | |_____| |__)  )  | |_____| |  \\ \\| |   | | || || | |_____| |_____| |  \\ \\ ")
        print(f" \\_____/|_______)______/    \\______)_|   |_|_|   |_|\\_____/|_______)_______)_|   |_|")
        print(f"  ")
        print(f"{RESET}{GREEN}Welcome to Website Link Crawler!{RESET}")
        print(f"{WHITE}--------------------------------\n{RESET}")
        website_url = input("Enter the Website URL You Want to Crawl: ")

        crawl_website(website_url)

        save_option = input("\nDo You Want to Save the Links to a File? (yes/no): ").lower()
        if save_option == 'yes':
            filename = input("Enter the Filename to Save the Links (e.g., links.txt): ")
            save_links_to_file(get_links(website_url), filename)
        else:
            print("\nLinks Not Saved.")

    if __name__ == "__main__":
        main()

def slow_big_urls():
    async def fetch(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                try:
                    response.raise_for_status()
                    return await response.text()
                except aiohttp.ClientError as e:
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

    async def crawl_website(url, printed=set(), collected_links={}):
        try:
            html = await fetch(url)
            if html:
                links = get_links(html, url)

                for link in links:
                    if link not in printed and urlparse(link).scheme in {'http', 'https'}:
                        ip_address = get_ip_address(link)
                        print(f"   - URL: {WHITE}{link}{RESET}, IP: {GREEN}{ip_address}{RESET}")
                        printed.add(link)
                        collected_links[link] = ip_address

                        # Recursively crawl internal links
                        parsed_url = urlparse(link)
                        if parsed_url.netloc == urlparse(url).netloc:
                            await crawl_website(link, printed, collected_links)
        except Exception as e:
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
            print(f"Error analyzing website structure: {e}")

    def print_structure(structure, indent=0):
        for key, value in structure.items():
            print(" " * indent + f"- {key}")
            if isinstance(value, dict):
                print_structure(value, indent + 4)

    async def main():
        website_url = input("Enter the Website URL You Want to Crawl: ")

        collected_links = {}
        start_time = time.time()
        await crawl_website(website_url, collected_links=collected_links)
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

def main():
    print(f"{GREEN} _  _  _ _______ ______     _______ ______  _______ _  _  _ _       _______ ______")
    print(f"(_)(_)(_|_______|____  \\   (_______|_____ \\(_______|_)(_)(_|_)     (_______|_____ \\ ")
    print(f" _  _  _ _____   ____)  )   _       _____) )_______ _  _  _ _       _____   _____) )")
    print(f"| || || |  ___) |  __  (   | |     |  __  /|  ___  | || || | |     |  ___) |  __  / ")
    print(f"| || || | |_____| |__)  )  | |_____| |  \\ \\| |   | | || || | |_____| |_____| |  \\ \\ ")
    print(f" \\_____/|_______)______/    \\______)_|   |_|_|   |_|\\_____/|_______)_______)_|   |_|")
    print(f"  ")
    print(f"{RESET}{GREEN}Welcome to Website Link Crawler!{RESET}")
    print(f"{WHITE}--------------------------------\n{RESET}")

    print("Which Code Do You Want To Use?\n")
    print("1. Fast, But Small Amount Of URLs.")
    print("2. Slow, But Big Amount Of URLs.")

    option = input("\nEnter the Option Number: ")

    if option == "1":
        clear_console()  # Clear console after choosing option
        fast_small_urls()
    elif option == "2":
        clear_console()  # Clear console after choosing option
        slow_big_urls()
    else:
        print("Invalid option. Please choose either '1' or '2'.")

if __name__ == "__main__":
    main()
