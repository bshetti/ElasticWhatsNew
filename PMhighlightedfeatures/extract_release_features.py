#!/usr/bin/env python3
"""
Extract release features from an Elastic Observability Release Input Document PDF
and output a structured markdown file suitable for Claude Code.

Usage:
    python extract_release_features.py <input.pdf> [output.md]

If output.md is not specified, it writes to the same directory as the input
with the name derived from the PDF filename.

Requirements:
    pip install pdfplumber
"""

import sys
import os
import re
import pdfplumber


def discover_releases_in_pdf(pdf_path):
    """Scan the PDF and return all release version strings in document order.

    Returns a list like ["9.3", "9.2"] where the first is the topmost (latest).
    """
    releases = []
    seen = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            for m in re.finditer(r"Observability (\d+\.\d+)", page_text):
                ver = m.group(1)
                if ver not in seen:
                    seen.add(ver)
                    releases.append(ver)

    return releases


def extract_tables_from_pdf(pdf_path, selected_releases=None):
    """Extract feature tables from the PDF, merging continuation rows.

    Args:
        pdf_path: Path to the PDF file.
        selected_releases: Optional list of release version strings (e.g. ["9.3"])
            to extract. If None, extracts only the first (latest) release
            for backward compatibility.

    Returns:
        A dict mapping release version string to list of feature dicts,
        e.g. {"9.3": [...], "9.2": [...]}.
        Also returns the release order as encountered in the PDF.
    """
    features_by_release: dict[str, list] = {}
    header = None
    current_release = None
    release_order = []

    # If no selection specified, discover and use only the first release
    if selected_releases is None:
        all_releases = discover_releases_in_pdf(pdf_path)
        selected_releases = [all_releases[0]] if all_releases else []

    selected_set = set(selected_releases)

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""

            # Detect release sections (e.g., "Observability 9.3")
            for m in re.finditer(r"Observability (\d+\.\d+)", page_text):
                ver = m.group(1)
                if ver != current_release:
                    current_release = ver
                    if ver not in features_by_release:
                        features_by_release[ver] = []
                        release_order.append(ver)

            # Skip pages for releases we're not interested in
            if current_release not in selected_set:
                continue

            tables = page.extract_tables()
            if not tables:
                continue

            main_table = tables[0]
            rows_list = features_by_release.get(current_release, [])

            for row in main_table:
                # Skip rows that are clearly metadata (single-column rows)
                if len(row) < 5:
                    continue

                if row[0] and "Feature name" in row[0]:
                    # This is the header row — capture it once
                    if header is None:
                        header = [clean(c) for c in row]
                    continue

                # Safe accessor
                def col(idx, _row=row):
                    return _row[idx] if idx < len(_row) and _row[idx] else ""

                # Check if this is a continuation row (no feature name)
                if not col(0) or col(0).strip() == "":
                    # Continuation of previous row — merge key messages and links
                    if rows_list:
                        prev = rows_list[-1]
                        if col(4):
                            prev["key_messages"] += " " + clean(col(4))
                        if col(9):
                            prev["links"].extend(extract_links(col(9)))
                else:
                    # New feature row
                    feature = {
                        "name": clean(col(0)),
                        "tier": clean(col(1)),
                        "status": clean(col(2)),
                        "impact": extract_impact(col(3)),
                        "key_messages": clean(col(4)),
                        "in_toi": clean(col(5)),
                        "in_blog": clean(col(6)),
                        "competitive": clean(col(8)),
                        "links": extract_links(col(9)),
                        "owner": clean(col(10)),
                    }
                    # Skip the blank template row
                    if feature["name"] and "name your" not in feature["name"].lower():
                        rows_list.append(feature)

            features_by_release[current_release] = rows_list

    # Filter to only selected releases that actually had features
    result = {r: features_by_release[r] for r in release_order if r in selected_set and features_by_release.get(r)}
    return result


def extract_release_metadata(pdf_path):
    """Extract release number, date, and other metadata from page 1."""
    metadata = {}
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""

        match = re.search(r"Release number:\s*(.+)", text)
        if match:
            metadata["release_number"] = match.group(1).strip()

        match = re.search(r"Release date:\s*(.+)", text)
        if match:
            metadata["release_date"] = match.group(1).strip()

        match = re.search(r"Feature freeze:\s*(.+)", text)
        if match:
            metadata["feature_freeze"] = match.group(1).strip()

    return metadata


def clean(text):
    """Clean extracted text: normalize whitespace and newlines."""
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    # Remove common PDF extraction artifacts
    text = text.replace("\ue081", "(").replace("\ue082", ")")
    text = text.replace("\ue0a3", "~").replace("\ue0a4", "")
    return text


def extract_impact(text):
    """Pull just the impact level (Large/Medium/Small) from the impact cell."""
    if not text:
        return ""
    text = clean(text)
    for level in ["Large", "Medium", "Small"]:
        if level in text:
            return level
    return text


def extract_links(text):
    """Extract URLs from a cell, reassembling those split across lines."""
    if not text:
        return []

    links = []

    # Split on "https://" to find URL boundaries, then reassemble each
    # URL by removing internal newlines
    parts = re.split(r"(?=https?://)", text)
    for part in parts:
        part = part.strip()
        if part.startswith("http"):
            # This is a URL — remove line breaks within it
            url = part.replace("\n", "").strip()
            # Clean trailing punctuation
            url = url.rstrip(".,;")
            links.append(url)
        elif part and len(part) > 3:
            # Non-URL reference text (e.g., "PRD - Metrics in Discover")
            # Split on double-newlines to separate distinct references
            for ref in re.split(r"\n\n+", part):
                ref = ref.replace("\n", " ").strip()
                if ref and len(ref) > 3:
                    links.append(ref)

    return links


def resolve_status(status_text):
    """Expand abbreviated status values."""
    s = status_text.lower().strip()
    if s.startswith("ga"):
        return "GA"
    elif "te" in s or "tech" in s:
        return "Tech Preview"
    elif "pre" in s or "prev" in s:
        return "Preview"
    elif "beta" in s:
        return "Beta"
    elif "pl" in s:
        return status_text  # Truncated, keep as-is
    return status_text


def resolve_tier(tier_text):
    """Expand abbreviated tier values."""
    t = tier_text.lower().strip()
    if "ent" in t:
        return "Enterprise"
    elif "plat" in t:
        return "Platinum"
    elif "sta" in t:
        return "Standard"
    return tier_text


def features_to_markdown(features, metadata):
    """Convert feature list to a structured markdown document."""
    release = metadata.get("release_number", "Unknown")
    date = metadata.get("release_date", "Unknown")
    freeze = metadata.get("feature_freeze", "Unknown")

    lines = []
    lines.append(f"# Elastic Observability {release} — Release Features\n")
    lines.append(f"Release date: {date}")
    lines.append(f"Feature freeze: {freeze}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, f in enumerate(features, 1):
        lines.append(f"## {i}. {f['name']}\n")
        lines.append(f"- **Key Messages:** {f['key_messages']}")
        lines.append(f"- **Impact:** {f['impact']}")
        lines.append(f"- **Status:** {resolve_status(f['status'])}")

        tier = resolve_tier(f["tier"])
        if tier and tier != "Standard":
            lines.append(f"- **Tier:** {tier}")

        if f["competitive"]:
            lines.append(f"- **Competitive Differentiator:** {f['competitive']}")

        lines.append(f"- **Owner:** {f['owner']}")

        if f["links"]:
            lines.append("- **Relevant Links:**")
            for link in f["links"]:
                lines.append(f"  - {link}")
        else:
            lines.append("- **Relevant Links:** (none listed)")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_release_features.py <input.pdf> [output.md]")
        print()
        print("Extracts features from an Elastic Observability Release Input")
        print("Document PDF and outputs a structured markdown file.")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        # Simplify the filename
        base = re.sub(r"\s*-\s*Google Docs$", "", base)
        base = re.sub(r"[^\w\s-]", "", base)
        base = re.sub(r"\s+", "-", base.strip()).lower()
        output_path = os.path.join(os.path.dirname(pdf_path) or ".", f"{base}-features.md")

    print(f"Reading: {pdf_path}")

    metadata = extract_release_metadata(pdf_path)
    print(f"Release: {metadata.get('release_number', 'Unknown')}")
    print(f"Date: {metadata.get('release_date', 'Unknown')}")

    features_by_release = extract_tables_from_pdf(pdf_path)
    # Flatten all features (CLI mode: only latest release by default)
    features = []
    for ver, feats in features_by_release.items():
        features.extend(feats)
    print(f"Features extracted: {len(features)}")

    md = features_to_markdown(features, metadata)

    # Ensure output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(md)

    print(f"Output: {output_path}")
    print("Done.")


if __name__ == "__main__":
    main()
