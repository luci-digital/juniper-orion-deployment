# GitHub Organization Analysis Integration

## Overview

The GitHub Organization Analyzer has been successfully integrated into dis_maops, enabling comprehensive analysis of GitHub organizations and their repositories. This integration allows you to analyze organizations like the NSA's GitHub (85+ repositories) with full cross-repository insights.

## What Was Added

### 1. GitHubOrgAnalyzer Agent (`analyze_github_org.py`)

A comprehensive analyzer that:
- Fetches all repositories for a GitHub organization via GitHub API
- Analyzes technology stacks (languages, licenses, topics)
- Performs cross-repository contributor analysis
- Categorizes repositories by type (security-tools, big-data, training-platforms, etc.)
- Generates detailed statistics and reports

**Key Features:**
- Rate limiting and error handling for GitHub API
- Support for both authenticated (higher rate limits) and unauthenticated access
- Cross-repository contributor correlation
- Repository categorization
- Comprehensive statistics generation

### 2. LuciaZeen Router Integration

Added `github_org_analysis` pattern detection:
- **Keywords**: github, organization, org, repositories, repos, github.com/orgs
- **Auto-detection**: Recognizes GitHub organization analysis requests
- **Priority**: 13

### 3. MCP Tool Integration

New MCP tool: `analyze_github_org`

**Parameters:**
- `org_name` (required): GitHub organization name (e.g., "NationalSecurityAgency")
- `github_token` (optional): GitHub personal access token for higher rate limits
- `output_file` (optional): Output JSON file path

**Example Usage:**
```json
{
  "tool": "analyze_github_org",
  "arguments": {
    "org_name": "NationalSecurityAgency",
    "output_file": "data/github_org_analysis.json"
  }
}
```

## Usage

### Direct Python Script

```bash
# Analyze NSA GitHub organization
python3 analyze_github_org.py NationalSecurityAgency

# With GitHub token for higher rate limits (optional)
export GITHUB_TOKEN=your_token_here
python3 analyze_github_org.py NationalSecurityAgency
```

### Via MCP Server

```json
{
  "tool": "analyze_github_org",
  "arguments": {
    "org_name": "NationalSecurityAgency"
  }
}
```

### Via LuciaZeen Intelligent Router

```json
{
  "tool": "luciazeen_analyze",
  "arguments": {
    "query": "analyze GitHub organization NationalSecurityAgency repositories",
    "auto_execute": true
  }
}
```

## Output

The analyzer generates:

1. **JSON Report** (`data/github_org_{org}_analysis.json`):
   - Complete repository metadata
   - Technology stack statistics
   - Contributor analysis
   - Cross-repository correlations
   - Repository categories

2. **Summary Report** (console output):
   - Total repositories
   - Top languages
   - Top licenses
   - Top topics
   - Repository categories
   - Contributor statistics
   - Cross-repository contributors

## Analysis Capabilities

### Repository Analysis
- Language distribution
- License analysis
- Topic/tag analysis
- Star/fork/watcher statistics
- Issue tracking
- Repository categorization

### Contributor Analysis
- Unique contributors per repository
- Cross-repository contributors
- Contribution patterns
- Contributor networks

### Technology Stack Analysis
- Primary languages per repository
- Language byte counts
- Technology trends across organization

### Repository Categorization
Automatically categorizes repositories into:
- `security-tools`: Reverse engineering, security tools (Ghidra, etc.)
- `big-data`: Data processing and analytics (DataWave, Accumulo)
- `training-platforms`: Learning and gamification (SkillTree)
- `workflow-orchestration`: Workflow and P2P systems (Emissary)
- `documentation`: Documentation sites
- `infrastructure`: Deployment and infrastructure tools
- `libraries`: SDKs and client libraries
- `testing-tools`: Testing and quality tools
- `other`: Uncategorized

## Rate Limiting

The analyzer includes intelligent rate limiting:
- **Unauthenticated**: 60 requests/hour (GitHub API limit)
- **Authenticated**: 5,000 requests/hour (with GitHub token)
- Automatic rate limit detection and waiting
- Configurable delay between requests

## Integration Points

### With Existing Agents

1. **LuciaZeen Router**: Automatically detects GitHub org analysis requests
2. **MCP Server**: Exposed as `analyze_github_org` tool
3. **ContributorAnalyzer**: Can use GitHub org data for cross-repo analysis
4. **DoxygenAnalyzer**: Can analyze documentation across organization repos

### Future Enhancements

Potential integrations:
- Repository cloning and local analysis
- Documentation coverage analysis across org
- Dependency graph analysis
- Security vulnerability scanning
- Contribution pattern visualization

## Example: NSA GitHub Organization

The NSA organization is an excellent use case:
- **85+ repositories** across multiple domains
- **Diverse technology stacks**: Java, Python, Rust, JavaScript
- **Security-focused**: Reverse engineering, big data, security tools
- **Active open source**: Well-maintained projects with community contributions

**Analysis Output Includes:**
- All 85 repositories with metadata
- Technology stack breakdown
- Cross-repository contributor networks
- Project categorization
- Statistics and trends

## Files Modified/Created

1. **Created**: `analyze_github_org.py` - Main analyzer agent
2. **Modified**: `projects/luciazeen_analyzer.py` - Added GitHub org pattern
3. **Modified**: `mcp_tool/mcp_server.py` - Added MCP tool and handler
4. **Created**: `GITHUB_ORG_INTEGRATION.md` - This documentation

## Testing

```bash
# Syntax check
python3 -m py_compile analyze_github_org.py

# Test import
python3 -c "from analyze_github_org import GitHubOrgAnalyzer; print('✓ Import successful')"

# Run analysis (will take time due to API rate limits)
python3 analyze_github_org.py NationalSecurityAgency
```

## Notes

- GitHub API rate limits apply (60/hour unauthenticated, 5000/hour authenticated)
- Analysis of large organizations (85+ repos) may take 10-30 minutes
- Set `GITHUB_TOKEN` environment variable for faster analysis
- Results are cached in JSON format for reuse

## Next Steps

1. ✅ GitHubOrgAnalyzer agent created
2. ✅ LuciaZeen integration complete
3. ✅ MCP tool integration complete
4. ⏳ Visualization outputs (HTML reports)
5. ⏳ Repository cloning and local analysis
6. ⏳ Cross-org comparison capabilities

