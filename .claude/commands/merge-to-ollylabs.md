# Merge What's New Data to Observability Labs

Merge the generated features and media from the whatsnew `liverun/` directory into the Observability Labs Next.js project. This replaces the feature data in `whatsnewData.ts` and syncs media files.

## Step 1: Ask for Repository Paths

Ask the user for both local repo paths:

1. **whatsnew repo** — contains `liverun/features.json` and `liverun/media/`
2. **observability-labs repo** — contains `src/components/whatsnew/whatsnewData.ts` and `public/assets/images/whatsnew/`

Verify both paths exist before proceeding:
- `{whatsnew}/liverun/features.json` must exist
- `{whatsnew}/liverun/media/` directory must exist
- `{ollylabs}/src/components/whatsnew/whatsnewData.ts` must exist
- `{ollylabs}/public/assets/images/whatsnew/` directory must exist

If any path is missing, tell the user what's wrong and stop.

## Step 2: Read and Parse features.json

Read `{whatsnew}/liverun/features.json`. The structure is:

```json
{
  "metadata": { "created_at": "...", "pm_count": N, "rn_count": N, ... },
  "sections": [
    { "key": "streams", "name": "Log Analytics & Streams", "tagClass": "tag-streams" },
    ...
  ],
  "features": [
    {
      "title": "Feature Name",
      "description": "...",
      "version": "9.3.0",
      "status": "GA",
      "section_key": "streams",
      "section_name": "Log Analytics & Streams",
      "feature_tags": ["Streams"],
      "pm_highlighted": true,
      "pm_order": 1,
      "include": true,
      "links": [
        { "link_type": "pull", "number": 243950, "repo": "elastic/kibana", "url": "..." }
      ],
      "media": [
        { "filename": "pr-243950-1.png", "media_type": "image" }
      ]
    }
  ]
}
```

**Only process features where `"include": true`**. Skip features with `include: false`.

## Step 3: Check Media File Sizes

For every media file referenced by included features, check its size in `{whatsnew}/liverun/media/`:

```bash
# Find all files larger than 50MB
find {whatsnew}/liverun/media/ -type f -size +50M -exec ls -lh {} \;
```

- Files **> 50MB (52,428,800 bytes)** must be EXCLUDED
- Track excluded filenames so their references are removed from the data
- Report excluded files to the user with their sizes

## Step 4: Copy Media Files

Copy only the media files that are:
1. Referenced by an included feature
2. 50MB or smaller

```bash
mkdir -p {ollylabs}/public/assets/images/whatsnew/
cp {whatsnew}/liverun/media/{filename} {ollylabs}/public/assets/images/whatsnew/
```

Copy ONLY files that are actually referenced by included features. Do not blindly copy all files from the media directory. Also copy `grid-bg.svg` if it exists in the media directory.

## Step 5: Generate whatsnewData.ts

Read the existing `{ollylabs}/src/components/whatsnew/whatsnewData.ts` to understand the exact TypeScript interfaces. Preserve the interface definitions at the top, then replace the `sections` array data.

### Interface Definitions (preserve these exactly)

```typescript
export interface FeatureMedia {
  type: 'image' | 'video'
  src: string
  alt: string
}

export interface FeatureLink {
  label: string
  url: string
  type: 'pr' | 'issue' | 'docs'
}

export interface Feature {
  name: string
  sectionTag: string
  tagClass: string
  featureTags: string[]
  status: 'GA' | 'Tech Preview'
  version: string
  description: string
  links: FeatureLink[]
  media: FeatureMedia[]
}

export interface Section {
  id: string
  title: string
  iconClass: string
  versionBadge: string
  features: Feature[]
}
```

### Data Transformation Rules

**Sections**: Group features by `section_key`. For each section:

| Field | Source |
|-------|--------|
| `id` | `section.key` from the sections array |
| `title` | `section.name` from the sections array |
| `iconClass` | Map from section key (see table below) |
| `versionBadge` | Extract major.minor from the versions in that section's features (e.g., "9.3.0" → "9.3"). If multiple versions, join with ", " |

**Section Icon Class Mapping:**

| Section Key | iconClass |
|---|---|
| `streams` | `icon-logs` |
| `infrastructure` | `icon-infra` |
| `ai-investigations` | `icon-ai` |
| `query-analysis` | `icon-query` |
| `opentelemetry` | `icon-otel` |
| `apm` | `icon-apm` |
| `digital-experience` | `icon-digital` |

For any unknown section key, use `icon-{key}`.

**Features**: For each feature, map fields as follows:

| whatsnewData.ts Field | features.json Source | Notes |
|---|---|---|
| `name` | `title` | Direct copy |
| `sectionTag` | `section_name` | Direct copy |
| `tagClass` | Look up from sections array by `section_key` → `tagClass` | e.g., `tag-streams` |
| `featureTags` | `feature_tags` | Direct copy of array |
| `status` | `status` | `"GA"` or `"Tech Preview"` |
| `version` | `version` | Direct copy |
| `description` | `description` | Direct copy (may contain backtick-delimited code — convert \`code\` to `<code>code</code>`) |
| `links` | `links` array | See link mapping below |
| `media` | `media` array | See media mapping below, **excluding files > 50MB** |

**Link Mapping** — Convert each link object:

| features.json | whatsnewData.ts | Rule |
|---|---|---|
| `link_type: "pull"` | `type: 'pr'` | |
| `link_type: "issue"` | `type: 'issue'` | |
| `link_type: "docs"` | `type: 'docs'` | |
| `url` | `url` | Direct copy |
| `number` + `repo` | `label` | See label rules below |

**Link Label Rules:**
- `link_type: "docs"` → label: `"Docs"`
- `repo: "elastic/elasticsearch"` → label: `"ES#<number>"`
- `repo: "elastic/kibana"` → label: `"#<number>"`
- Any other repo → label: `"<short-repo>#<number>"` (e.g., `"beats#12345"` from `"elastic/beats"`)
- If `number` is `0` and `link_type` is `"docs"` → label: `"Docs"`

**Media Mapping** — Convert each media object:

| features.json | whatsnewData.ts | Rule |
|---|---|---|
| `media_type: "image"` | `type: 'image'` | |
| `media_type: "video"` | `type: 'video'` | |
| `filename` | `src` | Just the filename, e.g., `'pr-243950-1.png'` |
| (generated) | `alt` | Use the feature's `title` as alt text |

**IMPORTANT**: Remove any media entry whose file exceeds 50MB. If a feature's entire media array becomes empty after removal, set `media: []`.

### Feature Ordering

Within each section, sort features by:
1. `pm_highlighted: true` features first (sorted by `pm_order` ascending)
2. `pm_highlighted: false` features after (maintain original order)

### Section Ordering

Only include sections that have at least one included feature. Maintain the order from the `sections` array in features.json.

### String Escaping

When writing TypeScript string literals:
- Escape single quotes: `'` → `\'`
- Escape backslashes: `\` → `\\`
- Convert backtick-delimited code in descriptions to `<code>...</code>` HTML tags
- Preserve `<code>` tags that already exist in descriptions
- Handle em-dashes (—) and other Unicode characters as-is (TypeScript handles UTF-8)

## Step 6: Write the File

Write the complete `whatsnewData.ts` to `{ollylabs}/src/components/whatsnew/whatsnewData.ts`.

## Step 7: Summary Report

After completion, report:
- Total sections processed
- Total features included
- Media files copied (count and total size)
- Media files excluded due to >50MB limit (list filenames and sizes)
- Any features that lost all media due to the size limit
- Path to the updated `whatsnewData.ts`

Suggest the user run:
```bash
cd {ollylabs} && npm run dev
```
Then check `http://localhost:3000/observability-labs/whatsnew` to verify.
