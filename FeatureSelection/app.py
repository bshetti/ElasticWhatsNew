#!/usr/bin/env python3
"""
Feature Selection UI — Flask app that scrapes Elastic Observability release
notes and presents an interactive table for curating "What's New" entries.
"""

import html as html_module
import json
import os
import re
import time
import urllib.request
import urllib.error
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")

# ---------------------------------------------------------------------------
# Configuration — mirrors generate_whatsnew.py constants
# ---------------------------------------------------------------------------

RELEASE_NOTES_URL = "https://www.elastic.co/docs/release-notes/observability"

SECTIONS = [
    {"key": "streams", "name": "Log Analytics & Streams", "tagClass": "tag-streams"},
    {"key": "infrastructure", "name": "Infrastructure Monitoring", "tagClass": "tag-infra"},
    {"key": "ai-investigations", "name": "Agentic Investigations", "tagClass": "tag-ai"},
    {"key": "query-analysis", "name": "Query, Analysis & Alerting", "tagClass": "tag-query"},
    {"key": "opentelemetry", "name": "OpenTelemetry", "tagClass": "tag-otel"},
    {"key": "apm", "name": "Application Performance Monitoring", "tagClass": "tag-apm"},
    {"key": "digital-experience", "name": "Digital Experience Monitoring", "tagClass": "tag-digital"},
]

SECTION_NAMES = [s["name"] for s in SECTIONS]
SECTION_KEY_MAP = {s["name"]: s["key"] for s in SECTIONS}

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

SECTION_DEFAULT_FEATURE_TAG = {
    "streams": "Streams",
    "infrastructure": "Infrastructure Monitoring",
    "ai-investigations": "AI Assistant",
    "query-analysis": "Alerting",
    "opentelemetry": "OpenTelemetry",
    "apm": "APM",
    "digital-experience": "Synthetics",
}


# ---------------------------------------------------------------------------
# Scraping helpers
# ---------------------------------------------------------------------------

def fetch_url(url: str, max_retries: int = 3) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (FeatureSelection-UI)"
    })
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(2 ** attempt)
                continue
            raise
        except urllib.error.URLError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    return ""


def discover_versions() -> list[str]:
    """Fetch the release notes page and return all available version strings."""
    page_html = fetch_url(RELEASE_NOTES_URL)
    if not page_html:
        return []

    pattern = re.compile(
        r'id=["\']elastic-observability-(\d+\.\d+\.\d+)-release-notes["\']',
        re.IGNORECASE,
    )
    seen = set()
    versions = []
    for m in pattern.finditer(page_html):
        v = m.group(1)
        if v not in seen:
            seen.add(v)
            versions.append(v)
    return versions


def infer_section(description: str) -> tuple[str, str]:
    """Use keyword heuristics to guess which section a feature belongs to."""
    desc_lower = description.lower()
    for keywords, (sec_key, sec_name) in KEYWORD_SECTION_HINTS:
        for kw in keywords:
            if kw in desc_lower:
                return sec_key, sec_name
    return "", ""


def scrape_features(requested_versions: list[str]) -> list[dict]:
    """Scrape features/enhancements for the given versions."""
    page_html = fetch_url(RELEASE_NOTES_URL)
    if not page_html:
        return []

    # Locate version heading divs
    h2_pattern = re.compile(
        r'<div[^>]*class=["\']heading-wrapper["\'][^>]*id=["\']elastic-observability-(\d+\.\d+\.\d+)-release-notes["\'][^>]*>.*?</div>',
        re.IGNORECASE | re.DOTALL,
    )

    version_sections = []
    for m in h2_pattern.finditer(page_html):
        version_sections.append((m.start(), m.group(1), m.end()))

    if not version_sections:
        fallback = re.compile(
            r'id=["\']elastic-observability-(\d+\.\d+\.\d+)-release-notes["\']',
            re.IGNORECASE,
        )
        for m in fallback.finditer(page_html):
            version_sections.append((m.start(), m.group(1), m.end()))

    # Deduplicate
    seen = set()
    unique = []
    for entry in version_sections:
        if entry[1] not in seen:
            seen.add(entry[1])
            unique.append(entry)
    version_sections = unique

    features = []
    fid = 0

    for i, (start_pos, version, heading_end) in enumerate(version_sections):
        if version not in requested_versions:
            continue

        end_pos = version_sections[i + 1][0] if i + 1 < len(version_sections) else len(page_html)
        section_html = page_html[heading_end:end_pos]

        # Find feature h3 subsection
        h3_wrapper = re.compile(
            r'<div[^>]*class=["\']heading-wrapper["\'][^>]*>.*?<h3[^>]*>(.*?)</h3>.*?</div>',
            re.IGNORECASE | re.DOTALL,
        )
        h3_plain = re.compile(r'<h3[^>]*>(.*?)</h3>', re.IGNORECASE | re.DOTALL)

        all_h3s = []
        for h3m in h3_wrapper.finditer(section_html):
            h3_text = re.sub(r'<[^>]+>', '', h3m.group(1)).strip()
            all_h3s.append((h3m.start(), h3m.end(), h3_text))
        if not all_h3s:
            for h3m in h3_plain.finditer(section_html):
                h3_text = re.sub(r'<[^>]+>', '', h3m.group(1)).strip()
                all_h3s.append((h3m.start(), h3m.end(), h3_text))

        feat_section = ""
        for idx, (h3_start, h3_end, h3_text) in enumerate(all_h3s):
            h3_lower = h3_text.lower()
            if "fix" in h3_lower or "deprecat" in h3_lower:
                continue
            if "feature" in h3_lower or "enhancement" in h3_lower:
                next_start = all_h3s[idx + 1][0] if idx + 1 < len(all_h3s) else len(section_html)
                feat_section = section_html[h3_end:next_start]
                break

        if not feat_section:
            continue

        li_pattern = re.compile(r'<li[^>]*>(.*?)</li>', re.DOTALL | re.IGNORECASE)
        for li_match in li_pattern.finditer(feat_section):
            li_html = li_match.group(1)

            # Strip PR link anchors from description text
            li_text_html = re.sub(
                r',?\s*<a[^>]*href=["\']https://github\.com/elastic/[^"\']+["\'][^>]*>#?\d+</a>',
                '', li_html,
            )
            li_text_html = re.sub(
                r',?\s*<a[^>]*href=["\']https://github\.com/elastic/[^"\']+["\'][^>]*>ES#\d+</a>',
                '', li_text_html,
            )

            text = re.sub(r'<[^>]+>', '', li_text_html).strip()
            text = html_module.unescape(text)
            text = re.sub(r'[,\s]+#\d+(?:[,\s]+#\d+)*\s*$', '', text)
            text = re.sub(r'[,\s]+ES#\d+(?:[,\s]+ES#\d+)*\s*$', '', text)
            text = re.sub(r'\s+', ' ', text).strip()

            if not text:
                continue

            # Extract PR/issue links
            link_pattern = re.compile(
                r'href=["\']?(https://github\.com/(elastic/(?:kibana|elasticsearch))/(?:pull|issues)/(\d+))["\']?'
            )
            links = []
            for lm in link_pattern.finditer(li_html):
                links.append({
                    "url": lm.group(1),
                    "repo": lm.group(2),
                    "number": int(lm.group(3)),
                    "type": "pull" if "/pull/" in lm.group(1) else "issue",
                })

            if not links and len(text) <= 20:
                continue

            # Infer section/tags
            sec_key, sec_name = infer_section(text)
            feature_tag = SECTION_DEFAULT_FEATURE_TAG.get(sec_key, "")

            fid += 1
            features.append({
                "id": fid,
                "description": text,
                "version": version,
                "links": links,
                "sectionKey": sec_key,
                "sectionName": sec_name,
                "releaseTag": version,
                "featureTag": feature_tag,
                "status": "Tech Preview",
                "addToWhatsNew": False,
            })

    return features


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/versions")
def api_versions():
    versions = discover_versions()
    return jsonify(versions)


@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json(force=True)
    versions = data.get("versions", [])
    if not versions:
        return jsonify({"error": "No versions specified"}), 400

    features = scrape_features(versions)
    return jsonify({
        "features": features,
        "sections": SECTIONS,
        "sectionNames": SECTION_NAMES,
    })


@app.route("/api/save", methods=["POST"])
def api_save():
    """Save selected features as a structured text file for the whatsnew generator."""
    data = request.get_json(force=True)
    features = data.get("features", [])
    selected = [f for f in features if f.get("addToWhatsNew")]

    if not selected:
        return jsonify({"error": "No features selected"}), 400

    # Group by section for readable output
    by_section: dict[str, list[dict]] = {}
    for f in selected:
        key = f.get("sectionName") or "Uncategorized"
        by_section.setdefault(key, []).append(f)

    # Header lines shared by both formats
    header = [
        "# Selected Features for What's New Page",
        "# Generated from FeatureSelection UI",
        f"# Releases scanned: {', '.join(sorted({f['releaseTag'] for f in selected}))}",
        f"# Total features selected: {len(selected)}",
        "",
    ]

    lines = list(header)       # .txt format (with === separators)
    md_lines = list(header)    # .md format (clean markdown)

    order = 0
    for section_name in [s["name"] for s in SECTIONS] + ["Uncategorized"]:
        feats = by_section.get(section_name)
        if not feats:
            continue

        lines.append(f"{'=' * 60}")
        lines.append(f"## {section_name}")
        lines.append(f"{'=' * 60}")
        lines.append("")

        md_lines.append(f"## {section_name}")
        md_lines.append("")

        for f in feats:
            order += 1
            feature_lines = []
            feature_lines.append(f"### {order}. {f['description'][:120]}")
            feature_lines.append("")
            feature_lines.append(f"- **Description:** {f['description']}")

            if f.get("links"):
                links_str = ", ".join(
                    f"{l['url']}" for l in f["links"]
                )
                feature_lines.append(f"- **Links:** {links_str}")

            feature_lines.append(f"- **Status:** {f.get('status', 'Tech Preview')}")
            feature_lines.append(f"- **TAG:** \"{section_name}\"")
            feature_lines.append(f"- **Release:** {f.get('releaseTag', '')}")

            # Support both featureTags (array) and legacy featureTag (string)
            tags = f.get("featureTags", [])
            if not tags and f.get("featureTag"):
                tags = [f["featureTag"]]
            feature_lines.append(f"- **Feature Tags:** {', '.join(tags)}")
            feature_lines.append("")

            lines.extend(feature_lines)
            md_lines.extend(feature_lines)

    output_path_txt = os.path.join(os.path.dirname(__file__), "selected_features.txt")
    output_path_md = os.path.join(os.path.dirname(__file__), "selected_features.md")
    with open(output_path_txt, "w") as fp:
        fp.write("\n".join(lines))
    with open(output_path_md, "w") as fp:
        fp.write("\n".join(md_lines))

    return jsonify({"saved": len(selected), "path": output_path_md})


if __name__ == "__main__":
    print("Starting Feature Selection UI at http://localhost:5002")
    app.run(port=5002)
