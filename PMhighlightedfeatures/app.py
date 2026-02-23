#!/usr/bin/env python3
"""
PM Highlighted Features UI — Flask app that accepts a Release Input Document PDF,
extracts features, and presents an interactive table for curating "What's New" entries.
"""

import json
import os
import re
import sys
import tempfile
import urllib.request
import urllib.error

from flask import Flask, jsonify, request, send_from_directory

# Import extraction functions from the existing script
sys.path.insert(0, os.path.dirname(__file__))
from extract_release_features import (
    extract_tables_from_pdf,
    extract_release_metadata,
    discover_releases_in_pdf,
    resolve_status,
    resolve_tier,
)

app = Flask(__name__, static_folder="static")

# Max upload size: 500 MB
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

# Cache the uploaded PDF path so we can re-extract for additional releases
_cached_pdf_path: str | None = None

# ---------------------------------------------------------------------------
# Configuration — mirrors FeatureSelection constants
# ---------------------------------------------------------------------------

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
      "bedrock", "function calling", "connector", "system prompt",
      "agentic", "workflow"],
     ("ai-investigations", "Agentic Investigations")),
    (["alert", "query", "discover", "case", "threshold", "rule",
      "api key", "dashboard", "saved quer", "workflow tag", "mute", "snooze",
      "tagging"],
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
# Helpers
# ---------------------------------------------------------------------------

def infer_section(text: str) -> tuple[str, str]:
    """Use keyword heuristics to guess which section a feature belongs to."""
    text_lower = text.lower()
    for keywords, (sec_key, sec_name) in KEYWORD_SECTION_HINTS:
        for kw in keywords:
            if kw in text_lower:
                return sec_key, sec_name
    return "", ""


def try_fetch_github_labels(url: str) -> list[str]:
    """Try to fetch Feature: labels from a GitHub PR/issue URL."""
    match = re.match(
        r"https://github\.com/([\w.-]+/[\w.-]+)/(?:pull|issues)/(\d+)", url
    )
    if not match:
        return []

    repo = match.group(1)
    number = match.group(2)
    is_pr = "/pull/" in url

    # Try to get GitHub token
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        try:
            import subprocess
            result = subprocess.run(
                ["gh", "auth", "token"], capture_output=True, text=True
            )
            if result.returncode == 0:
                token = result.stdout.strip()
        except Exception:
            pass

    if not token:
        return []

    try:
        api_url = (
            f"https://api.github.com/repos/{repo}/"
            f"{'pulls' if is_pr else 'issues'}/{number}"
        )
        req = urllib.request.Request(api_url, headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PMHighlightedFeatures-UI",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            labels = [lbl["name"] for lbl in data.get("labels", [])]
            return [
                lbl.replace("Feature:", "").strip()
                for lbl in labels
                if lbl.startswith("Feature:")
            ]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


def _raw_features_to_ui(raw_features: list[dict], release_number: str, start_id: int = 1) -> list[dict]:
    """Convert raw extracted features into UI-friendly format."""
    features = []
    for i, f in enumerate(raw_features, start_id):
        name = f["name"]
        raw_status = resolve_status(f["status"])
        # Normalize to the two allowed UI values
        status = "GA" if raw_status == "GA" else "Tech Preview"
        tier = resolve_tier(f["tier"])
        key_messages = f["key_messages"]

        # Build links list — only actual URLs
        links = []
        for link in f["links"]:
            if link.startswith("http"):
                link_type = "pull" if "/pull/" in link else (
                    "issue" if "/issues/" in link else "link"
                )
                links.append({
                    "url": link,
                    "type": link_type,
                    "custom": False,
                })

        # Infer section from name + key_messages
        sec_key, sec_name = infer_section(f"{name} {key_messages}")
        feature_tag = SECTION_DEFAULT_FEATURE_TAG.get(sec_key, "")

        features.append({
            "id": i,
            "name": name,
            "status": status,
            "tier": tier,
            "impact": f["impact"],
            "keyMessages": key_messages,
            "links": links,
            "sectionKey": sec_key,
            "sectionName": sec_name,
            "releaseNumber": release_number,
            "featureTags": [feature_tag] if feature_tag else [],
            "include": True,
            "owner": f["owner"],
            "competitive": f["competitive"],
        })
    return features


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Accept PDF upload, extract features for latest release, return JSON."""
    global _cached_pdf_path

    if "pdf" not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400

    pdf_file = request.files["pdf"]
    if not pdf_file.filename or not pdf_file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File must be a PDF"}), 400

    # Clean up previous cached PDF
    if _cached_pdf_path and os.path.exists(_cached_pdf_path):
        try:
            os.unlink(_cached_pdf_path)
        except OSError:
            pass

    # Save to temp file (keep it around for load-releases)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_file.save(tmp.name)
        _cached_pdf_path = tmp.name

    metadata = extract_release_metadata(_cached_pdf_path)

    # Discover all releases in the PDF
    available_releases = discover_releases_in_pdf(_cached_pdf_path)
    latest_release = available_releases[0] if available_releases else metadata.get("release_number", "Unknown")

    # Extract features for the latest release only
    features_by_release = extract_tables_from_pdf(_cached_pdf_path, selected_releases=[latest_release])
    raw_features = features_by_release.get(latest_release, [])

    features = _raw_features_to_ui(raw_features, latest_release)

    return jsonify({
        "features": features,
        "metadata": metadata,
        "sections": SECTIONS,
        "sectionNames": SECTION_NAMES,
        "releaseNumbers": [latest_release],
        "availableReleases": available_releases,
        "latestRelease": latest_release,
    })


@app.route("/api/load-releases", methods=["POST"])
def api_load_releases():
    """Re-extract features for the requested releases from the cached PDF."""
    global _cached_pdf_path

    if not _cached_pdf_path or not os.path.exists(_cached_pdf_path):
        return jsonify({"error": "No PDF uploaded. Please upload a PDF first."}), 400

    data = request.get_json(force=True)
    selected_releases = data.get("releases", [])
    if not selected_releases:
        return jsonify({"error": "No releases specified"}), 400

    metadata = extract_release_metadata(_cached_pdf_path)

    features_by_release = extract_tables_from_pdf(_cached_pdf_path, selected_releases=selected_releases)

    # Merge all selected releases into a flat feature list
    features = []
    fid = 1
    for release_ver in selected_releases:
        raw = features_by_release.get(release_ver, [])
        converted = _raw_features_to_ui(raw, release_ver, start_id=fid)
        features.extend(converted)
        fid += len(converted)

    return jsonify({
        "features": features,
        "metadata": metadata,
        "sections": SECTIONS,
        "sectionNames": SECTION_NAMES,
        "releaseNumbers": selected_releases,
    })


@app.route("/api/enrich-tags", methods=["POST"])
def api_enrich_tags():
    """Try to fetch Feature: labels from GitHub for all links."""
    data = request.get_json(force=True)
    features = data.get("features", [])

    enriched = []
    for f in features:
        tags_found = []
        for link in f.get("links", []):
            url = link.get("url", "")
            labels = try_fetch_github_labels(url)
            tags_found.extend(labels)

        if tags_found:
            existing = set(f.get("featureTags", []))
            for tag in tags_found:
                existing.add(tag)
            enriched.append({
                "id": f["id"],
                "featureTags": list(existing),
            })

    return jsonify({"enriched": enriched})


@app.route("/api/save", methods=["POST"])
def api_save():
    """Save selected features as a markdown file."""
    data = request.get_json(force=True)
    features = data.get("features", [])
    metadata = data.get("metadata", {})
    filename = data.get("filename", "pm-highlighted-features.md")

    selected = [f for f in features if f.get("include")]
    if not selected:
        return jsonify({"error": "No features selected"}), 400

    release = metadata.get("release_number", "Unknown")
    date = metadata.get("release_date", "Unknown")
    freeze = metadata.get("feature_freeze", "Unknown")

    # Group by section
    by_section: dict[str, list[dict]] = {}
    for f in selected:
        key = f.get("sectionName") or "Uncategorized"
        by_section.setdefault(key, []).append(f)

    lines = []
    lines.append(f"# Elastic Observability {release} — PM Highlighted Features\n")
    lines.append(f"Release date: {date}")
    lines.append(f"Feature freeze: {freeze}")
    lines.append("")
    lines.append("---")
    lines.append("")

    order = 0
    for section_name in SECTION_NAMES + ["Uncategorized"]:
        feats = by_section.get(section_name)
        if not feats:
            continue

        for f in feats:
            order += 1
            name = f.get("name", "")
            status = f.get("status", "")
            tier = f.get("tier", "")

            status_str = status
            if tier and tier not in ("", "Standard"):
                status_str += f", {tier}"

            lines.append(f"## {order}. {name}\n")
            lines.append(f"- **Key Messages:** {f.get('keyMessages', '')}")
            lines.append(f"- **Impact:** {f.get('impact', '')}")
            lines.append(f"- **Status:** {status_str}")

            if f.get("competitive"):
                lines.append(
                    f"- **Competitive Differentiator:** {f['competitive']}"
                )

            lines.append(f"- **Owner:** {f.get('owner', '')}")

            feat_links = f.get("links", [])
            if feat_links:
                lines.append("- **Relevant Links:**")
                for link in feat_links:
                    lines.append(f"  - {link.get('url', '')}")
            else:
                lines.append("- **Relevant Links:** (none listed)")

            lines.append(f'- **TAG** "{section_name}"')

            tags = f.get("featureTags", [])
            if tags:
                lines.append(f"- **Feature Tags:** {', '.join(tags)}")

            lines.append(
                f"- **Release:** {f.get('releaseNumber', '')}"
            )
            lines.append("")
            lines.append("---")
            lines.append("")

    output_dir = os.environ.get("OUTPUT_DIR", os.path.dirname(__file__))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "w") as fp:
        fp.write("\n".join(lines))

    return jsonify({
        "saved": len(selected),
        "path": output_path,
        "filename": filename,
    })


if __name__ == "__main__":
    print("Starting PM Highlighted Features UI at http://localhost:5003")
    app.run(port=5003, debug=False)
