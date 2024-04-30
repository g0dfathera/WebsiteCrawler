import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import socket
import time
import threading

# ANSI escape codes for colors
GREEN = '\033[92m'
WHITE = '\033[97m'
RESET = '\033[0m'

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

def get_ip_address(url):
    try:
        hostname = url.split('//')[1].split('/')[0]
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.gaierror:
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
    website_url = input("Enter the website URL to crawl: ")

    crawl_thread = threading.Thread(target=crawl_website, args=(website_url,))
    crawl_thread.start()

    crawl_thread.join()  # Wait for crawling to finish before asking to save links
    save_option = input("\nDo you want to save the links to a file? (yes/no): ").lower()
    if save_option == 'yes':
        filename = input("Enter the filename to save the links (e.g., links.txt): ")
        save_links_to_file(get_links(website_url), filename)
    else:
        print("\nLinks not saved.")

if __name__ == "__main__":
    main()
