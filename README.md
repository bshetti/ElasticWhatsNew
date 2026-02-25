# Elastic Observability — What's New Site

Static site showcasing new features across Elastic Observability releases. Deployed to Netlify.

## Pages

| Page | Description |
|------|-------------|
| `index.html` | Key Capabilities overview (landing page) |
| `whats-new.html` | Auto-generated What's New feature list |

## Prerequisites

- **Python 3.10+**
- **GitHub token** with SSO authorization for the `elastic` org (see [GitHub Token Setup](#github-token-setup) below)
- **(Optional) LLM API key** for AI-powered feature description enhancement (see [LLM Enhancement Setup](#llm-enhancement-setup) below)

## GitHub Token Setup

The orchestrator needs a GitHub Personal Access Token with SSO authorization for the `elastic` org to fetch PR media (images/videos).

1. Create a token at https://github.com/settings/tokens (needs `repo` scope)
2. Enable SSO: click **"Configure SSO"** next to the token → **"Authorize"** for `elastic`
3. Save the token to `.git-token/github.token` in the project root:

```bash
mkdir -p .git-token
echo "ghp_your_token_here" > .git-token/github.token
```

The `.git-token/` directory is in `.gitignore` and will never be committed. If no token is provided, the orchestrator will still work but media extraction from GitHub PRs will be skipped.

## LLM Enhancement Setup

The orchestrator includes an optional **Enhance** feature that uses an LLM to rewrite feature titles and descriptions into polished, user-facing copy. It gathers context from linked PRs/issues and documentation pages, then sends it to the LLM for rewriting.

This feature uses [litellm](https://github.com/BerriAI/litellm) for provider flexibility. Set one of the following API key environment variables before launching the orchestrator:

```bash
# Anthropic (default model: anthropic/claude-haiku-4-5-20251001)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Google Gemini
export GEMINI_API_KEY="..."
```

To change the model, set the `LLM_MODEL` environment variable:

```bash
# Examples
export LLM_MODEL="anthropic/claude-sonnet-4-5-20250929"
export LLM_MODEL="openai/gpt-4o"
export LLM_MODEL="gemini/gemini-2.0-flash"
export LLM_MODEL="ollama/llama3"   # local models via Ollama
```

If no API key is set, the orchestrator still works — the enhance buttons will simply be disabled.

## Workflow overview

The recommended way to generate the What's New page is via the **Orchestrator**, which provides a unified UI for the full 5-step workflow:

```
Step 1: PM Features UI       ──→  pm-highlighted-features.md
Step 2: Feature Selection UI  ──→  selected_features.md
Step 3: Merge + Extract Media ──→  features.json + media files
Step 4: Edit & Enhance Features ──→  edited features.json (with optional LLM rewriting)
Step 5: Generate HTML         ──→  whats-new-generated.html
```

All outputs are stored in the `liverun/` directory.

### Quick Start (Orchestrator)

```bash
./orchestrator/run.sh
# Opens at http://localhost:5001
```

This starts all three services (orchestrator on 5001, Feature Selection on 5002, PM Features on 5003) and guides you through each step.

### Manual Workflow

You can also run each step individually:

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
4. Saves the selected features to `FeatureSelection/selected_features.md`

The script creates a Python virtual environment and installs dependencies automatically.

---

## Step 3 — Generate the What's New page

Once you have both input files from Steps 1 and 2, you can generate the What's New page in one of two formats:

| Option | Script | Output | Use case |
|--------|--------|--------|----------|
| **A** | `generate_from_selections.py` | `whats-new-generated.html` | Final page for Netlify deployment |
| **B** | `generate_md_from_selections.py` | `whats-new-generated.md` | Markdown for reviewing and editing |

Both scripts share the same pipeline: parse input files → merge & deduplicate → enrich with media → download media → generate output.

### Option A — Generate HTML

```bash
# Generate using default file paths
python3 generate_from_selections.py

# Or specify paths explicitly
python3 generate_from_selections.py \
    --pm-file PMhighlightedfeatures/pm-highlighted-features.md \
    --selected-file FeatureSelection/selected_features.md \
    --output whats-new-generated.html

# Offline mode (skip GitHub API and media downloads)
python3 generate_from_selections.py --skip-github --skip-media
```

Produces a complete HTML page with dark theme, TOC, section headers, feature cards, media, and lightbox — ready for deployment to Netlify.

### Option B — Generate Markdown

```bash
# Generate using default file paths
python3 generate_md_from_selections.py

# Or specify paths explicitly
python3 generate_md_from_selections.py \
    --pm-file PMhighlightedfeatures/pm-highlighted-features.md \
    --selected-file FeatureSelection/selected_features.md \
    --output whats-new-generated.md

# Offline mode (skip GitHub API and media downloads)
python3 generate_md_from_selections.py --skip-github --skip-media
```

Produces a structured Markdown file with the same content, useful for reviewing the feature list, sharing for feedback, or editing before final HTML generation.

### What the scripts do

1. **Parse PM features** from `pm-highlighted-features.md` — these are shown first in each section (highlighted)
2. **Parse selected features** from `selected_features.md` — these are the release note features
3. **Deduplicate** by PR number — PM features take priority over release note features
4. **Fetch media via GitHub API** — extract images and videos from PR bodies
5. **Download media** to `media/` — skip files that already exist locally
6. **Generate output** — HTML (Option A) or Markdown (Option B)

### CLI flags (same for both scripts)

| Flag | Default | Description |
|------|---------|-------------|
| `--pm-file` | `PMhighlightedfeatures/pm-highlighted-features.md` | PM highlighted features markdown |
| `--selected-file` | `FeatureSelection/selected_features.md` | Selected release note features |
| `--output` | `.html` or `.md` (depends on script) | Output file path |
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
  orchestrator/                      # Unified orchestrator (recommended)
    run.sh                           # Launch all services (ports 5001, 5002, 5003)
    app.py                           # Flask orchestrator app
    llm_client.py                    # LLM enhancement via litellm
    context_fetcher.py               # Fetches PR bodies & doc text for LLM context
    static/index.html                # Orchestrator UI
    requirements.txt                 # Python dependencies (flask, certifi, litellm)
  generate_from_selections.py        # HTML generator (merges PM + selected features → HTML)
  generate_md_from_selections.py     # Markdown generator (merges PM + selected features → Markdown)
  index.html                         # Key Capabilities landing page
  favicon.svg                        # Site favicon
  grid-bg.svg                        # Hero background graphic
  .git-token/                        # GitHub token (not committed)
    github.token                     # SSO-authorized token for elastic org
  liverun/                           # Working directory (not committed)
    features.json                    # Merged features with edits
    context_cache.json               # Cached PR bodies & doc text for LLM enhancement
    whats-new-merged.md              # Generated markdown
    whats-new-generated.html         # Generated HTML output
    media/                           # Downloaded PR images and videos
  PMhighlightedfeatures/             # Step 1: PM feature curation
    run_ui.sh                        # Launch UI (port 5003)
    app.py                           # Flask app
    extract_release.sh               # CLI alternative: extract features from PDF
    extract_release_features.py      # PDF extraction script (requires pdfplumber)
    requirements.txt                 # Python dependencies
  FeatureSelection/                  # Step 2: Release note feature selection
    run.sh                           # Launch UI (port 5002)
    app.py                           # Flask app
    requirements.txt                 # Python dependencies
```
