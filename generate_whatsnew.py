#!/usr/bin/env python3
"""
Automated What's New Page Generator for Elastic Observability.

Scrapes release notes, enriches with GitHub data (labels, media),
downloads assets, cross-references PM priorities, and generates
the formatted HTML page.

Usage:
    python3 generate_whatsnew.py --releases 9.2.0,9.2.2,9.2.3,9.3.0
    python3 generate_whatsnew.py --releases 9.2.0,9.3.0 \
        --pm-file PMhighlightedfeatures/observability-9.3-features.md \
        --output whats-new.html --media-dir media/ \
        --github-token $GITHUB_TOKEN
"""

import argparse
import html as html_module
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Section / label mapping configuration
# ---------------------------------------------------------------------------

# Maps GitHub Feature:XXX labels to (section_key, section_name)
LABEL_TO_SECTION = {
    "Feature:Streams": ("streams", "Log Analytics & Streams"),
    "Feature:Logs": ("streams", "Log Analytics & Streams"),
    "Feature:Infrastructure Monitoring": ("infrastructure", "Infrastructure Monitoring"),
    "Feature:Inventory": ("infrastructure", "Infrastructure Monitoring"),
    "Feature:AI Assistant": ("ai-investigations", "Agentic Investigations"),
    "Feature:Automatic Import": ("ai-investigations", "Agentic Investigations"),
    "Feature:Query": ("query-analysis", "Query, Analysis & Alerting"),
    "Feature:Alerting": ("query-analysis", "Query, Analysis & Alerting"),
    "Feature:Cases": ("query-analysis", "Query, Analysis & Alerting"),
    "Feature:OpenTelemetry": ("opentelemetry", "OpenTelemetry"),
    "Feature:EDOT": ("opentelemetry", "OpenTelemetry"),
    "Feature:APM": ("apm", "Application Performance Monitoring"),
    "Feature:Synthetics": ("digital-experience", "Digital Experience Monitoring"),
    "Feature:Uptime": ("digital-experience", "Digital Experience Monitoring"),
    "Feature:SLO": ("digital-experience", "Digital Experience Monitoring"),
}

# Manual overrides for features that keyword heuristics misplace.
# Key: substring to match in description (case-insensitive).
# Value: dict with optional keys: section_key, section_name, title, add_links.
MANUAL_OVERRIDES = [
    {
        "match": "custom global ingest pipelines on slo rollup",
        "section_key": "query-analysis",
        "section_name": "Query, Analysis & Alerting",
    },
    {
        "match": "deactivate_all_instrumentations",
        "section_key": "opentelemetry",
        "section_name": "OpenTelemetry",
    },
    {
        "match": "metrics dashboard for non-edot agents",
        "section_key": "opentelemetry",
        "section_name": "OpenTelemetry",
    },
    {
        "match": "observability agent for agent builder",
        "section_key": "ai-investigations",
        "section_name": "Agentic Investigations",
        "title": "Observability Agent for Agent Builder in 9.3",
        "pm_highlighted": True,
        "pm_order": 1.5,
        "add_links": [("https://www.elastic.co/docs/solutions/observability/ai/agent-builder-observability", "docs")],
    },
    {
        "match_title": "Workflows",
        "title": "Workflows in Observability - NEW",
        "add_links": [("https://www.elastic.co/docs/explore-analyze/workflows", "docs")],
    },
]

# Keyword-based fallback inference when no Feature label is found
KEYWORD_SECTION_HINTS = [
    (["stream", "log", "ingest", "pipeline", "routing", "processor",
      "processing", "partitioning", "schema tab", "field mapping",
      "unlink", "preview"],
     ("streams", "Log Analytics & Streams")),
    (["infrastructure", "inventory", "host", "metrics", "tsdb", "downsampl",
      "time series", " ts ", "exponential histogram", "detect existing schemas",
      "rollback", "agent version", "integration version", "fleet"],
     ("infrastructure", "Infrastructure Monitoring")),
    (["ai ", "llm", "genai", "knowledge base", "assistant", "gemini",
      "bedrock", "function calling", "connector", "system prompt"],
     ("ai-investigations", "Agentic Investigations")),
    (["alert", "query", "discover", "case", "threshold", "rule",
      "api key", "dashboard", "saved quer", "workflow tag", "mute", "snooze"],
     ("query-analysis", "Query, Analysis & Alerting")),
    (["otel", "opentelemetry", "edot", "opamp", "agent config"],
     ("opentelemetry", "OpenTelemetry")),
    (["apm", "trace", "span", "transaction", "service map", "service inventory",
      "error.id", "custom link", "jvm metric", "similar error"],
     ("apm", "Application Performance Monitoring")),
    (["synthetics", "monitor", "uptime", "slo", "sli", "browser",
      "journey step", "test run"],
     ("digital-experience", "Digital Experience Monitoring")),
]

# Ordered sections for output
SECTIONS_ORDER = [
    ("streams", "Log Analytics & Streams", "tag-streams", "icon-logs"),
    ("infrastructure", "Infrastructure Monitoring", "tag-infra", "icon-infra"),
    ("ai-investigations", "Agentic Investigations", "tag-ai", "icon-ai"),
    ("query-analysis", "Query, Analysis & Alerting", "tag-query", "icon-query"),
    ("opentelemetry", "OpenTelemetry", "tag-otel", "icon-otel"),
    ("apm", "Application Performance Monitoring", "tag-apm", "icon-apm"),
    ("digital-experience", "Digital Experience Monitoring", "tag-digital", "icon-digital"),
]

# Section key -> anchor ID mapping for TOC
SECTION_ANCHORS = {s[0]: s[0] for s in SECTIONS_ORDER}

# Section key -> tag class
SECTION_TAG_CLASS = {s[0]: s[2] for s in SECTIONS_ORDER}

# Reverse lookup: for keyword-inferred sections, derive a feature tag from the
# LABEL_TO_SECTION mapping (pick the shortest/most common label per section)
_SECTION_DEFAULT_FEATURE_TAG = {
    "streams": "Streams",
    "infrastructure": "Infrastructure Monitoring",
    "ai-investigations": "AI Assistant",
    "query-analysis": "Alerting",
    "opentelemetry": "OpenTelemetry",
    "apm": "APM",
    "digital-experience": "Synthetics",
}

# Section icons (SVG markup)
SECTION_ICONS = {
    "streams": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "infrastructure": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
    "ai-investigations": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 014 4v1a1 1 0 001 1h1a4 4 0 010 8h-1a1 1 0 00-1 1v1a4 4 0 01-8 0v-1a1 1 0 00-1-1H6a4 4 0 010-8h1a1 1 0 001-1V6a4 4 0 014-4z"/></svg>',
    "query-analysis": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "opentelemetry": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "apm": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "digital-experience": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
}

# PR icon SVGs
PR_ICON_SVG = '<svg viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"/></svg>'
ISSUE_ICON_SVG = '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 9.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/><path fill-rule="evenodd" d="M8 0a8 8 0 100 16A8 8 0 008 0zM1.5 8a6.5 6.5 0 1113 0 6.5 6.5 0 01-13 0z"/></svg>'


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PRLink:
    """A GitHub PR or issue link."""
    repo: str          # e.g. "elastic/kibana" or "elastic/elasticsearch"
    number: int
    link_type: str     # "pull" or "issue"
    url: str

@dataclass
class Feature:
    """A single feature extracted from release notes."""
    description: str
    version: str
    pr_links: list = field(default_factory=list)      # list of PRLink
    labels: list = field(default_factory=list)         # GitHub labels
    section_key: str = ""                              # resolved section
    section_name: str = ""
    title: str = ""                                    # short title (from PM or derived)
    feature_tags: list = field(default_factory=list)   # e.g. ["Streams"] from Feature:Streams
    media: list = field(default_factory=list)          # list of (local_path, media_type)
    pm_highlighted: bool = False
    pm_order: int = 999


# ---------------------------------------------------------------------------
# Step 1: Parse release notes page
# ---------------------------------------------------------------------------

def fetch_url(url: str, headers: Optional[dict] = None, max_retries: int = 3) -> str:
    """Fetch URL content with retries."""
    req_headers = {"User-Agent": "Mozilla/5.0 (whatsnew-generator)"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                wait = 2 ** attempt
                print(f"  HTTP {e.code} fetching {url}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return ""


def parse_release_notes(requested_versions: list[str]) -> list[Feature]:
    """
    Fetch the Elastic Observability release notes page and extract
    features for the requested versions.

    Page structure:
      <h2 id="elastic-observability-X.Y.Z-release-notes"> X.Y.Z </h2>
      <h3 id="...-features-enhancements"> Features and enhancements </h3>  (or "Features")
      <ul><li>...</li></ul>
      <h3 id="...-fixes"> Fixes </h3>
      <ul><li>...</li></ul>
    """
    url = "https://www.elastic.co/docs/release-notes/observability"
    print(f"Step 1: Fetching release notes from {url}")
    page_html = fetch_url(url)

    if not page_html:
        print("  ERROR: Could not fetch release notes page")
        return []

    features = []

    # Find version sections. The page uses:
    #   <div class="heading-wrapper" id="elastic-observability-9.3.0-release-notes">
    #     <h2><a ...>9.3.0</a></h2>
    #   </div>
    h2_pattern = re.compile(
        r'<div[^>]*class=["\']heading-wrapper["\'][^>]*id=["\']elastic-observability-(\d+\.\d+\.\d+)-release-notes["\'][^>]*>.*?</div>',
        re.IGNORECASE | re.DOTALL
    )

    # Find all version headings and their positions
    version_sections = []
    for m in h2_pattern.finditer(page_html):
        version_sections.append((m.start(), m.group(1), m.end()))

    if not version_sections:
        # Fallback: try matching the id attribute on any element
        print("  WARNING: No version sections found via heading-wrapper, trying fallback...")
        fallback = re.compile(
            r'id=["\']elastic-observability-(\d+\.\d+\.\d+)-release-notes["\']',
            re.IGNORECASE
        )
        for m in fallback.finditer(page_html):
            version_sections.append((m.start(), m.group(1), m.end()))

    # Deduplicate: keep only first occurrence per version
    seen_versions = set()
    unique_sections = []
    for entry in version_sections:
        ver = entry[1]
        if ver not in seen_versions:
            seen_versions.add(ver)
            unique_sections.append(entry)
    version_sections = unique_sections

    print(f"  Found {len(version_sections)} version sections: "
          f"{[v[1] for v in version_sections[:10]]}{'...' if len(version_sections) > 10 else ''}")

    for i, (start_pos, version, heading_end) in enumerate(version_sections):
        if version not in requested_versions:
            continue

        # Get section text until next version h2 heading
        end_pos = version_sections[i + 1][0] if i + 1 < len(version_sections) else len(page_html)
        section_html = page_html[heading_end:end_pos]

        # Find h3 headings for "Features" subsections within this version
        # Page structure: <div class="heading-wrapper" id="..."><h3>...</h3></div>
        # Match the heading-wrapper divs containing h3
        h3_wrapper_pattern = re.compile(
            r'<div[^>]*class=["\']heading-wrapper["\'][^>]*>.*?<h3[^>]*>(.*?)</h3>.*?</div>',
            re.IGNORECASE | re.DOTALL
        )
        # Also match plain h3 as fallback
        h3_plain_pattern = re.compile(
            r'<h3[^>]*>(.*?)</h3>',
            re.IGNORECASE | re.DOTALL
        )

        # Find all h3-level headings (wrapper or plain)
        all_h3s = []
        for h3_match in h3_wrapper_pattern.finditer(section_html):
            h3_text = re.sub(r'<[^>]+>', '', h3_match.group(1)).strip()
            all_h3s.append((h3_match.start(), h3_match.end(), h3_text))
        if not all_h3s:
            for h3_match in h3_plain_pattern.finditer(section_html):
                h3_text = re.sub(r'<[^>]+>', '', h3_match.group(1)).strip()
                all_h3s.append((h3_match.start(), h3_match.end(), h3_text))

        feat_section = ""
        for idx, (h3_start, h3_end, h3_text) in enumerate(all_h3s):
            h3_lower = h3_text.lower()

            if "fix" in h3_lower or "deprecat" in h3_lower:
                continue  # Skip fixes and deprecations

            if "feature" in h3_lower or "enhancement" in h3_lower:
                # Found a features section — extract content until next h3 or end
                next_h3_start = all_h3s[idx + 1][0] if idx + 1 < len(all_h3s) else len(section_html)
                feat_section = section_html[h3_end:next_h3_start]
                break

        if not feat_section:
            print(f"  No features section for {version} (patch release with only fixes?)")
            continue

        # Extract list items from the features section only
        li_pattern = re.compile(r'<li[^>]*>(.*?)</li>', re.DOTALL | re.IGNORECASE)
        version_feature_count = 0
        for li_match in li_pattern.finditer(feat_section):
            li_html = li_match.group(1)

            # Remove PR/issue link anchors before extracting text so
            # "#239188" doesn't end up in the description
            li_text_html = re.sub(
                r',?\s*<a[^>]*href=["\']https://github\.com/elastic/[^"\']+["\'][^>]*>#?\d+</a>',
                '', li_html
            )
            # Also remove ES issue references like "ES#136250"
            li_text_html = re.sub(
                r',?\s*<a[^>]*href=["\']https://github\.com/elastic/[^"\']+["\'][^>]*>ES#\d+</a>',
                '', li_text_html
            )

            # Extract text content (strip remaining tags)
            text = re.sub(r'<[^>]+>', '', li_text_html).strip()
            text = html_module.unescape(text)
            # Remove any trailing bare PR references like "#239188" or ", #239188"
            text = re.sub(r'[,\s]+#\d+(?:[,\s]+#\d+)*\s*$', '', text)
            text = re.sub(r'[,\s]+ES#\d+(?:[,\s]+ES#\d+)*\s*$', '', text)
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text).strip()

            if not text:
                continue

            # Extract PR/issue links
            link_pattern = re.compile(
                r'href=["\']?(https://github\.com/(elastic/(?:kibana|elasticsearch))/(?:pull|issues)/(\d+))["\']?'
            )
            pr_links = []
            for lm in link_pattern.finditer(li_html):
                link_url = lm.group(1)
                repo = lm.group(2)
                number = int(lm.group(3))
                link_type = "pull" if "/pull/" in link_url else "issue"
                pr_links.append(PRLink(repo=repo, number=number, link_type=link_type, url=link_url))

            if pr_links or len(text) > 20:
                features.append(Feature(
                    description=text,
                    version=version,
                    pr_links=pr_links,
                ))
                version_feature_count += 1

        print(f"  {version}: {version_feature_count} features")

    print(f"  Extracted {len(features)} total features across requested versions")
    return features


# ---------------------------------------------------------------------------
# Step 2: Enrich via GitHub API
# ---------------------------------------------------------------------------

class GitHubAPI:
    """Thin wrapper around GitHub REST API with rate limiting."""

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.remaining = 5000 if token else 60
        self.reset_time = 0
        self._saml_blocked_orgs: set = set()  # orgs that need SSO auth

    def _headers(self) -> dict:
        h = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "whatsnew-generator",
        }
        if self.token:
            h["Authorization"] = f"token {self.token}"
        return h

    def _check_rate_limit(self):
        if self.remaining <= 5:
            wait = max(0, self.reset_time - time.time()) + 1
            if wait > 0:
                print(f"  Rate limit low ({self.remaining} remaining), sleeping {wait:.0f}s...")
                time.sleep(wait)

    def get(self, endpoint: str) -> Optional[dict]:
        """GET from GitHub API. Returns parsed JSON or None on error."""
        # Fast-fail if we already know this org is SAML-blocked
        for org in self._saml_blocked_orgs:
            if org in endpoint:
                return None

        self._check_rate_limit()

        url = f"https://api.github.com{endpoint}"
        req = urllib.request.Request(url, headers=self._headers())

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                # Update rate limit tracking
                self.remaining = int(resp.headers.get("X-RateLimit-Remaining", self.remaining))
                self.reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # Check if it's actually a rate limit or an auth/SAML error
                body = e.read().decode("utf-8", errors="replace")
                remaining = e.headers.get("X-RateLimit-Remaining", "?")
                if "SAML" in body or "revoked" in body:
                    # Extract org name from endpoint (e.g. /repos/elastic/kibana/...)
                    org_match = re.search(r'/repos/([^/]+)/', endpoint)
                    org = org_match.group(1) if org_match else "unknown"
                    self._saml_blocked_orgs.add(org)
                    print(f"  ERROR: SAML/SSO auth required for '{org}' org.")
                    print(f"    Your token needs SSO authorization. Skipping all '{org}' PRs.")
                    print(f"    Falling back to keyword-based categorization.")
                    return None
                elif remaining != "?" and int(remaining) > 0:
                    # 403 but rate limit not exhausted — secondary rate limit or auth issue
                    print(f"  WARNING: 403 for {endpoint} (remaining={remaining})")
                    print(f"    Response: {body[:200]}")
                    return None
                else:
                    # Actual rate limit
                    reset = int(e.headers.get("X-RateLimit-Reset", 0))
                    wait = max(0, reset - time.time()) + 1
                    print(f"  Rate limited! Waiting {wait:.0f}s...")
                    time.sleep(wait)
                    return self.get(endpoint)  # retry once
            elif e.code == 404:
                print(f"  WARNING: 404 for {endpoint}")
                return None
            else:
                print(f"  ERROR: HTTP {e.code} for {endpoint}")
                return None
        except Exception as e:
            print(f"  ERROR fetching {endpoint}: {e}")
            return None


def extract_media_urls(body: str) -> list[tuple[str, str]]:
    """Extract media URLs from a PR body. Returns list of (url, type)."""
    if not body:
        return []

    media_urls = []
    seen = set()

    # Pattern 1: <img> tags
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE):
        url = m.group(1)
        if "github.com/user-attachments/assets/" in url and url not in seen:
            media_urls.append((url, "image"))
            seen.add(url)

    # Pattern 2: Markdown image syntax ![alt](url)
    for m in re.finditer(r'!\[[^\]]*\]\(([^)]+)\)', body):
        url = m.group(1)
        if "github.com/user-attachments/assets/" in url and url not in seen:
            media_urls.append((url, "image"))
            seen.add(url)

    # Pattern 3: Bare URLs to user-attachments
    for m in re.finditer(r'(https://github\.com/user-attachments/assets/[a-f0-9-]+)', body):
        url = m.group(1)
        if url not in seen:
            # Could be video or image — we'll determine from Content-Type on download
            media_urls.append((url, "unknown"))
            seen.add(url)

    return media_urls


def enrich_features(features: list[Feature], github: GitHubAPI) -> list[Feature]:
    """Enrich features with GitHub labels and media URLs."""
    print(f"\nStep 2: Enriching {len(features)} features via GitHub API")

    # Collect unique PRs/issues to fetch
    seen_numbers = set()
    pr_data_cache = {}  # number -> API response

    for feat in features:
        for pr_link in feat.pr_links:
            key = (pr_link.repo, pr_link.number)
            if key in seen_numbers:
                continue
            seen_numbers.add(key)

            if pr_link.link_type == "pull":
                endpoint = f"/repos/{pr_link.repo}/pulls/{pr_link.number}"
            else:
                endpoint = f"/repos/{pr_link.repo}/issues/{pr_link.number}"

            # Skip if org is known to be SAML-blocked
            org = pr_link.repo.split("/")[0]
            if org in github._saml_blocked_orgs:
                continue

            print(f"  Fetching {pr_link.repo}#{pr_link.number}...")
            data = github.get(endpoint)
            if data:
                pr_data_cache[key] = data
            time.sleep(0.1)  # Small delay to be polite

    # Now apply enrichment
    for feat in features:
        all_labels = set()
        all_media_urls = []

        for pr_link in feat.pr_links:
            key = (pr_link.repo, pr_link.number)
            data = pr_data_cache.get(key)
            if not data:
                continue

            # Extract labels
            for label in data.get("labels", []):
                name = label.get("name", "")
                all_labels.add(name)

            # Extract media URLs from PR body
            body = data.get("body", "") or ""
            media = extract_media_urls(body)
            all_media_urls.extend(media)

        feat.labels = list(all_labels)

        # Extract Feature:XXX labels as feature tags (e.g. "Streams", "APM")
        for label in all_labels:
            if label.startswith("Feature:"):
                tag = label[len("Feature:"):]
                if tag and tag not in feat.feature_tags:
                    feat.feature_tags.append(tag)

        # Store raw media URLs for download step
        feat._raw_media_urls = all_media_urls

    print(f"  Enriched with {len(pr_data_cache)} API responses")
    return features


# ---------------------------------------------------------------------------
# Step 3: Download media
# ---------------------------------------------------------------------------

def determine_media_type(url: str, content_type: str, final_url: str) -> str:
    """Determine if a URL is an image or video."""
    # Check URL extension
    lower_url = final_url.lower()
    if any(lower_url.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
        return "image"
    if any(lower_url.endswith(ext) for ext in [".mp4", ".mov", ".webm", ".avi"]):
        return "video"

    # Check content type
    if content_type:
        if "image" in content_type:
            return "image"
        if "video" in content_type:
            return "video"

    return "image"  # default assumption


def get_extension(media_type: str, final_url: str) -> str:
    """Get file extension based on media type and URL."""
    lower_url = final_url.lower()
    if media_type == "video":
        if ".mov" in lower_url:
            return ".mov"
        return ".mp4"
    if ".gif" in lower_url:
        return ".gif"
    if ".jpg" in lower_url or ".jpeg" in lower_url:
        return ".jpg"
    return ".png"


def download_media(features: list[Feature], media_dir: str) -> tuple[list[dict], dict]:
    """
    Download media from PR bodies. Returns (download_results, url_mapping).
    Skips re-downloading if file already exists.
    """
    print(f"\nStep 3: Downloading media to {media_dir}/")
    os.makedirs(media_dir, exist_ok=True)

    download_results = []
    url_mapping = {}

    # Load existing results to skip re-downloads
    results_path = os.path.join(media_dir, "download_results.json")
    mapping_path = os.path.join(media_dir, "url_mapping.json")
    existing_files = set()

    if os.path.exists(results_path):
        try:
            with open(results_path) as f:
                old_results = json.load(f)
                for r in old_results:
                    existing_files.add(r["filename"])
                    download_results.append(r)
        except (json.JSONDecodeError, KeyError):
            pass

    if os.path.exists(mapping_path):
        try:
            with open(mapping_path) as f:
                url_mapping = json.load(f)
        except json.JSONDecodeError:
            pass

    for feat in features:
        raw_urls = getattr(feat, '_raw_media_urls', [])
        if not raw_urls:
            continue

        # Use first PR number as identifier
        pr_num = feat.pr_links[0].number if feat.pr_links else 0
        if pr_num == 0:
            continue

        pr_str = str(pr_num)
        if pr_str not in url_mapping:
            url_mapping[pr_str] = {
                "name": feat.title or feat.description[:60],
                "urls": []
            }

        for idx, (url, hint_type) in enumerate(raw_urls, 1):
            filename_base = f"pr-{pr_num}-{idx}"

            # Check if already downloaded
            already_exists = False
            for ext in [".png", ".jpg", ".gif", ".mp4", ".mov"]:
                candidate = filename_base + ext
                if candidate in existing_files or os.path.exists(os.path.join(media_dir, candidate)):
                    already_exists = True
                    # Find the actual file
                    actual_path = os.path.join(media_dir, candidate)
                    if os.path.exists(actual_path):
                        m_type = "video" if ext in [".mp4", ".mov"] else "image"
                        feat.media.append((candidate, m_type))
                        # Ensure URL mapping entry
                        url_entry = [url, m_type]
                        if url_entry not in url_mapping[pr_str]["urls"]:
                            url_mapping[pr_str]["urls"].append(url_entry)
                    break

            if already_exists:
                print(f"  Skipping {filename_base} (already exists)")
                continue

            # Download
            print(f"  Downloading {url[:80]}...")
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (whatsnew-generator)",
                })
                with urllib.request.urlopen(req, timeout=60) as resp:
                    content_type = resp.headers.get("Content-Type", "")
                    final_url = resp.url or url
                    data = resp.read()

                media_type = determine_media_type(url, content_type, final_url)
                if hint_type in ("image", "video"):
                    media_type = hint_type

                ext = get_extension(media_type, final_url)
                filename = filename_base + ext

                filepath = os.path.join(media_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(data)

                size_bytes = len(data)
                if size_bytes >= 1024 * 1024:
                    size_human = f"{size_bytes / (1024*1024):.1f} MB"
                else:
                    size_human = f"{size_bytes / 1024:.1f} KB"

                result = {
                    "pr": pr_num,
                    "index": idx,
                    "url": url,
                    "filename": filename,
                    "content_type": content_type,
                    "media_type": media_type,
                    "size_bytes": size_bytes,
                    "size_human": size_human,
                }
                download_results.append(result)
                feat.media.append((filename, media_type))

                url_mapping[pr_str]["urls"].append([url, media_type])

                print(f"    Saved {filename} ({size_human})")

            except Exception as e:
                print(f"    WARNING: Failed to download: {e}")

            time.sleep(0.2)

    # Also ensure features that already had media from existing files get populated
    # by scanning download_results
    pr_to_media = {}
    for r in download_results:
        pr = r["pr"]
        if pr not in pr_to_media:
            pr_to_media[pr] = []
        pr_to_media[pr].append((r["filename"], r["media_type"]))

    for feat in features:
        if feat.media:
            continue
        for pr_link in feat.pr_links:
            if pr_link.number in pr_to_media:
                feat.media = pr_to_media[pr_link.number]
                break

    # Save results
    with open(results_path, "w") as f:
        json.dump(download_results, f, indent=2)
    with open(mapping_path, "w") as f:
        json.dump(url_mapping, f, indent=2)

    total_new = sum(1 for r in download_results if r["filename"] not in existing_files)
    print(f"  Downloaded {total_new} new files, {len(download_results)} total tracked")

    return download_results, url_mapping


# ---------------------------------------------------------------------------
# Step 4: Map features to sections
# ---------------------------------------------------------------------------

def infer_section_from_keywords(text: str) -> Optional[tuple[str, str]]:
    """Try to infer section from description keywords."""
    lower = text.lower()
    for keywords, section in KEYWORD_SECTION_HINTS:
        if any(kw in lower for kw in keywords):
            return section
    return None


def map_features_to_sections(features: list[Feature]) -> list[Feature]:
    """Assign each feature to a section based on GitHub labels or keywords."""
    print(f"\nStep 4: Mapping {len(features)} features to sections")

    uncategorized = []

    # Lookup section key -> section display name
    section_key_to_name = {key: name for key, name, _, _ in SECTIONS_ORDER}

    for feat in features:
        # Skip features already assigned a section by PM TAG
        if feat.section_key and feat.section_key != "uncategorized":
            # Still derive default feature tags if missing
            if not feat.feature_tags and feat.section_key in _SECTION_DEFAULT_FEATURE_TAG:
                feat.feature_tags = [_SECTION_DEFAULT_FEATURE_TAG[feat.section_key]]
            if not feat.section_name and feat.section_key in section_key_to_name:
                feat.section_name = section_key_to_name[feat.section_key]
            continue

        assigned = False

        # Try label-based assignment (also extracts feature tags from labels)
        for label in feat.labels:
            if label in LABEL_TO_SECTION:
                feat.section_key, feat.section_name = LABEL_TO_SECTION[label]
                # Feature tag already set during GitHub enrichment (Step 2)
                assigned = True
                break

        if not assigned:
            # Try keyword inference
            result = infer_section_from_keywords(feat.description)
            if result:
                feat.section_key, feat.section_name = result
                assigned = True

        # If no feature_tags were set by GitHub API, derive from section mapping
        if not feat.feature_tags and feat.section_key in _SECTION_DEFAULT_FEATURE_TAG:
            feat.feature_tags = [_SECTION_DEFAULT_FEATURE_TAG[feat.section_key]]

        if not assigned:
            uncategorized.append(feat)
            feat.section_key = "uncategorized"
            feat.section_name = "Uncategorized"

    if uncategorized:
        print(f"  WARNING: {len(uncategorized)} features could not be categorized:")
        for f in uncategorized:
            pr_nums = ", ".join(f"#{p.number}" for p in f.pr_links)
            print(f"    - {f.description[:80]}... ({pr_nums})")

    # Count per section
    counts = {}
    for feat in features:
        counts[feat.section_key] = counts.get(feat.section_key, 0) + 1
    for key, count in sorted(counts.items()):
        print(f"  {key}: {count} features")

    return features


# ---------------------------------------------------------------------------
# Step 5: Cross-reference PM highlighted features
# ---------------------------------------------------------------------------

def parse_pm_file(pm_path: str) -> list[dict]:
    """Parse PM features markdown file."""
    print(f"\nStep 5: Reading PM features from {pm_path}")

    if not os.path.exists(pm_path):
        print(f"  WARNING: PM file not found: {pm_path}")
        return []

    with open(pm_path, "r") as f:
        content = f.read()

    # Extract release version from header (e.g. "9.3" from "Elastic Observability 9.3")
    release_ver_match = re.search(r'Observability\s+(\d+\.\d+)', content)
    release_ver = release_ver_match.group(1) + ".0" if release_ver_match else ""

    features = []
    # Split by ## N. headings
    sections = re.split(r'^## \d+\.\s+', content, flags=re.MULTILINE)

    for i, section in enumerate(sections[1:], 1):  # skip header
        lines = section.strip().split('\n')
        name = lines[0].strip()

        # Extract key messages (description)
        key_msg_match = re.search(
            r'\*\*Key Messages:\*\*\s*(.*?)(?=\n-\s+\*\*|\n---|\Z)',
            section, re.DOTALL
        )
        key_messages = ""
        if key_msg_match:
            key_messages = key_msg_match.group(1).strip()
            # Clean up markdown
            key_messages = re.sub(r'\s+', ' ', key_messages).strip()

        # Extract links and PR numbers
        links = []
        pr_links = []  # list of PRLink objects
        pr_numbers = set()
        for line in lines:
            for m in re.finditer(
                r'https://github\.com/(elastic/[\w-]+)/(?:pull|issues)/(\d+)', line
            ):
                repo = m.group(1)
                number = int(m.group(2))
                pr_numbers.add(number)
                url = m.group(0)
                link_type = "pull" if "/pull/" in url else "issue"
                pr_links.append(PRLink(repo=repo, number=number, link_type=link_type, url=url))
            for m in re.finditer(r'(https://github\.com/[^\s)]+)', line):
                links.append(m.group(1))

        # Extract impact
        impact_match = re.search(r'\*\*Impact:\*\*\s*(\w+)', section)
        impact = impact_match.group(1) if impact_match else "Unknown"

        # Extract TAG (section override from PM)
        tag_match = re.search(r'\*\*TAGS?\*\*\s*"([^"]+)"', section)
        tag = tag_match.group(1).strip() if tag_match else ""

        features.append({
            "order": i,
            "name": name,
            "pr_numbers": pr_numbers,
            "pr_links": pr_links,
            "links": links,
            "impact": impact,
            "key_messages": key_messages,
            "version": release_ver,
            "tag": tag,
        })

    print(f"  Parsed {len(features)} PM features (release {release_ver})")
    return features


def _normalize_for_matching(text: str) -> str:
    """Normalize text for fuzzy matching."""
    return re.sub(r'[^a-z0-9 ]', ' ', text.lower()).strip()


def cross_reference_pm(features: list[Feature], pm_features: list[dict]) -> list[Feature]:
    """
    Match PM features to release note features and mark them as highlighted.
    Any PM feature that doesn't match a release note is added as a new Feature,
    so the PM file acts as an authoritative source.
    """
    if not pm_features:
        return features

    # Reverse lookup: section display name -> section key (with short aliases)
    section_name_to_key = {name: key for key, name, _, _ in SECTIONS_ORDER}
    # Add common short aliases
    section_name_to_key.update({
        "APM": "apm",
        "Streams": "streams",
        "AI": "ai-investigations",
        "OTel": "opentelemetry",
    })

    # Build PR number -> feature index mapping
    pr_to_features = {}
    for i, feat in enumerate(features):
        for pr_link in feat.pr_links:
            pr_to_features.setdefault(pr_link.number, []).append(i)

    matched_pm = set()       # PM names that matched a release note
    matched_feat_idxs = set()  # release note indices that were matched
    added_from_pm = 0         # count of features added from PM file (Strategy 3)

    def _apply_pm_tag(feat: Feature, pm: dict):
        """Apply the PM TAG to override feature section if provided."""
        tag = pm.get("tag", "")
        if tag and tag in section_name_to_key:
            feat.section_key = section_name_to_key[tag]

    for pm in pm_features:
        matched = False

        # Strategy 1: Match by PR number
        for pr_num in pm["pr_numbers"]:
            if pr_num in pr_to_features:
                for feat_idx in pr_to_features[pr_num]:
                    features[feat_idx].pm_highlighted = True
                    features[feat_idx].pm_order = pm["order"]
                    features[feat_idx].title = pm["name"]
                    # Upgrade description from PM key messages if richer
                    if pm["key_messages"] and len(pm["key_messages"]) > len(features[feat_idx].description):
                        features[feat_idx].description = pm["key_messages"]
                    _apply_pm_tag(features[feat_idx], pm)
                    matched = True
                    matched_pm.add(pm["name"])
                    matched_feat_idxs.add(feat_idx)

        # Strategy 2: Fuzzy name match if PR numbers didn't match
        if not matched:
            pm_words = set(_normalize_for_matching(pm["name"]).split())
            pm_words -= {"the", "and", "for", "in", "of", "to", "a", "an", "is", "with"}
            if len(pm_words) >= 2:
                best_score = 0
                best_idx = -1
                for i, feat in enumerate(features):
                    # Skip features already claimed by another PM entry
                    if i in matched_feat_idxs:
                        continue
                    feat_text = _normalize_for_matching(feat.description)
                    feat_words = set(feat_text.split())
                    overlap = len(pm_words & feat_words)
                    score = overlap / len(pm_words) if pm_words else 0
                    if score > best_score:
                        best_score = score
                        best_idx = i
                if best_score >= 0.5 and best_idx >= 0:
                    features[best_idx].pm_highlighted = True
                    features[best_idx].pm_order = pm["order"]
                    features[best_idx].title = pm["name"]
                    if pm["key_messages"] and len(pm["key_messages"]) > len(features[best_idx].description):
                        features[best_idx].description = pm["key_messages"]
                    _apply_pm_tag(features[best_idx], pm)
                    matched = True
                    matched_pm.add(pm["name"])
                    matched_feat_idxs.add(best_idx)
                    print(f"  Matched PM \"{pm['name']}\" by name similarity "
                          f"(score={best_score:.0%})")

        # Strategy 3: Not found in release notes — create a new Feature from PM data
        if not matched:
            desc = pm["key_messages"] or pm["name"]
            new_feat = Feature(
                description=desc,
                version=pm.get("version", ""),
                pr_links=pm.get("pr_links", []),
                title=pm["name"],
                pm_highlighted=True,
                pm_order=pm["order"],
            )
            _apply_pm_tag(new_feat, pm)
            features.append(new_feat)
            # Track the new feature's index so later PM entries can't fuzzy-match it
            matched_feat_idxs.add(len(features) - 1)
            added_from_pm += 1
            matched_pm.add(pm["name"])
            print(f"  Added PM feature (not in release notes): \"{pm['name']}\"")

    matched_existing = len(matched_pm) - added_from_pm
    print(f"  {len(matched_pm)}/{len(pm_features)} PM features included "
          f"({matched_existing} matched release notes, "
          f"{added_from_pm} added from PM file)")

    # Derive titles for features that don't have one yet
    for feat in features:
        if not feat.title:
            desc = feat.description
            sentence_end = re.search(r'[.!]', desc)
            if sentence_end and sentence_end.start() < 80:
                feat.title = desc[:sentence_end.start()].strip()
            else:
                feat.title = desc[:80].strip()
                if len(desc) > 80:
                    feat.title += "..."

    return features


# ---------------------------------------------------------------------------
# Step 6: Generate HTML
# ---------------------------------------------------------------------------

def apply_manual_overrides(features: list[Feature]) -> list[Feature]:
    """Apply manual overrides to relocate, rename, or add links to specific features."""
    section_key_to_name = {key: name for key, name, _, _ in SECTIONS_ORDER}

    for override in MANUAL_OVERRIDES:
        for feat in features:
            # Match by description substring or exact title
            matched = False
            if "match" in override:
                matched = override["match"].lower() in feat.description.lower()
            if "match_title" in override and not matched:
                matched = (feat.title == override["match_title"])

            if not matched:
                continue

            if "section_key" in override:
                feat.section_key = override["section_key"]
                feat.section_name = override.get(
                    "section_name", section_key_to_name.get(override["section_key"], ""))
                # Reset feature tags to match new section
                if feat.section_key in _SECTION_DEFAULT_FEATURE_TAG:
                    feat.feature_tags = [_SECTION_DEFAULT_FEATURE_TAG[feat.section_key]]
                else:
                    feat.feature_tags = []
            if "title" in override:
                feat.title = override["title"]
            if "pm_highlighted" in override:
                feat.pm_highlighted = override["pm_highlighted"]
            if "pm_order" in override:
                feat.pm_order = override["pm_order"]
            if "add_links" in override:
                for url, link_type in override["add_links"]:
                    feat.pr_links.append(PRLink(
                        repo="docs", number=0, link_type=link_type, url=url))

            print(f"  Override applied: \"{feat.title}\" → {feat.section_key}")

    return features


def compute_version_badge(features: list[Feature]) -> str:
    """Compute the version badge text (e.g., '9.2 / 9.3') for a set of features."""
    majors = set()
    for f in features:
        parts = f.version.split(".")
        if len(parts) >= 2:
            majors.add(f"{parts[0]}.{parts[1]}")
    return " / ".join(sorted(majors))


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html_module.escape(text)


def render_pr_links(pr_links: list[PRLink]) -> str:
    """Render PR/issue links as HTML."""
    if not pr_links:
        return ""

    parts = []
    for i, pr in enumerate(pr_links):
        if pr.link_type == "docs":
            label = "Docs"
            icon = ISSUE_ICON_SVG
        elif pr.repo == "elastic/elasticsearch":
            label = f"ES#{pr.number}"
            icon = PR_ICON_SVG if pr.link_type == "pull" else ISSUE_ICON_SVG
        elif pr.repo == "elastic/kibana":
            label = f"#{pr.number}"
            icon = PR_ICON_SVG if pr.link_type == "pull" else ISSUE_ICON_SVG
        else:
            # Other repos: use short repo name prefix
            short_repo = pr.repo.replace("elastic/", "")
            label = f"{short_repo}#{pr.number}"
            icon = PR_ICON_SVG if pr.link_type == "pull" else ISSUE_ICON_SVG

        if i == 0:
            # First link gets the icon
            parts.append(
                f'<a href="{escape_html(pr.url)}" class="pr-link" target="_blank">'
                f'{icon} {label}</a>'
            )
        else:
            parts.append(
                f'<a href="{escape_html(pr.url)}" class="pr-link" target="_blank">'
                f'{label}</a>'
            )

    return "\n          ".join(parts)


def render_media(media: list[tuple[str, str]], title: str) -> str:
    """Render media (images/videos) as HTML."""
    if not media:
        return ""

    images = [(f, t) for f, t in media if t == "image"]
    videos = [(f, t) for f, t in media if t == "video"]

    html_parts = ['<div class="feature-media">']

    if len(images) > 1:
        # Multi-image gallery
        html_parts.append('  <div class="media-gallery">')
        for filename, _ in images:
            alt = escape_html(title)
            html_parts.append(
                f'    <img src="media/{filename}" alt="{alt}" onclick="openLightbox(this)">'
            )
        html_parts.append('  </div>')
    elif len(images) == 1:
        filename = images[0][0]
        alt = escape_html(title)
        html_parts.append(
            f'  <img src="media/{filename}" alt="{alt}" onclick="openLightbox(this)">'
        )

    if videos:
        # Show first video only (most relevant)
        filename = videos[0][0]
        html_parts.append(
            f'  <video controls preload="metadata">'
            f'<source src="media/{filename}" type="video/mp4"></video>'
        )

    html_parts.append('</div>')
    return "\n        ".join(html_parts)


def render_feature_card(feat: Feature) -> str:
    """Render a single feature card."""
    tag_class = SECTION_TAG_CLASS.get(feat.section_key, "tag-streams")
    section_display = escape_html(feat.section_name)
    title_display = escape_html(feat.title)

    # Build description - preserve inline code
    desc = feat.description
    # Re-wrap backtick-style code in <code> tags
    desc = re.sub(r'`([^`]+)`', r'<code>\1</code>', desc)
    # If description doesn't have <code> tags already, escape HTML
    if '<code>' not in desc:
        desc = escape_html(desc)

    pr_links_html = render_pr_links(feat.pr_links)
    media_html = render_media(feat.media, feat.title)

    # Render feature tags (e.g. "Streams" from Feature:Streams)
    # Only skip if it exactly matches the displayed section tag
    feature_tags_html = ""
    for ft in feat.feature_tags:
        if ft == section_display:
            continue
        feature_tags_html += f'\n        <span class="feature-tag">{escape_html(ft)}</span>'

    card = f'''    <div class="feature-card">
      <div class="feature-left">
        <div class="feature-name">{title_display}</div>
        <span class="section-tag {tag_class}">{section_display}</span>{feature_tags_html}
        <span class="version-tag">{feat.version}</span>
      </div>
      <div class="feature-right">
        <div class="feature-desc">{desc}</div>
        <div class="feature-meta">
          {pr_links_html}
        </div>'''

    if media_html:
        card += f'''
        {media_html}'''

    card += '''
      </div>
    </div>'''

    return card


def generate_html(features: list[Feature], releases: list[str], output_path: str):
    """Generate the complete HTML page."""
    print(f"\nStep 6: Generating HTML output to {output_path}")

    # Group features by section
    # PM-highlighted features that are uncategorized get placed in the last regular section
    section_features = {}
    for feat in features:
        if feat.section_key == "uncategorized":
            if feat.pm_highlighted:
                # Place PM features we couldn't categorize in the last section
                last_section_key = SECTIONS_ORDER[-1][0]
                feat.section_key = last_section_key
                print(f"  WARNING: PM feature \"{feat.title}\" uncategorized, placing in {last_section_key}")
            else:
                continue
        section_features.setdefault(feat.section_key, []).append(feat)

    # Sort within each section: PM highlighted first (by pm_order), then rest
    for key in section_features:
        section_features[key].sort(key=lambda f: (not f.pm_highlighted, f.pm_order, f.version))

    # Build releases string
    releases_str = ", ".join(sorted(releases, key=lambda v: [int(x) for x in v.split(".")]))

    # Build TOC
    toc_items = []
    for section_key, section_name, tag_class, icon_class in SECTIONS_ORDER:
        feats = section_features.get(section_key, [])
        if not feats:
            continue
        count = len(feats)
        anchor = SECTION_ANCHORS[section_key]
        display_name = escape_html(section_name)
        toc_items.append(
            f'      <li><a href="#{anchor}">{display_name} '
            f'<span class="toc-count">{count}</span></a></li>'
        )

    toc_html = "\n".join(toc_items)

    # Build sections
    sections_html_parts = []
    for section_key, section_name, tag_class, icon_class in SECTIONS_ORDER:
        feats = section_features.get(section_key, [])
        if not feats:
            continue

        version_badge = compute_version_badge(feats)
        anchor = SECTION_ANCHORS[section_key]
        icon_svg = SECTION_ICONS.get(section_key, "")
        display_name = escape_html(section_name)

        cards = "\n\n".join(render_feature_card(f) for f in feats)

        section_html = f'''  <!-- ============================================================ -->
  <!-- {section_name.upper()} -->
  <!-- ============================================================ -->
  <div class="section" id="{anchor}">
    <div class="section-header">
      <div class="section-icon {icon_class}">
        {icon_svg}
      </div>
      <h2>{display_name}</h2>
      <span class="version-badge">{version_badge}</span>
    </div>

{cards}
  </div>'''
        sections_html_parts.append(section_html)

    sections_html = "\n\n".join(sections_html_parts)

    # Assemble full page
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Elastic Observability — What's New</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <style>
    :root {{
      --bg-primary: #0B0B19;
      --bg-secondary: #141428;
      --bg-card: #1A1A35;
      --bg-card-hover: #222247;
      --bg-media: #111125;
      --border: #2A2A4A;
      --border-light: #363660;
      --text-primary: #F5F7FA;
      --text-secondary: #B4B9C8;
      --text-muted: #8B8FA8;
      --elastic-teal: #00BFB3;
      --elastic-blue: #36A2EF;
      --elastic-pink: #F04E98;
      --elastic-green: #00D1A7;
      --elastic-orange: #FF7A59;
      --elastic-purple: #B07CE8;
      --elastic-yellow: #FEC514;
      --radius: 10px;
      --shadow: 0 2px 12px rgba(0,0,0,0.3);
    }}

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.6;
      font-size: 16px;
    }}

    /* ===== Header bar ===== */
    .site-header {{
      background: var(--bg-primary);
      border-bottom: 1px solid var(--border);
      padding: 0 32px;
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .site-header-left {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}
    .elastic-logo svg {{
      height: 28px;
      width: auto;
      display: block;
    }}
    .site-header-nav {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .site-header-nav a {{
      color: var(--text-secondary);
      text-decoration: none;
      font-size: 0.875rem;
      font-weight: 500;
      padding: 6px 14px;
      border-radius: 6px;
      transition: all 0.15s ease;
    }}
    .site-header-nav a:hover {{
      color: var(--text-primary);
      background: rgba(255,255,255,0.06);
    }}
    .site-header-nav a.active {{
      color: var(--text-primary);
      background: rgba(255,255,255,0.08);
    }}

    /* ===== Hero with grid background ===== */
    .hero {{
      position: relative;
      overflow: hidden;
      min-height: 200px;
    }}
    .hero-grid-bg {{
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 100%;
      min-width: 1000px;
      max-width: 1670px;
      height: auto;
      opacity: 0.6;
      pointer-events: none;
      z-index: 0;
    }}
    .hero::after {{
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 50%;
      background: linear-gradient(to bottom, transparent, var(--bg-primary));
      pointer-events: none;
      z-index: 1;
    }}

    /* ===== Page title ===== */
    .page-title {{
      position: relative;
      z-index: 2;
      padding: 48px 32px 32px;
      max-width: 1200px;
      margin: 0 auto;
    }}
    .page-title h1 {{
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text-primary);
      margin-bottom: 8px;
    }}
    .page-title p {{
      font-size: 1rem;
      color: var(--text-secondary);
      max-width: 600px;
      line-height: 1.6;
    }}
    .page-title .releases-covered {{
      font-size: 0.875rem;
      color: var(--text-muted);
      margin-top: 8px;
    }}

    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 24px 80px;
    }}

    /* Table of contents */
    .toc {{
      background: var(--bg-card);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
      padding: 24px 28px;
      margin-bottom: 40px;
    }}
    .toc h2 {{
      font-size: 0.6875rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 14px;
    }}
    .toc-list {{
      list-style: none;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .toc-list a {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 20px;
      text-decoration: none;
      color: var(--elastic-blue);
      font-size: 0.8125rem;
      font-weight: 500;
      transition: all 0.15s ease;
    }}
    .toc-list a:hover {{
      background: rgba(54,162,239,0.1);
      border-color: var(--elastic-blue);
    }}
    .toc-count {{
      background: var(--elastic-blue);
      color: white;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 10px;
    }}

    /* Section headers */
    .section {{
      margin-bottom: 48px;
    }}
    .section-header {{
      display: flex;
      align-items: center;
      gap: 14px;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }}
    .section-icon {{
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .section-header h2 {{
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--text-primary);
    }}
    .section-header .version-badge {{
      background: var(--elastic-pink);
      color: white;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 12px;
      margin-left: auto;
    }}

    /* Feature cards — two-column layout */
    .feature-card {{
      background: var(--bg-card);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      border: 1px solid var(--border);
      margin-bottom: 16px;
      overflow: hidden;
      transition: border-color 0.2s ease;
      display: grid;
      grid-template-columns: 260px 1fr;
    }}
    .feature-card:hover {{
      border-color: var(--border-light);
    }}

    /* Left column: title + section tag */
    .feature-left {{
      padding: 24px 24px;
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .feature-name {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-primary);
      line-height: 1.4;
    }}
    .section-tag {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 12px;
      width: fit-content;
      letter-spacing: 0.02em;
    }}
    .tag-streams {{ background: rgba(54,162,239,0.15); color: var(--elastic-blue); }}
    .tag-infra {{ background: rgba(0,209,167,0.15); color: var(--elastic-green); }}
    .tag-apm {{ background: rgba(255,122,89,0.15); color: var(--elastic-orange); }}
    .tag-digital {{ background: rgba(176,124,232,0.15); color: var(--elastic-purple); }}
    .tag-ai {{ background: rgba(240,78,152,0.15); color: var(--elastic-pink); }}
    .tag-query {{ background: rgba(254,197,20,0.15); color: var(--elastic-yellow); }}
    .tag-otel {{ background: rgba(0,191,179,0.15); color: var(--elastic-teal); }}

    .feature-tag {{
      display: inline-flex;
      align-items: center;
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 12px;
      width: fit-content;
      letter-spacing: 0.02em;
      background: rgba(255,255,255,0.08);
      color: var(--text-secondary);
      border: 1px solid var(--border);
    }}

    .version-tag {{
      display: inline-flex;
      align-items: center;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 10px;
      width: fit-content;
      background: rgba(255,255,255,0.12);
      color: var(--text-secondary);
      border: 1px solid var(--border-light);
    }}

    /* Right column: description + meta + media */
    .feature-right {{
      padding: 24px 28px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .feature-desc {{
      color: var(--text-secondary);
      font-size: 0.875rem;
      line-height: 1.65;
    }}
    .feature-desc code {{
      background: rgba(54,162,239,0.15);
      color: var(--elastic-blue);
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 0.85em;
    }}
    .feature-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    .pr-link {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.82rem;
      text-decoration: none;
      padding: 4px 12px;
      border-radius: 16px;
      font-weight: 500;
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      color: var(--text-muted);
      transition: all 0.15s ease;
    }}
    .pr-link:hover {{
      background: rgba(54,162,239,0.1);
      border-color: var(--elastic-blue);
      color: var(--elastic-blue);
    }}
    .pr-link svg {{
      width: 14px;
      height: 14px;
    }}

    /* Media in right column */
    .feature-media {{
      background: var(--bg-media);
      border-radius: 8px;
      padding: 12px;
      border: 1px solid var(--border);
    }}
    .feature-media img {{
      width: 100%;
      border-radius: 6px;
      display: block;
      border: 1px solid var(--border);
    }}
    .feature-media video {{
      width: 100%;
      border-radius: 6px;
      display: block;
      border: 1px solid var(--border);
      background: #000;
    }}
    .media-gallery {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
    }}
    .media-gallery img {{
      cursor: pointer;
      transition: transform 0.15s ease;
    }}
    .media-gallery img:hover {{
      transform: scale(1.02);
    }}
    .media-caption {{
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 8px;
      text-align: center;
    }}

    /* Lightbox */
    .lightbox {{
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0,0,0,0.9);
      z-index: 1000;
      cursor: pointer;
      align-items: center;
      justify-content: center;
    }}
    .lightbox.active {{
      display: flex;
    }}
    .lightbox img {{
      max-width: 90vw;
      max-height: 90vh;
      border-radius: 8px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.5);
    }}

    /* Section icon colors */
    .icon-logs {{ background: rgba(54,162,239,0.15); color: var(--elastic-blue); }}
    .icon-infra {{ background: rgba(0,209,167,0.15); color: var(--elastic-green); }}
    .icon-apm {{ background: rgba(255,122,89,0.15); color: var(--elastic-orange); }}
    .icon-digital {{ background: rgba(176,124,232,0.15); color: var(--elastic-purple); }}
    .icon-ai {{ background: rgba(240,78,152,0.15); color: var(--elastic-pink); }}
    .icon-query {{ background: rgba(54,162,239,0.15); color: var(--elastic-blue); }}
    .icon-otel {{ background: rgba(0,191,179,0.15); color: var(--elastic-teal); }}

    footer {{
      text-align: center;
      padding: 32px;
      color: var(--text-muted);
      font-size: 0.8125rem;
      border-top: 1px solid var(--border);
    }}

    @media (max-width: 768px) {{
      .site-header {{ padding: 0 16px; height: 56px; }}
      .elastic-logo svg {{ height: 22px; }}
      .site-header-nav a {{ font-size: 0.8125rem; padding: 4px 10px; }}
      .page-title {{ padding: 32px 16px 24px; }}
      .page-title h1 {{ font-size: 1.5rem; }}
      .container {{ padding: 20px 16px 60px; }}
      .feature-card {{ grid-template-columns: 1fr; }}
      .feature-left {{ border-right: none; border-bottom: 1px solid var(--border); padding: 20px; }}
      .feature-right {{ padding: 20px; }}
      .section-header {{ flex-wrap: wrap; }}
      .section-header .version-badge {{ margin-left: 0; }}
      .media-gallery {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<!-- Header -->
<header class="site-header">
  <div class="site-header-left">
    <a href="index.html" class="elastic-logo">
      <svg width="241" height="30" viewBox="0 0 241 30" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path fill-rule="evenodd" clip-rule="evenodd" d="M28.9375 12.2584C29.6367 13.2553 30.0104 14.4441 30.0075 15.6617L30.0058 15.6582C29.9999 16.8809 29.6194 18.0724 28.9156 19.0722C28.2117 20.072 27.2184 20.832 26.0693 21.2499C26.4094 22.1667 26.4412 23.1693 26.1599 24.1058C25.8786 25.0423 25.2996 25.8615 24.5107 26.4392C23.7217 27.017 22.7659 27.3216 21.7882 27.307C20.8105 27.2924 19.8642 26.9594 19.0929 26.3584C18.0504 27.8142 16.5725 28.9013 14.8724 29.463C13.1722 30.0247 11.3376 30.0319 9.63303 29.4836C7.92851 28.9353 6.44212 27.8599 5.38821 26.4124C4.3343 24.9649 3.76734 23.2201 3.76905 21.4295C3.77044 20.8887 3.82242 20.3491 3.92428 19.818C2.77341 19.4076 1.77806 18.6505 1.07528 17.651C0.372492 16.6514 -0.00316662 15.4587 2.01081e-05 14.2368C0.00627077 13.0145 0.386703 11.8233 1.09015 10.8237C1.79359 9.82399 2.7863 9.06373 3.93474 8.64513C3.59351 7.72786 3.56055 6.72436 3.8408 5.78665C4.12106 4.84894 4.69926 4.02809 5.48787 3.44848C6.27645 2.86886 7.23248 2.56204 8.21107 2.57448C9.1897 2.58692 10.1376 2.91796 10.9112 3.51743C11.9598 2.0635 13.4424 0.979507 15.1459 0.421319C16.8494 -0.13687 18.686 -0.140504 20.3917 0.410937C22.0974 0.962383 23.5843 2.0405 24.6386 3.49029C25.693 4.94006 26.2604 6.68683 26.2594 8.47946C26.2593 9.02103 26.2067 9.56131 26.1024 10.0928C27.2482 10.505 28.2384 11.2614 28.9375 12.2584ZM11.7973 12.8746L18.3638 15.8728L24.9915 10.0683C25.0869 9.5894 25.1343 9.1021 25.1327 8.61377C25.1324 7.0327 24.6261 5.49328 23.6878 4.22072C22.7496 2.94817 21.4287 2.00929 19.9184 1.54148C18.4082 1.07367 16.7879 1.10148 15.2946 1.62085C13.8013 2.14021 12.5133 3.12387 11.6193 4.4279L10.5153 10.1381L11.7973 12.8746ZM5.00037 19.8284C4.90357 20.3149 4.85508 20.8097 4.8556 21.3057C4.85564 22.8933 5.36459 24.4391 6.30774 25.7162C7.25089 26.9934 8.57857 27.9345 10.0959 28.4016C11.6133 28.8687 13.2404 28.8371 14.7385 28.3115C16.2366 27.7859 17.5267 26.7939 18.4196 25.4811L19.5132 19.7831L18.0533 16.9925L11.4623 13.9891L5.00037 19.8284ZM9.46012 9.52765L4.96029 8.46548C4.69608 7.74426 4.67257 6.95686 4.89335 6.22116C5.11409 5.48546 5.5672 4.84109 6.18485 4.38447C6.8025 3.92787 7.55142 3.68362 8.31952 3.68829C9.08759 3.69297 9.83351 3.94633 10.4455 4.41042L9.46012 9.52765ZM4.56963 9.53637C3.58231 9.86955 2.72337 10.5021 2.11227 11.3461C1.50115 12.1901 1.16826 13.2035 1.15987 14.2455C1.15916 15.2525 1.46497 16.2359 2.03665 17.0649C2.60834 17.894 3.41881 18.5293 4.36033 18.8866L10.674 13.1798L9.51419 10.7032L4.56963 9.53637ZM21.6952 26.1986C20.9293 26.1945 20.1853 25.9428 19.5742 25.4811L20.5527 20.3883L25.049 21.4348C25.3111 22.1544 25.3334 22.9395 25.1125 23.6729C24.8917 24.4062 24.4395 25.0485 23.8236 25.5037C23.2077 25.9589 22.461 26.2027 21.6952 26.1986ZM20.4881 19.204L25.4379 20.3604C26.4258 20.0281 27.2853 19.3958 27.8965 18.5516C28.5078 17.7074 28.8403 16.6935 28.8477 15.6512C28.8468 14.6463 28.5404 13.6655 27.9691 12.8387C27.3978 12.012 26.5886 11.3786 25.649 11.0224L19.1748 16.6907L20.4881 19.204Z" fill="white"/>
        <path d="M41.9564 21.0004L42.5564 20.9394L42.5983 22.1603C41.2633 22.3619 39.916 22.4726 38.566 22.4917C37.0776 22.4917 36.023 22.0609 35.4021 21.1993C34.7812 20.3377 34.4713 18.997 34.4725 17.1774C34.4725 13.5531 35.9131 11.7403 38.7945 11.7392C40.1895 11.7392 41.2305 12.1287 41.9163 12.9078C42.6024 13.6868 42.9464 14.9077 42.9488 16.5704L42.8669 17.7494H36.044C36.044 18.8936 36.2508 19.7412 36.6649 20.2923C37.0786 20.8435 37.7986 21.119 38.8242 21.119C39.8519 21.1225 40.8959 21.083 41.9564 21.0004ZM41.3983 16.5146C41.3983 15.246 41.1956 14.3501 40.7895 13.8269C40.3838 13.3037 39.7221 13.0415 38.805 13.0403C37.8876 13.0403 37.1979 13.3159 36.7364 13.867C36.2749 14.4182 36.037 15.3007 36.023 16.5146H41.3983Z" fill="white"/>
        <path d="M45.1116 22.4097V8.8056H46.6622V22.4097H45.1116Z" fill="white"/>
        <path d="M56.4275 15.067V20.2819C56.4275 20.8051 57.7144 20.7772 57.7144 20.7772L57.6359 22.1481C56.5461 22.1481 55.6444 22.2388 55.1037 21.7138C53.9327 22.2338 52.6646 22.4984 51.3834 22.4899C50.4335 22.4899 49.7096 22.2207 49.2118 21.6824C48.7144 21.1441 48.466 20.3702 48.4671 19.361C48.4671 18.3541 48.7224 17.6128 49.2328 17.1372C49.7435 16.6617 50.5427 16.371 51.631 16.2652L54.877 15.9565V15.067C54.877 14.3693 54.7256 13.8659 54.4235 13.5566C54.2578 13.4011 54.0624 13.2807 53.8489 13.2028C53.6354 13.1249 53.4084 13.0909 53.1816 13.1031H49.1072V11.7375H53.0787C54.2508 11.7375 55.102 12.0066 55.6322 12.545C56.1624 13.0833 56.4275 13.924 56.4275 15.067ZM50.056 19.2842C50.056 20.5528 50.5793 21.1871 51.6258 21.1871C52.5698 21.186 53.5071 21.025 54.3973 20.7109L54.8717 20.5452V17.1338L51.8177 17.4233C51.1967 17.4791 50.7485 17.6582 50.4729 17.9605C50.1973 18.2628 50.0585 18.7041 50.056 19.2842Z" fill="white"/>
        <path d="M62.4813 13.124C60.9778 13.124 60.226 13.6473 60.226 14.6938C60.226 15.1775 60.4005 15.5187 60.7493 15.7175C61.0981 15.9164 61.8837 16.1233 63.1057 16.3385C64.3336 16.5535 65.2022 16.8535 65.7112 17.2384C66.2205 17.6233 66.4758 18.3465 66.4769 19.4081C66.4769 20.4708 66.1357 21.2499 65.453 21.7452C64.7707 22.2405 63.7748 22.4888 62.4656 22.49C61.6109 22.49 58.7574 22.1725 58.7574 22.1725L58.8412 20.8295C60.4807 20.9865 61.665 21.1034 62.4656 21.1034C63.2662 21.1034 63.8749 20.976 64.2952 20.7214C64.7156 20.4668 64.9249 20.0394 64.9249 19.4395C64.9249 18.8395 64.7505 18.4331 64.3877 18.2186C64.0249 18.0041 63.2435 17.8018 62.0313 17.6081C60.8191 17.4145 59.9557 17.132 59.4464 16.7605C58.9371 16.389 58.6807 15.6983 58.6807 14.692C58.6807 13.6856 59.0295 12.9479 59.7464 12.4595C60.4633 11.9712 61.3423 11.7357 62.4028 11.7357C63.2435 11.7357 66.1612 11.9503 66.1612 11.9503V13.3019C64.6214 13.2339 63.3621 13.124 62.4813 13.124Z" fill="white"/>
        <path d="M73.9503 13.288H70.6629V18.2308C70.6629 19.4157 70.7491 20.1941 70.9211 20.5662C71.0955 20.9395 71.5036 21.1243 72.1507 21.1243L73.9905 21.0005L74.0951 22.2824C73.3985 22.4112 72.6931 22.4876 71.985 22.5109C70.9106 22.5109 70.1665 22.2487 69.7524 21.7243C69.3384 21.1999 69.1322 20.2005 69.1333 18.7261V13.288H67.6716V11.945H69.1402V8.78122H70.6699V11.945H73.9503V13.288Z" fill="white"/>
        <path d="M76.1062 10.6248V8.82483H77.6567V10.6248H76.1062ZM76.1062 22.4097V11.945H77.6567V22.4097H76.1062Z" fill="white"/>
        <path d="M84.3733 11.7375C85.1477 11.7705 85.919 11.8538 86.6826 11.9869L87.1779 12.0479L87.1169 13.3089C86.3065 13.2062 85.4916 13.1445 84.675 13.124C83.5029 13.124 82.7072 13.4031 82.2876 13.9612C81.8676 14.5193 81.6572 15.553 81.6562 17.0622C81.6562 18.5738 81.8526 19.6249 82.2457 20.2156C82.6385 20.8063 83.4583 21.1028 84.7047 21.1051L87.1465 20.9202L87.2093 22.2022C86.2587 22.3632 85.2984 22.4599 84.3349 22.4917C82.7233 22.4917 81.6108 22.0777 80.9969 21.2499C80.3829 20.422 80.0759 19.0267 80.0759 17.064C80.0759 15.1001 80.4066 13.7217 81.0684 12.9287C81.7298 12.1357 82.8314 11.7386 84.3733 11.7375Z" fill="white"/>
      </svg>
    </a>
  </div>
  <nav class="site-header-nav">
    <a href="index.html">Key Capabilities</a>
    <a href="whats-new.html" class="active">What's New</a>
  </nav>
</header>

<!-- Hero with grid background -->
<div class="hero">
  <img src="grid-bg.svg" alt="" class="hero-grid-bg" aria-hidden="true">
  <div class="page-title">
    <h1>What's New in Elastic Observability</h1>
    <p>Latest features and improvements</p>
    <p class="releases-covered">Releases covered: {releases_str}</p>
  </div>
</div>

<div class="container">

  <!-- Table of Contents -->
  <div class="toc">
    <h2>Jump to section</h2>
    <ul class="toc-list">
{toc_html}
    </ul>
  </div>

{sections_html}


</div>

<footer>
  Elastic Observability &mdash; What's New
</footer>

<!-- Lightbox -->
<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <img id="lightbox-img" src="" alt="">
</div>

<script>
function openLightbox(el) {{
  const lb = document.getElementById('lightbox');
  document.getElementById('lightbox-img').src = el.src;
  lb.classList.add('active');
}}
function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('active');
}}
document.addEventListener('keydown', function(e) {{
  if (e.key === 'Escape') closeLightbox();
}});
</script>

</body>
</html>'''

    with open(output_path, "w") as f:
        f.write(full_html)

    # Print summary
    total = sum(len(v) for v in section_features.values())
    print(f"  Generated {output_path} with {total} features across {len(section_features)} sections")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def find_pm_file(base_dir: str) -> Optional[str]:
    """Auto-discover the PM features file."""
    pm_dir = os.path.join(base_dir, "PMhighlightedfeatures")
    if not os.path.isdir(pm_dir):
        return None
    for fname in sorted(os.listdir(pm_dir), reverse=True):
        if fname.startswith("observability-") and fname.endswith("-features.md"):
            return os.path.join(pm_dir, fname)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate What's New HTML page for Elastic Observability"
    )
    parser.add_argument(
        "--releases", required=True,
        help="Comma-separated release versions (e.g., 9.2.0,9.2.2,9.2.3,9.3.0)"
    )
    parser.add_argument(
        "--pm-file", default=None,
        help="Path to PM highlighted features markdown file"
    )
    parser.add_argument(
        "--output", default="whats-new.html",
        help="Output HTML file path (default: whats-new.html)"
    )
    parser.add_argument(
        "--media-dir", default="media",
        help="Directory for media downloads (default: media/)"
    )
    parser.add_argument(
        "--github-token", default=None,
        help="GitHub API token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--skip-github", action="store_true",
        help="Skip GitHub API enrichment (use for offline/testing)"
    )
    parser.add_argument(
        "--skip-media", action="store_true",
        help="Skip media downloads"
    )

    args = parser.parse_args()

    releases = [v.strip() for v in args.releases.split(",")]
    print(f"=== What's New Generator ===")
    print(f"Releases: {releases}")

    # Resolve paths
    base_dir = os.path.dirname(os.path.abspath(args.output)) or "."

    # Step 1: Parse release notes
    features = parse_release_notes(releases)

    if not features:
        print("\nERROR: No features extracted. Check the release notes page structure.")
        print("The page may have changed format. Try running with --skip-github to debug.")
        sys.exit(1)

    # Step 2: Enrich via GitHub API
    if not args.skip_github:
        token = args.github_token or os.environ.get("GITHUB_TOKEN")
        if not token:
            print("\nWARNING: No GitHub token provided. API rate limit is 60 requests/hour.")
            print("  Set GITHUB_TOKEN env var or use --github-token for 5000 requests/hour.")
        github = GitHubAPI(token=token)
        features = enrich_features(features, github)
    else:
        print("\nStep 2: Skipping GitHub API enrichment (--skip-github)")
        for feat in features:
            feat._raw_media_urls = []

    # Step 3: Download media
    if not args.skip_media and not args.skip_github:
        download_media(features, args.media_dir)
    else:
        print(f"\nStep 3: Skipping media downloads")
        # Try to populate media from existing files
        results_path = os.path.join(args.media_dir, "download_results.json")
        if os.path.exists(results_path):
            try:
                with open(results_path) as f:
                    existing = json.load(f)
                pr_to_media = {}
                for r in existing:
                    pr = r["pr"]
                    if pr not in pr_to_media:
                        pr_to_media[pr] = []
                    pr_to_media[pr].append((r["filename"], r["media_type"]))
                for feat in features:
                    for pr_link in feat.pr_links:
                        if pr_link.number in pr_to_media:
                            feat.media = pr_to_media[pr_link.number]
                            break
                print(f"  Loaded existing media mappings for {len(pr_to_media)} PRs")
            except (json.JSONDecodeError, KeyError):
                pass

    # Step 4: Map features to sections
    features = map_features_to_sections(features)

    # Step 5: Cross-reference PM features
    pm_path = args.pm_file
    if not pm_path:
        pm_path = find_pm_file(base_dir)
    if pm_path:
        count_before = len(features)
        pm_features = parse_pm_file(pm_path)
        features = cross_reference_pm(features, pm_features)
        # Re-run section mapping for any newly added PM features
        added = len(features) - count_before
        if added > 0:
            print(f"\n  Re-mapping {added} newly added PM features to sections...")
            features = map_features_to_sections(features)
    else:
        print("\nStep 5: No PM file found, skipping cross-reference")
        # Still derive titles
        for feat in features:
            if not feat.title:
                desc = feat.description
                sentence_end = re.search(r'[.!]', desc)
                if sentence_end and sentence_end.start() < 80:
                    feat.title = desc[:sentence_end.start()].strip()
                else:
                    feat.title = desc[:80].strip()
                    if len(desc) > 80:
                        feat.title += "..."

    # Apply manual overrides (relocations, renames, link additions)
    print("\n  Applying manual overrides...")
    features = apply_manual_overrides(features)

    # Step 6: Generate HTML
    generate_html(features, releases, args.output)

    print(f"\n=== Done! Open {args.output} in a browser to verify. ===")


if __name__ == "__main__":
    main()
