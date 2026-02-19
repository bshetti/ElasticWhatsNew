# Elastic Observability — What's New Site

Static site showcasing new features across Elastic Observability releases. Deployed to Netlify.

## Pages

| Page | Description |
|------|-------------|
| `index.html` | Key Capabilities overview (landing page) |
| `whats-new.html` | Auto-generated What's New feature list |

## Prerequisites

- **Python 3.10+**
- **GitHub CLI** (`gh`) installed and authenticated — or set `GITHUB_TOKEN` env var. The token needs SSO authorization for the `elastic` org to fetch PR media.

## Workflow overview

Generating the What's New page is a **three-step process**. Each step produces an output file that feeds into the next:

```
Step 1: PM Features UI  ──→  pm-highlighted-features.md
Step 2: Feature Selection UI  ──→  selected_features.txt
Step 3: Generate  ──→  whats-new-generated.html
```

---

## Step 1 — Create the PM highlighted features file

Use the **PM Highlighted Features UI** to upload the Release Input Document PDF, review extracted features, assign them to sections (TAGs), set release status (GA / Tech Preview), and curate the list.

```bash
# Launch the PM Highlighted Features UI (runs on http://localhost:5003)
./PMhighlightedfeatures/run_ui.sh
```

This starts a Flask web app that:
1. Lets you upload the Release Input Document PDF
2. Extracts features using `pdfplumber`
3. Provides a UI to review, edit, assign TAGs, and set release status
4. Saves the curated output to `PMhighlightedfeatures/pm-highlighted-features.md`

The script creates a Python virtual environment and installs dependencies automatically.

### Output format

The saved file (`pm-highlighted-features.md`) contains features in this structure:

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

---

## Step 2 — Create the selected features file

Use the **Feature Selection UI** to scan the Elastic Observability release notes, browse features by version, and select which ones to include on the What's New page.

```bash
# Launch the Feature Selection UI (runs on http://localhost:5002)
./FeatureSelection/run.sh
```

This starts a Flask web app that:
1. Scrapes release notes from `elastic.co/docs/release-notes/observability`
2. Displays features grouped by release version
3. Lets you select features and set release status (GA / Tech Preview)
4. Saves the selected features to `FeatureSelection/selected_features.txt`

The script creates a Python virtual environment and installs dependencies automatically.

---

## Step 3 — Generate the What's New page

Once you have both input files from Steps 1 and 2, run the generator to merge them and produce the final HTML page.

```bash
# Generate using default file paths
python3 generate_from_selections.py

# Or specify paths explicitly
python3 generate_from_selections.py \
    --pm-file PMhighlightedfeatures/pm-highlighted-features.md \
    --selected-file FeatureSelection/selected_features.txt \
    --output whats-new-generated.html

# Offline mode (skip GitHub API and media downloads)
python3 generate_from_selections.py --skip-github --skip-media
```

### What the script does

1. **Parses PM features** from `pm-highlighted-features.md` — these are shown first in each section (highlighted)
2. **Parses selected features** from `selected_features.txt` — these are the release note features
3. **Deduplicates** by PR number — PM features take priority over release note features
4. **Fetches media via GitHub API** — extracts images and videos from PR bodies
5. **Downloads media** to `media/` — skips files that already exist locally
6. **Generates HTML** — produces the complete page with dark theme, TOC, section headers, feature cards, media, and lightbox

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--pm-file` | `PMhighlightedfeatures/pm-highlighted-features.md` | PM highlighted features markdown |
| `--selected-file` | `FeatureSelection/selected_features.txt` | Selected release note features |
| `--output` | `whats-new-generated.html` | Output HTML file path |
| `--media-dir` | `media/` | Directory for downloaded media assets |
| `--github-token` | `$GITHUB_TOKEN` env var | GitHub personal access token |
| `--skip-github` | off | Skip GitHub API enrichment for media |
| `--skip-media` | off | Skip media downloads |

### GitHub API & SSO

The `elastic` org repos require SAML/SSO authorization. To fetch media from PR bodies, your GitHub token must have SSO authorization enabled for the `elastic` org. If you don't have this, use `--skip-github --skip-media` — any media files already in `media/` will be reused automatically.

---

## Deploying to Netlify

```bash
# 1. Generate the page (Step 3 above)
python3 generate_from_selections.py

# 2. Copy the generated file to the deploy name
cp whats-new-generated.html whats-new.html

# 3. Create the deployment zip
zip -r whatsnew-netlify.zip index.html whats-new.html favicon.svg grid-bg.svg media/ \
  -x "media/download_results.json" "media/url_mapping.json"

# 4. Upload whatsnew-netlify.zip to Netlify
```

## Project structure

```
whatsnew/
  generate_from_selections.py        # Main generator (merges PM + selected features → HTML)
  generate_whatsnew.py               # Legacy generator (scrapes release notes directly)
  run_generate.sh                    # Legacy runner script
  index.html                         # Key Capabilities landing page
  whats-new.html                     # Generated What's New page (deploy output)
  whats-new-generated.html           # Working copy of generated output
  favicon.svg                        # Site favicon
  grid-bg.svg                        # Hero background graphic
  media/                             # Downloaded PR images and videos
    pr-243950-1.png                  # Named as pr-{PR_NUMBER}-{INDEX}.{ext}
    download_results.json            # Media download tracking (not deployed)
    url_mapping.json                 # PR-to-media URL mapping (not deployed)
  PMhighlightedfeatures/             # Step 1: PM feature curation
    run_ui.sh                        # Launch UI (port 5003)
    app.py                           # Flask app
    extract_release.sh               # CLI alternative: extract features from PDF
    extract_release_features.py      # PDF extraction script (requires pdfplumber)
    pm-highlighted-features.md       # Output: curated PM features with TAGs
    requirements.txt                 # Python dependencies
  FeatureSelection/                  # Step 2: Release note feature selection
    run.sh                           # Launch UI (port 5002)
    app.py                           # Flask app
    selected_features.txt            # Output: selected release note features
    requirements.txt                 # Python dependencies
```
