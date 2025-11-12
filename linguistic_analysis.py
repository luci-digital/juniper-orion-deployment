#!/usr/bin/env python3
"""
Linguistic Analysis: Translate first 5 words of each paragraph,
identify semantic shifts, and trace linguistic divergence over time.
"""

import json
import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict
import html

class LinguisticAnalyzer:
    def __init__(self, html_file='User_Enyavar_DiscussingMaps - Wikimedia Commons.html'):
        self.html_file = html_file
        self.languages = ['en', 'de', 'fr', 'zh', 'ar', 'uk', 'es', 'it', 'ru']
        self.paragraphs = []
        self.translations = []
        self.semantic_shifts = []
        
    def extract_paragraphs(self):
        """Extract all paragraphs from HTML, preserving multilingual content."""
        print("Extracting paragraphs from HTML...")
        with open(self.html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'lxml')
        content_div = soup.find('div', id='mw-content-text')
        if not content_div:
            return []
        
        paragraphs = []
        
        # Extract multilingual paragraphs
        multilingual_divs = content_div.find_all('div', class_='multilingual')
        for div in multilingual_divs:
            # Get all language versions
            lang_paragraphs = {}
            for lang_div in div.find_all('div', class_='description'):
                lang_code = lang_div.get('lang', '')
                if lang_code:
                    # Extract text, removing language labels
                    text = lang_div.get_text(separator=' ', strip=True)
                    # Remove language label prefix
                    lang_span = lang_div.find('span', class_='language')
                    if lang_span:
                        label_text = lang_span.get_text()
                        if text.startswith(label_text):
                            text = text[len(label_text):].strip()
                    
                    if text:
                        lang_paragraphs[lang_code] = text
            
            if lang_paragraphs:
                paragraphs.append({
                    'type': 'multilingual',
                    'languages': lang_paragraphs,
                    'raw_html': str(div)[:500]  # Store snippet for reference
                })
        
        # Extract regular paragraphs
        for p in content_div.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 10:  # Filter out empty/short paragraphs
                paragraphs.append({
                    'type': 'single',
                    'languages': {'en': text},
                    'raw_html': str(p)[:500]
                })
        
        # Extract table cell descriptions
        for td in content_div.find_all('td'):
            text = td.get_text(strip=True)
            if text and len(text) > 20 and '<' not in text[:50]:  # Avoid HTML-heavy cells
                # Check if it's a description cell (not header)
                if td.find_parent('th') is None:
                    paragraphs.append({
                        'type': 'table_cell',
                        'languages': {'en': text},
                        'raw_html': str(td)[:500]
                    })
        
        self.paragraphs = paragraphs
        print(f"Extracted {len(paragraphs)} paragraphs")
        return paragraphs
    
    def get_first_five_words(self, text):
        """Extract first 5 words from text."""
        if not text:
            return ""
        # Clean and split
        words = re.findall(r'\b\w+\b', text)
        return ' '.join(words[:5]) if words else ""
    
    def translate_first_five_words(self, paragraph):
        """Translate first 5 words into all available languages."""
        translations = {}
        
        # Get base text (prefer English, fallback to first available)
        base_text = paragraph['languages'].get('en') or list(paragraph['languages'].values())[0]
        first_five = self.get_first_five_words(base_text)
        
        if not first_five:
            return None
        
        translations['original'] = first_five
        translations['original_lang'] = 'en' if 'en' in paragraph['languages'] else list(paragraph['languages'].keys())[0]
        
        # For multilingual paragraphs, extract first 5 words from each language
        for lang_code, lang_text in paragraph['languages'].items():
            lang_first_five = self.get_first_five_words(lang_text)
            if lang_first_five:
                translations[lang_code] = lang_first_five
        
        # For languages not present, we'll note them as missing
        for lang in self.languages:
            if lang not in translations:
                translations[lang] = None
        
        return translations
    
    def analyze_semantic_shift(self, translations, paragraph):
        """Analyze if translations show semantic shifts."""
        if not translations:
            return None
        
        original = translations.get('original', '')
        if not original:
            return None
        
        shifts = []
        
        # Compare each language's first 5 words
        for lang_code in self.languages:
            if lang_code == translations.get('original_lang'):
                continue
            
            lang_translation = translations.get(lang_code)
            if not lang_translation:
                continue
            
            # Simple semantic analysis: check for key concept words
            # This is a simplified approach - in reality, would need NLP models
            
            # Extract key nouns/verbs from original
            original_words = set(original.lower().split())
            lang_words = set(lang_translation.lower().split())
            
            # Check for missing key concepts
            important_words = {'map', 'karte', 'carte', 'mapa', 'mappa', 'карта', 'خريطة', '地圖', 'карта'}
            missing_concepts = important_words & original_words - lang_words
            
            # Check word order differences (indicator of structural shift)
            original_order = original.lower().split()[:3]
            lang_order = lang_translation.lower().split()[:3]
            
            if original_order != lang_order:
                shifts.append({
                    'lang': lang_code,
                    'type': 'word_order',
                    'original': original,
                    'translation': lang_translation,
                    'original_order': original_order,
                    'translation_order': lang_order
                })
            
            # Check for missing concepts
            if missing_concepts:
                shifts.append({
                    'lang': lang_code,
                    'type': 'missing_concept',
                    'original': original,
                    'translation': lang_translation,
                    'missing': list(missing_concepts)
                })
        
        return shifts if shifts else None
    
    def identify_meaning_changing_words(self, translations):
        """Identify words that change the meaning when translated."""
        meaning_changes = []
        
        if not translations:
            return meaning_changes
        
        original = translations.get('original', '')
        original_words = original.split()
        
        # Key words that often change meaning across languages
        semantic_markers = {
            'should': {'de': 'sollte', 'fr': 'devrait', 'es': 'debería', 'it': 'dovrebbe'},
            'must': {'de': 'muss', 'fr': 'doit', 'es': 'debe', 'it': 'deve'},
            'can': {'de': 'kann', 'fr': 'peut', 'es': 'puede', 'it': 'può'},
            'may': {'de': 'kann', 'fr': 'peut', 'es': 'puede', 'it': 'può'},
            'important': {'de': 'wichtig', 'fr': 'important', 'es': 'importante', 'it': 'importante'},
            'often': {'de': 'oft', 'fr': 'souvent', 'es': 'a menudo', 'it': 'spesso'},
            'usually': {'de': 'normalerweise', 'fr': 'généralement', 'es': 'generalmente', 'it': 'di solito'}
        }
        
        for word in original_words:
            word_lower = word.lower().rstrip('.,!?;:')
            if word_lower in semantic_markers:
                for lang_code in self.languages:
                    if lang_code in semantic_markers[word_lower]:
                        expected = semantic_markers[word_lower][lang_code]
                        actual = translations.get(lang_code, '')
                        if actual and expected.lower() not in actual.lower():
                            meaning_changes.append({
                                'word': word,
                                'lang': lang_code,
                                'expected': expected,
                                'actual': actual,
                                'position': original_words.index(word)
                            })
        
        return meaning_changes
    
    def trace_temporal_divergence(self, semantic_shifts):
        """Trace linguistic divergence from historical point to present."""
        divergence_timeline = []
        
        # Group shifts by language
        shifts_by_lang = defaultdict(list)
        for shift in semantic_shifts:
            lang = shift.get('lang', 'unknown')
            shifts_by_lang[lang].append(shift)
        
        # Analyze divergence patterns
        for lang, shifts in shifts_by_lang.items():
            # Count types of shifts
            order_shifts = [s for s in shifts if s.get('type') == 'word_order']
            concept_shifts = [s for s in shifts if s.get('type') == 'missing_concept']
            
            divergence_timeline.append({
                'language': lang,
                'total_shifts': len(shifts),
                'word_order_shifts': len(order_shifts),
                'concept_shifts': len(concept_shifts),
                'divergence_level': 'high' if len(shifts) > 3 else 'medium' if len(shifts) > 1 else 'low',
                'shifts': shifts[:5]  # Sample shifts
            })
        
        return divergence_timeline
    
    def analyze_all(self):
        """Run complete linguistic analysis."""
        print("="*60)
        print("LINGUISTIC ANALYSIS")
        print("="*60)
        print()
        
        # Step 1: Extract paragraphs
        paragraphs = self.extract_paragraphs()
        
        # Step 2: Translate first 5 words
        print("\nTranslating first 5 words of each paragraph...")
        all_translations = []
        for i, para in enumerate(paragraphs, 1):
            translations = self.translate_first_five_words(para)
            if translations:
                translations['paragraph_index'] = i
                translations['paragraph_type'] = para['type']
                all_translations.append(translations)
                if i <= 5:  # Show first 5
                    print(f"  Para {i}: {translations.get('original', '')[:50]}")
        
        self.translations = all_translations
        print(f"\nProcessed {len(all_translations)} paragraphs with translations")
        
        # Step 3: Analyze semantic shifts
        print("\nAnalyzing semantic shifts...")
        all_shifts = []
        meaning_changes = []
        
        for translations in all_translations:
            shifts = self.analyze_semantic_shift(translations, paragraphs[translations['paragraph_index'] - 1])
            if shifts:
                for shift in shifts:
                    shift['paragraph_index'] = translations['paragraph_index']
                    all_shifts.append(shift)
            
            # Identify meaning-changing words
            changes = self.identify_meaning_changing_words(translations)
            if changes:
                for change in changes:
                    change['paragraph_index'] = translations['paragraph_index']
                    meaning_changes.append(change)
        
        self.semantic_shifts = all_shifts
        print(f"Found {len(all_shifts)} semantic shifts")
        print(f"Found {len(meaning_changes)} meaning-changing words")
        
        # Step 4: Trace temporal divergence
        print("\nTracing temporal divergence...")
        divergence_timeline = self.trace_temporal_divergence(all_shifts)
        
        # Step 5: Identify paragraphs with significant meaning changes
        print("\nIdentifying paragraphs with significant meaning changes...")
        significant_paragraphs = []
        para_shift_count = defaultdict(int)
        
        for shift in all_shifts:
            para_idx = shift.get('paragraph_index')
            para_shift_count[para_idx] += 1
        
        for para_idx, count in para_shift_count.items():
            if count >= 2:  # Multiple shifts indicate significant change
                para = paragraphs[para_idx - 1]
                significant_paragraphs.append({
                    'paragraph_index': para_idx,
                    'shift_count': count,
                    'paragraph_text': list(para['languages'].values())[0][:200],
                    'shifts': [s for s in all_shifts if s.get('paragraph_index') == para_idx]
                })
        
        print(f"Found {len(significant_paragraphs)} paragraphs with significant meaning changes")
        
        # Compile results
        results = {
            'total_paragraphs': len(paragraphs),
            'translated_paragraphs': len(all_translations),
            'semantic_shifts': all_shifts,
            'meaning_changes': meaning_changes,
            'divergence_timeline': divergence_timeline,
            'significant_paragraphs': significant_paragraphs,
            'translations': all_translations[:20]  # Sample
        }
        
        # Save results
        os.makedirs('data', exist_ok=True)
        output_file = 'data/linguistic_analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print("Analysis Complete!")
        print(f"Results saved to: {output_file}")
        print(f"\nSummary:")
        print(f"  Total paragraphs: {len(paragraphs)}")
        print(f"  Translated: {len(all_translations)}")
        print(f"  Semantic shifts: {len(all_shifts)}")
        print(f"  Meaning changes: {len(meaning_changes)}")
        print(f"  Significant paragraphs: {len(significant_paragraphs)}")
        print(f"  Languages analyzed: {len(divergence_timeline)}")
        
        return results

if __name__ == '__main__':
    analyzer = LinguisticAnalyzer()
    analyzer.analyze_all()

