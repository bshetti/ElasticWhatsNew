# What's New in Elastic Observability
Releases covered: 9.3, 9.3.0

## Log Analytics & Streams

### 1. Streams - Generate Processing Pipeline
- **Source:** PM Highlighted
- **Description:** Parse logs from the message field in a log document with the click of a button. An Agentic workflow will use the available processors in Streams to extract data like the timestamp, log level and more from a users logs and put it into either ECS or OTel fields. Separately the dissect processor now also has AI suggestions.
- **Status:** Tech Preview
- **Tags:** Streams
- **Release:** 9.3
- **Links:**
  - [PR #243950](https://github.com/elastic/kibana/pull/243950)
- **Media:**
  - `media/pr-243950-1.png` (image)

---

### 2. Streams - Improved Processing Capabilities
- **Source:** PM Highlighted
- **Description:** New Processors: - Drop - Remove - Remove by prefix - Convert - Replace - Append YAML mode for expert users and more complex pipelines - https://github.com/elastic/kibana/pull/242 743 Autocomplete for fields/value Autocomplete for Ingest Pipeline JSON config
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3
- **Links:**
  - [PR #242](https://github.com/elastic/kibana/pull/242)

---

### 3. Adds the math, replace, drop, and convert processors.
- **Source:** Release Notes
- **Description:** Adds the math, replace, drop, and convert processors.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #246050](https://github.com/elastic/kibana/pull/246050)
  - [PR #242310](https://github.com/elastic/kibana/pull/242310)
  - [PR #242161](https://github.com/elastic/kibana/pull/242161)
  - [PR #240023](https://github.com/elastic/kibana/pull/240023)

---

### 4. Enforces field name spacing in wired streams and detects type mismatches in proc...
- **Source:** Release Notes
- **Description:** Enforces field name spacing in wired streams and detects type mismatches in processor configurations.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #244221](https://github.com/elastic/kibana/pull/244221)

---

### 5. Allows users to configure Streams visibility on a space-by-space basis.
- **Source:** Release Notes
- **Description:** Allows users to configure Streams visibility on a space-by-space basis.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #244285](https://github.com/elastic/kibana/pull/244285)

---

### 6. Adds AI pattern suggestions for the Streams dissect processor.
- **Source:** Release Notes
- **Description:** Adds AI pattern suggestions for the Streams dissect processor.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #242377](https://github.com/elastic/kibana/pull/242377)

---

### 7. Improves processing warnings with truncation logic and wrapped text.
- **Source:** Release Notes
- **Description:** Improves processing warnings with truncation logic and wrapped text.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #239188](https://github.com/elastic/kibana/pull/239188)

---

### 8. Adds support for geo_point fields to classic streams.
- **Source:** Release Notes
- **Description:** Adds support for geo_point fields to classic streams.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #244356](https://github.com/elastic/kibana/pull/244356)
- **Media:**
  - `media/pr-244356-1.mp4` (video)

---

### 9. Allows users to add custom description for processors.
- **Source:** Release Notes
- **Description:** Allows users to add custom description for processors.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #243998](https://github.com/elastic/kibana/pull/243998)

---

### 10. Adds a tour of the Streams UI.
- **Source:** Release Notes
- **Description:** Adds a tour of the Streams UI.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #244808](https://github.com/elastic/kibana/pull/244808)
- **Media:**
  - `media/pr-244808-1.mp4` (video)

---

### 11. Adds a message to tell users when a stream is missing.
- **Source:** Release Notes
- **Description:** Adds a message to tell users when a stream is missing.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #244366](https://github.com/elastic/kibana/pull/244366)

---

### 12. Prevents conflicts in Processing tab when editing and reordering streams.
- **Source:** Release Notes
- **Description:** Prevents conflicts in Processing tab when editing and reordering streams.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #244228](https://github.com/elastic/kibana/pull/244228)

---

### 13. Adds field type icons to the Processing UI.
- **Source:** Release Notes
- **Description:** Adds field type icons to the Processing UI.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #242134](https://github.com/elastic/kibana/pull/242134)
  - [PR #241825](https://github.com/elastic/kibana/pull/241825)

---

### 14. Adds timezone and locale parameters to Streamlang.
- **Source:** Release Notes
- **Description:** Adds timezone and locale parameters to Streamlang.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #241369](https://github.com/elastic/kibana/pull/241369)

---

### 15. Adds specific error messaging to the Streams schema editor when expensive querie...
- **Source:** Release Notes
- **Description:** Adds specific error messaging to the Streams schema editor when expensive queries are turned off.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #243406](https://github.com/elastic/kibana/pull/243406)

---

### 16. Adds autoscroll to Review partitioning suggestions panels.
- **Source:** Release Notes
- **Description:** Adds autoscroll to Review partitioning suggestions panels.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #242891](https://github.com/elastic/kibana/pull/242891)

---

### 17. Improves Streams attachment filters with multi-type selection, server-side filte...
- **Source:** Release Notes
- **Description:** Improves Streams attachment filters with multi-type selection, server-side filtering, and suggestions limit.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #245248](https://github.com/elastic/kibana/pull/245248)

---

### 18. Adds details flyout and improved UX to the Streams attachment feature.
- **Source:** Release Notes
- **Description:** Adds details flyout and improved UX to the Streams attachment feature.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #244880](https://github.com/elastic/kibana/pull/244880)

---

### 19. Hides document match filter controls in the processing preview for users without...
- **Source:** Release Notes
- **Description:** Hides document match filter controls in the processing preview for users without manage privileges.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #242119](https://github.com/elastic/kibana/pull/242119)

---

### 20. Adds messaging to show nested processors and conditions.
- **Source:** Release Notes
- **Description:** Adds messaging to show nested processors and conditions.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #240778](https://github.com/elastic/kibana/pull/240778)

---

### 21. Adds abort capabilities and silent mode when generating stream descriptions.
- **Source:** Release Notes
- **Description:** Adds abort capabilities and silent mode when generating stream descriptions.
- **Status:** GA
- **Tags:** Streams
- **Release:** 9.3.0
- **Links:**
  - [PR #247082](https://github.com/elastic/kibana/pull/247082)

---

## Infrastructure Monitoring

### 22. Metrics exploration in Discover
- **Source:** PM Highlighted
- **Description:** View ingested metrics, explore and filter metrics, dimensions of interest, with visually rich grid of charts and graphs depicting the metric trends over chosen time intervals, all right within Discover. Corresponding ES|QL commands automatically populated when filtering metrics, helping users ease in and tweak the commands vs having to write from scratch. Handy one-click functions help users add those metric charts automatically to dashboards and Cases.
- **Status:** GA
- **Tags:** Metrics Analytics
- **Release:** 9.3
- **Links:**
  - [Docs](https://www.elastic.co/docs/solutions/observability/infra-and-hosts/discover-metrics)
- **Media:**
  - `media/doc-metrics-exploration-in-discove-1.png` (image)
  - `media/doc-metrics-exploration-in-discove-2.png` (image)
  - `media/doc-metrics-exploration-in-discove-3.png` (image)
  - `media/doc-metrics-exploration-in-discove-4.png` (image)

---

### 23. ES|QL TS command enhancements
- **Source:** PM Highlighted
- **Description:** The TS command in ES|QL now supports more time series aggregations, making it possible to do richer and more comprehensive analytics on metrics data. TRANGE, clamp, percentile, stddev, stdvar, deriv, and better extrapolation for rate are supported. Step functions, similar to the PromQL step functions, will help users control the resolution and execution time of their analytics. Note: This will also be repeated in platform
- **Status:** Tech Preview
- **Tags:** Metrics Analytics
- **Release:** 9.3
- **Links:**
  - [Issue #136250](https://github.com/elastic/elasticsearch/issues/136250)
  - [Issue #135599](https://github.com/elastic/elasticsearch/issues/135599)
  - [Issue #136281](https://github.com/elastic/elasticsearch/issues/136281)
  - [Issue #270](https://github.com/elastic/metrics-program/issues/270)
  - [Issue #136251](https://github.com/elastic/elasticsearch/issues/136251)
  - [Issue #136272](https://github.com/elastic/elasticsearch/issues/136272)
  - [Docs](https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/conditional-functions-and-expressions#esql-clamp)

---

### 24. Exponential histogram field support in TSDB, ES|QL
- **Source:** PM Highlighted
- **Description:** OpenTelemetry Exponential Histograms are an advanced metric type designed to capture the distribution of values, like request latency, using automatically adjusting, exponentially-sized buckets. They are crucial for time series analytics by significantly reducing storage overhead and improving the accuracy of calculated percentiles (e.g., p99 latency), especially for long-tail distributions common in microservices. This release adds support for ingesting exponential histograms, and querying them via ES|QL. In addition, downsampling exponential histograms will also be supported. Note: This will also be repeated in platform
- **Status:** Tech Preview
- **Tags:** Metrics Analytics
- **Release:** 9.3
- **Links:**
  - [Issue #128622](https://github.com/elastic/elasticsearch/issues/128622)

---

### 25. Downsampling enhancements
- **Source:** PM Highlighted
- **Description:** Metrics downsampling introduces an enhancement to retain the last value per downsampling interval, exchanging accuracy for performance and results in a downsampled index with the same mapping as the raw data making analytics on downsampled data consistent with analytics on raw data. Note: This will also be repeated in platform
- **Status:** Tech Preview
- **Tags:** Metrics Datastore
- **Release:** 9.3
- **Links:**
  - [Issue #128357](https://github.com/elastic/elasticsearch/issues/128357)

---

### 26. ES|QL TS query performance improvements
- **Source:** PM Highlighted
- **Description:** Multiple improvements to ES|QL query performance result in significant reduction in query latency (~5x+) when wildcarding/filtering by dimensions as part of the query.
- **Status:** Tech Preview
- **Tags:** Metrics Analytics
- **Release:** 9.3
- **Links:**
  - [Issue #136252](https://github.com/elastic/elasticsearch/issues/136252)

---

### 27. Adds dashboard suggestions for ECS, K8s, and OTel dashboards when selecting Pods...
- **Source:** Release Notes
- **Description:** Adds dashboard suggestions for ECS, K8s, and OTel dashboards when selecting Pods in Infra Inventory UI.
- **Status:** GA
- **Tags:** Infrastructure Monitoring
- **Release:** 9.3.0
- **Links:**
  - [PR #245784](https://github.com/elastic/kibana/pull/245784)

---

### 28. Ensures Infra Inventory UIs reflect supported schemas.
- **Source:** Release Notes
- **Description:** Ensures Infra Inventory UIs reflect supported schemas.
- **Status:** GA
- **Tags:** Infrastructure Monitoring
- **Release:** 9.3.0
- **Links:**
  - [PR #244481](https://github.com/elastic/kibana/pull/244481)
- **Media:**
  - `media/pr-244481-1.png` (image)
  - `media/pr-244481-2.png` (image)
  - `media/pr-244481-3.png` (image)
  - `media/pr-244481-4.png` (image)
  - `media/pr-244481-5.png` (image)
  - `media/pr-244481-6.png` (image)
  - `media/pr-244481-7.png` (image)
  - `media/pr-244481-8.png` (image)

---

## Agentic Investigations

### 29. Workflows
- **Source:** PM Highlighted
- **Description:** Workflows help SREs manage the known operational processes that keep services healthy: correlating signals, escalating known failure modes, updating metadata, and orchestrating remediation steps. But performance degradations and system regressions rarely follow a predictable path. Teams often chase symptoms across dashboards without clarity on where to start.
- **Status:** Tech Preview
- **Tags:** Workflow
- **Release:** 9.3
- **Links:**
  - [Docs](https://www.elastic.co/docs/explore-analyze/workflows)

---

### 30. Amazon Bedrock AgentCore integration
- **Source:** PM Highlighted
- **Description:** Part of our end-to-end Agentic AI observability for agentic apps running in Amazon Bedrock AgentCore
- **Status:** Tech Preview
- **Tags:** LLM Obs
- **Release:** 9.3
- **Links:**
  - [Issue #686](https://github.com/elastic/obs-integration-team/issues/686)

---

### 31. Adds the ELSER in EIS model option for the Observability and Search AI Assistant...
- **Source:** Release Notes
- **Description:** Adds the ELSER in EIS model option for the Observability and Search AI Assistant Knowledge Base.
- **Status:** GA
- **Tags:** AI Assistant
- **Release:** 9.3.0
- **Links:**
  - [PR #243298](https://github.com/elastic/kibana/pull/243298)

---

### 32. Removes the AI Assistants Settings privilege.
- **Source:** Release Notes
- **Description:** Removes the AI Assistants Settings privilege.
- **Status:** GA
- **Tags:** AI Assistant
- **Release:** 9.3.0
- **Links:**
  - [PR #239144](https://github.com/elastic/kibana/pull/239144)

---

### 33. Observability Agent for Agent Builder is released in 9.3. This includes Observab...
- **Source:** Release Notes
- **Description:** Observability Agent for Agent Builder is released in 9.3. This includes Observability related tools and AI Insights for alerts, logs in Discover, and errors in APM.
- **Status:** Tech Preview
- **Tags:** Agent Builder, Observability Agent
- **Release:** 9.3.0
- **Links:**
  - [Docs](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/builtin-agents-reference)

---

## Query, Analysis & Alerting

### 34. OOTB alert rule templates in integrations
- **Source:** PM Highlighted
- **Description:** Customers want to set up best practice alerts for their business critical services and resources, but donʼt have the knowledge or observability experience with every service. With alert presets for some of the key integrations, they can now do this with a click of a button and have confidence that they will have adequate observability coverage.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3
- **Links:**
  - [Issue #464](https://github.com/elastic/obs-integration-team/issues/464)

---

### 35. Supporting Tagging and Bulk Tagging of Alerts
- **Source:** PM Highlighted
- **Description:** The feature addresses a gap in how users organise and work with alerts. Today, alerts inherit rule tags but cannot be further enriched with metadata after they are created, which limits teams trying to classify alerts by ownership, service, triage state or internal workflows. This proposal introduces first class alert tagging in Kibana and via the API, including adding, removing and bulk editing tags, autocomplete suggestions, persistence on the alert document and full support in search, filters and exports. It preserves existing rule tags and aligns with the Security solutionʼs use of workflow tags, giving users a flexible way to segment and manage alerts without changing permissions or migrating to Kibana tags.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3
- **Links:**
  - [Issue #40](https://github.com/elastic/rna-program/issues/40)

---

### 36. Improved Muting (Alert-Level Snooze) for Observability Alerts
- **Source:** PM Highlighted
- **Description:** This feature closes a major operational gap by enabling teams to mute alerts at the individual alert instance level rather than only at the rule level. Many regulated or high discipline environments need to suppress notifications for a specific alert during planned work, expected conditions or noisy periods while still allowing other alerts from the same rule to fire normally. The proposal introduces mute controls in the Alerts table and flyout, stores mute state and audit metadata on the alert document, and ensures muted alerts stop triggering actions but remain visible with clear UI markers. It aligns Elastic with common “snoozeˮ behaviour in competing tools and removes a migration blocker for customers like NSE that rely on fine grained alert suppression.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3
- **Links:**
  - [Issue #42](https://github.com/elastic/rna-program/issues/42)

---

### 37. Allows users to bulk mute and unmute alerts.
- **Source:** Release Notes
- **Description:** Allows users to bulk mute and unmute alerts.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3.0
- **Links:**
  - [PR #245690](https://github.com/elastic/kibana/pull/245690)

---

### 38. Adds a Find Alert Rule Templates API that shows installed templates in the Creat...
- **Source:** Release Notes
- **Description:** Adds a Find Alert Rule Templates API that shows installed templates in the Create new rule modal.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3.0
- **Links:**
  - [PR #245373](https://github.com/elastic/kibana/pull/245373)

---

### 39. Adds a unified rules list.
- **Source:** Release Notes
- **Description:** Adds a unified rules list.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3.0
- **Links:**
  - [PR #242208](https://github.com/elastic/kibana/pull/242208)

---

### 40. Adds View in discover button to alert details for Infrastructure rules.
- **Source:** Release Notes
- **Description:** Adds View in discover button to alert details for Infrastructure rules.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3.0
- **Links:**
  - [PR #236880](https://github.com/elastic/kibana/pull/236880)

---

### 41. Allows users to view and filter by manually added workflow tags.
- **Source:** Release Notes
- **Description:** Allows users to view and filter by manually added workflow tags.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3.0
- **Links:**
  - [PR #244251](https://github.com/elastic/kibana/pull/244251)

---

### 42. Shows alert workflow tags on the Overview tab of the alert details flyout.
- **Source:** Release Notes
- **Description:** Shows alert workflow tags on the Overview tab of the alert details flyout.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3.0
- **Links:**
  - [PR #246440](https://github.com/elastic/kibana/pull/246440)

---

### 43. Adds a warning when deleting API keys currently in use by alerting rules.
- **Source:** Release Notes
- **Description:** Adds a warning when deleting API keys currently in use by alerting rules.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3.0
- **Links:**
  - [PR #243353](https://github.com/elastic/kibana/pull/243353)

---

### 44. Allows users to configure custom global ingest pipelines on SLO rollup data.
- **Source:** Release Notes
- **Description:** Allows users to configure custom global ingest pipelines on SLO rollup data.
- **Status:** GA
- **Tags:** SLO
- **Release:** 9.3.0
- **Links:**
  - [PR #245025](https://github.com/elastic/kibana/pull/245025)

---

### 45. Adds index sorting to SLI index settings.
- **Source:** Release Notes
- **Description:** Adds index sorting to SLI index settings.
- **Status:** GA
- **Tags:** SLO
- **Release:** 9.3.0
- **Links:**
  - [PR #244978](https://github.com/elastic/kibana/pull/244978)

---

### 46. Allows users to view the SLO associated with a burn rate rule from the rule deta...
- **Source:** Release Notes
- **Description:** Allows users to view the SLO associated with a burn rate rule from the rule details page.
- **Status:** GA
- **Tags:** SLO
- **Release:** 9.3.0
- **Links:**
  - [PR #240535](https://github.com/elastic/kibana/pull/240535)

---

### 47. Adds SLO attachments and migrates UI to attachments API.
- **Source:** Release Notes
- **Description:** Adds SLO attachments and migrates UI to attachments API.
- **Status:** GA
- **Tags:** SLO
- **Release:** 9.3.0
- **Links:**
  - [PR #244092](https://github.com/elastic/kibana/pull/244092)

---

### 48. Replaces current document count chart with RED metrics.
- **Source:** Release Notes
- **Description:** Replaces current document count chart with RED metrics.
- **Status:** GA
- **Tags:** APM, Metrics Analytics
- **Release:** 9.3.0
- **Links:**
  - [PR #236635](https://github.com/elastic/kibana/pull/236635)

---

### 49. Adds Edit tags to alert actions.
- **Source:** Release Notes
- **Description:** Adds Edit tags to alert actions.
- **Status:** GA
- **Tags:** Alerting
- **Release:** 9.3.0
- **Links:**
  - [PR #243792](https://github.com/elastic/kibana/pull/243792)

---

## OpenTelemetry

### 50. EDOT Cloud Forwarder for AWS S3
- **Source:** PM Highlighted
- **Description:** EDOT Collector runs as an event triggered Lambda function. It removes the need to manage infrastructure that scales with log volume from S3 buckets, and it parses the logs into OTel format.
- **Status:** GA
- **Tags:** OpenTelemetry
- **Release:** 9.3
- **Links:**
  - [Issue #4384](https://github.com/elastic/observability-dev/issues/4384)

---

### 51. Adds deactivate_all_instrumentations, deactivate_instrumentations, send_logs, se...
- **Source:** Release Notes
- **Description:** Adds deactivate_all_instrumentations, deactivate_instrumentations, send_logs, send_metrics, and send_traces agent configuration settings for EDOT PHP.
- **Status:** GA
- **Tags:** OpenTelemetry
- **Release:** 9.3.0
- **Links:**
  - [PR #246021](https://github.com/elastic/kibana/pull/246021)

---

### 52. Adds metrics dashboard for non-EDOT agents in the OTEL native ingestion path.
- **Source:** Release Notes
- **Description:** Adds metrics dashboard for non-EDOT agents in the OTEL native ingestion path.
- **Status:** GA
- **Tags:** OpenTelemetry
- **Release:** 9.3.0
- **Links:**
  - [PR #236978](https://github.com/elastic/kibana/pull/236978)

---

### 53. Adds sampling_rate central configuration to EDOT PHP.
- **Source:** Release Notes
- **Description:** Adds sampling_rate central configuration to EDOT PHP.
- **Status:** GA
- **Tags:** OpenTelemetry
- **Release:** 9.3.0
- **Links:**
  - [PR #241908](https://github.com/elastic/kibana/pull/241908)

---

### 54. Adds opamp_polling_interval and sampling_rate central configuration to EDOT Node...
- **Source:** Release Notes
- **Description:** Adds opamp_polling_interval and sampling_rate central configuration to EDOT Node.js.
- **Status:** GA
- **Tags:** OpenTelemetry
- **Release:** 9.3.0
- **Links:**
  - [PR #241048](https://github.com/elastic/kibana/pull/241048)

---

## Application Performance Monitoring

### 55. Find Similar Error Logs for Traces in Discover
- **Source:** PM Highlighted
- **Description:** When users find a failed transaction within a trace, itʼs very helpful to understand why it happened, how often it happens and when it started happening. In addition to finding the correlated error logs for a span within a trace directly Discover, you will now see a timeline of how often that error happens and simply click through to query those similar errors.
- **Status:** GA
- **Tags:** APM
- **Release:** 9.3
- **Links:**
  - [PR #244665](https://github.com/elastic/kibana/pull/244665)

---

### 56. Adds badge sync to Trace timeline.
- **Source:** Release Notes
- **Description:** Adds badge sync to Trace timeline.
- **Status:** GA
- **Tags:** APM
- **Release:** 9.3.0
- **Links:**
  - [PR #246510](https://github.com/elastic/kibana/pull/246510)

---

### 57. Adds errors to Trace timeline.
- **Source:** Release Notes
- **Description:** Adds errors to Trace timeline.
- **Status:** GA
- **Tags:** APM
- **Release:** 9.3.0
- **Links:**
  - [PR #245161](https://github.com/elastic/kibana/pull/245161)

---

### 58. Adds Span links badge to Trace timeline.
- **Source:** Release Notes
- **Description:** Adds Span links badge to Trace timeline.
- **Status:** GA
- **Tags:** APM
- **Release:** 9.3.0
- **Links:**
  - [PR #244389](https://github.com/elastic/kibana/pull/244389)

---

## Digital Experience Monitoring

### 59. Adds new sub-feature privileges for Synthetics global parameters.
- **Source:** Release Notes
- **Description:** Adds new sub-feature privileges for Synthetics global parameters.
- **Status:** GA
- **Tags:** Synthetics
- **Release:** 9.3.0
- **Links:**
  - [PR #243821](https://github.com/elastic/kibana/pull/243821)

---
