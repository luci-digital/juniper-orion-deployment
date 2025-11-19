#!/usr/bin/env python3
"""
MCP Server for Maps Chronology Project
Exposes analysis and processing tools from the dis_maops project.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Sequence
import traceback

# Add the project directory to the path so we can import modules
project_dir = Path(__file__).parent
parent_dir = project_dir.parent  # Root of dis_maops
sys.path.insert(0, str(project_dir))
sys.path.insert(0, str(parent_dir))

try:
    # Try newer MCP SDK API
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_NEW_API = True
except ImportError:
    # Fallback for older MCP SDK versions
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
        MCP_NEW_API = False
    except ImportError:
        print("Error: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
        sys.exit(1)

# Import project modules
try:
    from advanced_contributor_analysis import AdvancedContributorAnalyzer
    from analyze_anomalies import analyze_anomalies
    from analyze_expertise import ContributorExpertiseAnalyzer
    from correlate_contributors import ContributorAnalyzer
    from create_luci_project_refined import load_and_filter_repos, create_project_structure
    from extract_maps import MapExtractor
    from download_images import ImageDownloader
    from fetch_metadata import MetadataFetcher
    from organize_chronology import ChronologyOrganizer
    from generate_output import OutputGenerator
    from run_pipeline import main as run_pipeline_main
    from luciazeen_analyzer import LuciaZeenAnalyzer
    from analyze_app_bundle import AppBundleAnalyzer
    from analyze_doxygen import DoxygenAnalyzer
    from analyze_github_org import GitHubOrgAnalyzer
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}", file=sys.stderr)

# Initialize MCP server
app = Server("dis-maops-mcp")

# Initialize LuciaZeen intelligent analyzer
luciazeen = LuciaZeenAnalyzer(str(project_dir))

# Helper function to run synchronous code in executor
async def run_sync(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="luciazeen_analyze",
            description="Intelligent analysis router (LuciaZeen enzyme pattern). Automatically detects what type of analysis is needed based on query, file path, or data sample, and routes to the appropriate tool. Acts as a catalyst that identifies patterns and activates the right analysis pathway.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query describing what you want to analyze (e.g., 'analyze contributors', 'find anomalies', 'extract maps from HTML')"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Optional: Path to a file to analyze (will auto-detect file type and content)"
                    },
                    "auto_execute": {
                        "type": "boolean",
                        "description": "Whether to automatically execute the recommended analysis (default: false - returns recommendations only)",
                        "default": False
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional: Additional context about the analysis request"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="analyze_contributors_advanced",
            description="Perform advanced contributor correlation analysis including language patterns, username classification, temporal coordination, and location matching.",
            inputSchema={
                "type": "object",
                "properties": {
                    "enriched_maps_file": {
                        "type": "string",
                        "description": "Path to enriched maps JSON file",
                        "default": "data/enriched_maps.json"
                    },
                    "generate_report": {
                        "type": "boolean",
                        "description": "Whether to generate HTML report",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="analyze_anomalies",
            description="Analyze data for anomalies and unusual patterns in dates, links, metadata, geography, linguistics, and temporal patterns.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="analyze_expertise",
            description="Analyze if contributors are subject matter experts or task providers based on their contribution patterns.",
            inputSchema={
                "type": "object",
                "properties": {
                    "advanced_analysis_file": {
                        "type": "string",
                        "description": "Path to advanced contributor analysis JSON file",
                        "default": "data/advanced_contributor_analysis.json"
                    },
                    "enriched_maps_file": {
                        "type": "string",
                        "description": "Path to enriched maps JSON file",
                        "default": "data/enriched_maps.json"
                    }
                }
            }
        ),
        Tool(
            name="correlate_contributors",
            description="Correlate contributors - analyze authors, uploaders, and their relationships based on shared regions, themes, and temporal overlap.",
            inputSchema={
                "type": "object",
                "properties": {
                    "enriched_maps_file": {
                        "type": "string",
                        "description": "Path to enriched maps JSON file",
                        "default": "data/enriched_maps.json"
                    },
                    "generate_html": {
                        "type": "boolean",
                        "description": "Whether to generate HTML report",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="create_luci_project",
            description="Create a Luci_Digital project structure from extracted repository list with filtering and categorization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "json_file": {
                        "type": "string",
                        "description": "Path to extracted repositories JSON file",
                        "default": "extracted_repos.json"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path where to create the project",
                        "default": "Luci_Digital_Mosh_Spark"
                    }
                }
            }
        ),
        Tool(
            name="extract_maps",
            description="Extract maps and metadata from a saved Wikimedia Commons HTML page.",
            inputSchema={
                "type": "object",
                "properties": {
                    "html_file": {
                        "type": "string",
                        "description": "Path to HTML file containing Wikimedia Commons discussion page",
                        "default": "User_Enyavar_DiscussingMaps - Wikimedia Commons.html"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output JSON file path",
                        "default": "data/extracted_maps.json"
                    }
                }
            }
        ),
        Tool(
            name="download_images",
            description="Download original high-resolution images from Wikimedia Commons.",
            inputSchema={
                "type": "object",
                "properties": {
                    "maps_data_file": {
                        "type": "string",
                        "description": "Path to maps data JSON file",
                        "default": "data/extracted_maps.json"
                    },
                    "download_dir": {
                        "type": "string",
                        "description": "Directory to save downloaded images",
                        "default": "downloads/originals"
                    }
                }
            }
        ),
        Tool(
            name="fetch_metadata",
            description="Fetch additional metadata from Wikimedia Commons API.",
            inputSchema={
                "type": "object",
                "properties": {
                    "maps_data_file": {
                        "type": "string",
                        "description": "Path to maps data JSON file",
                        "default": "data/extracted_maps.json"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output JSON file path",
                        "default": "data/enriched_maps.json"
                    }
                }
            }
        ),
        Tool(
            name="organize_chronology",
            description="Organize maps chronologically and build inter-related links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "enriched_maps_file": {
                        "type": "string",
                        "description": "Path to enriched maps JSON file",
                        "default": "data/enriched_maps.json"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output JSON file path",
                        "default": "data/organized_maps.json"
                    }
                }
            }
        ),
        Tool(
            name="generate_output",
            description="Generate HTML output structure including timeline and individual map pages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "organized_maps_file": {
                        "type": "string",
                        "description": "Path to organized maps JSON file",
                        "default": "data/organized_maps.json"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory for HTML files",
                        "default": "chronology"
                    }
                }
            }
        ),
        Tool(
            name="run_pipeline",
            description="Run the complete pipeline: extract maps, download images, fetch metadata, organize chronologically, and generate output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "html_file": {
                        "type": "string",
                        "description": "Path to HTML file containing Wikimedia Commons discussion page",
                        "default": "User_Enyavar_DiscussingMaps - Wikimedia Commons.html"
                    },
                    "skip_downloads": {
                        "type": "boolean",
                        "description": "Skip image downloads",
                        "default": False
                    },
                    "skip_metadata": {
                        "type": "boolean",
                        "description": "Skip metadata fetching",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="analyze_app_bundle",
            description="Analyze macOS application bundle structure, Info.plist, executables, resources, and code signature.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_bundle_path": {
                        "type": "string",
                        "description": "Path to the app bundle Contents directory or .app bundle",
                        "default": ""
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output JSON file path",
                        "default": "app_bundle_analysis.json"
                    }
                },
                "required": ["app_bundle_path"]
            }
        ),
        Tool(
            name="analyze_doxygen",
            description="Analyze Doxygen documentation projects. Based on Doxygen internals (https://doxygen.github.io/doxygen-docs/). Analyzes Doxyfile configuration, XML output, HTML output, and documentation coverage.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory containing Doxygen files",
                        "default": "."
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output JSON file path",
                        "default": "doxygen_analysis.json"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="analyze_github_org",
            description="Analyze a GitHub organization and all its repositories. Fetches repository metadata, contributors, technology stacks, and performs cross-repository analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_name": {
                        "type": "string",
                        "description": "GitHub organization name (e.g., 'NationalSecurityAgency')",
                        "default": "NationalSecurityAgency"
                    },
                    "github_token": {
                        "type": "string",
                        "description": "Optional GitHub personal access token for higher rate limits (set GITHUB_TOKEN env var instead)"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output JSON file path",
                        "default": "data/github_org_analysis.json"
                    }
                },
                "required": ["org_name"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "luciazeen_analyze":
            query = arguments.get("query", "")
            file_path = arguments.get("file_path")
            auto_execute = arguments.get("auto_execute", False)
            context = arguments.get("context", {})
            
            # Analyze file if provided
            file_info = None
            data_sample = None
            if file_path:
                file_info = await run_sync(luciazeen.analyze_file, file_path)
                if file_info:
                    data_sample = file_info.get("data_sample", {})
            
            # Build context for recommendation
            analysis_context = {
                "file_path": file_path,
                "data_sample": data_sample,
                **context
            }
            
            # Get pipeline recommendation
            pipeline = await run_sync(luciazeen.recommend_analysis_pipeline, query, analysis_context)
            
            # Find available data files
            available_files = await run_sync(luciazeen.find_available_data_files)
            
            # Build response
            response_parts = [
                "🔬 LuciaZeen Intelligent Analysis Router",
                "=" * 60,
                f"\nQuery: {query}",
                f"\nDetected Analysis Types:"
            ]
            
            for detection in pipeline["detected_types"]:
                confidence_pct = detection["confidence"] * 100
                response_parts.append(
                    f"  • {detection['type']}: {confidence_pct:.1f}% confidence"
                )
            
            response_parts.append(f"\nRecommended Pipeline ({pipeline['estimated_complexity']} complexity):")
            for step in pipeline["recommended_steps"]:
                response_parts.append(
                    f"\n  Step {step['step']}: {step['tool']}"
                )
                response_parts.append(f"    Analysis Type: {step['analysis_type']}")
                response_parts.append(f"    Confidence: {step['confidence']*100:.1f}%")
                if step['requires']:
                    response_parts.append(f"    Requires: {', '.join(step['requires'])}")
                if step['produces']:
                    response_parts.append(f"    Produces: {', '.join(step['produces'])}")
            
            if available_files:
                response_parts.append("\nAvailable Data Files:")
                for file_type, files in available_files.items():
                    if files:
                        response_parts.append(f"  {file_type}: {len(files)} files")
                        for f in files[:3]:  # Show first 3
                            response_parts.append(f"    - {os.path.basename(f)}")
            
            # Auto-execute if requested
            execution_results = []
            if auto_execute and pipeline["recommended_steps"]:
                response_parts.append("\n\n🚀 Auto-executing recommended analysis...")
                
                # Execute first recommended step
                first_step = pipeline["recommended_steps"][0]
                tool_name = first_step["tool"]
                
                # Map tool names to execution arguments
                tool_args_map = {
                    "analyze_contributors_advanced": {
                        "enriched_maps_file": "data/enriched_maps.json",
                        "generate_report": True
                    },
                    "analyze_anomalies": {},
                    "analyze_expertise": {
                        "advanced_analysis_file": "data/advanced_contributor_analysis.json",
                        "enriched_maps_file": "data/enriched_maps.json"
                    },
                    "correlate_contributors": {
                        "enriched_maps_file": "data/enriched_maps.json",
                        "generate_html": True
                    },
                    "extract_maps": {
                        "html_file": file_path or "User_Enyavar_DiscussingMaps - Wikimedia Commons.html",
                        "output_file": "data/extracted_maps.json"
                    },
                    "organize_chronology": {
                        "enriched_maps_file": "data/enriched_maps.json",
                        "output_file": "data/organized_maps.json"
                    },
                    "fetch_metadata": {
                        "maps_data_file": "data/extracted_maps.json",
                        "output_file": "data/enriched_maps.json"
                    },
                    "download_images": {
                        "maps_data_file": "data/extracted_maps.json",
                        "download_dir": "downloads/originals"
                    },
                    "generate_output": {
                        "organized_maps_file": "data/organized_maps.json",
                        "output_dir": "chronology"
                    },
                    "create_luci_project": {
                        "json_file": file_path or "extracted_repos.json",
                        "project_path": "Luci_Digital_Mosh_Spark"
                    },
                    "analyze_app_bundle": {
                        "app_bundle_path": file_path or "",
                        "output_file": "app_bundle_analysis.json"
                    },
                    "analyze_doxygen": {
                        "project_path": file_path or ".",
                        "output_file": "doxygen_analysis.json"
                    },
                    "analyze_github_org": {
                        "org_name": file_path or "NationalSecurityAgency",
                        "output_file": "data/github_org_analysis.json"
                    }
                }
                
                if tool_name in tool_args_map:
                    try:
                        exec_result = await call_tool(tool_name, tool_args_map[tool_name])
                        execution_results.append(f"\n✓ Executed: {tool_name}")
                        result_preview = exec_result[0].text[:200] if exec_result else "No result"
                        execution_results.append(f"  Result: {result_preview}...")
                    except Exception as e:
                        execution_results.append(f"\n✗ Failed to execute {tool_name}: {str(e)}")
                        execution_results.append(f"  Error details: {traceback.format_exc()[:300]}")
                else:
                    execution_results.append(f"\n⚠ Tool {tool_name} not yet implemented for auto-execution")
            
            response_text = "\n".join(response_parts)
            if execution_results:
                response_text += "\n" + "\n".join(execution_results)
            
            # Also return pipeline as JSON for programmatic use
            pipeline_json = json.dumps(pipeline, indent=2)
            response_text += f"\n\nPipeline JSON:\n{pipeline_json}"
            
            return [TextContent(type="text", text=response_text)]
        
        elif name == "analyze_contributors_advanced":
            enriched_file = arguments.get("enriched_maps_file", "data/enriched_maps.json")
            generate_report = arguments.get("generate_report", True)
            
            analyzer = AdvancedContributorAnalyzer(enriched_file)
            results = await run_sync(analyzer.analyze_all)
            
            if generate_report and results:
                await run_sync(analyzer.generate_advanced_report, results)
            
            return [TextContent(
                type="text",
                text=f"Advanced contributor analysis complete.\n\nResults:\n- Contributors analyzed: {len(results.get('contributors', []))}\n- Username types: {len(results.get('username_type_distribution', {}))}\n- Languages detected: {len(results.get('language_distribution', {}))}\n- Temporal coordination events: {len(results.get('temporal_coordination', []))}\n- Location matches: {len(results.get('location_matches', []))}\n\nResults saved to: data/advanced_contributor_analysis.json"
            )]
        
        elif name == "analyze_anomalies":
            await run_sync(analyze_anomalies)
            return [TextContent(
                type="text",
                text="Anomaly analysis complete. Check console output for details."
            )]
        
        elif name == "analyze_expertise":
            advanced_file = arguments.get("advanced_analysis_file", "data/advanced_contributor_analysis.json")
            enriched_file = arguments.get("enriched_maps_file", "data/enriched_maps.json")
            
            analyzer = ContributorExpertiseAnalyzer(advanced_file, enriched_file)
            results = await run_sync(analyzer.analyze_all)
            
            return [TextContent(
                type="text",
                text=f"Expertise analysis complete.\n\nResults:\n- Experts identified: {len(results.get('experts', []))}\n- Task providers: {len(results.get('task_providers', []))}\n- Generalists: {len(results.get('generalists', []))}\n- Specialized contributors: {len(results.get('specializations', []))}\n\nResults saved to: data/contributor_expertise_analysis.json"
            )]
        
        elif name == "correlate_contributors":
            enriched_file = arguments.get("enriched_maps_file", "data/enriched_maps.json")
            generate_html = arguments.get("generate_html", True)
            
            analyzer = ContributorAnalyzer(enriched_file)
            results = await run_sync(analyzer.generate_contributor_report)
            
            if generate_html and results:
                await run_sync(analyzer.generate_contributor_network_html, results)
            
            return [TextContent(
                type="text",
                text=f"Contributor correlation analysis complete.\n\nResults:\n- Total contributors: {results.get('statistics', {}).get('total_contributors', 0)}\n- Total contributions: {results.get('statistics', {}).get('total_contributions', 0)}\n- Correlations found: {len(results.get('correlations', []))}\n\nResults saved to: data/contributor_analysis.json"
            )]
        
        elif name == "create_luci_project":
            json_file = arguments.get("json_file", "extracted_repos.json")
            project_path = arguments.get("project_path", "Luci_Digital_Mosh_Spark")
            
            repos = await run_sync(load_and_filter_repos, json_file)
            await run_sync(create_project_structure, project_path, repos)
            
            return [TextContent(
                type="text",
                text=f"Luci_Digital project created successfully.\n\n- Total repositories: {len(repos)}\n- Project path: {project_path}\n- Configuration saved to: {project_path}/config/project.json"
            )]
        
        elif name == "extract_maps":
            html_file = arguments.get("html_file", "User_Enyavar_DiscussingMaps - Wikimedia Commons.html")
            output_file = arguments.get("output_file", "data/extracted_maps.json")
            
            extractor = MapExtractor(html_file)
            result = await run_sync(extractor.extract)
            
            # Save to specified output file
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            return [TextContent(
                type="text",
                text=f"Maps extracted successfully.\n\n- Maps found: {result.get('total_maps', 0)}\n- Output saved to: {output_file}"
            )]
        
        elif name == "download_images":
            maps_data_file = arguments.get("maps_data_file", "data/extracted_maps.json")
            download_dir = arguments.get("download_dir", "downloads/originals")
            
            downloader = ImageDownloader(maps_data_file)
            downloader.download_dir = download_dir
            os.makedirs(download_dir, exist_ok=True)
            
            results = await run_sync(downloader.download_all)
            
            return [TextContent(
                type="text",
                text=f"Image download complete.\n\n- Downloaded: {results.get('downloaded', 0)}\n- Skipped: {results.get('skipped', 0)}\n- Failed: {results.get('failed', 0)}\n- Results saved to: data/download_results.json"
            )]
        
        elif name == "fetch_metadata":
            maps_data_file = arguments.get("maps_data_file", "data/extracted_maps.json")
            output_file = arguments.get("output_file", "data/enriched_maps.json")
            
            fetcher = MetadataFetcher(maps_data_file)
            result = await run_sync(fetcher.fetch_all)
            
            # Save to specified output file
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            return [TextContent(
                type="text",
                text=f"Metadata fetching complete.\n\n- Maps processed: {result.get('total_maps', 0)}\n- Metadata fetched: {result.get('metadata_fetched', 0)}\n- Output saved to: {output_file}"
            )]
        
        elif name == "organize_chronology":
            enriched_maps_file = arguments.get("enriched_maps_file", "data/enriched_maps.json")
            output_file = arguments.get("output_file", "data/organized_maps.json")
            
            organizer = ChronologyOrganizer(enriched_maps_file)
            result = await run_sync(organizer.organize)
            
            # Save to specified output file
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            return [TextContent(
                type="text",
                text=f"Chronological organization complete.\n\n- Maps organized: {result.get('total_maps', 0)}\n- Timeline groups: {len(result.get('timeline', {}))}\n- Links created: {sum(len(links) for links in result.get('links', {}).values())}\n- Output saved to: {output_file}"
            )]
        
        elif name == "generate_output":
            organized_maps_file = arguments.get("organized_maps_file", "data/organized_maps.json")
            output_dir = arguments.get("output_dir", "chronology")
            
            generator = OutputGenerator(organized_maps_file)
            generator.output_dir = output_dir
            result = await run_sync(generator.generate)
            
            return [TextContent(
                type="text",
                text=f"Output generation complete.\n\n- HTML files generated in: {output_dir}\n- Main timeline: {output_dir}/index.html\n- Map pages: {output_dir}/maps/"
            )]
        
        elif name == "run_pipeline":
            html_file = arguments.get("html_file", "User_Enyavar_DiscussingMaps - Wikimedia Commons.html")
            skip_downloads = arguments.get("skip_downloads", False)
            skip_metadata = arguments.get("skip_metadata", False)
            
            # We need to modify run_pipeline to accept parameters
            # For now, we'll run the steps individually
            results = []
            
            # Step 1: Extract maps
            extractor = MapExtractor(html_file)
            extract_result = await run_sync(extractor.extract)
            results.append(f"Extracted {extract_result.get('total_maps', 0)} maps")
            
            # Step 2: Download images (if not skipped)
            if not skip_downloads:
                downloader = ImageDownloader('data/extracted_maps.json')
                download_result = await run_sync(downloader.download_all)
                results.append(f"Downloaded {download_result.get('downloaded', 0)} images")
            
            # Step 3: Fetch metadata (if not skipped)
            enriched_file = 'data/extracted_maps.json'
            if not skip_metadata:
                fetcher = MetadataFetcher('data/extracted_maps.json')
                fetch_result = await run_sync(fetcher.fetch_all)
                enriched_file = 'data/enriched_maps.json'
                results.append(f"Fetched metadata for {fetch_result.get('metadata_fetched', 0)} maps")
            
            # Step 4: Organize chronologically
            organizer = ChronologyOrganizer(enriched_file)
            organize_result = await run_sync(organizer.organize)
            results.append(f"Organized {organize_result.get('total_maps', 0)} maps chronologically")
            
            # Step 5: Generate output
            generator = OutputGenerator('data/organized_maps.json')
            generate_result = await run_sync(generator.generate)
            results.append("Generated HTML output")
            
            return [TextContent(
                type="text",
                text=f"Pipeline complete!\n\n" + "\n".join(f"- {r}" for r in results) + f"\n\nOutput files:\n- chronology/index.html - Main timeline page\n- chronology/maps/ - Individual map pages\n- chronology/data/ - JSON data files"
            )]
        
        elif name == "analyze_app_bundle":
            app_bundle_path = arguments.get("app_bundle_path", "")
            output_file = arguments.get("output_file", "app_bundle_analysis.json")
            
            if not app_bundle_path:
                return [TextContent(
                    type="text",
                    text="Error: app_bundle_path is required"
                )]
            
            analyzer = AppBundleAnalyzer(app_bundle_path)
            result = await run_sync(analyzer.analyze)
            output_path = await run_sync(analyzer.generate_report, result, output_file)
            
            stats = result.get("statistics", {})
            info_plist = result.get("info_plist", {})
            
            return [TextContent(
                type="text",
                text=f"App bundle analysis complete!\n\n"
                     f"Application: {info_plist.get('CFBundleName', 'Unknown')}\n"
                     f"Bundle ID: {info_plist.get('CFBundleIdentifier', 'Unknown')}\n"
                     f"Version: {info_plist.get('CFBundleShortVersionString', 'Unknown')}\n\n"
                     f"Statistics:\n"
                     f"- Total files: {stats.get('total_files', 0)}\n"
                     f"- Total size: {stats.get('total_size_mb', 0):.2f} MB\n"
                     f"- Executables: {stats.get('executable_count', 0)}\n"
                     f"- Resource files: {stats.get('resource_file_count', 0)}\n"
                     f"- Code signed: {stats.get('is_signed', False)}\n\n"
                     f"Results saved to: {output_path}"
            )]
        
        elif name == "analyze_doxygen":
            project_path = arguments.get("project_path", ".")
            output_file = arguments.get("output_file", "doxygen_analysis.json")
            
            analyzer = DoxygenAnalyzer(project_path)
            result = await run_sync(analyzer.analyze)
            output_path = await run_sync(analyzer.generate_report, result, output_file)
            
            stats = result.get("statistics", {})
            doxyfile_config = result.get("doxyfile_config", {})
            
            return [TextContent(
                type="text",
                text=f"Doxygen analysis complete!\n\n"
                     f"Project: {doxyfile_config.get('project_name', 'Unknown')}\n"
                     f"Version: {doxyfile_config.get('project_version', 'Unknown')}\n\n"
                     f"Configuration:\n"
                     f"- Has Doxyfile: {stats.get('has_doxyfile', False)}\n"
                     f"- Output formats: {', '.join(stats.get('output_formats', []))}\n"
                     f"- Extract all: {doxyfile_config.get('extract_all', False)}\n"
                     f"- Extract private: {doxyfile_config.get('extract_private', False)}\n\n"
                     f"Output:\n"
                     f"- Has XML output: {stats.get('has_xml_output', False)}\n"
                     f"- Has HTML output: {stats.get('has_html_output', False)}\n"
                     f"- Total symbols: {stats.get('total_symbols', 0)}\n"
                     f"- Classes: {stats.get('classes', 0)}\n"
                     f"- Functions: {stats.get('functions', 0)}\n"
                     f"- Namespaces: {stats.get('namespaces', 0)}\n\n"
                     f"Results saved to: {output_path}"
            )]
        
        elif name == "analyze_github_org":
            org_name = arguments.get("org_name", "NationalSecurityAgency")
            github_token = arguments.get("github_token") or os.environ.get("GITHUB_TOKEN")
            output_file = arguments.get("output_file", f"data/github_org_{org_name.lower()}_analysis.json")
            
            analyzer = GitHubOrgAnalyzer(org_name, github_token)
            analysis = await run_sync(analyzer.analyze_repositories)
            output_path = await run_sync(analyzer.generate_report, analysis, output_file)
            summary = await run_sync(analyzer.generate_summary, analysis)
            
            stats = analysis.get("statistics", {})
            contributors = analysis.get("contributors", {})
            
            return [TextContent(
                type="text",
                text=f"GitHub organization analysis complete!\n\n"
                     f"Organization: {org_name}\n"
                     f"Total Repositories: {analysis.get('total_repositories', 0)}\n"
                     f"  Public: {stats.get('by_visibility', {}).get('public', 0)}\n"
                     f"  Private: {stats.get('by_visibility', {}).get('private', 0)}\n\n"
                     f"Statistics:\n"
                     f"- Total Stars: {stats.get('stars', 0):,}\n"
                     f"- Total Forks: {stats.get('forks', 0):,}\n"
                     f"- Open Issues: {stats.get('open_issues', 0):,}\n"
                     f"- Unique Contributors: {len(contributors.get('total_unique', []))}\n"
                     f"- Cross-Repo Contributors: {len(contributors.get('cross_repo_contributors', []))}\n\n"
                     f"Top Languages: {', '.join(list(stats.get('by_language', {}).keys())[:5])}\n\n"
                     f"Results saved to: {output_path}\n\n"
                     f"{summary}"
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return [TextContent(type="text", text=error_msg)]

async def main():
    """Main entry point for the MCP server."""
    # Use stdio transport
    async with stdio_server() as (read_stream, write_stream):
        if MCP_NEW_API:
            try:
                await app.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="dis-maops-mcp",
                        server_version="1.0.0",
                        capabilities=app.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
            except (AttributeError, TypeError):
                # Fallback for simpler API
                await app.run(read_stream, write_stream)
        else:
            # Older API
            await app.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())

