#!/usr/bin/env python3
"""
Advanced Contributor Correlation Analysis:
- Language patterns and usage
- Username type classification
- Coordinated posting dates
- Location/credential matching to topics
- Edit patterns (fixes vs new content)
- Language-to-posting relationships
"""

import json
import os
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from urllib.parse import urlparse

class AdvancedContributorAnalyzer:
    def __init__(self, enriched_maps_file='data/enriched_maps.json'):
        self.enriched_maps_file = enriched_maps_file
        self.contributors = []
        
    def classify_username_type(self, username):
        """Classify username type."""
        if not username:
            return 'unknown'
        
        username_lower = username.lower()
        
        # Bot detection
        if 'bot' in username_lower or 'Bot' in username:
            return 'bot'
        
        # Organization/institution
        if any(x in username_lower for x in ['library', 'archive', 'museum', 'institution', 'org', 'foundation']):
            return 'institution'
        
        # Real name patterns (capitalized first and last)
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', username):
            return 'real_name'
        
        # Wikimedia user pattern
        if username.startswith('User:') or 'user:' in username_lower:
            return 'wikimedia_user'
        
        # URL/website
        if 'http' in username_lower or 'www.' in username_lower or '.com' in username_lower:
            return 'external_source'
        
        # Single word (likely username)
        if ' ' not in username:
            return 'username'
        
        # Multiple words
        return 'compound_name'
    
    def extract_language_from_content(self, map_data):
        """Extract language from map content, filename, captions."""
        languages = set()
        
        filename = map_data.get('filename', '').lower()
        captions = map_data.get('captions', {})
        categories = map_data.get('categories', [])
        
        # Language codes in captions
        for lang_code in captions.keys():
            languages.add(lang_code)
        
        # Detect language from filename patterns
        lang_patterns = {
            'de': ['deutsch', 'german', '_de.', '-de.', '_de_'],
            'fr': ['français', 'french', '_fr.', '-fr.', '_fr_'],
            'en': ['english', '_en.', '-en.', '_en_'],
            'es': ['español', 'spanish', '_es.', '-es.'],
            'it': ['italiano', 'italian', '_it.', '-it.'],
            'zh': ['chinese', '中文', '_zh.', '-zh.'],
            'ar': ['arabic', 'العربية', '_ar.', '-ar.'],
            'uk': ['ukrainian', 'українська', '_ukr.', '-ukr.'],
            'ru': ['russian', 'русский', '_ru.', '-ru.']
        }
        
        for lang, patterns in lang_patterns.items():
            if any(pattern in filename for pattern in patterns):
                languages.add(lang)
        
        # Detect from categories
        for cat in categories:
            cat_lower = cat.lower()
            for lang, patterns in lang_patterns.items():
                if any(pattern in cat_lower for pattern in patterns):
                    languages.add(lang)
        
        return list(languages) if languages else ['unknown']
    
    def analyze_edit_patterns(self, map_data, api_metadata):
        """Determine if contributor is fixing pages or making reaching changes."""
        edit_type = 'new_content'  # default
        
        # Check revision history
        revisions = api_metadata.get('revisions', {})
        content = revisions.get('content', '')
        
        if content:
            # Look for fix indicators
            fix_keywords = ['fix', 'correct', 'update', 'repair', 'typo', 'error', 'mistake']
            if any(keyword in content.lower() for keyword in fix_keywords):
                edit_type = 'fix'
            
            # Look for translation indicators
            if 'translation' in content.lower() or 'translate' in content.lower():
                edit_type = 'translation'
            
            # Look for categorization (reaching change)
            if 'category' in content.lower() and ('add' in content.lower() or 'move' in content.lower()):
                edit_type = 'categorization'
        
        # Check if multiple revisions suggest fixes
        if api_metadata.get('revisions', {}).get('user') != api_metadata.get('imageinfo', {}).get('user'):
            edit_type = 'revision'
        
        return edit_type
    
    def extract_location_from_username(self, username):
        """Try to extract location hints from username."""
        # This is heuristic - usernames rarely contain real locations
        # But we can check for country/city names
        location_keywords = {
            'france': ['paris', 'france', 'français'],
            'germany': ['deutsch', 'german', 'berlin'],
            'spain': ['spain', 'español', 'madrid'],
            'italy': ['italy', 'italiano', 'rome'],
            'uk': ['london', 'british', 'uk'],
            'usa': ['usa', 'american', 'us'],
            'russia': ['russian', 'россия', 'moscow'],
            'china': ['chinese', '中文', 'beijing'],
            'japan': ['japanese', 'tokyo']
        }
        
        username_lower = username.lower()
        for location, keywords in location_keywords.items():
            if any(keyword in username_lower for keyword in keywords):
                return location
        
        return None
    
    def analyze_temporal_coordination(self, contributors_data):
        """Analyze if contributors post at coordinated times."""
        # Group uploads by date
        uploads_by_date = defaultdict(list)
        
        for contrib in contributors_data:
            upload_date = contrib.get('upload_date', '')
            if upload_date:
                try:
                    # Parse ISO date
                    dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                    date_key = dt.date()
                    uploads_by_date[date_key].append({
                        'contributor': contrib['primary_contributor'],
                        'datetime': dt,
                        'map': contrib['map_filename']
                    })
                except:
                    pass
        
        # Find dates with multiple contributors
        coordinated_dates = []
        for date, uploads in uploads_by_date.items():
            unique_contributors = set(u['contributor'] for u in uploads)
            if len(unique_contributors) > 1:
                # Check time proximity (within same day or hour)
                times = [u['datetime'] for u in uploads]
                time_spans = []
                for i in range(len(times) - 1):
                    span = abs((times[i+1] - times[i]).total_seconds())
                    time_spans.append(span)
                
                if time_spans:
                    min_span = min(time_spans)
                # Convert datetime objects to strings for JSON serialization
                uploads_serializable = []
                for u in uploads:
                    uploads_serializable.append({
                        'contributor': u['contributor'],
                        'datetime': u['datetime'].isoformat(),
                        'map': u['map']
                    })
                
                coordinated_dates.append({
                    'date': str(date),
                    'contributors': list(unique_contributors),
                    'upload_count': len(uploads),
                    'min_time_gap_hours': min_span / 3600,
                    'uploads': uploads_serializable
                })
        
        return sorted(coordinated_dates, key=lambda x: x['upload_count'], reverse=True)
    
    def match_location_to_topics(self, contributor, contributor_maps):
        """Check if contributor location matches their map topics."""
        username_location = self.extract_location_from_username(contributor)
        
        if not username_location:
            return None
        
        # Get all regions from contributor's maps
        all_regions = set()
        for m in contributor_maps:
            all_regions.update(m.get('regions', []))
        
        # Check if username location matches any map region
        regions_lower = [r.lower() for r in all_regions]
        username_location_lower = username_location.lower() if username_location else ''
        
        matches = []
        for region in all_regions:
            if username_location_lower and (username_location_lower in region.lower() or region.lower() in username_location_lower):
                matches.append(region)
        
        return {
            'username_location': username_location,
            'map_regions': list(all_regions),
            'matches': matches,
            'match_count': len(matches)
        } if matches else None
    
    def correlate_language_to_posting(self, contributors_data):
        """Correlate language usage with posting patterns."""
        language_patterns = defaultdict(lambda: {
            'contributors': set(),
            'maps': [],
            'upload_dates': [],
            'edit_types': [],
            'username_types': []
        })
        
        for contrib in contributors_data:
            languages = contrib.get('languages', [])
            contributor = contrib['primary_contributor']
            edit_type = contrib.get('edit_type', 'unknown')
            username_type = contrib.get('username_type', 'unknown')
            
            for lang in languages:
                language_patterns[lang]['contributors'].add(contributor)
                language_patterns[lang]['maps'].append(contrib['map_filename'])
                if contrib.get('upload_date'):
                    language_patterns[lang]['upload_dates'].append(contrib['upload_date'])
                language_patterns[lang]['edit_types'].append(edit_type)
                language_patterns[lang]['username_types'].append(username_type)
        
        # Analyze patterns
        analysis = {}
        for lang, data in language_patterns.items():
            analysis[lang] = {
                'contributor_count': len(data['contributors']),
                'map_count': len(data['maps']),
                'unique_contributors': list(data['contributors']),
                'most_common_edit_type': Counter(data['edit_types']).most_common(1)[0][0] if data['edit_types'] else 'unknown',
                'most_common_username_type': Counter(data['username_types']).most_common(1)[0][0] if data['username_types'] else 'unknown',
                'edit_type_distribution': dict(Counter(data['edit_types'])),
                'username_type_distribution': dict(Counter(data['username_types']))
            }
        
        return analysis
    
    def analyze_all(self):
        """Perform complete advanced analysis."""
        print("="*60)
        print("ADVANCED CONTRIBUTOR CORRELATION ANALYSIS")
        print("="*60)
        print()
        
        # Load data
        print("Loading enriched maps data...")
        with open(self.enriched_maps_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        maps = data.get('maps', [])
        print(f"Processing {len(maps)} maps...")
        
        # Extract and enrich contributor data
        contributors_data = []
        
        for map_data in maps:
            filename = map_data.get('filename', '')
            api_metadata = map_data.get('api_metadata', {})
            parsed_metadata = map_data.get('parsed_metadata', {})
            
            # Extract contributor info
            uploader = api_metadata.get('imageinfo', {}).get('user', '')
            author = parsed_metadata.get('author', '')
            revisions = api_metadata.get('revisions', {})
            revision_user = revisions.get('user', '')
            
            # Clean names
            def clean_name(name):
                if not name:
                    return ''
                name = name.replace('[[User:', '').replace('[[File:', '').replace(']]', '')
                name = name.replace('[', '').replace(']', '')
                if 'http' in name.lower():
                    return ''
                name = name.split('|')[-1].strip()
                name = name.split(':')[-1].strip()
                return name.strip()
            
            primary_contributor = clean_name(author) or clean_name(uploader) or clean_name(revision_user) or 'Unknown'
            
            if primary_contributor and primary_contributor != 'Unknown':
                # Classify username type
                username_type = self.classify_username_type(primary_contributor)
                
                # Extract languages
                languages = self.extract_language_from_content(map_data)
                
                # Analyze edit patterns
                edit_type = self.analyze_edit_patterns(map_data, api_metadata)
                
                # Get upload date
                upload_date = api_metadata.get('imageinfo', {}).get('timestamp', '')
                
                contributors_data.append({
                    'map_filename': filename,
                    'primary_contributor': primary_contributor,
                    'username_type': username_type,
                    'uploader': clean_name(uploader),
                    'author': clean_name(author),
                    'revision_user': clean_name(revision_user),
                    'upload_date': upload_date,
                    'languages': languages,
                    'edit_type': edit_type,
                    'regions': map_data.get('geographic_regions', []),
                    'themes': map_data.get('themes', []),
                    'categories': map_data.get('categories', []),
                    'date': map_data.get('chronological_date', 0)
                })
        
        self.contributors = contributors_data
        print(f"Extracted data for {len(contributors_data)} contributions")
        
        # 1. Username type analysis
        print("\n1. Analyzing username types...")
        username_types = Counter([c['username_type'] for c in contributors_data])
        print(f"   Username type distribution:")
        for utype, count in username_types.most_common():
            print(f"     {utype}: {count}")
        
        # 2. Language analysis
        print("\n2. Analyzing language patterns...")
        all_languages = []
        for c in contributors_data:
            all_languages.extend(c['languages'])
        language_counts = Counter(all_languages)
        print(f"   Languages detected:")
        for lang, count in language_counts.most_common():
            print(f"     {lang}: {count} maps")
        
        # 3. Temporal coordination
        print("\n3. Analyzing temporal coordination...")
        coordinated = self.analyze_temporal_coordination(contributors_data)
        print(f"   Found {len(coordinated)} dates with multiple contributors")
        if coordinated:
            print(f"   Most coordinated date: {coordinated[0]['date']}")
            print(f"     Contributors: {', '.join(coordinated[0]['contributors'][:5])}")
            print(f"     Uploads: {coordinated[0]['upload_count']}")
        
        # 4. Location matching
        print("\n4. Analyzing location-to-topic matching...")
        contributor_maps = defaultdict(list)
        for c in contributors_data:
            contributor_maps[c['primary_contributor']].append(c)
        
        location_matches = []
        for contributor, maps_list in contributor_maps.items():
            match = self.match_location_to_topics(contributor, maps_list)
            if match:
                location_matches.append({
                    'contributor': contributor,
                    **match
                })
        
        print(f"   Found {len(location_matches)} contributors with location matches")
        
        # 5. Edit pattern analysis
        print("\n5. Analyzing edit patterns...")
        edit_types = Counter([c['edit_type'] for c in contributors_data])
        print(f"   Edit type distribution:")
        for etype, count in edit_types.most_common():
            print(f"     {etype}: {count}")
        
        # 6. Language-to-posting correlation
        print("\n6. Correlating language to posting patterns...")
        lang_posting = self.correlate_language_to_posting(contributors_data)
        
        # Compile results
        results = {
            'contributors': contributors_data,
            'username_type_distribution': dict(username_types),
            'language_distribution': dict(language_counts),
            'temporal_coordination': coordinated,
            'location_matches': location_matches,
            'edit_patterns': dict(edit_types),
            'language_to_posting': lang_posting,
            'analysis_date': datetime.now().isoformat()
        }
        
        # Save results
        output_file = 'data/advanced_contributor_analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"Advanced analysis complete! Results saved to: {output_file}")
        
        return results
    
    def generate_advanced_report(self, results):
        """Generate comprehensive HTML report."""
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Contributor Correlation Analysis</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
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
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }
        .section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #0066cc;
            color: white;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .coordinated-date {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
        }
        .location-match {
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin: 10px 0;
        }
        .lang-pattern {
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <h1>Advanced Contributor Correlation Analysis</h1>
    <p><em>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</em></p>
"""
        
        # Username types
        html_content += """
    <div class="section">
        <h2>1. Username Type Distribution</h2>
        <table>
            <thead>
                <tr>
                    <th>Username Type</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
"""
        username_types = results.get('username_type_distribution', {})
        total = sum(username_types.values())
        for utype, count in sorted(username_types.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            html_content += f"""
                <tr>
                    <td><strong>{utype}</strong></td>
                    <td>{count}</td>
                    <td>{pct:.1f}%</td>
                </tr>
"""
        html_content += """
            </tbody>
        </table>
    </div>
"""
        
        # Language distribution
        html_content += """
    <div class="section">
        <h2>2. Language Distribution</h2>
        <table>
            <thead>
                <tr>
                    <th>Language</th>
                    <th>Maps</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
"""
        languages = results.get('language_distribution', {})
        lang_total = sum(languages.values())
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            pct = (count / lang_total * 100) if lang_total > 0 else 0
            html_content += f"""
                <tr>
                    <td><strong>{lang.upper()}</strong></td>
                    <td>{count}</td>
                    <td>{pct:.1f}%</td>
                </tr>
"""
        html_content += """
            </tbody>
        </table>
    </div>
"""
        
        # Temporal coordination
        html_content += """
    <div class="section">
        <h2>3. Temporal Coordination</h2>
        <p>Dates where multiple contributors posted within close timeframes:</p>
"""
        coordinated = results.get('temporal_coordination', [])
        for coord in coordinated[:10]:
            html_content += f"""
        <div class="coordinated-date">
            <strong>Date: {coord['date']}</strong><br>
            Contributors: {', '.join(coord['contributors'][:5])}<br>
            Uploads: {coord['upload_count']}<br>
            Minimum time gap: {coord['min_time_gap_hours']:.2f} hours
        </div>
"""
        html_content += """
    </div>
"""
        
        # Location matches
        html_content += """
    <div class="section">
        <h2>4. Location-to-Topic Matching</h2>
        <p>Contributors whose username suggests a location that matches their map topics:</p>
"""
        location_matches = results.get('location_matches', [])
        for match in location_matches[:10]:
            html_content += f"""
        <div class="location-match">
            <strong>{match['contributor']}</strong><br>
            Username location: {match['username_location']}<br>
            Map regions: {', '.join(match['map_regions'][:5])}<br>
            Matches: {match['match_count']} ({', '.join(match['matches'][:3])})
        </div>
"""
        html_content += """
    </div>
"""
        
        # Edit patterns
        html_content += """
    <div class="section">
        <h2>5. Edit Patterns</h2>
        <table>
            <thead>
                <tr>
                    <th>Edit Type</th>
                    <th>Count</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
"""
        edit_types = results.get('edit_patterns', {})
        edit_descriptions = {
            'new_content': 'New map uploads',
            'fix': 'Fixes and corrections',
            'translation': 'Language translations',
            'categorization': 'Category organization',
            'revision': 'Revisions and updates'
        }
        for etype, count in sorted(edit_types.items(), key=lambda x: x[1], reverse=True):
            desc = edit_descriptions.get(etype, 'Other edits')
            html_content += f"""
                <tr>
                    <td><strong>{etype}</strong></td>
                    <td>{count}</td>
                    <td>{desc}</td>
                </tr>
"""
        html_content += """
            </tbody>
        </table>
    </div>
"""
        
        # Language-to-posting correlation
        html_content += """
    <div class="section">
        <h2>6. Language-to-Posting Patterns</h2>
        <p>How language usage correlates with posting behavior:</p>
"""
        lang_posting = results.get('language_to_posting', {})
        for lang, pattern in sorted(lang_posting.items(), key=lambda x: x[1]['map_count'], reverse=True)[:10]:
            html_content += f"""
        <div class="lang-pattern">
            <strong>Language: {lang.upper()}</strong><br>
            Contributors: {pattern['contributor_count']} | Maps: {pattern['map_count']}<br>
            Most common edit type: {pattern['most_common_edit_type']}<br>
            Most common username type: {pattern['most_common_username_type']}<br>
            Contributors: {', '.join(pattern['unique_contributors'][:5])}
        </div>
"""
        html_content += """
    </div>
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
        <p>Advanced Contributor Correlation Analysis</p>
    </footer>
</body>
</html>
"""
        
        output_file = 'chronology/advanced_contributor_analysis.html'
        os.makedirs('chronology', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Advanced HTML report generated: {output_file}")
        return output_file

if __name__ == '__main__':
    analyzer = AdvancedContributorAnalyzer()
    results = analyzer.analyze_all()
    if results:
        analyzer.generate_advanced_report(results)

