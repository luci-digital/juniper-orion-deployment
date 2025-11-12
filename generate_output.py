#!/usr/bin/env python3
"""
Generate output structure with HTML index, individual map pages, and citations.
"""

import json
import os
import re
from datetime import datetime

class OutputGenerator:
    def __init__(self, organized_data_file='data/organized_maps.json'):
        self.organized_data_file = organized_data_file
        self.output_dir = 'chronology'
        self.maps_dir = os.path.join(self.output_dir, 'maps')
        self.data_dir = os.path.join(self.output_dir, 'data')
        self.assets_dir = os.path.join(self.output_dir, 'assets')
        
        os.makedirs(self.maps_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.assets_dir, exist_ok=True)
    
    def format_citation(self, map_data):
        """Format citation and attribution information."""
        citations = []
        
        filename = map_data.get('filename', '')
        commons_url = map_data.get('commons_url', '')
        
        # Get author information
        author = None
        parsed_metadata = map_data.get('parsed_metadata', {})
        if parsed_metadata:
            author = parsed_metadata.get('author')
        
        api_metadata = map_data.get('api_metadata', {})
        if not author and api_metadata:
            imageinfo = api_metadata.get('imageinfo', {})
            author = imageinfo.get('user')
        
        # Get license information
        license_info = None
        if parsed_metadata:
            license_info = parsed_metadata.get('license')
        
        # Get source information
        source = None
        if parsed_metadata:
            source = parsed_metadata.get('source')
        
        # Build citation
        citation_parts = []
        
        if author:
            citation_parts.append(f"Author: {author}")
        
        if source:
            citation_parts.append(f"Source: {source}")
        
        if commons_url:
            citation_parts.append(f"Wikimedia Commons: {commons_url}")
        
        if license_info:
            citation_parts.append(f"License: {license_info}")
        else:
            citation_parts.append("License: See Wikimedia Commons page for license information")
        
        citation = " | ".join(citation_parts)
        citations.append(citation)
        
        # Add API metadata citation if available
        if api_metadata:
            imageinfo = api_metadata.get('imageinfo', {})
            if imageinfo.get('descriptionurl'):
                citations.append(f"Description page: {imageinfo['descriptionurl']}")
        
        return citations
    
    def format_footnotes(self, map_data):
        """Extract and format footnotes from metadata."""
        footnotes = []
        
        # Get parsed metadata
        parsed_metadata = map_data.get('parsed_metadata', {})
        api_metadata = map_data.get('api_metadata', {})
        
        # Extract date information
        date_info = parsed_metadata.get('date')
        if date_info:
            footnotes.append(f"Date: {date_info}")
        
        # Extract categories as footnotes
        categories = map_data.get('categories', [])
        if categories:
            footnotes.append(f"Categories: {', '.join(categories[:5])}")  # Limit to first 5
        
        # Extract geographic regions
        regions = map_data.get('geographic_regions', [])
        if regions:
            footnotes.append(f"Geographic regions: {', '.join(regions)}")
        
        # Extract themes
        themes = map_data.get('themes', [])
        if themes:
            footnotes.append(f"Themes: {', '.join(themes)}")
        
        return footnotes
    
    def generate_map_page(self, map_data, index, total):
        """Generate individual page for a map."""
        filename = map_data.get('filename', '')
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        map_dir = os.path.join(self.maps_dir, f"{index:04d}_{safe_filename}")
        os.makedirs(map_dir, exist_ok=True)
        
        # Copy image if it exists
        image_source = os.path.join('downloads', 'originals', filename)
        if os.path.exists(image_source):
            import shutil
            image_dest = os.path.join(map_dir, filename)
            shutil.copy2(image_source, image_dest)
        
        # Generate metadata JSON
        metadata_file = os.path.join(map_dir, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, indent=2, ensure_ascii=False)
        
        # Generate description markdown
        citations = self.format_citation(map_data)
        footnotes = self.format_footnotes(map_data)
        
        description_content = f"""# {filename}

## Description

"""
        
        # Add multilingual captions
        captions = map_data.get('captions', {})
        if captions:
            description_content += "### Captions\n\n"
            for lang, caption in captions.items():
                description_content += f"**{lang.upper()}**: {caption}\n\n"
        
        # Add dates
        dates = map_data.get('dates', [])
        if dates:
            description_content += f"### Dates\n\n"
            description_content += f"Extracted dates: {', '.join(map(str, dates))}\n\n"
            description_content += f"Chronological date: {map_data.get('chronological_date', 'Unknown')}\n\n"
        
        # Add geographic regions
        regions = map_data.get('geographic_regions', [])
        if regions:
            description_content += f"### Geographic Regions\n\n"
            description_content += f"{', '.join(regions)}\n\n"
        
        # Add themes
        themes = map_data.get('themes', [])
        if themes:
            description_content += f"### Themes\n\n"
            description_content += f"{', '.join(themes)}\n\n"
        
        # Add citations
        if citations:
            description_content += "## Citations\n\n"
            for citation in citations:
                description_content += f"- {citation}\n"
            description_content += "\n"
        
        # Add footnotes
        if footnotes:
            description_content += "## Footnotes\n\n"
            for i, footnote in enumerate(footnotes, 1):
                description_content += f"{i}. {footnote}\n"
            description_content += "\n"
        
        # Add links to related maps
        links = map_data.get('related_links', [])
        if links:
            description_content += "## Related Maps\n\n"
            for link in links[:10]:  # Limit to 10 links
                target_filename = link.get('target_filename', '')
                reasons = link.get('reasons', [])
                description_content += f"- [{target_filename}](#) - {', '.join(reasons[:2])}\n"
            description_content += "\n"
        
        description_file = os.path.join(map_dir, 'description.md')
        with open(description_file, 'w', encoding='utf-8') as f:
            f.write(description_content)
        
        return map_dir
    
    def generate_index_html(self, organized_data):
        """Generate main HTML index page."""
        maps = organized_data.get('maps', [])
        timeline = organized_data.get('timeline', [])
        links = organized_data.get('links', {})
        
        # Add related links to each map
        for map_data in maps:
            map_id = map_data.get('id')
            map_data['related_links'] = links.get(map_id, [])
        
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Maps Chronology - Wikimedia Commons Discussion</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .timeline {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .year-group {
            margin-bottom: 30px;
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #0066cc;
        }
        .year-group h3 {
            margin-top: 0;
            color: #0066cc;
        }
        .map-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid #ddd;
            transition: box-shadow 0.3s;
        }
        .map-item:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .map-title {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .map-meta {
            font-size: 0.9em;
            color: #666;
            margin: 5px 0;
        }
        .map-links {
            margin-top: 10px;
            font-size: 0.85em;
        }
        .map-links a {
            color: #0066cc;
            text-decoration: none;
            margin-right: 10px;
        }
        .map-links a:hover {
            text-decoration: underline;
        }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .stat-item {
            text-align: center;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #0066cc;
        }
        .stat-label {
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <h1>Maps Chronology - Wikimedia Commons Discussion</h1>
    
    <div class="stats">
        <h2>Statistics</h2>
        <div class="stats-grid">
"""
        
        stats = organized_data.get('statistics', {})
        html_content += f"""
            <div class="stat-item">
                <div class="stat-value">{stats.get('total_maps', 0)}</div>
                <div class="stat-label">Total Maps</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{stats.get('maps_with_dates', 0)}</div>
                <div class="stat-label">Maps with Dates</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{stats.get('total_links', 0)}</div>
                <div class="stat-label">Inter-related Links</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(timeline)}</div>
                <div class="stat-label">Timeline Groups</div>
            </div>
"""
        
        html_content += """
        </div>
    </div>
    
    <div class="timeline">
        <h2>Chronological Timeline</h2>
"""
        
        for group in timeline:
            year = group.get('year', 'Unknown')
            map_ids = group.get('maps', [])
            
            html_content += f"""
        <div class="year-group">
            <h3>Year: {year} ({len(map_ids)} maps)</h3>
"""
            
            for map_id in map_ids:
                if map_id < len(maps):
                    map_data = maps[map_id]
                    filename = map_data.get('filename', 'Unknown')
                    dates = map_data.get('dates', [])
                    regions = map_data.get('geographic_regions', [])
                    themes = map_data.get('themes', [])
                    commons_url = map_data.get('commons_url', '#')
                    related_links = map_data.get('related_links', [])
                    
                    html_content += f"""
            <div class="map-item">
                <div class="map-title">
                    <a href="{commons_url}" target="_blank">{filename}</a>
                </div>
"""
                    
                    if dates:
                        html_content += f'<div class="map-meta">Dates: {", ".join(map(str, dates))}</div>'
                    
                    if regions:
                        html_content += f'<div class="map-meta">Regions: {", ".join(regions[:5])}</div>'
                    
                    if themes:
                        html_content += f'<div class="map-meta">Themes: {", ".join(themes)}</div>'
                    
                    if related_links:
                        html_content += '<div class="map-links">Related: '
                        for link in related_links[:3]:
                            target_filename = link.get('target_filename', '')
                            html_content += f'<a href="#map-{link.get("target_id")}">{target_filename[:30]}...</a>'
                        html_content += '</div>'
                    
                    html_content += '</div>'
            
            html_content += '</div>'
        
        html_content += """
    </div>
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
        <p>Generated from Wikimedia Commons Discussion Page</p>
        <p>All maps are from Wikimedia Commons and subject to their respective licenses.</p>
    </footer>
</body>
</html>
"""
        
        index_file = os.path.join(self.output_dir, 'index.html')
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return index_file
    
    def generate(self):
        """Generate all output files."""
        print(f"Loading organized data from {self.organized_data_file}...")
        with open(self.organized_data_file, 'r', encoding='utf-8') as f:
            organized_data = json.load(f)
        
        maps = organized_data.get('maps', [])
        links = organized_data.get('links', {})
        
        # Add related links to each map
        for map_data in maps:
            map_id = map_data.get('id')
            map_data['related_links'] = links.get(map_id, [])
        
        print(f"Generating output for {len(maps)} maps...\n")
        
        # Generate individual map pages
        for i, map_data in enumerate(maps, 1):
            print(f"[{i}/{len(maps)}] Generating page for: {map_data.get('filename')}")
            self.generate_map_page(map_data, i - 1, len(maps))
        
        # Generate index HTML
        print("\nGenerating index HTML...")
        index_file = self.generate_index_html(organized_data)
        
        # Save data files
        print("Saving data files...")
        timeline_file = os.path.join(self.data_dir, 'timeline.json')
        with open(timeline_file, 'w', encoding='utf-8') as f:
            json.dump(organized_data.get('timeline', []), f, indent=2, ensure_ascii=False)
        
        links_file = os.path.join(self.data_dir, 'links.json')
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(links, f, indent=2, ensure_ascii=False)
        
        metadata_file = os.path.join(self.data_dir, 'metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(organized_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Output Generation Summary:")
        print(f"  Index HTML: {index_file}")
        print(f"  Map pages: {len(maps)} pages in {self.maps_dir}")
        print(f"  Data files: {self.data_dir}")
        print(f"  Output complete!")
        
        return {
            'index_file': index_file,
            'maps_dir': self.maps_dir,
            'data_dir': self.data_dir
        }

if __name__ == '__main__':
    generator = OutputGenerator()
    generator.generate()

