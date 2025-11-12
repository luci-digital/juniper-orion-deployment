# Maps Chronology Project

This project extracts maps from a saved Wikimedia Commons discussion page, organizes them chronologically, and creates an interactive timeline with inter-related links and citations.

## Project Structure

```
dis_maops/
├── extract_maps.py          # Extract maps and metadata from HTML
├── download_images.py        # Download original images from Wikimedia Commons
├── fetch_metadata.py         # Fetch additional metadata via API
├── organize_chronology.py    # Organize maps chronologically and build links
├── generate_output.py        # Generate HTML output and structure
├── run_pipeline.py          # Main script to run all steps
├── requirements.txt         # Python dependencies
├── data/                    # Intermediate data files
│   ├── extracted_maps.json
│   ├── enriched_maps.json (optional)
│   ├── organized_maps.json
│   └── download_results.json (optional)
├── downloads/               # Downloaded original images
│   └── originals/
└── chronology/              # Final output
    ├── index.html           # Main timeline page
    ├── maps/                # Individual map pages
    │   ├── 0000_*/         # One folder per map
    │   │   ├── image.*
    │   │   ├── metadata.json
    │   │   └── description.md
    └── data/                # JSON data files
        ├── timeline.json
        ├── links.json
        └── metadata.json
```

## Usage

### Quick Start

Run the complete pipeline:
```bash
python3 run_pipeline.py
```

### Step by Step

1. **Extract maps from HTML:**
   ```bash
   python3 extract_maps.py
   ```

2. **Download original images (optional, may take time):**
   ```bash
   python3 download_images.py
   ```

3. **Fetch metadata from API (optional, may take time):**
   ```bash
   python3 fetch_metadata.py
   ```

4. **Organize chronologically:**
   ```bash
   python3 organize_chronology.py
   ```

5. **Generate output:**
   ```bash
   python3 generate_output.py
   ```

## Features

- **Chronological Organization**: Maps are sorted by date (extracted from filenames, captions, and metadata)
- **Inter-Related Links**: Maps are linked by geographic regions, themes, and temporal proximity
- **Citations & Footnotes**: All citations and attribution information is preserved
- **Multilingual Support**: Captions in multiple languages are extracted and displayed
- **Timeline View**: Interactive HTML timeline showing maps organized by year
- **Individual Map Pages**: Each map has its own page with metadata, descriptions, and related maps

## Output

The main output is in the `chronology/` directory:
- `index.html` - Interactive timeline showing all maps chronologically
- `maps/` - Individual folders for each map with images, metadata, and descriptions
- `data/` - JSON files with timeline, links, and metadata

## Statistics

From the current extraction:
- **65 maps** extracted from the HTML page
- **23 maps** have identifiable dates
- **25 maps** have geographic region information
- **32 inter-related links** created between maps
- **21 timeline groups** (by year)

## Notes

- Image downloads and API metadata fetching are optional steps that can take significant time due to rate limiting
- The system works with extracted data even if downloads/metadata fetching are skipped
- All scripts include error handling and progress reporting
- Citations and footnotes are extracted from both HTML content and API metadata

## Dependencies

Install required packages:
```bash
pip3 install -r requirements.txt
```

Required packages:
- beautifulsoup4
- requests
- python-dateutil
- lxml
- html5lib

