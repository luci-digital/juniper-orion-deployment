# Analysis Agents Directory

This document catalogs the specialized analysis agents available in the dis_maops MCP ecosystem. Each agent is designed for specific types of data analysis and processing tasks.

## 🧠 LuciaZeen (Intelligent Router Agent)

**Role**: Multi-purpose intelligent analysis router and catalyst

**Function**: Acts as the primary "enzyme" that detects analysis needs from natural language queries and routes to appropriate specialized agents. Uses pattern recognition to identify analysis requirements and construct optimal analysis pipelines.

**Specialization**: Analysis orchestration, pattern detection, pipeline construction

**Input Types**: Natural language queries, file paths, data samples
**Output Types**: Analysis recommendations, confidence scores, execution pipelines

---

## 🗺️ MapsChronology Agent

**Role**: Cartographic data extraction and chronological organization specialist

**Function**: Extracts maps from Wikimedia Commons HTML, organizes chronologically, builds geographic and thematic relationships, and generates interactive timelines.

**Specialization**: Historical cartography, temporal organization, geographic analysis

**Input Types**: Wikimedia Commons HTML pages, map metadata, image files
**Output Types**: Chronological timelines, geographic region analysis, inter-related map networks

---

## 👥 ContributorAnalyzer Agent

**Role**: Human contributor pattern analysis and correlation specialist

**Function**: Analyzes contributor behavior patterns, username classifications, language usage, posting patterns, and relationship networks. Detects coordinated activities and expertise levels.

**Specialization**: Social network analysis, behavioral pattern recognition, linguistic analysis

**Input Types**: User contribution data, metadata, timestamps, language patterns
**Output Types**: Contributor networks, expertise classifications, correlation matrices, language analysis reports

---

## 🔍 AnomalyDetector Agent

**Role**: Data quality and outlier detection specialist

**Function**: Identifies unusual patterns, data inconsistencies, temporal anomalies, and statistical outliers in datasets. Performs multi-dimensional anomaly detection.

**Specialization**: Statistical analysis, pattern anomaly detection, data quality assessment

**Input Types**: Structured data, time series, metadata collections
**Output Types**: Anomaly reports, quality metrics, statistical analysis, data validation results

---

## 🎯 ExpertiseClassifier Agent

**Role**: Subject matter expertise assessment specialist

**Function**: Distinguishes between subject matter experts and task providers based on contribution patterns, content quality, and behavioral indicators.

**Specialization**: Expertise assessment, content analysis, behavioral classification

**Input Types**: Contribution histories, content quality metrics, behavioral data
**Output Types**: Expertise classifications, confidence scores, behavioral pattern analysis

---

## 🔗 CorrelationAnalyzer Agent

**Role**: Relationship and network analysis specialist

**Function**: Analyzes relationships between contributors, maps, regions, and temporal patterns. Builds correlation networks and identifies significant associations.

**Specialization**: Network analysis, correlation detection, relationship mapping

**Input Types**: Multi-entity datasets, relationship data, temporal sequences
**Output Types**: Correlation networks, relationship graphs, association strength metrics

---

## 📊 ChronologyOrganizer Agent

**Role**: Temporal organization and sequencing specialist

**Function**: Organizes data chronologically, builds temporal relationships, and creates timeline structures with proper sequencing and dating.

**Specialization**: Temporal analysis, chronological organization, date extraction and validation

**Input Types**: Date-containing data, temporal sequences, historical records
**Output Types**: Chronological timelines, temporal relationships, date validation reports

---

## 🌐 MetadataFetcher Agent

**Role**: External data enrichment and API integration specialist

**Function**: Retrieves additional metadata from external APIs, enriches existing datasets, and integrates third-party information sources.

**Specialization**: API integration, data enrichment, external data sources

**Input Types**: Partial metadata, API endpoints, data identifiers
**Output Types**: Enriched datasets, API responses, metadata supplements

---

## 📥 ImageDownloader Agent

**Role**: Media asset acquisition and management specialist

**Function**: Downloads, organizes, and manages image and media assets from various sources with rate limiting and error handling.

**Specialization**: Media asset management, download orchestration, file organization

**Input Types**: Media URLs, file lists, download specifications
**Output Types**: Organized media collections, download reports, asset inventories

---

## 🎨 OutputGenerator Agent

**Role**: Data visualization and presentation specialist

**Function**: Transforms analyzed data into interactive HTML interfaces, reports, and visual presentations with proper citations and navigation.

**Specialization**: Data visualization, HTML generation, interactive interfaces

**Input Types**: Processed data, analysis results, metadata collections
**Output Types**: HTML interfaces, interactive timelines, visualization reports

---

## 📋 PipelineOrchestrator Agent

**Role**: Complete analysis pipeline management specialist

**Function**: Coordinates multi-step analysis workflows, manages dependencies between agents, and ensures complete pipeline execution from data ingestion to final output.

**Specialization**: Workflow orchestration, dependency management, pipeline optimization

**Input Types**: Pipeline specifications, data inputs, agent configurations
**Output Types**: Complete analysis results, pipeline execution reports, optimized workflows

---

## 🔧 DoxygenAnalyzer Agent

**Role**: Documentation analysis and project structure specialist

**Function**: Analyzes Doxygen documentation projects, extracts structural information, and assesses documentation coverage and quality.

**Specialization**: Technical documentation analysis, project structure assessment, coverage metrics

**Input Types**: Doxygen projects, documentation files, source code structures
**Output Types**: Documentation analysis reports, coverage metrics, structural insights

---

## 🎯 Skill-Based Agent Routing

### Data Processing Skills
- **LuciaZeen**: Intelligent routing and pattern detection
- **MetadataFetcher**: External data enrichment
- **ImageDownloader**: Media asset management

### Analysis Skills
- **AnomalyDetector**: Statistical analysis and outlier detection
- **CorrelationAnalyzer**: Network and relationship analysis
- **ExpertiseClassifier**: Behavioral pattern classification

### Domain-Specific Skills
- **MapsChronology**: Cartographic and temporal analysis
- **ContributorAnalyzer**: Social and behavioral analysis
- **DoxygenAnalyzer**: Technical documentation analysis

### Output Skills
- **OutputGenerator**: Visualization and presentation
- **ChronologyOrganizer**: Temporal organization
- **PipelineOrchestrator**: Workflow coordination

---

## Agent Communication Protocol

All agents communicate through the MCP (Model Context Protocol) server using:

1. **Tool Registration**: Each agent registers its capabilities with the MCP server
2. **Request Routing**: LuciaZeen routes requests based on pattern matching
3. **Result Aggregation**: PipelineOrchestrator combines results from multiple agents
4. **Error Handling**: Standardized error reporting and recovery mechanisms

---

## Agent Development Guidelines

### New Agent Creation
1. Define clear specialization and role
2. Implement MCP-compatible tool interface
3. Register with LuciaZeen pattern recognition
4. Provide comprehensive input/output specifications
5. Include error handling and logging

### Agent Testing
- Unit tests for core functionality
- Integration tests with MCP server
- Cross-agent compatibility testing
- Performance benchmarking

This agent ecosystem provides comprehensive coverage for data analysis, processing, and visualization tasks while maintaining modularity and extensibility.
