#!/usr/bin/env python3
"""
Extract structured data from a W3C report HTML file.
"""

import json
import os
import argparse
from bs4 import BeautifulSoup
import re

class W3CReportExtractor:
    def __init__(self, html_file):
        self.html_file = html_file

    def extract(self):
        """Main extraction method."""
        print(f"Reading HTML file: {self.html_file}")
        with open(self.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        print("Parsing HTML...")
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except Exception:
            print("lxml not found, falling back to html.parser")
            soup = BeautifulSoup(html_content, 'html.parser')

        report_data = {
            'title': self.extract_title(soup),
            'abstract': self.extract_abstract(soup),
            'executive_summary': self.extract_executive_summary(soup),
            'sections': self.extract_sections(soup),
            'references': self.extract_references(soup),
        }
        
        return report_data

    def extract_title(self, soup):
        title_tag = soup.find('h1')
        return title_tag.get_text(strip=True) if title_tag else None

    def extract_abstract(self, soup):
        abstract_h2 = soup.find('h2', string='Abstract')
        if abstract_h2:
            abstract_p = abstract_h2.find_next_sibling('p')
            if abstract_p:
                return abstract_p.get_text(strip=True)
        return None

    def extract_executive_summary(self, soup):
        summary_h2 = soup.find('h2', id='executive-summary')
        if not summary_h2:
            # Try finding by text
            summary_h2 = soup.find('h2', string=lambda t: t and 'executive summary' in t.lower())
        
        if summary_h2:
            summary_content = []
            for sibling in summary_h2.find_next_siblings():
                if sibling.name == 'h2':
                    break
                summary_content.append(sibling.get_text(strip=True))
            return "\n".join(summary_content)
        return None
        
    def extract_sections(self, soup):
        sections = []
        # Find all h2, h3, h4 tags that are not in the header
        main_content = soup.find('main') or soup.find('body')
        for header in main_content.find_all(['h2', 'h3', 'h4']):
            # Skip abstract and ToC
            if header.get_text(strip=True).lower() in ['abstract', 'status of this document', 'table of contents']:
                continue

            section_id = header.get('id', '')
            level = int(header.name[1])
            title = header.get_text(strip=True)
            
            content = []
            for sibling in header.find_next_siblings():
                if sibling.name and sibling.name.startswith('h') and int(sibling.name[1]) <= level:
                    break
                content.append(sibling.get_text(strip=True))

            sections.append({
                'id': section_id,
                'title': title,
                'level': level,
                'content': "\n".join(content).strip()
            })
        return sections

    def extract_references(self, soup):
        references = []
        # References are typically in a section at the end
        references_h2 = soup.find('h2', id='references')
        if references_h2:
            # Use regex as a fallback
            html_content = str(soup)
            ref_section = html_content[html_content.find('id="references"'):]
            
            # Pattern to find <dt> and the following <dd>
            pattern = re.compile(r'<dt id="[^"]+">\[([^\]]+)\]\s*<dd>(.*?)</dd>', re.DOTALL)
            matches = pattern.findall(ref_section)
            
            for match in matches:
                ref_id = match[0]
                dd_content = match[1]
                
                # Parse the dd content with BeautifulSoup to extract link and text
                dd_soup = BeautifulSoup(dd_content, 'html.parser')
                ref_text = dd_soup.get_text(strip=True)
                url_tag = dd_soup.find('a')
                url = url_tag['href'] if url_tag else None
                
                references.append({
                    'id': ref_id,
                    'text': ref_text,
                    'url': url
                })
        return references


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract structured data from a W3C report HTML file.")
    parser.add_argument("html_file", help="Path to the HTML file to process.")
    parser.add_argument("--output", default="w3c_identity_report/extracted_report.json", help="Path to the output JSON file.")
    args = parser.parse_args()

    extractor = W3CReportExtractor(args.html_file)
    data = extractor.extract()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nExtraction complete! Data saved to {args.output}")
    print(f"Extracted title: {data['title']}")
    print(f"Extracted {len(data['sections'])} sections and {len(data['references'])} references.")
