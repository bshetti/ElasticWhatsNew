#!/usr/bin/env python3
"""
What's New Orchestrator — Flask app that coordinates the full workflow:
  1. PM Highlighted Features curation (iframe to port 5003)
  2. Release Note Feature Selection (iframe to port 5002)
  3. Merge both sources
  4. Edit the merged feature list
  5. Generate final HTML
"""

import json
import os
import ssl
import sys
import time

# Fix SSL certificates for macOS Python installations missing cert.pem
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

from flask import Flask, jsonify, request, send_from_directory, send_file

# Add project root to path for importing generation scripts
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from generate_from_selections import (
    SECTIONS_ORDER,
    Feature,
    PRLink,
    parse_pm_file,
    parse_selected_features,
    merge_features,
    generate_html,
    enrich_with_media,
    download_media,
    resolve_github_token,
    GitHubAPI,
    SECTION_NAME_TO_KEY,
    _SECTION_DEFAULT_FEATURE_TAG,
)
from generate_md_from_selections import generate_markdown
from validate_links import validate_html_file

app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB max upload

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

LIVERUN_DIR = os.path.join(PROJECT_ROOT, "liverun")
PM_SOURCE = os.path.join(LIVERUN_DIR, "pm-highlighted-features.md")
SELECTED_SOURCE = os.path.join(LIVERUN_DIR, "selected_features.md")
FEATURES_JSON = os.path.join(LIVERUN_DIR, "features.json")
MERGED_MD = os.path.join(LIVERUN_DIR, "whats-new-merged.md")
GENERATED_HTML = os.path.join(LIVERUN_DIR, "whats-new-generated.html")
MEDIA_DIR = os.path.join(LIVERUN_DIR, "media")


# ---------------------------------------------------------------------------
# Feature serialization
# ---------------------------------------------------------------------------

def feature_to_dict(feat: Feature, idx: int) -> dict:
    """Convert a Feature object to a JSON-serializable dict."""
    return {
        "id": idx,
        "title": feat.title,
        "description": feat.description,
        "version": feat.version,
        "section_key": feat.section_key,
        "section_name": feat.section_name,
        "status": feat.status,
        "feature_tags": list(feat.feature_tags),
        "pm_highlighted": feat.pm_highlighted,
        "pm_order": feat.pm_order,
        "include": True,
        "links": [
            {
                "repo": pr.repo,
                "number": pr.number,
                "link_type": pr.link_type,
                "url": pr.url,
            }
            for pr in feat.pr_links
        ],
        "media": [
            {"filename": filename, "media_type": media_type}
            for filename, media_type in feat.media
        ],
        "labels": list(feat.labels),
    }


def dict_to_feature(d: dict) -> Feature:
    """Convert a JSON dict back to a Feature object."""
    return Feature(
        description=d.get("description", ""),
        version=d.get("version", ""),
        pr_links=[
            PRLink(
                repo=l.get("repo", ""),
                number=l.get("number", 0),
                link_type=l.get("link_type", "link"),
                url=l.get("url", ""),
            )
            for l in d.get("links", [])
        ],
        labels=d.get("labels", []),
        section_key=d.get("section_key", ""),
        section_name=d.get("section_name", ""),
        title=d.get("title", ""),
        feature_tags=d.get("feature_tags", []),
        media=[
            (m["filename"], m["media_type"])
            for m in d.get("media", [])
        ],
        pm_highlighted=d.get("pm_highlighted", False),
        pm_order=d.get("pm_order", 999),
        status=d.get("status", ""),
    )


def _save_features_json(features_data: dict):
    """Write features data to features.json."""
    os.makedirs(LIVERUN_DIR, exist_ok=True)
    with open(FEATURES_JSON, "w") as f:
        json.dump(features_data, f, indent=2)


def _load_features_json() -> dict:
    """Load features.json."""
    with open(FEATURES_JSON) as f:
        return json.load(f)


def _regenerate_md(features_data: dict):
    """Regenerate the merged markdown from features data."""
    included = [d for d in features_data["features"] if d.get("include", True)]
    feature_objects = [dict_to_feature(d) for d in included]
    generate_markdown(feature_objects, MERGED_MD)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/status")
def api_status():
    """Check completion status of each step."""
    def file_info(path):
        if os.path.exists(path):
            return {"done": True, "mtime": os.path.getmtime(path)}
        return {"done": False, "mtime": None}

    return jsonify({
        "step1_pm": file_info(PM_SOURCE),
        "step2_rn": file_info(SELECTED_SOURCE),
        "step3_merge": file_info(FEATURES_JSON),
        "step5_generate": file_info(GENERATED_HTML),
    })


@app.route("/api/merge", methods=["POST"])
def api_merge():
    """Step 3: Parse + merge + generate MD + extract & download media."""
    # Check source files exist (both sub-apps save directly to liverun/)
    errors = []
    if not os.path.exists(PM_SOURCE):
        errors.append("PM highlighted features file not found. Complete Step 1 first.")
    if not os.path.exists(SELECTED_SOURCE):
        errors.append("Selected features file not found. Complete Step 2 first.")
    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    # Create directories
    os.makedirs(MEDIA_DIR, exist_ok=True)

    # 1. Parse and merge
    pm_features = parse_pm_file(PM_SOURCE)
    selected_features = parse_selected_features(SELECTED_SOURCE)
    merged = merge_features(pm_features, selected_features)

    pm_count = sum(1 for f in merged if f.pm_highlighted)
    rn_count = len(merged) - pm_count

    # 2. Generate merged markdown FIRST
    generate_markdown(merged, MERGED_MD)

    # 3. Fetch GitHub PR bodies → extract media URLs → download to liverun/media/
    skip_github = request.args.get("skip_github", "").lower() == "true"
    media_count = 0
    if not skip_github:
        token = resolve_github_token()
        if token:
            github = GitHubAPI(token)
            enrich_with_media(merged, github)
            download_media(merged, MEDIA_DIR)
    media_count = sum(len(f.media) for f in merged)

    # 4. Save features.json (with media references) for the Edit step
    features_list = [feature_to_dict(f, i) for i, f in enumerate(merged)]

    features_data = {
        "metadata": {
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "pm_source": "pm-highlighted-features.md",
            "rn_source": "selected_features.md",
            "pm_count": pm_count,
            "rn_count": rn_count,
            "merged_count": len(merged),
            "media_count": media_count,
        },
        "sections": [
            {"key": k, "name": n, "tagClass": tc}
            for k, n, tc, _ in SECTIONS_ORDER
        ],
        "features": features_list,
    }

    _save_features_json(features_data)

    return jsonify({
        "status": "ok",
        "pm_count": pm_count,
        "rn_count": rn_count,
        "merged_count": len(merged),
        "media_count": media_count,
    })


@app.route("/api/features")
def api_get_features():
    """Return features.json for the edit table."""
    if not os.path.exists(FEATURES_JSON):
        return jsonify({"error": "No merged features yet. Run Merge first."}), 404
    return jsonify(_load_features_json())


@app.route("/api/features", methods=["PUT"])
def api_save_features():
    """Save edited features back to features.json and regenerate MD."""
    data = request.get_json(force=True)
    features_data = _load_features_json()
    features_data["features"] = data.get("features", [])
    features_data["metadata"]["last_edited"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    _save_features_json(features_data)
    _regenerate_md(features_data)

    included = sum(1 for f in features_data["features"] if f.get("include", True))
    return jsonify({"saved": len(features_data["features"]), "included": included})


@app.route("/api/media/upload", methods=["POST"])
def api_upload_media():
    """Accept media file upload, save to liverun/media/, update features.json."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    feature_id = request.form.get("feature_id", "0")

    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    # Determine extension and media type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
        media_type = "image"
    elif ext in (".mp4", ".webm", ".mov", ".avi"):
        media_type = "video"
    else:
        return jsonify({"error": f"Unsupported file type: {ext}"}), 400

    # Generate unique filename
    timestamp = int(time.time() * 1000)
    filename = f"upload-{feature_id}-{timestamp}{ext}"
    filepath = os.path.join(MEDIA_DIR, filename)

    os.makedirs(MEDIA_DIR, exist_ok=True)
    file.save(filepath)

    # Update features.json
    if os.path.exists(FEATURES_JSON):
        features_data = _load_features_json()
        fid = int(feature_id)
        for feat in features_data["features"]:
            if feat["id"] == fid:
                feat.setdefault("media", []).append({
                    "filename": filename,
                    "media_type": media_type,
                })
                break
        _save_features_json(features_data)

    return jsonify({
        "filename": filename,
        "media_type": media_type,
        "path": f"/api/media/{filename}",
    })


@app.route("/api/media/<filename>", methods=["DELETE"])
def api_delete_media(filename):
    """Delete a media file and remove from features.json."""
    filepath = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(filepath):
        os.unlink(filepath)

    # Remove from features.json
    if os.path.exists(FEATURES_JSON):
        features_data = _load_features_json()
        for feat in features_data["features"]:
            feat["media"] = [
                m for m in feat.get("media", [])
                if m["filename"] != filename
            ]
        _save_features_json(features_data)

    return jsonify({"deleted": filename})


@app.route("/api/media/<filename>")
def api_serve_media(filename):
    """Serve a media file from liverun/media/."""
    return send_from_directory(MEDIA_DIR, filename)


# Also serve media at /media/ path for HTML preview compatibility
@app.route("/media/<filename>")
def serve_media_compat(filename):
    """Serve media at /media/ path so HTML preview resolves relative paths."""
    return send_from_directory(MEDIA_DIR, filename)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Generate final HTML from features.json."""
    if not os.path.exists(FEATURES_JSON):
        return jsonify({"error": "No features to generate from. Run Merge first."}), 400

    features_data = _load_features_json()
    included = [d for d in features_data["features"] if d.get("include", True)]

    if not included:
        return jsonify({"error": "No features are included. Check at least one feature."}), 400

    feature_objects = [dict_to_feature(d) for d in included]

    # Generate HTML
    generate_html(feature_objects, GENERATED_HTML)

    # Also regenerate MD
    generate_markdown(feature_objects, MERGED_MD)

    return jsonify({
        "status": "ok",
        "feature_count": len(included),
        "html_path": GENERATED_HTML,
    })


@app.route("/api/preview")
def api_preview():
    """Serve the generated HTML for preview."""
    if not os.path.exists(GENERATED_HTML):
        return "<html><body style='background:#0b0e14;color:#e2e8f0;font-family:sans-serif;padding:40px;'>" \
               "<h2>No HTML generated yet</h2><p>Click 'Generate HTML' first.</p></body></html>"
    return send_file(GENERATED_HTML)


@app.route("/api/validate-links", methods=["POST"])
def api_validate_links():
    """Validate links in generated HTML — remove non-public links."""
    if not os.path.exists(GENERATED_HTML):
        return jsonify({"error": "No HTML generated yet. Run Generate first."}), 400

    results = validate_html_file(GENERATED_HTML)

    accessible = sum(1 for r in results if r["accessible"])
    removed = sum(1 for r in results if not r["accessible"])

    return jsonify({
        "status": "ok",
        "total_links": len(results),
        "accessible": accessible,
        "removed": removed,
        "details": results,
    })


@app.route("/api/download/<filename>")
def api_download(filename):
    """Download a file from liverun/."""
    allowed = {"whats-new-generated.html", "whats-new-merged.md", "features.json"}
    if filename not in allowed:
        return jsonify({"error": "File not available for download"}), 404
    filepath = os.path.join(LIVERUN_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    os.makedirs(LIVERUN_DIR, exist_ok=True)
    os.makedirs(MEDIA_DIR, exist_ok=True)
    print("Starting What's New Orchestrator at http://localhost:5001")
    app.run(port=5001, debug=False)
