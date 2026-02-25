#!/usr/bin/env python3
"""
Generate What's New page from PM Highlighted Features and Feature Selection files.

This is the standard workflow for creating What's New pages:
  1. Use PMHighlightedFeatures UI to curate PM features → pm-highlighted-features.md
  2. Use FeatureSelection UI to select release note features → selected_features.txt
  3. Run this script to merge, enrich with media, and generate HTML

Usage:
    python3 generate_from_selections.py
    python3 generate_from_selections.py \
        --pm-file PMhighlightedfeatures/pm-highlighted-features.md \
        --selected-file FeatureSelection/selected_features.txt \
        --output whats-new-generated.html

    # Skip GitHub API / media (offline mode):
    python3 generate_from_selections.py --skip-github --skip-media
"""

import argparse
import html as html_module
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration (same as generate_whatsnew.py)
# ---------------------------------------------------------------------------

SECTIONS_ORDER = [
    ("streams", "Log Analytics & Streams", "tag-streams", "icon-logs"),
    ("infrastructure", "Infrastructure Monitoring", "tag-infra", "icon-infra"),
    ("ai-investigations", "Agentic Investigations", "tag-ai", "icon-ai"),
    ("query-analysis", "Query, Analysis & Alerting", "tag-query", "icon-query"),
    ("opentelemetry", "OpenTelemetry", "tag-otel", "icon-otel"),
    ("apm", "Application Performance Monitoring", "tag-apm", "icon-apm"),
    ("digital-experience", "Digital Experience Monitoring", "tag-digital", "icon-digital"),
]

SECTION_NAME_TO_KEY = {name: key for key, name, _, _ in SECTIONS_ORDER}
# Common aliases
SECTION_NAME_TO_KEY.update({
    "APM": "apm",
    "Streams": "streams",
    "AI": "ai-investigations",
    "OTel": "opentelemetry",
})

SECTION_TAG_CLASS = {s[0]: s[2] for s in SECTIONS_ORDER}

_SECTION_DEFAULT_FEATURE_TAG = {
    "streams": "Streams",
    "infrastructure": "Infrastructure Monitoring",
    "ai-investigations": "AI Assistant",
    "query-analysis": "Alerting",
    "opentelemetry": "OpenTelemetry",
    "apm": "APM",
    "digital-experience": "Synthetics",
}

SECTION_ICONS = {
    "streams": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "infrastructure": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>',
    "ai-investigations": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 014 4v1a1 1 0 001 1h1a4 4 0 010 8h-1a1 1 0 00-1 1v1a4 4 0 01-8 0v-1a1 1 0 00-1-1H6a4 4 0 010-8h1a1 1 0 001-1V6a4 4 0 014-4z"/></svg>',
    "query-analysis": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "opentelemetry": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "apm": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "digital-experience": '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
}

PR_ICON_SVG = '<svg viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"/></svg>'
ISSUE_ICON_SVG = '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 9.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/><path fill-rule="evenodd" d="M8 0a8 8 0 100 16A8 8 0 008 0zM1.5 8a6.5 6.5 0 1113 0 6.5 6.5 0 01-13 0z"/></svg>'
DOCS_ICON_SVG = '<svg viewBox="0 0 16 16" fill="currentColor"><path fill-rule="evenodd" d="M2 1.75C2 .784 2.784 0 3.75 0h6.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v9.586A1.75 1.75 0 0113.25 16h-9.5A1.75 1.75 0 012 14.25V1.75zm1.75-.25a.25.25 0 00-.25.25v12.5c0 .138.112.25.25.25h9.5a.25.25 0 00.25-.25V6h-2.75A1.75 1.75 0 019 4.25V1.5H3.75zM10.5 1.62V4.25c0 .138.112.25.25.25h2.63L10.5 1.62z"/></svg>'


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PRLink:
    repo: str
    number: int
    link_type: str  # "pull", "issue", "docs", "link"
    url: str

@dataclass
class Feature:
    description: str
    version: str
    pr_links: list = field(default_factory=list)
    labels: list = field(default_factory=list)
    section_key: str = ""
    section_name: str = ""
    title: str = ""
    feature_tags: list = field(default_factory=list)
    media: list = field(default_factory=list)
    pm_highlighted: bool = False
    pm_order: int = 999
    status: str = ""


# ---------------------------------------------------------------------------
# Step 1: Parse the two input files
# ---------------------------------------------------------------------------

def _extract_pr_links(text: str) -> list[PRLink]:
    """Extract GitHub PR/issue links from text."""
    links = []
    seen = set()
    for m in re.finditer(
        r'(https://github\.com/([\w.-]+/[\w.-]+)/(?:pull|issues)/(\d+))', text
    ):
        url = m.group(1)
        if url in seen:
            continue
        seen.add(url)
        repo = m.group(2)
        number = int(m.group(3))
        link_type = "pull" if "/pull/" in url else "issue"
        links.append(PRLink(repo=repo, number=number, link_type=link_type, url=url))
    return links


def _extract_doc_links(text: str) -> list[PRLink]:
    """Extract non-GitHub documentation links."""
    links = []
    seen = set()
    for m in re.finditer(r'(https?://(?:www\.)?elastic\.co/[^\s,)]+)', text):
        url = m.group(1).rstrip(".,;")
        if url in seen:
            continue
        seen.add(url)
        links.append(PRLink(repo="docs", number=0, link_type="docs", url=url))
    return links


def parse_pm_file(pm_path: str) -> list[Feature]:
    """Parse pm-highlighted-features.md into Feature objects."""
    print(f"\nParsing PM features from {pm_path}")

    with open(pm_path) as f:
        content = f.read()

    # Extract release version
    ver_match = re.search(r'Observability\s+(\d+\.\d+)', content)
    release_ver = ver_match.group(1) if ver_match else ""

    features = []
    sections = re.split(r'^## \d+\.\s+', content, flags=re.MULTILINE)

    for i, section in enumerate(sections[1:], 1):
        lines_text = section.strip()
        first_line = lines_text.split('\n')[0].strip()
        name = first_line

        # Key Messages
        km_match = re.search(
            r'\*\*Key Messages:\*\*\s*(.*?)(?=\n-\s+\*\*|\n---|\Z)',
            lines_text, re.DOTALL
        )
        key_messages = ""
        if km_match:
            key_messages = re.sub(r'\s+', ' ', km_match.group(1)).strip()

        # Status
        status_match = re.search(r'\*\*Status:\*\*\s*(.+)', lines_text)
        status = status_match.group(1).strip() if status_match else ""
        # Normalize: extract just GA or Tech Preview
        if status.upper().startswith("GA"):
            status = "GA"
        else:
            status = "Tech Preview"

        # TAG (section)
        tag_match = re.search(r'\*\*TAGS?\*\*\s*"([^"]+)"', lines_text)
        tag_name = tag_match.group(1).strip() if tag_match else ""
        section_key = SECTION_NAME_TO_KEY.get(tag_name, "")

        # Feature Tags
        ft_match = re.search(r'\*\*Feature Tags:\*\*\s*(.+)', lines_text)
        feature_tags = []
        if ft_match:
            feature_tags = [t.strip() for t in ft_match.group(1).split(",") if t.strip()]

        # Release
        rel_match = re.search(r'\*\*Release:\*\*\s*(.+)', lines_text)
        release = rel_match.group(1).strip() if rel_match else release_ver

        # Links
        pr_links = _extract_pr_links(lines_text)
        doc_links = _extract_doc_links(lines_text)

        feat = Feature(
            description=key_messages or name,
            version=release,
            pr_links=pr_links + doc_links,
            section_key=section_key,
            section_name=tag_name,
            title=name,
            feature_tags=feature_tags if feature_tags else (
                [_SECTION_DEFAULT_FEATURE_TAG[section_key]] if section_key in _SECTION_DEFAULT_FEATURE_TAG else []
            ),
            pm_highlighted=True,
            pm_order=i,
            status=status,
        )
        features.append(feat)

    print(f"  Parsed {len(features)} PM features")
    return features


def parse_selected_features(selected_path: str) -> list[Feature]:
    """Parse selected_features.txt into Feature objects."""
    print(f"\nParsing selected features from {selected_path}")

    with open(selected_path) as f:
        content = f.read()

    features = []
    # Split by ### N. headings
    entries = re.split(r'^### \d+\.\s+', content, flags=re.MULTILINE)

    for entry in entries[1:]:
        lines_text = entry.strip()
        first_line = lines_text.split('\n')[0].strip()

        # Description
        desc_match = re.search(r'\*\*Description:\*\*\s*(.+)', lines_text)
        description = desc_match.group(1).strip() if desc_match else first_line

        # Status
        status_match = re.search(r'\*\*Status:\*\*\s*(.+)', lines_text)
        status = status_match.group(1).strip() if status_match else "GA"
        if status.upper().startswith("GA"):
            status = "GA"
        else:
            status = "Tech Preview"

        # TAG (section)
        tag_match = re.search(r'\*\*TAG:\*\*\s*"([^"]+)"', lines_text)
        tag_name = tag_match.group(1).strip() if tag_match else ""
        section_key = SECTION_NAME_TO_KEY.get(tag_name, "")

        # Release
        rel_match = re.search(r'\*\*Release:\*\*\s*(.+)', lines_text)
        release = rel_match.group(1).strip() if rel_match else ""

        # Feature Tags
        ft_match = re.search(r'\*\*Feature Tags:\*\*\s*(.+)', lines_text)
        feature_tags = []
        if ft_match:
            feature_tags = [t.strip() for t in ft_match.group(1).split(",") if t.strip()]

        # Links
        pr_links = _extract_pr_links(lines_text)
        doc_links = _extract_doc_links(lines_text)

        # Derive title from first line (short description)
        title = first_line
        if len(title) > 80:
            title = title[:80].strip() + "..."

        feat = Feature(
            description=description,
            version=release,
            pr_links=pr_links + doc_links,
            section_key=section_key,
            section_name=tag_name,
            title=title,
            feature_tags=feature_tags if feature_tags else (
                [_SECTION_DEFAULT_FEATURE_TAG[section_key]] if section_key in _SECTION_DEFAULT_FEATURE_TAG else []
            ),
            pm_highlighted=False,
            pm_order=999,
            status=status,
        )
        features.append(feat)

    print(f"  Parsed {len(features)} selected features")
    return features


# ---------------------------------------------------------------------------
# Step 2: Merge and deduplicate
# ---------------------------------------------------------------------------

def merge_features(pm_features: list[Feature], selected_features: list[Feature]) -> list[Feature]:
    """Merge PM and selected features, deduplicating by PR number."""
    print(f"\nMerging {len(pm_features)} PM + {len(selected_features)} selected features")

    # Build set of PR numbers from PM features
    pm_pr_numbers = set()
    for feat in pm_features:
        for pr in feat.pr_links:
            if pr.number > 0:
                pm_pr_numbers.add(pr.number)

    # Start with all PM features
    merged = list(pm_features)

    # Add selected features that don't overlap with PM
    duplicates = 0
    for feat in selected_features:
        feat_pr_nums = {pr.number for pr in feat.pr_links if pr.number > 0}
        if feat_pr_nums & pm_pr_numbers:
            duplicates += 1
            continue
        merged.append(feat)
        # Track the new PR numbers to avoid inter-selected duplicates
        pm_pr_numbers.update(feat_pr_nums)

    print(f"  {duplicates} duplicates removed, {len(merged)} total features")
    return merged


# ---------------------------------------------------------------------------
# Step 3: GitHub API enrichment for media
# ---------------------------------------------------------------------------

class GitHubAPI:
    """Thin wrapper around GitHub REST API."""
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self._saml_blocked_orgs: set[str] = set()

    def get(self, endpoint: str) -> Optional[dict]:
        url = f"https://api.github.com{endpoint}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "whatsnew-from-selections",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                body = e.read().decode("utf-8", errors="replace")
                if "SAML" in body or "SSO" in body:
                    org = endpoint.split("/")[2] if len(endpoint.split("/")) > 2 else ""
                    self._saml_blocked_orgs.add(org)
                    print(f"    SAML/SSO blocked for {org}")
            elif e.code == 404:
                pass
            else:
                print(f"    HTTP {e.code} for {endpoint}")
            return None
        except Exception as e:
            print(f"    Error: {e}")
            return None


def extract_media_urls(body: str) -> list[tuple[str, str]]:
    """Extract image/video URLs from a GitHub PR body."""
    media_urls = []
    seen = set()

    # <img> tags
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE):
        url = m.group(1)
        if "github" in url and url not in seen:
            seen.add(url)
            media_urls.append((url, "image"))

    # Markdown images ![alt](url)
    for m in re.finditer(r'!\[[^\]]*\]\(([^)]+)\)', body):
        url = m.group(1)
        if "github" in url and url not in seen:
            seen.add(url)
            media_urls.append((url, "image"))

    # Video URLs
    for m in re.finditer(
        r'(https://github\.com/user-attachments/assets/[a-f0-9-]+)', body
    ):
        url = m.group(1)
        if url not in seen:
            seen.add(url)
            media_urls.append((url, ""))

    # Private user-content URLs (images uploaded via GitHub UI)
    for m in re.finditer(
        r'(https://private-user-images\.githubusercontent\.com/[^\s)"\']+)', body
    ):
        url = m.group(1)
        if url not in seen:
            seen.add(url)
            media_urls.append((url, "image"))

    return media_urls


def fetch_page(url: str) -> str:
    """Fetch a web page and return its HTML content."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (whatsnew-generator)",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"    Failed to fetch {url}: {e}")
        return ""


def extract_images_from_docs(page_html: str, page_url: str) -> list[tuple[str, str]]:
    """Extract meaningful images from an Elastic docs page."""
    images = []
    seen = set()

    # Resolve base URL for relative paths
    from urllib.parse import urljoin

    # <img> tags
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', page_html, re.IGNORECASE):
        src = m.group(1)
        url = urljoin(page_url, src)

        if url in seen:
            continue
        seen.add(url)

        # Skip tiny UI elements: icons, logos, badges, avatars, svgs
        lower = src.lower()
        skip_patterns = [
            "icon", "logo", "badge", "avatar", "favicon", ".svg",
            "spacer", "pixel", "tracking", "analytics", "1x1",
            "arrow", "caret", "chevron", "spinner", "loader",
        ]
        if any(p in lower for p in skip_patterns):
            continue

        # Check for size hints in the tag — skip very small images
        width_match = re.search(r'width=["\']?(\d+)', m.group(0))
        height_match = re.search(r'height=["\']?(\d+)', m.group(0))
        if width_match and int(width_match.group(1)) < 50:
            continue
        if height_match and int(height_match.group(1)) < 50:
            continue

        # Only include images that look like screenshots or feature illustrations
        if any(ext in lower for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
            images.append((url, "image"))

    return images


def enrich_from_docs(features: list[Feature]):
    """Fetch doc pages to extract images for features without GitHub media."""
    doc_count = 0
    seen_doc_urls: set[str] = set()
    for feat in features:
        if getattr(feat, '_raw_media_urls', []):
            continue
        for pr_link in feat.pr_links:
            if pr_link.link_type != "docs":
                continue
            if pr_link.url in seen_doc_urls:
                continue
            seen_doc_urls.add(pr_link.url)

            print(f"  Fetching docs page: {pr_link.url[:80]}...")
            page_html = fetch_page(pr_link.url)
            if not page_html:
                continue

            doc_images = extract_images_from_docs(page_html, pr_link.url)
            if doc_images:
                feat._raw_media_urls = doc_images
                doc_count += 1
                print(f"    Found {len(doc_images)} image(s)")
            time.sleep(0.3)

    if doc_count:
        print(f"  Extracted images from {doc_count} doc page(s)")


def enrich_with_media(features: list[Feature], github: GitHubAPI):
    """Fetch PR bodies and doc pages to extract media URLs."""
    print(f"\nEnriching {len(features)} features with media")

    seen_prs = set()
    pr_cache: dict[tuple, dict] = {}

    # --- GitHub PR/issue enrichment ---
    for feat in features:
        for pr_link in feat.pr_links:
            if pr_link.link_type not in ("pull", "issue"):
                continue
            key = (pr_link.repo, pr_link.number)
            if key in seen_prs:
                continue
            seen_prs.add(key)

            org = pr_link.repo.split("/")[0]
            if org in github._saml_blocked_orgs:
                continue

            ep_type = "pulls" if pr_link.link_type == "pull" else "issues"
            endpoint = f"/repos/{pr_link.repo}/{ep_type}/{pr_link.number}"
            print(f"  Fetching {pr_link.repo}#{pr_link.number}...")
            data = github.get(endpoint)
            if data:
                pr_cache[key] = data
            time.sleep(0.1)

    # Apply GitHub media URLs to features
    for feat in features:
        all_media = []
        for pr_link in feat.pr_links:
            key = (pr_link.repo, pr_link.number)
            data = pr_cache.get(key)
            if not data:
                continue
            body = data.get("body", "") or ""
            media = extract_media_urls(body)
            all_media.extend(media)

        feat._raw_media_urls = all_media

    print(f"  Fetched {len(pr_cache)} PR/issue bodies")

    # --- Doc page enrichment for features without GitHub media ---
    enrich_from_docs(features)


# ---------------------------------------------------------------------------
# Step 4: Download media
# ---------------------------------------------------------------------------

def determine_media_type(url: str, content_type: str, final_url: str) -> str:
    lower_url = final_url.lower()
    if any(lower_url.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
        return "image"
    if any(lower_url.endswith(ext) for ext in [".mp4", ".mov", ".webm", ".avi"]):
        return "video"
    if content_type:
        if "image" in content_type:
            return "image"
        if "video" in content_type:
            return "video"
    return "image"


def get_extension(media_type: str, final_url: str) -> str:
    lower_url = final_url.lower()
    if media_type == "video":
        return ".mov" if ".mov" in lower_url else ".mp4"
    if ".gif" in lower_url:
        return ".gif"
    if ".jpg" in lower_url or ".jpeg" in lower_url:
        return ".jpg"
    return ".png"


def download_media(features: list[Feature], media_dir: str):
    """Download media from PR bodies into media_dir."""
    print(f"\nDownloading media to {media_dir}/")
    os.makedirs(media_dir, exist_ok=True)

    results_path = os.path.join(media_dir, "download_results.json")
    mapping_path = os.path.join(media_dir, "url_mapping.json")

    download_results = []
    url_mapping = {}
    existing_files = set()

    # Load existing results
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

        # Use PR number if available, otherwise generate a slug from the title
        pr_num = feat.pr_links[0].number if feat.pr_links else 0
        if pr_num > 0:
            feat_key = str(pr_num)
            prefix = f"pr-{pr_num}"
        else:
            # Create a short slug from the feature title for doc-sourced images
            slug = re.sub(r'[^a-z0-9]+', '-', (feat.title or feat.description[:40]).lower()).strip('-')[:30]
            feat_key = f"doc-{slug}"
            prefix = f"doc-{slug}"

        if feat_key not in url_mapping:
            url_mapping[feat_key] = {"name": feat.title or feat.description[:60], "urls": []}

        for idx, (url, hint_type) in enumerate(raw_urls, 1):
            filename_base = f"{prefix}-{idx}"

            # Check if already downloaded
            already_exists = False
            for ext in [".png", ".jpg", ".gif", ".mp4", ".mov"]:
                candidate = filename_base + ext
                if candidate in existing_files or os.path.exists(os.path.join(media_dir, candidate)):
                    already_exists = True
                    actual_path = os.path.join(media_dir, candidate)
                    if os.path.exists(actual_path):
                        m_type = "video" if ext in [".mp4", ".mov"] else "image"
                        feat.media.append((candidate, m_type))
                        url_entry = [url, m_type]
                        if url_entry not in url_mapping[feat_key]["urls"]:
                            url_mapping[feat_key]["urls"].append(url_entry)
                    break

            if already_exists:
                print(f"  Skipping {filename_base} (already exists)")
                continue

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
                size_human = (f"{size_bytes / (1024*1024):.1f} MB" if size_bytes >= 1024 * 1024
                              else f"{size_bytes / 1024:.1f} KB")

                download_results.append({
                    "pr": feat_key, "index": idx, "url": url,
                    "filename": filename, "content_type": content_type,
                    "media_type": media_type, "size_bytes": size_bytes,
                    "size_human": size_human,
                })
                feat.media.append((filename, media_type))
                url_mapping[feat_key]["urls"].append([url, media_type])
                print(f"    Saved {filename} ({size_human})")

            except Exception as e:
                print(f"    WARNING: Failed to download: {e}")

            time.sleep(0.2)

    # Populate media from existing download_results for features that didn't get any
    key_to_media: dict[str, list] = {}
    for r in download_results:
        k = str(r["pr"])
        if k not in key_to_media:
            key_to_media[k] = []
        key_to_media[k].append((r["filename"], r["media_type"]))

    for feat in features:
        if feat.media:
            continue
        # Try PR number keys first
        for pr_link in feat.pr_links:
            if str(pr_link.number) in key_to_media:
                feat.media = key_to_media[str(pr_link.number)]
                break
        # Then try doc slug key
        if not feat.media:
            slug = re.sub(r'[^a-z0-9]+', '-', (feat.title or feat.description[:40]).lower()).strip('-')[:30]
            doc_key = f"doc-{slug}"
            if doc_key in key_to_media:
                feat.media = key_to_media[doc_key]

    # Save tracking files
    with open(results_path, "w") as f:
        json.dump(download_results, f, indent=2)
    with open(mapping_path, "w") as f:
        json.dump(url_mapping, f, indent=2)

    total_new = sum(1 for r in download_results if r["filename"] not in existing_files)
    print(f"  Downloaded {total_new} new files, {len(download_results)} total tracked")


# ---------------------------------------------------------------------------
# Step 5: Generate HTML
# ---------------------------------------------------------------------------

def escape_html(text: str) -> str:
    return html_module.escape(text)


def render_pr_links(pr_links: list[PRLink]) -> str:
    if not pr_links:
        return ""

    parts = []
    for i, pr in enumerate(pr_links):
        if pr.link_type == "docs":
            label = "Docs"
            icon = DOCS_ICON_SVG
        elif pr.repo == "elastic/elasticsearch":
            label = f"ES#{pr.number}"
            icon = PR_ICON_SVG if pr.link_type == "pull" else ISSUE_ICON_SVG
        elif pr.repo == "elastic/kibana":
            label = f"#{pr.number}"
            icon = PR_ICON_SVG if pr.link_type == "pull" else ISSUE_ICON_SVG
        else:
            short_repo = pr.repo.replace("elastic/", "")
            label = f"{short_repo}#{pr.number}" if pr.number else "Link"
            icon = PR_ICON_SVG if pr.link_type == "pull" else ISSUE_ICON_SVG

        if i == 0:
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
    if not media:
        return ""

    images = [(f, t) for f, t in media if t == "image"]
    videos = [(f, t) for f, t in media if t == "video"]

    html_parts = ['<div class="feature-media">']

    if len(images) > 1:
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
        filename = videos[0][0]
        html_parts.append(
            f'  <video controls preload="metadata">'
            f'<source src="media/{filename}" type="video/mp4"></video>'
        )

    html_parts.append('</div>')
    return "\n        ".join(html_parts)


def render_feature_card(feat: Feature) -> str:
    tag_class = SECTION_TAG_CLASS.get(feat.section_key, "tag-streams")
    section_display = escape_html(feat.section_name)
    title_display = escape_html(feat.title)

    desc = feat.description
    desc = re.sub(r'`([^`]+)`', r'<code>\1</code>', desc)
    if '<code>' not in desc:
        desc = escape_html(desc)

    pr_links_html = render_pr_links(feat.pr_links)
    media_html = render_media(feat.media, feat.title)

    feature_tags_html = ""
    for ft in feat.feature_tags:
        if ft == section_display:
            continue
        feature_tags_html += f'\n        <span class="feature-tag">{escape_html(ft)}</span>'

    # Status badge
    status_html = ""
    if feat.status:
        status_class = "status-ga" if feat.status == "GA" else "status-tp"
        status_html = f'\n        <span class="status-tag {status_class}">{escape_html(feat.status)}</span>'

    card = f'''    <div class="feature-card">
      <div class="feature-left">
        <div class="feature-name">{title_display}</div>
        <span class="section-tag {tag_class}">{section_display}</span>{feature_tags_html}{status_html}
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


def compute_version_badge(features: list[Feature]) -> str:
    majors = set()
    for f in features:
        parts = f.version.split(".")
        if len(parts) >= 2:
            majors.add(f"{parts[0]}.{parts[1]}")
    return " / ".join(sorted(majors))


def generate_html(features: list[Feature], output_path: str):
    """Generate the complete HTML page."""
    print(f"\nGenerating HTML to {output_path}")

    # Group by section
    section_features: dict[str, list[Feature]] = {}
    for feat in features:
        if not feat.section_key or feat.section_key == "uncategorized":
            continue
        section_features.setdefault(feat.section_key, []).append(feat)

    # Sort: PM highlighted first (by pm_order), then rest
    for key in section_features:
        section_features[key].sort(key=lambda f: (not f.pm_highlighted, f.pm_order, f.version))

    # Collect all release versions
    all_versions = sorted(
        {f.version for f in features if f.version},
        key=lambda v: [int(x) for x in v.split(".") if x.isdigit()]
    )
    releases_str = ", ".join(all_versions) if all_versions else "9.3"

    # Build TOC
    toc_items = []
    for section_key, section_name, tag_class, icon_class in SECTIONS_ORDER:
        feats = section_features.get(section_key, [])
        if not feats:
            continue
        count = len(feats)
        display_name = escape_html(section_name)
        toc_items.append(
            f'      <li><a href="#{section_key}">{display_name} '
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
        icon_svg = SECTION_ICONS.get(section_key, "")
        display_name = escape_html(section_name)
        cards = "\n\n".join(render_feature_card(f) for f in feats)

        section_html = f'''  <div class="section" id="{section_key}">
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

    # Full page template (same as generate_whatsnew.py)
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

    .status-tag {{
      display: inline-flex;
      align-items: center;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 12px;
      width: fit-content;
      letter-spacing: 0.02em;
    }}
    .status-ga {{
      background: rgba(0,209,167,0.15);
      color: var(--elastic-green);
    }}
    .status-tp {{
      background: rgba(176,124,232,0.15);
      color: var(--elastic-purple);
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
    <a href="whats-new.html" class="active">What's New</a>
  </nav>
</header>

<div class="hero">
  <img src="grid-bg.svg" alt="" class="hero-grid-bg" aria-hidden="true">
  <div class="page-title">
    <h1>What's New in Elastic Observability</h1>
    <p>Latest features and improvements</p>
    <p class="releases-covered">Releases covered: {releases_str}</p>
  </div>
</div>

<div class="container">

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

    total = sum(len(v) for v in section_features.values())
    print(f"  Generated {output_path} with {total} features across {len(section_features)} sections")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_github_token() -> Optional[str]:
    """Try to get GitHub token from env or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate What's New page from PM and Feature Selection files"
    )
    parser.add_argument(
        "--pm-file",
        default="PMhighlightedfeatures/pm-highlighted-features.md",
        help="Path to PM highlighted features markdown (default: PMhighlightedfeatures/pm-highlighted-features.md)"
    )
    parser.add_argument(
        "--selected-file",
        default="FeatureSelection/selected_features.md",
        help="Path to selected features markdown (default: FeatureSelection/selected_features.md)"
    )
    parser.add_argument(
        "--output", default="whats-new-generated.html",
        help="Output HTML file path (default: whats-new-generated.html)"
    )
    parser.add_argument(
        "--media-dir", default="liverun/media",
        help="Directory for media downloads (default: liverun/media/)"
    )
    parser.add_argument(
        "--github-token", default=None,
        help="GitHub API token (or set GITHUB_TOKEN env var, or have gh CLI authenticated)"
    )
    parser.add_argument(
        "--skip-github", action="store_true",
        help="Skip GitHub API enrichment for media"
    )
    parser.add_argument(
        "--skip-media", action="store_true",
        help="Skip media downloads"
    )

    args = parser.parse_args()

    print("=== What's New Generator (from selections) ===")

    # Step 1: Parse input files
    pm_features = []
    if os.path.exists(args.pm_file):
        pm_features = parse_pm_file(args.pm_file)
    else:
        print(f"\nWARNING: PM file not found: {args.pm_file}")

    selected_features = []
    if os.path.exists(args.selected_file):
        selected_features = parse_selected_features(args.selected_file)
    else:
        print(f"\nWARNING: Selected features file not found: {args.selected_file}")

    if not pm_features and not selected_features:
        print("\nERROR: No features found in either file. Nothing to generate.")
        sys.exit(1)

    # Step 2: Merge
    features = merge_features(pm_features, selected_features)

    # Step 3: GitHub API enrichment for media
    if not args.skip_github:
        token = args.github_token or resolve_github_token()
        if not token:
            print("\nWARNING: No GitHub token found. Media enrichment may be limited.")
            print("  Set GITHUB_TOKEN, use --github-token, or authenticate with gh CLI.")
        github = GitHubAPI(token=token)
        enrich_with_media(features, github)
    else:
        print("\nSkipping GitHub API enrichment (--skip-github)")
        for feat in features:
            feat._raw_media_urls = []
        # Still try doc pages for images (no GitHub token needed)
        enrich_from_docs(features)

    # Step 4: Download media
    if not args.skip_media:
        download_media(features, args.media_dir)
    else:
        print("\nSkipping media downloads")
        # Try to populate from existing downloads
        results_path = os.path.join(args.media_dir, "download_results.json")
        if os.path.exists(results_path):
            try:
                with open(results_path) as f:
                    existing = json.load(f)
                key_to_media: dict[str, list] = {}
                for r in existing:
                    k = str(r["pr"])
                    if k not in key_to_media:
                        key_to_media[k] = []
                    key_to_media[k].append((r["filename"], r["media_type"]))
                for feat in features:
                    if feat.media:
                        continue
                    for pr_link in feat.pr_links:
                        if str(pr_link.number) in key_to_media:
                            feat.media = key_to_media[str(pr_link.number)]
                            break
                    if not feat.media:
                        slug = re.sub(r'[^a-z0-9]+', '-', (feat.title or feat.description[:40]).lower()).strip('-')[:30]
                        doc_key = f"doc-{slug}"
                        if doc_key in key_to_media:
                            feat.media = key_to_media[doc_key]
                print(f"  Loaded existing media for {len(key_to_media)} PRs")
            except (json.JSONDecodeError, KeyError):
                pass

    # Step 5: Generate HTML
    generate_html(features, args.output)

    print(f"\n=== Done! Open {args.output} in a browser to verify. ===")


if __name__ == "__main__":
    main()
