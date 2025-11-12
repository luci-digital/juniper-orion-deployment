#!/usr/bin/env python3
"""
Download original high-resolution images from Wikimedia Commons.
"""

import json
import os
import requests
from urllib.parse import urlparse, unquote
import time

class ImageDownloader:
    def __init__(self, maps_data_file='data/extracted_maps.json'):
        self.maps_data_file = maps_data_file
        self.download_dir = 'downloads/originals'
        os.makedirs(self.download_dir, exist_ok=True)
        
    def construct_download_url(self, filename):
        """Construct direct download URL for Wikimedia Commons file."""
        if not filename:
            return None
        
        # Wikimedia Commons uses first character and first two characters for URL structure
        # e.g., File:Example.jpg -> https://upload.wikimedia.org/wikipedia/commons/E/x/Example.jpg
        first_char = filename[0]
        if len(filename) > 1:
            second_char = filename[1]
        else:
            second_char = first_char
        
        # URL encode the filename
        encoded_filename = filename.replace(' ', '_')
        
        # Construct URL
        url = f"https://upload.wikimedia.org/wikipedia/commons/{first_char}/{first_char}{second_char}/{encoded_filename}"
        return url
    
    def download_image(self, url, filepath):
        """Download an image from URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"  Error downloading {url}: {e}")
            return False
    
    def download_all(self):
        """Download all images from the extracted maps data."""
        print(f"Loading maps data from {self.maps_data_file}...")
        with open(self.maps_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        maps = data.get('maps', [])
        print(f"Found {len(maps)} maps to download\n")
        
        downloaded = []
        failed = []
        
        for i, map_data in enumerate(maps, 1):
            filename = map_data.get('filename')
            if not filename:
                continue
            
            print(f"[{i}/{len(maps)}] Processing: {filename}")
            
            # Construct download URL
            download_url = self.construct_download_url(filename)
            if not download_url:
                print(f"  Could not construct URL for {filename}")
                failed.append(map_data)
                continue
            
            # Determine file extension
            ext = os.path.splitext(filename)[1] or '.jpg'
            filepath = os.path.join(self.download_dir, filename)
            
            # Check if already downloaded
            if os.path.exists(filepath):
                print(f"  Already exists: {filepath}")
                downloaded.append({
                    'map': map_data,
                    'filepath': filepath,
                    'url': download_url
                })
                continue
            
            # Try downloading
            print(f"  Downloading from: {download_url}")
            if self.download_image(download_url, filepath):
                print(f"  ✓ Downloaded: {filepath}")
                downloaded.append({
                    'map': map_data,
                    'filepath': filepath,
                    'url': download_url
                })
            else:
                # Try alternative URL format (without subdirectory structure)
                alt_url = f"https://upload.wikimedia.org/wikipedia/commons/{filename.replace(' ', '_')}"
                print(f"  Trying alternative URL: {alt_url}")
                if self.download_image(alt_url, filepath):
                    print(f"  ✓ Downloaded: {filepath}")
                    downloaded.append({
                        'map': map_data,
                        'filepath': filepath,
                        'url': alt_url
                    })
                else:
                    print(f"  ✗ Failed to download")
                    failed.append(map_data)
            
            # Be polite - small delay between requests
            time.sleep(0.5)
        
        # Save download results
        results = {
            'downloaded': downloaded,
            'failed': failed,
            'total': len(maps),
            'successful': len(downloaded),
            'failed_count': len(failed)
        }
        
        results_file = 'data/download_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Download Summary:")
        print(f"  Total maps: {results['total']}")
        print(f"  Successful: {results['successful']}")
        print(f"  Failed: {results['failed_count']}")
        print(f"  Results saved to: {results_file}")
        
        return results

if __name__ == '__main__':
    downloader = ImageDownloader()
    downloader.download_all()

