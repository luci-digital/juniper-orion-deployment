#!/usr/bin/env python3
"""
Main script to run the complete pipeline:
1. Extract maps from HTML
2. Download images
3. Fetch metadata from API
4. Organize chronologically
5. Generate output
"""

import sys
import os

def main():
    print("="*60)
    print("Maps Chronology Pipeline")
    print("="*60)
    print()
    
    # Step 1: Extract maps from HTML
    print("STEP 1: Extracting maps from HTML...")
    print("-"*60)
    from extract_maps import MapExtractor
    extractor = MapExtractor('User_Enyavar_DiscussingMaps - Wikimedia Commons.html')
    result = extractor.extract()
    print()
    
    # Step 2: Download images (optional - can be skipped if files already exist)
    print("STEP 2: Downloading original images...")
    print("-"*60)
    print("Note: This may take a while. You can skip this step if images are already downloaded.")
    response = input("Download images now? (y/n, default: y): ").strip().lower()
    if response != 'n':
        from download_images import ImageDownloader
        downloader = ImageDownloader()
        downloader.download_all()
    else:
        print("Skipping image download.")
    print()
    
    # Step 3: Fetch metadata from API
    print("STEP 3: Fetching metadata from Wikimedia Commons API...")
    print("-"*60)
    print("Note: This may take a while due to API rate limiting.")
    response = input("Fetch metadata now? (y/n, default: y): ").strip().lower()
    if response != 'n':
        from fetch_metadata import MetadataFetcher
        fetcher = MetadataFetcher('data/extracted_maps.json')
        fetcher.fetch_all()
        enriched_file = 'data/enriched_maps.json'
    else:
        print("Skipping metadata fetch. Using extracted data only.")
        enriched_file = 'data/extracted_maps.json'
    print()
    
    # Step 4: Organize chronologically
    print("STEP 4: Organizing maps chronologically...")
    print("-"*60)
    from organize_chronology import ChronologyOrganizer
    organizer = ChronologyOrganizer(enriched_file)
    organizer.organize()
    print()
    
    # Step 5: Generate output
    print("STEP 5: Generating output structure...")
    print("-"*60)
    from generate_output import OutputGenerator
    generator = OutputGenerator('data/organized_maps.json')
    generator.generate()
    print()
    
    print("="*60)
    print("Pipeline Complete!")
    print("="*60)
    print()
    print("Output files:")
    print("  - chronology/index.html - Main timeline page")
    print("  - chronology/maps/ - Individual map pages")
    print("  - chronology/data/ - JSON data files")
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

