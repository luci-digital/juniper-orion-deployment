#!/usr/bin/env python3
"""
Analyze macOS application bundle structure and contents.
"""

import json
import os
import plistlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class AppBundleAnalyzer:
    def __init__(self, app_bundle_path: str):
        self.app_bundle_path = Path(app_bundle_path)
        self.contents_path = self.app_bundle_path / "Contents" if (self.app_bundle_path / "Contents").exists() else self.app_bundle_path
        
    def analyze(self) -> Dict:
        """Perform complete app bundle analysis."""
        result = {
            "app_bundle_path": str(self.app_bundle_path),
            "analysis_date": datetime.now().isoformat(),
            "structure": {},
            "info_plist": {},
            "executables": [],
            "resources": {},
            "code_signature": {},
            "statistics": {}
        }
        
        # Analyze structure
        result["structure"] = self._analyze_structure()
        
        # Analyze Info.plist
        info_plist_path = self.contents_path / "Info.plist"
        if info_plist_path.exists():
            result["info_plist"] = self._analyze_info_plist(info_plist_path)
        
        # Find executables
        result["executables"] = self._find_executables()
        
        # Analyze resources
        resources_path = self.contents_path / "Resources"
        if resources_path.exists():
            result["resources"] = self._analyze_resources(resources_path)
        
        # Analyze code signature
        code_signature_path = self.contents_path / "_CodeSignature"
        if code_signature_path.exists():
            result["code_signature"] = self._analyze_code_signature(code_signature_path)
        
        # Calculate statistics
        result["statistics"] = self._calculate_statistics(result)
        
        return result
    
    def _analyze_structure(self) -> Dict:
        """Analyze the directory structure."""
        structure = {
            "directories": [],
            "files": [],
            "total_size": 0
        }
        
        try:
            for item in self.contents_path.rglob("*"):
                if item.is_file():
                    structure["files"].append({
                        "path": str(item.relative_to(self.contents_path)),
                        "size": item.stat().st_size,
                        "extension": item.suffix.lower()
                    })
                    structure["total_size"] += item.stat().st_size
                elif item.is_dir():
                    structure["directories"].append(str(item.relative_to(self.contents_path)))
        except PermissionError:
            structure["error"] = "Permission denied accessing some files"
        except Exception as e:
            structure["error"] = str(e)
        
        return structure
    
    def _analyze_info_plist(self, plist_path: Path) -> Dict:
        """Analyze Info.plist file."""
        info = {}
        
        try:
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
                
            # Extract key information
            info = {
                "CFBundleIdentifier": plist_data.get("CFBundleIdentifier", "Unknown"),
                "CFBundleName": plist_data.get("CFBundleName", "Unknown"),
                "CFBundleVersion": plist_data.get("CFBundleVersion", "Unknown"),
                "CFBundleShortVersionString": plist_data.get("CFBundleShortVersionString", "Unknown"),
                "CFBundleExecutable": plist_data.get("CFBundleExecutable", "Unknown"),
                "CFBundlePackageType": plist_data.get("CFBundlePackageType", "Unknown"),
                "LSMinimumSystemVersion": plist_data.get("LSMinimumSystemVersion", "Unknown"),
                "CFBundleIconFile": plist_data.get("CFBundleIconFile", "Unknown"),
                "all_keys": list(plist_data.keys())
            }
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    def _find_executables(self) -> List[Dict]:
        """Find executable files."""
        executables = []
        
        macos_path = self.contents_path / "MacOS"
        if macos_path.exists():
            for item in macos_path.iterdir():
                if item.is_file() and os.access(item, os.X_OK):
                    stat = item.stat()
                    executables.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.contents_path)),
                        "size": stat.st_size,
                        "permissions": oct(stat.st_mode)[-3:]
                    })
        
        return executables
    
    def _analyze_resources(self, resources_path: Path) -> Dict:
        """Analyze Resources directory."""
        resources = {
            "total_files": 0,
            "file_types": {},
            "directories": [],
            "largest_files": []
        }
        
        file_sizes = []
        
        try:
            for item in resources_path.rglob("*"):
                if item.is_file():
                    resources["total_files"] += 1
                    ext = item.suffix.lower() or "no_extension"
                    resources["file_types"][ext] = resources["file_types"].get(ext, 0) + 1
                    
                    size = item.stat().st_size
                    file_sizes.append({
                        "path": str(item.relative_to(resources_path)),
                        "size": size
                    })
                elif item.is_dir():
                    resources["directories"].append(str(item.relative_to(resources_path)))
            
            # Get largest files
            file_sizes.sort(key=lambda x: x["size"], reverse=True)
            resources["largest_files"] = file_sizes[:10]
            
        except PermissionError:
            resources["error"] = "Permission denied"
        except Exception as e:
            resources["error"] = str(e)
        
        return resources
    
    def _analyze_code_signature(self, code_signature_path: Path) -> Dict:
        """Analyze code signature."""
        signature = {
            "exists": True,
            "files": []
        }
        
        try:
            for item in code_signature_path.iterdir():
                if item.is_file():
                    signature["files"].append({
                        "name": item.name,
                        "size": item.stat().st_size
                    })
        except Exception as e:
            signature["error"] = str(e)
        
        return signature
    
    def _calculate_statistics(self, result: Dict) -> Dict:
        """Calculate overall statistics."""
        stats = {
            "total_files": len(result["structure"].get("files", [])),
            "total_directories": len(result["structure"].get("directories", [])),
            "total_size_mb": result["structure"].get("total_size", 0) / (1024 * 1024),
            "executable_count": len(result.get("executables", [])),
            "resource_file_count": result.get("resources", {}).get("total_files", 0),
            "is_signed": bool(result.get("code_signature", {}).get("exists", False))
        }
        
        return stats
    
    def generate_report(self, result: Dict, output_file: str = "app_bundle_analysis.json") -> str:
        """Generate analysis report and save to file."""
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return output_file

if __name__ == "__main__":
    import sys
    bundle_path = sys.argv[1] if len(sys.argv) > 1 else "/Applications/PEPE_ElementsBundle_2026.app/Contents"
    
    analyzer = AppBundleAnalyzer(bundle_path)
    result = analyzer.analyze()
    
    output_file = analyzer.generate_report(result)
    print(f"Analysis complete! Results saved to: {output_file}")
    print(f"\nStatistics:")
    stats = result["statistics"]
    print(f"  Total files: {stats['total_files']}")
    print(f"  Total size: {stats['total_size_mb']:.2f} MB")
    print(f"  Executables: {stats['executable_count']}")
    print(f"  Resource files: {stats['resource_file_count']}")
    print(f"  Code signed: {stats['is_signed']}")


