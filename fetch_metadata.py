#!/usr/bin/env python3
"""
Fetch additional metadata from Wikimedia Commons API.
"""

import json
import os
import requests
import time
from urllib.parse import quote

class MetadataFetcher:
    def __init__(self, maps_data_file='data/extracted_maps.json'):
        self.maps_data_file = maps_data_file
        self.api_url = 'https://commons.wikimedia.org/w/api.php'
        
    def fetch_file_info(self, filename):
        """Fetch file information from Wikimedia Commons API."""
        if not filename:
            return None
        
        params = {
            'action': 'query',
            'format': 'json',
            'titles': f'File:{filename}',
            'prop': 'imageinfo|revisions',
            'iiprop': 'url|size|mime|extmetadata|timestamp|user',
            'rvprop': 'content|timestamp|user',
            'rvslots': 'main'
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.api_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return None
            
            # Get first page (should only be one)
            page_id = list(pages.keys())[0]
            page_data = pages[page_id]
            
            if page_id == '-1':
                return None
            
            file_info = {
                'filename': filename,
                'page_id': page_id,
                'title': page_data.get('title', ''),
                'imageinfo': [],
                'revisions': []
            }
            
            # Extract imageinfo
            imageinfo = page_data.get('imageinfo', [])
            if imageinfo:
                info = imageinfo[0]
                file_info['imageinfo'] = {
                    'url': info.get('url', ''),
                    'descriptionurl': info.get('descriptionurl', ''),
                    'size': info.get('size', 0),
                    'width': info.get('width', 0),
                    'height': info.get('height', 0),
                    'mime': info.get('mime', ''),
                    'timestamp': info.get('timestamp', ''),
                    'user': info.get('user', ''),
                    'extmetadata': info.get('extmetadata', {})
                }
            
            # Extract revisions (description page content)
            revisions = page_data.get('revisions', [])
            if revisions:
                rev = revisions[0]
                file_info['revisions'] = {
                    'content': rev.get('slots', {}).get('main', {}).get('*', ''),
                    'timestamp': rev.get('timestamp', ''),
                    'user': rev.get('user', '')
                }
            
            return file_info
            
        except Exception as e:
            print(f"  Error fetching metadata for {filename}: {e}")
            return None
    
    def parse_wikitext_metadata(self, wikitext):
        """Parse metadata from wikitext description page."""
        metadata = {
            'license': None,
            'author': None,
            'source': None,
            'date': None,
            'categories': [],
            'description': None
        }
        
        if not wikitext:
            return metadata
        
        # Extract license
        license_patterns = [
            r'\{\{([^}]*[Ll]icense[^}]*)\}\}',
            r'==\s*[Ll]icensing\s*==(.*?)(?=\n==|\Z)',
        ]
        for pattern in license_patterns:
            import re
            match = re.search(pattern, wikitext, re.DOTALL | re.IGNORECASE)
            if match:
                metadata['license'] = match.group(1).strip()
                break
        
        # Extract author
        author_patterns = [
            r'\|\s*[Aa]uthor\s*=\s*([^\n|]+)',
            r'==\s*[Aa]uthor\s*==(.*?)(?=\n==|\Z)',
        ]
        for pattern in author_patterns:
            match = re.search(pattern, wikitext, re.DOTALL | re.IGNORECASE)
            if match:
                metadata['author'] = match.group(1).strip()
                break
        
        # Extract source
        source_patterns = [
            r'\|\s*[Ss]ource\s*=\s*([^\n|]+)',
            r'==\s*[Ss]ource\s*==(.*?)(?=\n==|\Z)',
        ]
        for pattern in source_patterns:
            match = re.search(pattern, wikitext, re.DOTALL | re.IGNORECASE)
            if match:
                metadata['source'] = match.group(1).strip()
                break
        
        # Extract date
        date_patterns = [
            r'\|\s*[Dd]ate\s*=\s*([^\n|]+)',
            r'==\s*[Dd]ate\s*==(.*?)(?=\n==|\Z)',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, wikitext, re.DOTALL | re.IGNORECASE)
            if match:
                metadata['date'] = match.group(1).strip()
                break
        
        # Extract categories
        category_pattern = r'\[\[Category:([^\]]+)\]\]'
        categories = re.findall(category_pattern, wikitext)
        metadata['categories'] = categories
        
        return metadata
    
    def fetch_all(self):
        """Fetch metadata for all maps."""
        print(f"Loading maps data from {self.maps_data_file}...")
        with open(self.maps_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        maps = data.get('maps', [])
        print(f"Found {len(maps)} maps to fetch metadata for\n")
        
        enriched_maps = []
        failed = []
        
        for i, map_data in enumerate(maps, 1):
            filename = map_data.get('filename')
            if not filename:
                continue
            
            print(f"[{i}/{len(maps)}] Fetching metadata for: {filename}")
            
            file_info = self.fetch_file_info(filename)
            if file_info:
                # Merge API data with existing map data
                enriched_map = map_data.copy()
                
                # Add API metadata
                enriched_map['api_metadata'] = {
                    'page_id': file_info.get('page_id'),
                    'title': file_info.get('title'),
                    'imageinfo': file_info.get('imageinfo', {}),
                    'revisions': file_info.get('revisions', {})
                }
                
                # Parse wikitext for additional metadata
                wikitext = file_info.get('revisions', {}).get('content', '')
                if wikitext:
                    parsed_metadata = self.parse_wikitext_metadata(wikitext)
                    enriched_map['parsed_metadata'] = parsed_metadata
                    
                    # Extract categories from parsed metadata
                    if parsed_metadata.get('categories'):
                        enriched_map['categories'].extend(parsed_metadata['categories'])
                        enriched_map['categories'] = list(set(enriched_map['categories']))
                
                # Use API URL if available
                if file_info.get('imageinfo', {}).get('url'):
                    enriched_map['original_url'] = file_info['imageinfo']['url']
                
                enriched_maps.append(enriched_map)
                print(f"  ✓ Metadata fetched")
            else:
                print(f"  ✗ Failed to fetch metadata")
                enriched_maps.append(map_data)  # Keep original data
                failed.append(filename)
            
            # Be polite - delay between API requests
            time.sleep(0.5)
        
        # Update data with enriched maps
        data['maps'] = enriched_maps
        
        # Save enriched data
        output_file = 'data/enriched_maps.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Metadata Fetch Summary:")
        print(f"  Total maps: {len(maps)}")
        print(f"  Successful: {len(enriched_maps) - len(failed)}")
        print(f"  Failed: {len(failed)}")
        print(f"  Enriched data saved to: {output_file}")
        
        return data

if __name__ == '__main__':
    fetcher = MetadataFetcher()
    fetcher.fetch_all()

