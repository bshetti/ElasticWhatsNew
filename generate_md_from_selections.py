#!/usr/bin/env python3
"""
Generate What's New page as Markdown from PM Highlighted Features and Feature Selection files.

Same pipeline as generate_from_selections.py (parse → merge → enrich → download media),
but outputs Markdown instead of HTML for easy reviewing and editing.

Usage:
    python3 generate_md_from_selections.py
    python3 generate_md_from_selections.py \
        --pm-file PMhighlightedfeatures/pm-highlighted-features.md \
        --selected-file FeatureSelection/selected_features.txt \
        --output whats-new-generated.md

    # Skip GitHub API / media (offline mode):
    python3 generate_md_from_selections.py --skip-github --skip-media
"""

import argparse
import json
import os
import re
import sys

from generate_from_selections import (
    SECTIONS_ORDER,
    Feature,
    PRLink,
    GitHubAPI,
    parse_pm_file,
    parse_selected_features,
    merge_features,
    enrich_with_media,
    enrich_from_docs,
    download_media,
    resolve_github_token,
)


def generate_markdown(features: list[Feature], output_path: str):
    """Generate the Markdown output file."""
    print(f"\nGenerating Markdown to {output_path}")

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

    lines = []
    lines.append("# What's New in Elastic Observability")
    lines.append(f"Releases covered: {releases_str}")
    lines.append("")

    feature_num = 0
    for section_key, section_name, _, _ in SECTIONS_ORDER:
        feats = section_features.get(section_key, [])
        if not feats:
            continue

        lines.append(f"## {section_name}")
        lines.append("")

        for feat in feats:
            feature_num += 1
            lines.append(f"### {feature_num}. {feat.title}")

            source = "PM Highlighted" if feat.pm_highlighted else "Release Notes"
            lines.append(f"- **Source:** {source}")
            lines.append(f"- **Description:** {feat.description}")
            if feat.status:
                lines.append(f"- **Status:** {feat.status}")
            if feat.feature_tags:
                lines.append(f"- **Tags:** {', '.join(feat.feature_tags)}")
            if feat.version:
                lines.append(f"- **Release:** {feat.version}")

            if feat.pr_links:
                lines.append("- **Links:**")
                for pr in feat.pr_links:
                    if pr.link_type == "docs":
                        lines.append(f"  - [Docs]({pr.url})")
                    elif pr.link_type == "pull":
                        label = f"PR #{pr.number}"
                        lines.append(f"  - [{label}]({pr.url})")
                    elif pr.link_type == "issue":
                        label = f"Issue #{pr.number}"
                        lines.append(f"  - [{label}]({pr.url})")
                    else:
                        lines.append(f"  - [Link]({pr.url})")

            if feat.media:
                lines.append("- **Media:**")
                for filename, media_type in feat.media:
                    lines.append(f"  - `media/{filename}` ({media_type})")

            lines.append("")
            lines.append("---")
            lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    total = sum(len(v) for v in section_features.values())
    print(f"  Generated {output_path} with {total} features across {len(section_features)} sections")


def main():
    parser = argparse.ArgumentParser(
        description="Generate What's New Markdown from PM and Feature Selection files"
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
        "--output", default="whats-new-generated.md",
        help="Output Markdown file path (default: whats-new-generated.md)"
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

    print("=== What's New Markdown Generator (from selections) ===")

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
        enrich_from_docs(features)

    # Step 4: Download media
    if not args.skip_media:
        download_media(features, args.media_dir)
    else:
        print("\nSkipping media downloads")
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

    # Step 5: Generate Markdown
    generate_markdown(features, args.output)

    print(f"\n=== Done! Output written to {args.output} ===")


if __name__ == "__main__":
    main()
