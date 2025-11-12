#!/usr/bin/env python3
"""
Generate detailed linguistic analysis report with translations,
semantic shifts, and temporal divergence analysis.
"""

import json
import os
import html
from datetime import datetime

class LinguisticReportGenerator:
    def __init__(self, analysis_file='data/linguistic_analysis.json'):
        self.analysis_file = analysis_file
        
    def generate_html_report(self):
        """Generate comprehensive HTML report."""
        print("Loading linguistic analysis data...")
        with open(self.analysis_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Linguistic Analysis Report - Maps Discussion</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
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
        h3 {
            color: #666;
            margin-top: 20px;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .stat-box {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #0066cc;
        }
        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .translation-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .paragraph-block {
            border-left: 4px solid #0066cc;
            padding: 15px;
            margin: 15px 0;
            background: #f9f9f9;
        }
        .paragraph-header {
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .translations-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .translation-item {
            background: white;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .lang-code {
            font-weight: bold;
            color: #0066cc;
            font-size: 0.9em;
        }
        .translation-text {
            margin-top: 5px;
            color: #333;
        }
        .shift-indicator {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
        }
        .shift-type {
            font-weight: bold;
            color: #856404;
        }
        .significant-paragraph {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 15px 0;
        }
        .divergence-timeline {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .divergence-item {
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #28a745;
            background: #f9f9f9;
        }
        .divergence-high {
            border-left-color: #dc3545;
        }
        .divergence-medium {
            border-left-color: #ffc107;
        }
        .divergence-low {
            border-left-color: #28a745;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 10px;
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
    </style>
</head>
<body>
    <h1>Linguistic Analysis Report</h1>
    <p><em>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</em></p>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-grid">
"""
        
        # Add summary statistics
        html_content += f"""
            <div class="stat-box">
                <div class="stat-value">{data.get('total_paragraphs', 0)}</div>
                <div class="stat-label">Total Paragraphs</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{data.get('translated_paragraphs', 0)}</div>
                <div class="stat-label">Translated Paragraphs</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(data.get('semantic_shifts', []))}</div>
                <div class="stat-label">Semantic Shifts</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(data.get('significant_paragraphs', []))}</div>
                <div class="stat-label">Significant Changes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(data.get('divergence_timeline', []))}</div>
                <div class="stat-label">Languages Analyzed</div>
            </div>
"""
        
        html_content += """
        </div>
    </div>
    
    <div class="translation-section">
        <h2>Translations: First 5 Words of Each Paragraph</h2>
"""
        
        # Add translation samples
        translations = data.get('translations', [])
        for i, trans in enumerate(translations[:10], 1):  # Show first 10
            html_content += f"""
        <div class="paragraph-block">
            <div class="paragraph-header">Paragraph {trans.get('paragraph_index', i)} ({trans.get('paragraph_type', 'unknown')})</div>
            <div class="translations-grid">
"""
            
            for lang_code in ['en', 'de', 'fr', 'es', 'it', 'zh', 'ar', 'uk', 'ru']:
                lang_text = trans.get(lang_code)
                if lang_text:
                    html_content += f"""
                <div class="translation-item">
                    <div class="lang-code">{lang_code.upper()}</div>
                    <div class="translation-text">{html.escape(lang_text)}</div>
                </div>
"""
            
            html_content += """
            </div>
"""
            
            # Check for shifts in this paragraph
            para_shifts = [s for s in data.get('semantic_shifts', []) 
                          if s.get('paragraph_index') == trans.get('paragraph_index')]
            if para_shifts:
                html_content += '<div class="shift-indicator">'
                html_content += f'<div class="shift-type">⚠ Semantic shifts detected: {len(para_shifts)}</div>'
                for shift in para_shifts[:2]:
                    html_content += f'<div>{shift.get("type", "unknown")} in {shift.get("lang", "unknown")}</div>'
                html_content += '</div>'
            
            html_content += '</div>'
        
        html_content += """
    </div>
    
    <div class="translation-section">
        <h2>Significant Paragraphs with Meaning Changes</h2>
"""
        
        # Add significant paragraphs
        significant = data.get('significant_paragraphs', [])
        for para in significant:
            html_content += f"""
        <div class="significant-paragraph">
            <h3>Paragraph {para.get('paragraph_index')} - {para.get('shift_count')} semantic shifts</h3>
            <p><strong>Text:</strong> {html.escape(para.get('paragraph_text', '')[:300])}...</p>
            <h4>Shifts Detected:</h4>
            <ul>
"""
            
            for shift in para.get('shifts', [])[:5]:
                html_content += f"""
                <li>
                    <strong>{shift.get('type', 'unknown')}</strong> in {shift.get('lang', 'unknown')}: 
                    {html.escape(str(shift.get('original', ''))[:50])} → 
                    {html.escape(str(shift.get('translation', ''))[:50])}
                </li>
"""
            
            html_content += """
            </ul>
        </div>
"""
        
        html_content += """
    </div>
    
    <div class="divergence-timeline">
        <h2>Temporal Divergence Analysis</h2>
        <p>Analysis of linguistic divergence across languages from historical point to present.</p>
"""
        
        # Add divergence timeline
        divergence = data.get('divergence_timeline', [])
        for div_item in divergence:
            level = div_item.get('divergence_level', 'low')
            html_content += f"""
        <div class="divergence-item divergence-{level}">
            <h3>Language: {div_item.get('language', 'unknown').upper()}</h3>
            <p><strong>Divergence Level:</strong> {level.upper()}</p>
            <p><strong>Total Shifts:</strong> {div_item.get('total_shifts', 0)}</p>
            <p><strong>Word Order Shifts:</strong> {div_item.get('word_order_shifts', 0)}</p>
            <p><strong>Concept Shifts:</strong> {div_item.get('concept_shifts', 0)}</p>
"""
            
            if div_item.get('shifts'):
                html_content += '<h4>Sample Shifts:</h4><ul>'
                for shift in div_item.get('shifts', [])[:3]:
                    html_content += f'<li>{html.escape(str(shift.get("original", ""))[:50])} → {html.escape(str(shift.get("translation", ""))[:50])}</li>'
                html_content += '</ul>'
            
            html_content += '</div>'
        
        html_content += """
    </div>
    
    <div class="translation-section">
        <h2>Complete Semantic Shifts Table</h2>
        <table>
            <thead>
                <tr>
                    <th>Paragraph</th>
                    <th>Language</th>
                    <th>Type</th>
                    <th>Original</th>
                    <th>Translation</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add semantic shifts table
        shifts = data.get('semantic_shifts', [])
        for shift in shifts[:50]:  # Limit to 50 for readability
            html_content += f"""
                <tr>
                    <td>{shift.get('paragraph_index', 'N/A')}</td>
                    <td>{shift.get('lang', 'N/A')}</td>
                    <td>{shift.get('type', 'N/A')}</td>
                    <td>{html.escape(str(shift.get('original', ''))[:60])}</td>
                    <td>{html.escape(str(shift.get('translation', ''))[:60])}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
    </div>
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
        <p>Linguistic Analysis Report - Maps Discussion Page</p>
        <p>Analysis includes translation of first 5 words of each paragraph into multiple languages,</p>
        <p>identification of semantic shifts, and tracing of linguistic divergence over time.</p>
    </footer>
</body>
</html>
"""
        
        # Save HTML report
        output_file = 'chronology/linguistic_analysis_report.html'
        os.makedirs('chronology', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {output_file}")
        return output_file
    
    def generate_detailed_text_report(self):
        """Generate detailed text report."""
        print("Generating detailed text report...")
        with open(self.analysis_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        report_lines = []
        report_lines.append("="*80)
        report_lines.append("DETAILED LINGUISTIC ANALYSIS REPORT")
        report_lines.append("="*80)
        report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Summary
        report_lines.append("SUMMARY")
        report_lines.append("-"*80)
        report_lines.append(f"Total paragraphs analyzed: {data.get('total_paragraphs', 0)}")
        report_lines.append(f"Paragraphs with translations: {data.get('translated_paragraphs', 0)}")
        report_lines.append(f"Semantic shifts detected: {len(data.get('semantic_shifts', []))}")
        report_lines.append(f"Meaning-changing words: {len(data.get('meaning_changes', []))}")
        report_lines.append(f"Paragraphs with significant changes: {len(data.get('significant_paragraphs', []))}")
        report_lines.append(f"Languages analyzed: {len(data.get('divergence_timeline', []))}")
        report_lines.append("")
        
        # Translations
        report_lines.append("="*80)
        report_lines.append("TRANSLATIONS: FIRST 5 WORDS OF EACH PARAGRAPH")
        report_lines.append("="*80)
        report_lines.append("")
        
        translations = data.get('translations', [])
        for trans in translations:
            para_idx = trans.get('paragraph_index', 'N/A')
            report_lines.append(f"Paragraph {para_idx}:")
            report_lines.append("-"*40)
            
            for lang_code in ['en', 'de', 'fr', 'es', 'it', 'zh', 'ar', 'uk', 'ru']:
                lang_text = trans.get(lang_code)
                if lang_text:
                    report_lines.append(f"  {lang_code.upper():3}: {lang_text}")
            
            report_lines.append("")
        
        # Significant paragraphs
        report_lines.append("="*80)
        report_lines.append("PARAGRAPHS WITH SIGNIFICANT MEANING CHANGES")
        report_lines.append("="*80)
        report_lines.append("")
        
        significant = data.get('significant_paragraphs', [])
        for para in significant:
            report_lines.append(f"Paragraph {para.get('paragraph_index')} ({para.get('shift_count')} shifts):")
            report_lines.append(f"Text: {para.get('paragraph_text', '')[:200]}...")
            report_lines.append("Shifts:")
            for shift in para.get('shifts', []):
                report_lines.append(f"  - {shift.get('type')} in {shift.get('lang')}: {shift.get('original', '')[:50]} → {shift.get('translation', '')[:50]}")
            report_lines.append("")
        
        # Divergence timeline
        report_lines.append("="*80)
        report_lines.append("TEMPORAL DIVERGENCE ANALYSIS")
        report_lines.append("="*80)
        report_lines.append("")
        report_lines.append("Tracing linguistic divergence from historical point to present:")
        report_lines.append("")
        
        divergence = data.get('divergence_timeline', [])
        for div_item in divergence:
            report_lines.append(f"Language: {div_item.get('language', 'unknown').upper()}")
            report_lines.append(f"  Divergence Level: {div_item.get('divergence_level', 'unknown').upper()}")
            report_lines.append(f"  Total Shifts: {div_item.get('total_shifts', 0)}")
            report_lines.append(f"  Word Order Shifts: {div_item.get('word_order_shifts', 0)}")
            report_lines.append(f"  Concept Shifts: {div_item.get('concept_shifts', 0)}")
            report_lines.append("")
        
        # Save text report
        output_file = 'chronology/linguistic_analysis_report.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Text report generated: {output_file}")
        return output_file

if __name__ == '__main__':
    generator = LinguisticReportGenerator()
    generator.generate_html_report()
    generator.generate_detailed_text_report()
    print("\nReports generated successfully!")

