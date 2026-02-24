"""
Context fetcher for LLM enhancement — fetches PR bodies and doc page text.

Reuses GitHubAPI and resolve_github_token() from generate_from_selections.py.
Caches results in liverun/context_cache.json to avoid re-fetching on re-enhance.
"""

import json
import os
import re
import sys
from html.parser import HTMLParser

# Add project root for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from generate_from_selections import GitHubAPI, resolve_github_token, fetch_page

LIVERUN_DIR = os.path.join(PROJECT_ROOT, "liverun")
CACHE_PATH = os.path.join(LIVERUN_DIR, "context_cache.json")


class _TextExtractor(HTMLParser):
    """Simple HTML parser that strips tags and extracts meaningful text."""

    def __init__(self):
        super().__init__()
        self._text_parts = []
        self._skip = False
        self._skip_tags = {"script", "style", "nav", "header", "footer", "noscript", "svg"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self._text_parts.append(text)

    def get_text(self) -> str:
        return " ".join(self._text_parts)


def _load_cache() -> dict:
    """Load the context cache from disk."""
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_cache(cache: dict):
    """Save the context cache to disk."""
    os.makedirs(LIVERUN_DIR, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def fetch_pr_body(repo: str, number: int, link_type: str) -> str:
    """
    Fetch a PR or issue body via GitHub API. Returns empty string on failure.
    Results are cached in context_cache.json.
    """
    cache_key = f"{repo}#{number}"
    cache = _load_cache()

    if cache_key in cache:
        return cache[cache_key].get("body", "")

    token = resolve_github_token()
    if not token:
        return ""

    github = GitHubAPI(token)
    ep_type = "pulls" if link_type == "pull" else "issues"
    endpoint = f"/repos/{repo}/{ep_type}/{number}"

    data = github.get(endpoint)
    body = ""
    if data:
        body = data.get("body", "") or ""

    # Cache the result (even empty ones to avoid re-fetching)
    cache[cache_key] = {"body": body, "repo": repo, "number": number}
    _save_cache(cache)

    return body


def fetch_doc_text(url: str) -> str:
    """
    Fetch a documentation page and extract meaningful text content.
    Results are cached in context_cache.json.
    """
    cache_key = f"doc:{url}"
    cache = _load_cache()

    if cache_key in cache:
        return cache[cache_key].get("text", "")

    html_content = fetch_page(url)
    if not html_content:
        cache[cache_key] = {"text": "", "url": url}
        _save_cache(cache)
        return ""

    extractor = _TextExtractor()
    try:
        extractor.feed(html_content)
    except Exception:
        return ""

    text = extractor.get_text()

    # Cache the result
    cache[cache_key] = {"text": text, "url": url}
    _save_cache(cache)

    return text


def gather_context_for_feature(feature_dict: dict) -> dict:
    """
    Gather PR bodies and doc summaries for a feature.

    Args:
        feature_dict: A feature dict from features.json

    Returns:
        {"pr_bodies": [str, ...], "doc_summaries": [str, ...]}
    """
    pr_bodies = []
    doc_summaries = []

    for link in feature_dict.get("links", []):
        link_type = link.get("link_type", "link")

        if link_type in ("pull", "issue"):
            repo = link.get("repo", "")
            number = link.get("number", 0)
            if repo and number:
                body = fetch_pr_body(repo, number, link_type)
                if body:
                    pr_bodies.append(body)

        elif link_type == "docs":
            url = link.get("url", "")
            if url:
                text = fetch_doc_text(url)
                if text:
                    doc_summaries.append(text)

    return {"pr_bodies": pr_bodies, "doc_summaries": doc_summaries}
