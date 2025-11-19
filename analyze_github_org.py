#!/usr/bin/env python3
"""
GitHub Organization Analyzer
Analyzes GitHub organizations and their repositories, including:
- Repository metadata extraction
- Technology stack analysis
- Cross-repository contributor analysis
- Project categorization
- Documentation coverage
"""

import json
import os
import time
import requests
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

class GitHubOrgAnalyzer:
    """
    Analyzes GitHub organizations and their repositories.
    Supports both authenticated and unauthenticated API access.
    """
    
    def __init__(self, org_name: str, github_token: Optional[str] = None):
        self.org_name = org_name
        self.github_token = github_token
        self.api_base = 'https://api.github.com'
        self.rate_limit_delay = 0.5  # Delay between requests (seconds)
        self.repositories = []
        self.contributors_map = defaultdict(set)  # repo -> set of contributors
        self.language_stats = Counter()
        self.license_stats = Counter()
        self.topic_stats = Counter()
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a GitHub API request with rate limiting and error handling."""
        url = f"{self.api_base}{endpoint}"
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'dis_maops-GitHubOrgAnalyzer/1.0'
        }
        
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Check rate limit
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            if remaining < 10:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(0, reset_time - int(time.time())) + 1
                print(f"  ⚠ Rate limit low ({remaining} remaining). Waiting {wait_time}s...")
                time.sleep(wait_time)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"  ✗ API request failed: {e}")
            return None
    
    def fetch_organization_repos(self, per_page: int = 100) -> List[Dict]:
        """Fetch all repositories for the organization."""
        print(f"Fetching repositories for organization: {self.org_name}")
        repos = []
        page = 1
        
        while True:
            print(f"  Fetching page {page}...")
            endpoint = f"/orgs/{self.org_name}/repos"
            params = {
                'per_page': per_page,
                'page': page,
                'type': 'all',  # all, public, private, forks, sources, member
                'sort': 'updated',
                'direction': 'desc'
            }
            
            data = self._make_request(endpoint, params)
            if not data:
                break
            
            if not isinstance(data, list):
                # Error response
                print(f"  ✗ Error: {data.get('message', 'Unknown error')}")
                break
            
            if len(data) == 0:
                break
            
            repos.extend(data)
            print(f"    Found {len(data)} repositories (total: {len(repos)})")
            
            if len(data) < per_page:
                break
            
            page += 1
            time.sleep(self.rate_limit_delay)
        
        self.repositories = repos
        print(f"\n✓ Fetched {len(repos)} repositories total\n")
        return repos
    
    def fetch_repo_contributors(self, repo_full_name: str) -> List[Dict]:
        """Fetch contributors for a specific repository."""
        endpoint = f"/repos/{repo_full_name}/contributors"
        params = {'per_page': 100}
        
        contributors = []
        page = 1
        
        while True:
            params['page'] = page
            data = self._make_request(endpoint, params)
            
            if not data or not isinstance(data, list):
                break
            
            if len(data) == 0:
                break
            
            contributors.extend(data)
            
            if len(data) < 100:
                break
            
            page += 1
            time.sleep(self.rate_limit_delay)
        
        return contributors
    
    def fetch_repo_languages(self, repo_full_name: str) -> Dict[str, int]:
        """Fetch language statistics for a repository."""
        endpoint = f"/repos/{repo_full_name}/languages"
        data = self._make_request(endpoint)
        return data if data else {}
    
    def analyze_repositories(self) -> Dict:
        """Perform comprehensive analysis of all repositories."""
        print("="*60)
        print("GITHUB ORGANIZATION ANALYSIS")
        print("="*60)
        print()
        
        if not self.repositories:
            print("No repositories loaded. Fetching...")
            self.fetch_organization_repos()
        
        analysis = {
            'organization': self.org_name,
            'analysis_date': datetime.now().isoformat(),
            'total_repositories': len(self.repositories),
            'repositories': [],
            'statistics': {
                'by_language': {},
                'by_license': {},
                'by_topic': {},
                'by_visibility': {'public': 0, 'private': 0},
                'forks': 0,
                'stars': 0,
                'watchers': 0,
                'open_issues': 0
            },
            'contributors': {
                'total_unique': set(),
                'by_repository': {},
                'cross_repo_contributors': []
            },
            'categories': {}
        }
        
        # Analyze each repository
        print(f"Analyzing {len(self.repositories)} repositories...")
        for i, repo in enumerate(self.repositories, 1):
            repo_name = repo.get('full_name', repo.get('name', 'unknown'))
            print(f"[{i}/{len(self.repositories)}] Analyzing: {repo_name}")
            
            repo_analysis = {
                'name': repo.get('name'),
                'full_name': repo.get('full_name'),
                'url': repo.get('html_url'),
                'description': repo.get('description'),
                'language': repo.get('language'),
                'license': repo.get('license', {}).get('name') if repo.get('license') else None,
                'topics': repo.get('topics', []),
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'watchers': repo.get('watchers_count', 0),
                'open_issues': repo.get('open_issues_count', 0),
                'created_at': repo.get('created_at'),
                'updated_at': repo.get('updated_at'),
                'pushed_at': repo.get('pushed_at'),
                'size': repo.get('size', 0),
                'archived': repo.get('archived', False),
                'disabled': repo.get('disabled', False),
                'private': repo.get('private', False),
                'default_branch': repo.get('default_branch'),
                'has_wiki': repo.get('has_wiki', False),
                'has_pages': repo.get('has_pages', False),
                'has_issues': repo.get('has_issues', True),
                'has_projects': repo.get('has_projects', False),
                'has_downloads': repo.get('has_downloads', True),
                'contributors': [],
                'languages': {},
                'category': self._categorize_repository(repo)
            }
            
            # Fetch detailed language stats
            languages = self.fetch_repo_languages(repo.get('full_name'))
            if languages:
                repo_analysis['languages'] = languages
                for lang, bytes_count in languages.items():
                    self.language_stats[lang] += bytes_count
            
            # Fetch contributors
            contributors = self.fetch_repo_contributors(repo.get('full_name'))
            contributor_logins = [c.get('login') for c in contributors if c.get('login')]
            repo_analysis['contributors'] = [
                {
                    'login': c.get('login'),
                    'contributions': c.get('contributions', 0),
                    'url': c.get('html_url')
                }
                for c in contributors
            ]
            
            # Track contributors
            self.contributors_map[repo.get('full_name')] = set(contributor_logins)
            analysis['contributors']['total_unique'].update(contributor_logins)
            analysis['contributors']['by_repository'][repo.get('full_name')] = contributor_logins
            
            # Update statistics
            if repo_analysis['language']:
                analysis['statistics']['by_language'][repo_analysis['language']] = \
                    analysis['statistics']['by_language'].get(repo_analysis['language'], 0) + 1
            
            if repo_analysis['license']:
                analysis['statistics']['by_license'][repo_analysis['license']] = \
                    analysis['statistics']['by_license'].get(repo_analysis['license'], 0) + 1
            
            for topic in repo_analysis['topics']:
                analysis['statistics']['by_topic'][topic] = \
                    analysis['statistics']['by_topic'].get(topic, 0) + 1
            
            if repo_analysis['private']:
                analysis['statistics']['by_visibility']['private'] += 1
            else:
                analysis['statistics']['by_visibility']['public'] += 1
            
            analysis['statistics']['forks'] += repo_analysis['forks']
            analysis['statistics']['stars'] += repo_analysis['stars']
            analysis['statistics']['watchers'] += repo_analysis['watchers']
            analysis['statistics']['open_issues'] += repo_analysis['open_issues']
            
            analysis['repositories'].append(repo_analysis)
            
            time.sleep(self.rate_limit_delay)
        
        # Find cross-repository contributors
        print("\nAnalyzing cross-repository contributors...")
        all_contributors = analysis['contributors']['total_unique']
        repo_list = list(self.contributors_map.keys())
        
        for contributor in all_contributors:
            contributing_repos = [
                repo for repo in repo_list
                if contributor in self.contributors_map[repo]
            ]
            if len(contributing_repos) > 1:
                analysis['contributors']['cross_repo_contributors'].append({
                    'contributor': contributor,
                    'repositories': contributing_repos,
                    'repo_count': len(contributing_repos)
                })
        
        # Convert sets to lists for JSON serialization
        analysis['contributors']['total_unique'] = list(analysis['contributors']['total_unique'])
        
        # Categorize repositories
        analysis['categories'] = self._categorize_all_repositories(analysis['repositories'])
        
        return analysis
    
    def _categorize_repository(self, repo: Dict) -> str:
        """Categorize a repository based on its name, description, and topics."""
        name_lower = repo.get('name', '').lower()
        desc_lower = (repo.get('description') or '').lower()
        topics = [t.lower() for t in repo.get('topics', [])]
        all_text = f"{name_lower} {desc_lower} {' '.join(topics)}"
        
        # Security and reverse engineering
        if any(x in all_text for x in ['ghidra', 'reverse', 'disassemble', 'malware', 'security', 'vulnerability']):
            return 'security-tools'
        
        # Big data and analytics
        if any(x in all_text for x in ['datawave', 'accumulo', 'bigdata', 'analytics', 'query', 'ingest']):
            return 'big-data'
        
        # Learning and training
        if any(x in all_text for x in ['skill', 'training', 'gamification', 'learning']):
            return 'training-platforms'
        
        # Workflow and orchestration
        if any(x in all_text for x in ['emissary', 'workflow', 'p2p', 'distributed']):
            return 'workflow-orchestration'
        
        # Documentation and websites
        if any(x in all_text for x in ['docs', 'documentation', 'github.io', 'site']):
            return 'documentation'
        
        # Infrastructure and deployment
        if any(x in all_text for x in ['helm', 'docker', 'kubernetes', 'deploy', 'stack']):
            return 'infrastructure'
        
        # Libraries and utilities
        if any(x in all_text for x in ['utils', 'library', 'client', 'sdk', 'api']):
            return 'libraries'
        
        # Testing and quality
        if any(x in all_text for x in ['test', 'stress', 'quality', 'profiler']):
            return 'testing-tools'
        
        return 'other'
    
    def _categorize_all_repositories(self, repos: List[Dict]) -> Dict[str, List[str]]:
        """Categorize all repositories and return by category."""
        categories = defaultdict(list)
        for repo in repos:
            category = repo.get('category', 'other')
            categories[category].append(repo.get('full_name'))
        return dict(categories)
    
    def generate_report(self, analysis: Dict, output_file: str = 'github_org_analysis.json') -> str:
        """Generate a comprehensive analysis report."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Analysis report saved to: {output_path}")
        return str(output_path)
    
    def generate_summary(self, analysis: Dict) -> str:
        """Generate a human-readable summary."""
        stats = analysis['statistics']
        contributors = analysis['contributors']
        
        summary = []
        summary.append("="*60)
        summary.append(f"GITHUB ORGANIZATION ANALYSIS SUMMARY: {self.org_name}")
        summary.append("="*60)
        summary.append("")
        
        summary.append(f"Total Repositories: {analysis['total_repositories']}")
        summary.append(f"  Public: {stats['by_visibility']['public']}")
        summary.append(f"  Private: {stats['by_visibility']['private']}")
        summary.append("")
        
        summary.append("Top Languages:")
        lang_items = sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True)
        for lang, count in lang_items[:10]:
            summary.append(f"  {lang}: {count} repositories")
        summary.append("")
        
        summary.append("Top Licenses:")
        license_items = sorted(stats['by_license'].items(), key=lambda x: x[1], reverse=True)
        for license_name, count in license_items[:5]:
            summary.append(f"  {license_name}: {count} repositories")
        summary.append("")
        
        summary.append("Top Topics:")
        topic_items = sorted(stats['by_topic'].items(), key=lambda x: x[1], reverse=True)
        for topic, count in topic_items[:10]:
            summary.append(f"  {topic}: {count} repositories")
        summary.append("")
        
        summary.append("Repository Categories:")
        for category, repos in sorted(analysis['categories'].items()):
            summary.append(f"  {category}: {len(repos)} repositories")
        summary.append("")
        
        summary.append(f"Total Unique Contributors: {len(contributors['total_unique'])}")
        summary.append(f"Cross-Repository Contributors: {len(contributors['cross_repo_contributors'])}")
        if contributors['cross_repo_contributors']:
            top_cross = sorted(contributors['cross_repo_contributors'], 
                             key=lambda x: x['repo_count'], reverse=True)[:5]
            summary.append("  Top contributors across multiple repos:")
            for contrib in top_cross:
                summary.append(f"    {contrib['contributor']}: {contrib['repo_count']} repositories")
        summary.append("")
        
        summary.append(f"Total Stars: {stats['stars']:,}")
        summary.append(f"Total Forks: {stats['forks']:,}")
        summary.append(f"Total Watchers: {stats['watchers']:,}")
        summary.append(f"Open Issues: {stats['open_issues']:,}")
        summary.append("")
        
        return "\n".join(summary)

if __name__ == '__main__':
    import sys
    
    org_name = sys.argv[1] if len(sys.argv) > 1 else 'NationalSecurityAgency'
    github_token = os.environ.get('GITHUB_TOKEN')  # Optional: set GITHUB_TOKEN env var
    
    analyzer = GitHubOrgAnalyzer(org_name, github_token)
    analysis = analyzer.analyze_repositories()
    
    output_file = f'data/github_org_{org_name.lower()}_analysis.json'
    analyzer.generate_report(analysis, output_file)
    
    print("\n" + analyzer.generate_summary(analysis))

