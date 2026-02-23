#!/usr/bin/env python3
"""
Validate links in generated HTML — remove any that are not publicly accessible.

This checks all <a> links in the generated HTML by making unauthenticated HEAD/GET
requests. Links that require authentication (403, 401) or are otherwise inaccessible
are removed from the HTML.

Usage:
    python3 validate_links.py input.html output.html
    python3 validate_links.py input.html  # overwrites in place

Can also be used as a library:
    from validate_links import validate_and_clean_html
    cleaned_html = validate_and_clean_html(html_string)

NOTE: This is a placeholder implementation using HTTP requests.
      Eventually this will be replaced with an LLM-based link checker.
"""

import os
import re
import ssl
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix SSL certificates for macOS
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass


def check_link_public(url: str, timeout: int = 15) -> dict:
    """
    Check if a URL is publicly accessible without authentication.

    Returns a dict with:
        - url: the URL checked
        - accessible: True if publicly accessible
        - status: HTTP status code or error string
        - reason: human-readable reason if not accessible
    """
    # Skip non-HTTP links, anchors, and media paths
    if not url.startswith("http"):
        return {"url": url, "accessible": True, "status": "skip", "reason": "non-http"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
    }

    # Try HEAD first, fall back to GET
    for method in ["HEAD", "GET"]:
        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return {
                    "url": url,
                    "accessible": True,
                    "status": resp.status,
                    "reason": "ok",
                }
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return {
                    "url": url,
                    "accessible": False,
                    "status": e.code,
                    "reason": f"HTTP {e.code} — requires authentication",
                }
            if e.code == 404:
                return {
                    "url": url,
                    "accessible": False,
                    "status": 404,
                    "reason": "HTTP 404 — not found",
                }
            if e.code in (301, 302, 303, 307, 308):
                # Redirects are usually fine
                return {
                    "url": url,
                    "accessible": True,
                    "status": e.code,
                    "reason": "redirect",
                }
            if method == "HEAD":
                continue  # Some servers reject HEAD, try GET
            return {
                "url": url,
                "accessible": False,
                "status": e.code,
                "reason": f"HTTP {e.code}",
            }
        except urllib.error.URLError as e:
            if method == "HEAD":
                continue
            return {
                "url": url,
                "accessible": False,
                "status": "error",
                "reason": str(e.reason),
            }
        except Exception as e:
            if method == "HEAD":
                continue
            return {
                "url": url,
                "accessible": False,
                "status": "error",
                "reason": str(e),
            }

    return {"url": url, "accessible": False, "status": "error", "reason": "all methods failed"}


def extract_links_from_html(html: str) -> list[str]:
    """Extract all unique href URLs from <a> tags in HTML."""
    pattern = r'<a\s[^>]*href="([^"]+)"[^>]*>'
    urls = re.findall(pattern, html)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for url in urls:
        if url not in seen and url.startswith("http"):
            seen.add(url)
            unique.append(url)
    return unique


def remove_link_from_html(html: str, url: str) -> str:
    """Remove <a> tags with the given href, keeping the link text."""
    # Replace <a href="URL" ...>text</a> with just text
    pattern = re.compile(
        r'<a\s[^>]*href="' + re.escape(url) + r'"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    return pattern.sub(r'\1', html)


def validate_and_clean_html(html: str, max_workers: int = 10) -> tuple[str, list[dict]]:
    """
    Validate all links in the HTML and remove inaccessible ones.

    Returns:
        - cleaned HTML string
        - list of validation results for all links
    """
    urls = extract_links_from_html(html)
    if not urls:
        return html, []

    print(f"\nValidating {len(urls)} links for public accessibility...")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(check_link_public, url): url for url in urls}
        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)
            status = "OK" if result["accessible"] else "REMOVED"
            print(f"  [{status}] {result['url'][:80]} — {result['reason']}")

    # Remove inaccessible links from HTML
    removed_count = 0
    for result in results:
        if not result["accessible"]:
            html = remove_link_from_html(html, result["url"])
            removed_count += 1

    print(f"\nLink validation complete: {len(results)} checked, {removed_count} removed")
    return html, results


def validate_html_file(input_path: str, output_path: str = None) -> list[dict]:
    """
    Validate links in an HTML file and write cleaned version.

    Args:
        input_path: path to the HTML file to validate
        output_path: path to write cleaned HTML (defaults to overwriting input)

    Returns:
        list of validation results
    """
    if output_path is None:
        output_path = input_path

    with open(input_path) as f:
        html = f.read()

    cleaned_html, results = validate_and_clean_html(html)

    with open(output_path, "w") as f:
        f.write(cleaned_html)

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_links.py <input.html> [output.html]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file

    results = validate_html_file(input_file, output_file)

    accessible = sum(1 for r in results if r["accessible"])
    removed = sum(1 for r in results if not r["accessible"])
    print(f"\nSummary: {accessible} accessible, {removed} removed")
