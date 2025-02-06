#!/usr/bin/env python3
import os
import sys
import logging
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import mimetypes
import hashlib
from datetime import datetime
import re
import unicodedata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('grabr.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MenuGrabber:
    def __init__(self, url=None, output_dir='./menu_items'):
        self.url = url
        self.output_dir = output_dir
        self.session = requests.Session()
        # Set a user agent to avoid being blocked by some websites
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def slugify(self, value):
        """Convert a string to a URL and file system friendly slug."""
        # Turkish character mappings
        tr_map = {
            'ı': 'i', 'İ': 'i', 'ğ': 'g', 'Ğ': 'g',
            'ü': 'u', 'Ü': 'u', 'ş': 's', 'Ş': 's',
            'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c'
        }
        
        # Replace Turkish characters
        for k, v in tr_map.items():
            value = value.replace(k, v)
            
        # Then normalize
        value = unicodedata.normalize('NFKD', value)
        value = value.encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        return re.sub(r'[-\s]+', '-', value)

    def fetch_page(self, url=None):
        """Fetch the HTML content of the webpage."""
        try:
            target_url = url or self.url
            if not target_url:
                raise ValueError("URL is required")

            response = self.session.get(target_url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page: {str(e)}")
            raise

    def parse_menu_items(self, html_content):
        """Extract menu items with their details."""
        soup = BeautifulSoup(html_content, 'html.parser')
        menu_items = []

        logger.info("Searching for menu items...")

        # Find all GhostKit grid items
        grid_items = soup.find_all('div', class_='ghostkit-grid-inner')
        logger.info(f"Found {len(grid_items)} grid items")
        
        for grid in grid_items:
            try:
                # Each menu item has two columns: image (col-4) and content (col-8)
                image_col = grid.find('div', class_='ghostkit-col-4')
                content_col = grid.find('div', class_='ghostkit-col-8')
                
                if not (image_col and content_col):
                    logger.info("Missing image or content column, skipping...")
                    continue

                # Get title from h2
                title_elem = content_col.find(['h2', 'h1', 'h3', 'h4', 'h5', 'h6'])
                if not title_elem:
                    logger.info("No title found, skipping...")
                    continue
                
                title = title_elem.get_text(strip=True)
                logger.info(f"Found title: {title}")

                # Get description from p tag
                desc_elem = content_col.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                logger.info(f"Found description: {description}")

                # Get image URL - try multiple approaches
                img_url = None
                
                # First try: Find img tag with wp-image class
                img = image_col.find('img', class_=lambda x: x and 'wp-image-' in x)
                if img:
                    # Try data-src first
                    src = img.get('data-src', '')
                    if not src:
                        src = img.get('src', '')
                    
                    if src and not src.startswith('data:') and not 'svg' in src.lower():
                        img_url = src
                        logger.info(f"Found image URL from wp-image: {img_url}")
                
                # Second try: Find picture element and get source
                if not img_url:
                    picture = image_col.find('picture')
                    if picture:
                        source = picture.find('source')
                        if source:
                            # Try data-srcset first
                            srcset = source.get('data-srcset', '')
                            if not srcset:
                                srcset = source.get('srcset', '')
                            
                            if srcset:
                                # Get all URLs from srcset
                                urls = [url.strip().split(' ')[0] for url in srcset.split(',')]
                                # Filter valid image URLs
                                valid_urls = [url for url in urls 
                                            if not url.startswith('data:') 
                                            and not 'svg' in url.lower()
                                            and any(url.lower().endswith(ext) 
                                                  for ext in ['.jpg','.jpeg','.png','.webp'])]
                                if valid_urls:
                                    img_url = valid_urls[0]
                                    logger.info(f"Found image URL from picture source: {img_url}")
                
                # Third try: Find any img tag with data-src
                if not img_url:
                    for img in image_col.find_all('img'):
                        src = img.get('data-src', '')
                        if not src:
                            src = img.get('src', '')
                        
                        if src and not src.startswith('data:') and not 'svg' in src.lower():
                            if any(src.lower().endswith(ext) for ext in ['.jpg','.jpeg','.png','.webp']):
                                img_url = src
                                logger.info(f"Found image URL from generic img: {img_url}")
                                break

                # Make URL absolute if it's relative
                if img_url:
                    img_url = urljoin(self.url, img_url)
                    logger.info(f"Final image URL: {img_url}")

                if title and (description or img_url):
                    menu_items.append({
                        'title': title,
                        'description': description,
                        'image_url': img_url
                    })
                    logger.info(f"Added menu item: {title} with image: {img_url}")

            except Exception as e:
                logger.error(f"Error parsing menu item: {str(e)}")
                continue

        if not menu_items:
            logger.warning("No menu items found after parsing")
            # Print sample HTML for debugging
            logger.info("Sample HTML structure:")
            if grid_items:
                logger.info(grid_items[0].prettify())
        else:
            logger.info(f"Successfully found {len(menu_items)} menu items")

        return menu_items

    def download_image(self, url, folder_path, title):
        """Download an image for a menu item."""
        try:
            if not url:
                return None

            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"Skipping non-image content type: {content_type} for URL: {url}")
                return None

            # Generate filename from title and extension
            ext = mimetypes.guess_extension(content_type) or '.jpg'
            filename = f"{self.slugify(title)}{ext}"
            filepath = os.path.join(folder_path, filename)

            # Download with progress bar
            total_size = int(response.headers.get('content-length', 0))
            with open(filepath, 'wb') as f:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=f"Downloading {filename}"
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            logger.info(f"Successfully downloaded: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error downloading image {url}: {str(e)}")
            return None

    def save_menu_item(self, item):
        """Save a menu item's details and image to its own folder."""
        # Create folder name from item title
        folder_name = self.slugify(item['title'])
        folder_path = os.path.join(self.output_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Save details to <product-name>_details.txt with UTF-8 encoding
        details_filename = f"{folder_name}_details.txt"
        details_path = os.path.join(folder_path, details_filename)
        with open(details_path, 'w', encoding='utf-8-sig') as f:  # Use utf-8-sig for BOM
            f.write(f"Başlık: {item['title']}\n\n")
            if item['description']:
                f.write(f"Açıklama: {item['description']}\n")

        # Download image if available
        if item['image_url']:
            image_filename = self.download_image(item['image_url'], folder_path, item['title'])
            if image_filename:
                logger.info(f"Saved image as {image_filename}")

        return folder_path

    def run(self):
        """Main execution method."""
        try:
            # Fetch and parse the webpage
            html_content = self.fetch_page()
            menu_items = self.parse_menu_items(html_content)

            if not menu_items:
                logger.warning("No menu items found on the page")
                return

            # Create main output directory
            os.makedirs(self.output_dir, exist_ok=True)

            # Process each menu item
            logger.info(f"Found {len(menu_items)} menu items. Starting download...")
            for item in menu_items:
                folder_path = self.save_menu_item(item)
                logger.info(f"Saved menu item '{item['title']}' to {folder_path}")

            logger.info("Menu item download complete!")

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Download menu items from a webpage')
    parser.add_argument('--url', help='URL of the webpage to download menu items from')
    parser.add_argument('--output', help='Output directory for menu items', default='./menu_items')
    
    args = parser.parse_args()
    url = args.url

    # If URL is not provided via command line, ask for it interactively
    if not url:
        url = input("Please enter the webpage URL: ").strip()

    try:
        grabber = MenuGrabber(url=url, output_dir=args.output)
        grabber.run()
    except Exception as e:
        logger.error(f"Program terminated with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 