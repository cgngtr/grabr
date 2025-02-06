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

class ImageGrabber:
    def __init__(self, url=None, output_dir='./downloads'):
        self.url = url
        self.output_dir = output_dir
        self.session = requests.Session()
        # Set a user agent to avoid being blocked by some websites
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

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

    def parse_images(self, html_content):
        """Extract image URLs from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and not src.startswith('data:'):  # Skip data URLs
                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(self.url, src)
                images.append(absolute_url)
        
        logger.info(f"Found {len(images)} images on the page")
        return images

    def generate_filename(self, url, content_type):
        """Generate a unique filename for the image."""
        # Try to get the original filename from the URL
        parsed_url = urlparse(url)
        original_name = os.path.basename(parsed_url.path)
        
        # If no extension in original name, try to get it from content type
        if not os.path.splitext(original_name)[1]:
            ext = mimetypes.guess_extension(content_type) or '.jpg'
            # Generate a unique filename using timestamp and URL hash
            hash_object = hashlib.md5(url.encode())
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_name = f"image_{timestamp}_{hash_object.hexdigest()[:6]}{ext}"
        
        return original_name

    def download_image(self, url):
        """Download a single image."""
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Check if the content type is an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"Skipping non-image content type: {content_type} for URL: {url}")
                return False

            filename = self.generate_filename(url, content_type)
            filepath = os.path.join(self.output_dir, filename)

            # Create the output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)

            # Get the total file size for progress bar
            total_size = int(response.headers.get('content-length', 0))

            # Download with progress bar
            with open(filepath, 'wb') as f:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=filename
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            logger.info(f"Successfully downloaded: {filename}")
            return True

        except Exception as e:
            logger.error(f"Error downloading image {url}: {str(e)}")
            return False

    def run(self):
        """Main execution method."""
        try:
            # Fetch and parse the webpage
            html_content = self.fetch_page()
            image_urls = self.parse_images(html_content)

            if not image_urls:
                logger.warning("No images found on the page")
                return

            # Download all images
            successful_downloads = 0
            logger.info(f"Starting download of {len(image_urls)} images...")
            
            for url in image_urls:
                if self.download_image(url):
                    successful_downloads += 1

            logger.info(f"Download complete. Successfully downloaded {successful_downloads} out of {len(image_urls)} images.")

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Download all images from a webpage')
    parser.add_argument('--url', help='URL of the webpage to download images from')
    parser.add_argument('--output', help='Output directory for downloaded images', default='./downloads')
    
    args = parser.parse_args()
    url = args.url

    # If URL is not provided via command line, ask for it interactively
    if not url:
        url = input("Please enter the webpage URL: ").strip()

    try:
        grabber = ImageGrabber(url=url, output_dir=args.output)
        grabber.run()
    except Exception as e:
        logger.error(f"Program terminated with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 