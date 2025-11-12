#!/usr/bin/env python3
"""
Organize maps chronologically and build inter-related links.
"""

import json
import os
import re
from collections import defaultdict

class ChronologyOrganizer:
    def __init__(self, enriched_maps_file='data/enriched_maps.json'):
        self.enriched_maps_file = enriched_maps_file
        
    def extract_best_date(self, map_data):
        """Extract the best available date for chronological sorting."""
        dates = map_data.get('dates', [])
        
        # If we have dates extracted from filename/captions, use the earliest
        if dates:
            return min(dates)
        
        # Try to extract from parsed metadata
        parsed_metadata = map_data.get('parsed_metadata', {})
        date_str = parsed_metadata.get('date')
        if date_str:
            # Try to extract year from date string
            year_match = re.search(r'\b(1[0-9]{3}|2[0-9]{3})\b', date_str)
            if year_match:
                return int(year_match.group(1))
        
        # Try to extract from API timestamp
        api_metadata = map_data.get('api_metadata', {})
        imageinfo = api_metadata.get('imageinfo', {})
        timestamp = imageinfo.get('timestamp')
        if timestamp:
            # Extract year from timestamp (format: 2024-01-01T00:00:00Z)
            year_match = re.search(r'^(\d{4})', timestamp)
            if year_match:
                return int(year_match.group(1))
        
        # Try to extract from filename
        filename = map_data.get('filename', '')
        year_match = re.search(r'\b(1[0-9]{3}|2[0-9]{3})\b', filename)
        if year_match:
            return int(year_match.group(1))
        
        # Default to a very old date if no date found (will sort to beginning)
        return 0
    
    def extract_geographic_regions(self, map_data):
        """Extract geographic regions from filename, captions, and categories."""
        regions = set()
        
        # Common geographic terms
        geo_terms = [
            'Europe', 'Asia', 'Africa', 'America', 'North', 'South', 'East', 'West',
            'Germany', 'France', 'Spain', 'Italy', 'UK', 'United States', 'USA',
            'China', 'Japan', 'India', 'Brazil', 'Russia', 'Austria', 'Hungary',
            'Netherlands', 'Belgium', 'Switzerland', 'Poland', 'Romania',
            'Madagascar', 'Indonesia', 'Southeast Asia', 'Balkans', 'Holy Land',
            'Paris', 'Vienna', 'Budapest', 'Linz', 'Luxembourg', 'Bayern',
            'Colorado', 'Kazakhstan', 'Karaganda', 'Antwerp', 'Chieti',
            'Luhansk', 'Praha', 'Machakos', 'Weehawken', 'Lučenec'
        ]
        
        # Check filename
        filename = map_data.get('filename', '').lower()
        for term in geo_terms:
            if term.lower() in filename:
                regions.add(term)
        
        # Check captions
        for lang, caption in map_data.get('captions', {}).items():
            caption_lower = caption.lower()
            for term in geo_terms:
                if term.lower() in caption_lower:
                    regions.add(term)
        
        # Check categories
        for category in map_data.get('categories', []):
            category_lower = category.lower()
            for term in geo_terms:
                if term.lower() in category_lower:
                    regions.add(term)
        
        return list(regions)
    
    def extract_themes(self, map_data):
        """Extract themes/subjects from categories and captions."""
        themes = set()
        
        # Common theme keywords
        theme_keywords = {
            'historical': ['historical', 'history', 'old', 'ancient', 'antique'],
            'economic': ['economic', 'gdp', 'income', 'wealth', 'poverty', 'trade'],
            'transport': ['transport', 'road', 'rail', 'metro', 'highway', 'autobahn', 'shinkansen'],
            'political': ['political', 'election', 'council', 'governor'],
            'topographic': ['topographic', 'topography', 'relief', 'geology'],
            'population': ['population', 'density', 'demographic'],
            'location': ['location', 'locator', 'blank', 'outline'],
            'thematic': ['thematic', 'theme', 'subject']
        }
        
        # Check categories
        for category in map_data.get('categories', []):
            category_lower = category.lower()
            for theme, keywords in theme_keywords.items():
                if any(keyword in category_lower for keyword in keywords):
                    themes.add(theme)
        
        # Check captions
        for lang, caption in map_data.get('captions', {}).items():
            caption_lower = caption.lower()
            for theme, keywords in theme_keywords.items():
                if any(keyword in caption_lower for keyword in keywords):
                    themes.add(theme)
        
        return list(themes)
    
    def build_links(self, maps):
        """Build inter-related links between maps."""
        links = defaultdict(list)
        
        for i, map1 in enumerate(maps):
            map1_id = map1.get('id', i)
            map1_regions = set(map1.get('geographic_regions', []))
            map1_themes = set(map1.get('themes', []))
            map1_date = map1.get('chronological_date', 0)
            
            for j, map2 in enumerate(maps):
                if i == j:
                    continue
                
                map2_id = map2.get('id', j)
                map2_regions = set(map2.get('geographic_regions', []))
                map2_themes = set(map2.get('themes', []))
                map2_date = map2.get('chronological_date', 0)
                
                # Calculate similarity score
                score = 0
                link_reasons = []
                
                # Geographic similarity
                common_regions = map1_regions & map2_regions
                if common_regions:
                    score += len(common_regions) * 2
                    link_reasons.append(f"Same region: {', '.join(common_regions)}")
                
                # Theme similarity
                common_themes = map1_themes & map2_themes
                if common_themes:
                    score += len(common_themes) * 2
                    link_reasons.append(f"Same theme: {', '.join(common_themes)}")
                
                # Temporal proximity (within 50 years)
                if map1_date > 0 and map2_date > 0:
                    date_diff = abs(map1_date - map2_date)
                    if date_diff <= 50:
                        score += 1
                        link_reasons.append(f"Temporal proximity: {date_diff} years apart")
                
                # If score is significant, create link
                if score >= 2:
                    links[map1_id].append({
                        'target_id': map2_id,
                        'target_filename': map2.get('filename'),
                        'score': score,
                        'reasons': link_reasons
                    })
        
        return dict(links)
    
    def organize(self):
        """Organize maps chronologically and build links."""
        # Try enriched file first, fall back to extracted if not available
        if not os.path.exists(self.enriched_maps_file):
            fallback_file = 'data/extracted_maps.json'
            if os.path.exists(fallback_file):
                print(f"Enriched maps not found, using {fallback_file}...")
                self.enriched_maps_file = fallback_file
            else:
                raise FileNotFoundError(f"Neither {self.enriched_maps_file} nor {fallback_file} found")
        
        print(f"Loading maps from {self.enriched_maps_file}...")
        with open(self.enriched_maps_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        maps = data.get('maps', [])
        print(f"Processing {len(maps)} maps...\n")
        
        # Process each map
        for i, map_data in enumerate(maps):
            # Assign ID
            map_data['id'] = i
            
            # Extract chronological date
            map_data['chronological_date'] = self.extract_best_date(map_data)
            
            # Extract geographic regions
            map_data['geographic_regions'] = self.extract_geographic_regions(map_data)
            
            # Extract themes
            map_data['themes'] = self.extract_themes(map_data)
        
        # Sort chronologically
        print("Sorting maps chronologically...")
        maps_sorted = sorted(maps, key=lambda x: (
            x.get('chronological_date', 0),
            x.get('filename', '')
        ))
        
        # Reassign IDs after sorting
        for i, map_data in enumerate(maps_sorted):
            map_data['id'] = i
        
        # Build inter-related links
        print("Building inter-related links...")
        links = self.build_links(maps_sorted)
        
        # Create timeline structure
        timeline = []
        current_year = None
        current_group = None
        
        for map_data in maps_sorted:
            year = map_data.get('chronological_date', 0)
            
            if year != current_year:
                if current_group:
                    timeline.append(current_group)
                current_year = year
                current_group = {
                    'year': year if year > 0 else 'Unknown',
                    'maps': []
                }
            
            current_group['maps'].append(map_data['id'])
        
        if current_group:
            timeline.append(current_group)
        
        # Prepare output
        organized_data = {
            'maps': maps_sorted,
            'timeline': timeline,
            'links': links,
            'statistics': {
                'total_maps': len(maps_sorted),
                'maps_with_dates': len([m for m in maps_sorted if m.get('chronological_date', 0) > 0]),
                'maps_with_regions': len([m for m in maps_sorted if m.get('geographic_regions')]),
                'maps_with_themes': len([m for m in maps_sorted if m.get('themes')]),
                'total_links': sum(len(links_list) for links_list in links.values())
            }
        }
        
        # Save organized data
        output_file = 'data/organized_maps.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(organized_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Organization Summary:")
        print(f"  Total maps: {organized_data['statistics']['total_maps']}")
        print(f"  Maps with dates: {organized_data['statistics']['maps_with_dates']}")
        print(f"  Maps with regions: {organized_data['statistics']['maps_with_regions']}")
        print(f"  Maps with themes: {organized_data['statistics']['maps_with_themes']}")
        print(f"  Total links: {organized_data['statistics']['total_links']}")
        print(f"  Timeline entries: {len(timeline)}")
        print(f"  Organized data saved to: {output_file}")
        
        return organized_data

if __name__ == '__main__':
    organizer = ChronologyOrganizer()
    organizer.organize()

