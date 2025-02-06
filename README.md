# Grabr - Web Image Downloader

Grabr is a Python tool that downloads all images from a specified webpage. It extracts image sources from HTML content and saves them to your local disk.

## Features

- Downloads all images from a given webpage
- Supports both absolute and relative image URLs
- Shows download progress with progress bar
- Allows specifying custom download directory
- Handles errors gracefully with proper logging

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

You can run the script in two ways:

1. With command line arguments:
```bash
python grabr.py --url https://example.com --output ./downloads
```

2. Interactive mode:
```bash
python grabr.py
```

### Arguments

- `--url`: The webpage URL to download images from
- `--output`: (Optional) Output directory for downloaded images. Default is './downloads'

## Error Handling

The tool includes comprehensive error handling for:
- Invalid URLs
- Network connection issues
- Invalid image files
- Permission errors
- File system errors 