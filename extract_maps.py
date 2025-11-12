#!/usr/bin/env python3
"""
Extract maps and metadata from the saved Wikimedia Commons HTML page.
"""

import re
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from datetime import datetime
from dateutil import parser as date_parser
import html

class MapExtractor:
    def __init__(self, html_file):
        self.html_file = html_file
        self.maps = []
        self.sections = []
        
    def extract_dates(self, text):
        """Extract dates from text, filenames, or captions."""
        dates = []
        
        # Look for 4-digit years (1000-2999)
        year_pattern = r'\b(1[0-9]{3}|2[0-9]{3})\b'
        years = re.findall(year_pattern, text)
        
        for year in years:
            try:
                year_int = int(year)
                if 1000 <= year_int <= 2999:
                    dates.append(year_int)
            except ValueError:
                continue
        
        return sorted(set(dates))
    
    def extract_file_name_from_url(self, url):
        """Extract filename from Wikimedia Commons URL."""
        if 'File:' in url:
            filename = url.split('File:')[-1].split('#')[0].split('?')[0]
            return unquote(filename)
        return None
    
    def parse_multilingual_text(self, element):
        """Extract multilingual descriptions from HTML."""
        descriptions = {}
        
        # Look for multilingual divs
        lang_divs = element.find_all('div', class_='description')
        for div in lang_divs:
            lang_span = div.find('span', class_='language')
            if lang_span:
                lang_code = lang_span.get('lang', '')
                if lang_code:
                    # Get text after the language label
                    text_parts = []
                    for content in div.contents:
                        if isinstance(content, str):
                            text_parts.append(content.strip())
                        elif content.name not in ['span', 'b']:
                            text_parts.append(content.get_text(strip=True))
                    desc_text = ' '.join(text_parts).strip()
                    # Remove language label prefix
                    if desc_text.startswith(lang_span.get_text()):
                        desc_text = desc_text[len(lang_span.get_text()):].strip()
                    if desc_text:
                        descriptions[lang_code] = desc_text
        
        # Also get plain text if no multilingual found
        if not descriptions:
            text = element.get_text(strip=True)
            if text:
                descriptions['en'] = text
        
        return descriptions
    
    def parse_figure(self, figure):
        """Parse a figure element containing a map."""
        map_data = {
            'commons_url': None,
            'filename': None,
            'thumb_url': None,
            'original_url': None,
            'captions': {},
            'descriptions': {},
            'dates': [],
            'categories': [],
            'section': None,
            'width': None,
            'height': None,
            'file_width': None,
            'file_height': None
        }
        
        # Find the link to Wikimedia Commons file page
        link = figure.find('a', href=re.compile(r'commons\.wikimedia\.org/wiki/File:'))
        if link:
            map_data['commons_url'] = link.get('href', '')
            map_data['filename'] = self.extract_file_name_from_url(map_data['commons_url'])
        
        # Find image element
        img = figure.find('img')
        if img:
            # Get thumbnail URL
            map_data['thumb_url'] = img.get('src', '')
            
            # Get dimensions
            map_data['width'] = img.get('width')
            map_data['height'] = img.get('height')
            map_data['file_width'] = img.get('data-file-width')
            map_data['file_height'] = img.get('data-file-height')
            
            # Construct original URL from thumbnail URL or use srcset
            srcset = img.get('srcset', '')
            if srcset:
                # Get the largest size from srcset
                srcset_parts = srcset.split(',')
                if srcset_parts:
                    largest = srcset_parts[-1].strip().split()[0]
                    if largest.startswith('http'):
                        map_data['original_url'] = largest
                    else:
                        # Construct from thumbnail URL
                        thumb_base = map_data['thumb_url'].replace('/thumb/', '/').split('/')[0:-1]
                        if '/thumb/' in map_data['thumb_url']:
                            # Extract original filename from thumb URL
                            parts = map_data['thumb_url'].split('/thumb/')
                            if len(parts) > 1:
                                file_part = parts[1].split('/')[0]
                                map_data['original_url'] = f"https://upload.wikimedia.org/wikipedia/commons/{file_part}"
        
        # Parse figcaption
        figcaption = figure.find('figcaption')
        if figcaption:
            map_data['captions'] = self.parse_multilingual_text(figcaption)
        
        # Extract dates from filename, captions, and titles
        date_texts = []
        if map_data['filename']:
            date_texts.append(map_data['filename'])
        for lang, caption in map_data['captions'].items():
            date_texts.append(caption)
        if link:
            title = link.get('title', '')
            date_texts.append(title)
        
        all_dates = []
        for text in date_texts:
            all_dates.extend(self.extract_dates(text))
        map_data['dates'] = sorted(set(all_dates))
        
        return map_data
    
    def parse_gallery_item(self, gallery_item):
        """Parse a gallery item."""
        map_data = {
            'commons_url': None,
            'filename': None,
            'thumb_url': None,
            'original_url': None,
            'captions': {},
            'descriptions': {},
            'dates': [],
            'categories': [],
            'section': None,
            'width': None,
            'height': None,
            'file_width': None,
            'file_height': None
        }
        
        # Find link
        link = gallery_item.find('a', href=re.compile(r'commons\.wikimedia\.org/wiki/File:'))
        if link:
            map_data['commons_url'] = link.get('href', '')
            map_data['filename'] = self.extract_file_name_from_url(map_data['commons_url'])
            title = link.get('title', '')
            if title:
                map_data['captions'] = {'en': title}
        
        # Find image
        img = gallery_item.find('img')
        if img:
            map_data['thumb_url'] = img.get('src', '')
            map_data['width'] = img.get('width')
            map_data['height'] = img.get('height')
            map_data['file_width'] = img.get('data-file-width')
            map_data['file_height'] = img.get('data-file-height')
            
            alt = img.get('alt', '')
            if alt and not map_data['captions']:
                map_data['captions'] = {'en': alt}
        
        # Get gallery text
        gallerytext = gallery_item.find('div', class_='gallerytext')
        if gallerytext:
            text = gallerytext.get_text(strip=True)
            if text:
                map_data['captions'] = {'en': text}
        
        # Extract dates
        date_texts = []
        if map_data['filename']:
            date_texts.append(map_data['filename'])
        for lang, caption in map_data['captions'].items():
            date_texts.append(caption)
        
        all_dates = []
        for text in date_texts:
            all_dates.extend(self.extract_dates(text))
        map_data['dates'] = sorted(set(all_dates))
        
        return map_data
    
    def extract_sections(self, soup):
        """Extract section headings and structure."""
        sections = []
        content_div = soup.find('div', id='mw-content-text')
        if not content_div:
            return sections
        
        current_section = None
        for element in content_div.find_all(['h2', 'h3', 'h4']):
            section_id = element.get('id', '')
            section_text = element.get_text(strip=True)
            
            if element.name == 'h2':
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'id': section_id,
                    'title': section_text,
                    'level': 2,
                    'subsections': []
                }
            elif element.name == 'h3' and current_section:
                current_section['subsections'].append({
                    'id': section_id,
                    'title': section_text,
                    'level': 3
                })
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def extract(self):
        """Main extraction method."""
        print(f"Reading HTML file: {self.html_file}")
        with open(self.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print("Parsing HTML...")
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract sections
        print("Extracting sections...")
        self.sections = self.extract_sections(soup)
        
        # Extract figures
        print("Extracting figures...")
        figures = soup.find_all('figure', typeof=re.compile(r'mw:File'))
        for i, figure in enumerate(figures):
            map_data = self.parse_figure(figure)
            if map_data['filename']:
                self.maps.append(map_data)
                print(f"  Found figure {i+1}: {map_data['filename']}")
        
        # Extract gallery items
        print("Extracting gallery items...")
        galleries = soup.find_all('ul', class_='gallery')
        for gallery in galleries:
            gallery_items = gallery.find_all('li', class_='gallerybox')
            for item in gallery_items:
                map_data = self.parse_gallery_item(item)
                if map_data['filename']:
                    # Try to determine section from parent elements
                    parent_h2 = item.find_parent('h2')
                    if parent_h2:
                        section_id = parent_h2.get('id', '')
                        map_data['section'] = section_id
                    self.maps.append(map_data)
                    print(f"  Found gallery item: {map_data['filename']}")
        
        # Extract images from tables
        print("Extracting images from tables...")
        tables = soup.find_all('table')
        for table in tables:
            images = table.find_all('img', src=re.compile(r'commons'))
            for img in images:
                # Find parent link
                link = img.find_parent('a', href=re.compile(r'commons\.wikimedia\.org/wiki/File:'))
                if link:
                    map_data = {
                        'commons_url': link.get('href', ''),
                        'filename': self.extract_file_name_from_url(link.get('href', '')),
                        'thumb_url': img.get('src', ''),
                        'original_url': None,
                        'captions': {},
                        'descriptions': {},
                        'dates': [],
                        'categories': [],
                        'section': None,
                        'width': img.get('width'),
                        'height': img.get('height'),
                        'file_width': img.get('data-file-width'),
                        'file_height': img.get('data-file-height')
                    }
                    
                    if map_data['filename']:
                        # Check if we already have this map
                        existing = [m for m in self.maps if m['filename'] == map_data['filename']]
                        if not existing:
                            title = link.get('title', '')
                            if title:
                                map_data['captions'] = {'en': title}
                            
                            # Extract dates
                            date_texts = [map_data['filename'], title]
                            all_dates = []
                            for text in date_texts:
                                all_dates.extend(self.extract_dates(text))
                            map_data['dates'] = sorted(set(all_dates))
                            
                            self.maps.append(map_data)
                            print(f"  Found table image: {map_data['filename']}")
        
        # Remove duplicates based on filename
        seen = set()
        unique_maps = []
        for map_data in self.maps:
            if map_data['filename'] and map_data['filename'] not in seen:
                seen.add(map_data['filename'])
                unique_maps.append(map_data)
        
        self.maps = unique_maps
        print(f"\nTotal unique maps found: {len(self.maps)}")
        
        return {
            'maps': self.maps,
            'sections': self.sections
        }

if __name__ == '__main__':
    html_file = 'User_Enyavar_DiscussingMaps - Wikimedia Commons.html'
    extractor = MapExtractor(html_file)
    result = extractor.extract()
    
    # Save results
    os.makedirs('data', exist_ok=True)
    with open('data/extracted_maps.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nExtraction complete! Results saved to data/extracted_maps.json")
    print(f"Found {len(result['maps'])} maps and {len(result['sections'])} sections")

