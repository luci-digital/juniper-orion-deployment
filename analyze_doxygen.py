#!/usr/bin/env python3
"""
Analyze Doxygen documentation projects.
Based on Doxygen internals: https://doxygen.github.io/doxygen-docs/
"""

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import re

class DoxygenAnalyzer:
    """
    Analyze Doxygen documentation projects.
    Supports:
    - Doxyfile configuration analysis
    - XML output analysis
    - HTML output analysis
    - Documentation coverage
    - Symbol extraction
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.doxyfile_path = None
        self.xml_dir = None
        self.html_dir = None
        
    def find_doxygen_files(self) -> Dict:
        """Find Doxygen-related files in the project."""
        found = {
            "doxyfile": None,
            "doxyfile_in": None,
            "xml_output": None,
            "html_output": None,
            "latex_output": None,
            "rtf_output": None,
            "man_output": None
        }
        
        # Look for Doxyfile
        for pattern in ["Doxyfile", "doxyfile", "Doxyfile.in", "doxyfile.in"]:
            doxyfile = self.project_path / pattern
            if doxyfile.exists():
                if pattern.endswith(".in"):
                    found["doxyfile_in"] = str(doxyfile)
                else:
                    found["doxyfile"] = str(doxyfile)
                break
        
        # Look for output directories (common names)
        output_patterns = {
            "xml_output": ["xml", "doxygen/xml", "docs/xml", "doc/xml"],
            "html_output": ["html", "doxygen/html", "docs/html", "doc/html"],
            "latex_output": ["latex", "doxygen/latex", "docs/latex"],
            "rtf_output": ["rtf", "doxygen/rtf"],
            "man_output": ["man", "doxygen/man"]
        }
        
        for output_type, patterns in output_patterns.items():
            for pattern in patterns:
                output_dir = self.project_path / pattern
                if output_dir.exists() and output_dir.is_dir():
                    found[output_type] = str(output_dir)
                    break
        
        return found
    
    def analyze_doxyfile(self, doxyfile_path: str) -> Dict:
        """Analyze Doxygen configuration file."""
        config = {
            "path": doxyfile_path,
            "options": {},
            "input_files": [],
            "output_formats": [],
            "language": None,
            "extract_all": False,
            "extract_private": False,
            "extract_static": False
        }
        
        try:
            with open(doxyfile_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY = VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        
                        config["options"][key] = value
                        
                        # Extract important options
                        if key == "INPUT":
                            config["input_files"] = [p.strip() for p in value.split() if p.strip()]
                        elif key == "GENERATE_HTML":
                            if value.upper() == "YES":
                                config["output_formats"].append("HTML")
                        elif key == "GENERATE_XML":
                            if value.upper() == "YES":
                                config["output_formats"].append("XML")
                        elif key == "GENERATE_LATEX":
                            if value.upper() == "YES":
                                config["output_formats"].append("LaTeX")
                        elif key == "GENERATE_RTF":
                            if value.upper() == "YES":
                                config["output_formats"].append("RTF")
                        elif key == "GENERATE_MAN":
                            if value.upper() == "YES":
                                config["output_formats"].append("Man")
                        elif key == "EXTRACT_ALL":
                            config["extract_all"] = value.upper() == "YES"
                        elif key == "EXTRACT_PRIVATE":
                            config["extract_private"] = value.upper() == "YES"
                        elif key == "EXTRACT_STATIC":
                            config["extract_static"] = value.upper() == "YES"
                        elif key == "PROJECT_NAME":
                            config["project_name"] = value
                        elif key == "PROJECT_NUMBER":
                            config["project_version"] = value
                        elif key == "OUTPUT_DIRECTORY":
                            config["output_directory"] = value
        except Exception as e:
            config["error"] = str(e)
        
        return config
    
    def analyze_xml_output(self, xml_dir: str) -> Dict:
        """Analyze Doxygen XML output."""
        xml_path = Path(xml_dir)
        analysis = {
            "xml_dir": str(xml_dir),
            "index_file": None,
            "compound_files": [],
            "symbols": {
                "classes": [],
                "namespaces": [],
                "files": [],
                "functions": [],
                "variables": [],
                "enums": [],
                "defines": []
            },
            "statistics": {}
        }
        
        # Look for index.xml
        index_xml = xml_path / "index.xml"
        if index_xml.exists():
            analysis["index_file"] = str(index_xml)
            try:
                tree = ET.parse(index_xml)
                root = tree.getroot()
                
                # Count compounds
                compounds = root.findall(".//compound")
                analysis["statistics"]["total_compounds"] = len(compounds)
                
                for compound in compounds:
                    kind = compound.get("kind", "")
                    refid = compound.get("refid", "")
                    name = compound.findtext("name", "")
                    
                    compound_info = {
                        "kind": kind,
                        "refid": refid,
                        "name": name
                    }
                    
                    # Categorize by kind
                    if kind == "class":
                        analysis["symbols"]["classes"].append(compound_info)
                    elif kind == "namespace":
                        analysis["symbols"]["namespaces"].append(compound_info)
                    elif kind == "file":
                        analysis["symbols"]["files"].append(compound_info)
                    
                    analysis["compound_files"].append(compound_info)
                
                # Count members
                members = root.findall(".//member")
                analysis["statistics"]["total_members"] = len(members)
                
            except Exception as e:
                analysis["error"] = str(e)
        
        # Analyze individual compound files
        for xml_file in xml_path.glob("*.xml"):
            if xml_file.name == "index.xml":
                continue
            
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Extract memberdef elements
                for memberdef in root.findall(".//memberdef"):
                    kind = memberdef.get("kind", "")
                    name = memberdef.findtext("name", "")
                    
                    member_info = {
                        "name": name,
                        "kind": kind,
                        "file": xml_file.name
                    }
                    
                    if kind == "function":
                        analysis["symbols"]["functions"].append(member_info)
                    elif kind == "variable":
                        analysis["symbols"]["variables"].append(member_info)
                    elif kind == "enum":
                        analysis["symbols"]["enums"].append(member_info)
                    elif kind == "define":
                        analysis["symbols"]["defines"].append(member_info)
                        
            except Exception as e:
                continue
        
        # Calculate statistics
        analysis["statistics"]["classes"] = len(analysis["symbols"]["classes"])
        analysis["statistics"]["namespaces"] = len(analysis["symbols"]["namespaces"])
        analysis["statistics"]["files"] = len(analysis["symbols"]["files"])
        analysis["statistics"]["functions"] = len(analysis["symbols"]["functions"])
        analysis["statistics"]["variables"] = len(analysis["symbols"]["variables"])
        analysis["statistics"]["enums"] = len(analysis["symbols"]["enums"])
        analysis["statistics"]["defines"] = len(analysis["symbols"]["defines"])
        
        return analysis
    
    def analyze_html_output(self, html_dir: str) -> Dict:
        """Analyze Doxygen HTML output."""
        html_path = Path(html_dir)
        analysis = {
            "html_dir": str(html_dir),
            "index_file": None,
            "pages": [],
            "has_search": False,
            "has_treeview": False,
            "statistics": {}
        }
        
        # Look for index.html
        index_html = html_path / "index.html"
        if index_html.exists():
            analysis["index_file"] = str(index_html)
        
        # Count HTML files
        html_files = list(html_path.glob("*.html"))
        analysis["statistics"]["total_pages"] = len(html_files)
        
        # Check for search functionality
        search_files = ["search.js", "searchdata.js", "search/search.js"]
        for search_file in search_files:
            if (html_path / search_file).exists():
                analysis["has_search"] = True
                break
        
        # Check for treeview
        if (html_path / "navtree.js").exists() or (html_path / "navtree.css").exists():
            analysis["has_treeview"] = True
        
        return analysis
    
    def analyze(self) -> Dict:
        """Perform complete Doxygen analysis."""
        result = {
            "project_path": str(self.project_path),
            "analysis_date": datetime.now().isoformat(),
            "doxygen_files": {},
            "doxyfile_config": {},
            "xml_analysis": {},
            "html_analysis": {},
            "statistics": {}
        }
        
        # Find Doxygen files
        doxygen_files = self.find_doxygen_files()
        result["doxygen_files"] = doxygen_files
        
        # Analyze Doxyfile if found
        doxyfile_path = doxygen_files.get("doxyfile") or doxygen_files.get("doxyfile_in")
        if doxyfile_path:
            result["doxyfile_config"] = self.analyze_doxyfile(doxyfile_path)
        
        # Analyze XML output if found
        if doxygen_files.get("xml_output"):
            result["xml_analysis"] = self.analyze_xml_output(doxygen_files["xml_output"])
        
        # Analyze HTML output if found
        if doxygen_files.get("html_output"):
            result["html_analysis"] = self.analyze_html_output(doxygen_files["html_output"])
        
        # Calculate overall statistics
        result["statistics"] = self._calculate_statistics(result)
        
        return result
    
    def _calculate_statistics(self, result: Dict) -> Dict:
        """Calculate overall statistics."""
        stats = {
            "has_doxyfile": bool(result.get("doxyfile_config", {}).get("path")),
            "has_xml_output": bool(result.get("xml_analysis", {}).get("xml_dir")),
            "has_html_output": bool(result.get("html_analysis", {}).get("html_dir")),
            "output_formats": result.get("doxyfile_config", {}).get("output_formats", []),
            "total_symbols": 0
        }
        
        # Sum up symbols from XML analysis
        xml_stats = result.get("xml_analysis", {}).get("statistics", {})
        if xml_stats:
            stats["total_symbols"] = (
                xml_stats.get("classes", 0) +
                xml_stats.get("namespaces", 0) +
                xml_stats.get("files", 0) +
                xml_stats.get("functions", 0) +
                xml_stats.get("variables", 0) +
                xml_stats.get("enums", 0) +
                xml_stats.get("defines", 0)
            )
            stats.update(xml_stats)
        
        return stats
    
    def generate_report(self, result: Dict, output_file: str = "doxygen_analysis.json") -> str:
        """Generate analysis report and save to file."""
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return output_file

if __name__ == "__main__":
    import sys
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    analyzer = DoxygenAnalyzer(project_path)
    result = analyzer.analyze()
    
    output_file = analyzer.generate_report(result)
    print(f"Doxygen analysis complete! Results saved to: {output_file}")
    
    stats = result.get("statistics", {})
    print(f"\nStatistics:")
    print(f"  Has Doxyfile: {stats.get('has_doxyfile', False)}")
    print(f"  Has XML output: {stats.get('has_xml_output', False)}")
    print(f"  Has HTML output: {stats.get('has_html_output', False)}")
    print(f"  Output formats: {', '.join(stats.get('output_formats', []))}")
    if stats.get("total_symbols", 0) > 0:
        print(f"  Total symbols: {stats['total_symbols']}")
        print(f"  Classes: {stats.get('classes', 0)}")
        print(f"  Functions: {stats.get('functions', 0)}")

