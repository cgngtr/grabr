# Coffy Menu Grabber

A Python tool specifically designed to scrape and download menu items from Coffy's website (coffy.com.tr). This tool can extract menu items, their descriptions, and associated images.

## Features

- Downloads menu items and images from Coffy's menu page
- Multiple download modes:
  - Full content (menu items with images)
  - Images only
  - Menu items only (without images)
  - Flat mode (all images in a single directory)
- Proper handling of Turkish characters
- Progress bars for downloads
- Comprehensive logging
- Supports both command-line and interactive usage

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - requests>=2.31.0
  - beautifulsoup4>=4.12.0
  - tqdm>=4.66.0
  - urllib3>=2.0.0

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/coffy-grabber.git
cd coffy-grabber
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode

Simply run the script without arguments:
```bash
python grabr.py
```

The tool will prompt you for:
1. The menu URL (https://coffy.com.tr/menu)
2. Download mode selection:
   - Option 1: Full content (menu items and images)
   - Option 2: Images only
   - Option 3: Menu items only (without images)
   - Option 4: Flat mode (all images in single directory)

### Command Line Mode

You can also run the tool with command-line arguments:

```bash
# Download everything (menu items and images)
python grabr.py --url https://coffy.com.tr/menu --mode all

# Download only images
python grabr.py --url https://coffy.com.tr/menu --mode images

# Download only menu items (no images)
python grabr.py --url https://coffy.com.tr/menu --mode menu

# Download all images to a single directory
python grabr.py --url https://coffy.com.tr/menu --mode flat
```

Optional arguments:
- `--output`: Specify custom output directory (default: ./menu_items)

## Output Structure

### Normal Modes (all, images, menu)
```
menu_items/
├── espresso/
│   ├── espresso_details.txt
│   └── espresso.jpg
├── latte/
│   ├── latte_details.txt
│   └── latte.jpg
└── ...
```

### Flat Mode
```
menu_items/
├── espresso.jpg
├── latte.jpg
└── ...
```

## Notes

- The tool is specifically designed for Coffy's menu page structure
- Turkish characters in menu items are properly handled
- Images are downloaded with their original quality
- A log file (grabr.log) is created for debugging purposes

## Error Handling

The tool includes comprehensive error handling for:
- Network connection issues
- Invalid image URLs
- File system errors
- Character encoding issues

## License

This project is licensed under the MIT License - see the LICENSE file for details. 