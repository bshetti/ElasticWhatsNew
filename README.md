# Elastic Observability — What's New Site

Static site showcasing new features across Elastic Observability releases. Deployed to Netlify.

## Pages

| Page | Description |
|------|-------------|
| `index.html` | Key Capabilities overview (landing page) |
| `whats-new.html` | Auto-generated What's New feature list |

## Prerequisites

- **Python 3.10+**
- **GitHub CLI** (`gh`) installed and authenticated — or set `GITHUB_TOKEN` env var. The token needs SSO authorization for the `elastic` org to fetch PR labels and media.
- **PM features markdown file** — this is a required input that lists the PM-highlighted features with descriptions, links, and section TAGs. See [Generating the PM file](#generating-the-pm-features-file) below.

## Quick start

```bash
# 1. Generate the PM features file from the Release Input Document PDF
#    (skip if you already have the .md file)
./PMhighlightedfeatures/extract_release.sh /path/to/release-input-document.pdf

# 2. Add **TAG** fields to the generated .md file (manual step — see format below)

# 3. Generate the What's New page
./run_generate.sh \
  --releases 9.2.0,9.2.2,9.2.3,9.3.0 \
  --pm-file PMhighlightedfeatures/observability-9.3-features.md
```

## Generating the PM features file

The PM features markdown file is a **required input** for the generator. It lists which features to highlight, their descriptions, and which section they belong to.

### From the Release Input Document PDF

The `PMhighlightedfeatures/` folder contains scripts to extract features from the Elastic Observability Release Input Document PDF:

```bash
# Creates a temp venv, installs pdfplumber, extracts features, cleans up
./PMhighlightedfeatures/extract_release.sh /path/to/release-input-document.pdf

# Or specify output path
./PMhighlightedfeatures/extract_release.sh /path/to/release-input-document.pdf \
  PMhighlightedfeatures/observability-9.4-features.md
```

### Manual edits after extraction

After extraction, you need to:

1. **Review and prune** — remove features that shouldn't appear on the What's New page
2. **Add `**TAG**` fields** — each feature needs a TAG to assign it to a section
3. **Verify links** — ensure GitHub PR/issue links are correct

See [PM features markdown format](#pm-features-markdown-format) for the expected structure.

## Generating the What's New page

### Using the runner script (recommended)

`run_generate.sh` sets up a temporary venv, resolves the GitHub token, runs the generator, and cleans up:

```bash
./run_generate.sh \
  --releases 9.2.0,9.2.2,9.2.3,9.3.0 \
  --pm-file PMhighlightedfeatures/observability-9.3-features.md
```

### Using the Python script directly

`generate_whatsnew.py` has no external dependencies (pure Python stdlib):

```bash
python3 generate_whatsnew.py \
  --releases 9.2.0,9.2.2,9.2.3,9.3.0 \
  --pm-file PMhighlightedfeatures/observability-9.3-features.md \
  --output whats-new-generated.html \
  --github-token "$(gh auth token)"
```

### What the script does

1. **Scrapes release notes** from `elastic.co/docs/release-notes/observability` — extracts only "Features and enhancements" for the requested versions
2. **Enriches via GitHub API** — fetches `Feature:XXX` labels for section categorization and PR body media URLs (images/videos). Falls back to keyword-based categorization if the API is unavailable.
3. **Downloads media** — saves images and videos from PR bodies to `media/` (skips existing files)
4. **Maps features to sections** — uses GitHub labels, then keyword heuristics, then manual overrides
5. **Cross-references PM features** — reads the PM markdown file, matches entries to release notes by PR number or fuzzy name, and adds any unmatched PM features as new cards. The PM file is authoritative.
6. **Generates HTML** — produces the complete page with dark theme, TOC, section headers, feature cards, media, and lightbox

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--releases` | *(required)* | Comma-separated version list (e.g. `9.2.0,9.3.0`) |
| `--pm-file` | `PMhighlightedfeatures/observability-*.md` | PM highlighted features markdown |
| `--output` | `whats-new.html` | Output HTML file path |
| `--media-dir` | `media/` | Directory for downloaded media assets |
| `--github-token` | `$GITHUB_TOKEN` env var | GitHub personal access token |

## PM features markdown format

Each feature in the PM markdown file uses this structure:

```markdown
## 1. Feature Name

- **Key Messages:** Description text...
- **Impact:** Large
- **Status:** GA
- **Owner:** Name
- **Relevant Links:**
  - https://github.com/elastic/kibana/pull/123456
- **TAG** "Log Analytics & Streams"
```

The `**TAG**` field maps the feature to a section. Valid values:

| TAG value | Section |
|-----------|---------|
| `"Log Analytics & Streams"` | Log Analytics & Streams |
| `"Infrastructure Monitoring"` | Infrastructure Monitoring |
| `"Agentic Investigations"` | Agentic Investigations |
| `"Query, Analysis & Alerting"` | Query, Analysis & Alerting |
| `"OpenTelemetry"` | OpenTelemetry |
| `"APM"` | Application Performance Monitoring |
| `"Digital Experience Monitoring"` | Digital Experience Monitoring |

## Manual overrides

The `MANUAL_OVERRIDES` list near the top of `generate_whatsnew.py` allows relocating, renaming, or adding links to specific features without changing the general categorization logic. Each override matches by description substring or exact title. Use this for one-off fixes that don't warrant changing keyword heuristics.

## Deploying to Netlify

```bash
# 1. Generate the page
./run_generate.sh --releases 9.2.0,9.2.2,9.2.3,9.3.0 \
  --pm-file PMhighlightedfeatures/observability-9.3-features.md

# 2. Create the deployment zip
zip -r whatsnew-netlify.zip index.html whats-new.html favicon.svg grid-bg.svg media/ \
  -x "media/download_results.json" "media/url_mapping.json"

# 3. Upload whatsnew-netlify.zip to Netlify
```

## Project structure

```
whatsnew/
  run_generate.sh                    # Runner script (venv + generate)
  generate_whatsnew.py               # Main automation script (pure stdlib)
  index.html                         # Key Capabilities landing page
  whats-new.html                     # Generated What's New page (deploy output)
  whats-new-generated.html           # Working copy of generated output
  favicon.svg                        # Site favicon
  grid-bg.svg                        # Hero background graphic
  media/                             # Downloaded PR images and videos
    pr-243950-1.png                  # Named as pr-{PR_NUMBER}-{INDEX}.{ext}
    download_results.json            # Media download tracking (not deployed)
    url_mapping.json                 # PR-to-media URL mapping (not deployed)
  PMhighlightedfeatures/
    extract_release.sh               # Runner: extracts PM features from PDF (uses venv)
    extract_release_features.py      # PDF extraction script (requires pdfplumber)
    observability-9.3-features.md    # PM input: highlighted features with TAGs
```
