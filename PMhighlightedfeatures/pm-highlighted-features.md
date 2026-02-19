# Elastic Observability 9.3 — PM Highlighted Features

Release date: 1/27/2026
Feature freeze: 12/16/2025

---

## 1. Streams - Generate Processing Pipeline

- **Key Messages:** Parse logs from the message field in a log document with the click of a button. An Agentic workflow will use the available processors in Streams to extract data like the timestamp, log level and more from a users logs and put it into either ECS or OTel fields. Separately the dissect processor now also has AI suggestions.
- **Impact:** Medium
- **Status:** Tech Preview, Enterprise
- **Competitive Differentiator:** Unique against Opensearc h, Grafana
- **Owner:** Luca Wintergerst
- **Relevant Links:**
  - https://github.com/elastic/kibana/pull/243950
- **TAG** "Log Analytics & Streams"
- **Feature Tags:** Streams
- **Release:** 9.3

---

## 2. Streams - Improved Processing Capabilities

- **Key Messages:** New Processors: - Drop - Remove - Remove by prefix - Convert - Replace - Append YAML mode for expert users and more complex pipelines - https://github.com/elastic/kibana/pull/242 743 Autocomplete for fields/value Autocomplete for Ingest Pipeline JSON config
- **Impact:** Medium
- **Status:** GA
- **Owner:** Luca Wintergerst
- **Relevant Links:** (none listed)
- **TAG** "Log Analytics & Streams"
- **Feature Tags:** Streams
- **Release:** 9.3

---

## 3. Metrics exploration in Discover

- **Key Messages:** View ingested metrics, explore and filter metrics, dimensions of interest, with visually rich grid of charts and graphs depicting the metric trends over chosen time intervals, all right within Discover. Corresponding ES|QL commands automatically populated when filtering metrics, helping users ease in and tweak the commands vs having to write from scratch. Handy one-click functions help users add those metric charts automatically to dashboards and Cases.
- **Impact:** Medium
- **Status:** GA
- **Owner:** Miguel Sánchez
- **Relevant Links:**
  - https://www.elastic.co/docs/solutions/observability/infra-and-hosts/discover-metrics
- **TAG** "Infrastructure Monitoring"
- **Feature Tags:** Metrics Analytics
- **Release:** 9.3

---

## 4. ES|QL TS command enhancements

- **Key Messages:** The TS command in ES|QL now supports more time series aggregations, making it possible to do richer and more comprehensive analytics on metrics data. TRANGE, clamp, percentile, stddev, stdvar, deriv, and better extrapolation for rate are supported. Step functions, similar to the PromQL step functions, will help users control the resolution and execution time of their analytics. Note: This will also be repeated in platform
- **Impact:** Medium
- **Status:** Tech Preview
- **Owner:** Vinay Chandra…
- **Relevant Links:**
  - https://github.com/elastic/elasticsearch/issues/136250
  - https://github.com/elastic/elasticsearch/issues/135599
  - https://github.com/elastic/elasticsearch/issues/136281
  - https://github.com/elastic/metrics-program/issues/270
  - https://github.com/elastic/elasticsearch/issues/136251
  - https://github.com/elastic/elasticsearch/issues/136272
  - https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/conditional-functions-and-expressions#esql-clamp
- **TAG** "Infrastructure Monitoring"
- **Feature Tags:** Metrics Analytics
- **Release:** 9.3

---

## 5. Exponential histogram field support in TSDB, ES|QL

- **Key Messages:** OpenTelemetry Exponential Histograms are an advanced metric type designed to capture the distribution of values, like request latency, using automatically adjusting, exponentially-sized buckets. They are crucial for time series analytics by significantly reducing storage overhead and improving the accuracy of calculated percentiles (e.g., p99 latency), especially for long-tail distributions common in microservices. This release adds support for ingesting exponential histograms, and querying them via ES|QL. In addition, downsampling exponential histograms will also be supported. Note: This will also be repeated in platform
- **Impact:** Small
- **Status:** Tech Preview
- **Owner:** Vinay Chandra…
- **Relevant Links:**
  - https://github.com/elastic/elasticsearch/issues/128622
- **TAG** "Infrastructure Monitoring"
- **Feature Tags:** Metrics Analytics
- **Release:** 9.3

---

## 6. Downsampling enhancements

- **Key Messages:** Metrics downsampling introduces an enhancement to retain the last value per downsampling interval, exchanging accuracy for performance and results in a downsampled index with the same mapping as the raw data making analytics on downsampled data consistent with analytics on raw data. Note: This will also be repeated in platform
- **Impact:** Small
- **Status:** Tech Preview, Platinum
- **Owner:** Vinay Chandra…
- **Relevant Links:**
  - https://github.com/elastic/elasticsearch/issues/128357
- **TAG** "Infrastructure Monitoring"
- **Feature Tags:** Metrics Datastore
- **Release:** 9.3

---

## 7. ES|QL TS query performance improvements

- **Key Messages:** Multiple improvements to ES|QL query performance result in significant reduction in query latency (~5x+) when wildcarding/filtering by dimensions as part of the query.
- **Impact:** Small
- **Status:** Tech Preview
- **Owner:** Vinay Chandra…
- **Relevant Links:**
  - https://github.com/elastic/elasticsearch/issues/136252
- **TAG** "Infrastructure Monitoring"
- **Feature Tags:** Metrics Analytics
- **Release:** 9.3

---

## 8. Workflows

- **Key Messages:** Workflows help SREs manage the known operational processes that keep services healthy: correlating signals, escalating known failure modes, updating metadata, and orchestrating remediation steps. But performance degradations and system regressions rarely follow a predictable path. Teams often chase symptoms across dashboards without clarity on where to start.
- **Impact:** Large
- **Status:** Tech Preview, Plea…
- **Owner:** Tinsae Erkailo
- **Relevant Links:**
  - https://www.elastic.co/docs/explore-analyze/workflows
- **TAG** "Agentic Investigations"
- **Feature Tags:** Workflow
- **Release:** 9.3

---

## 9. Amazon Bedrock AgentCore integration

- **Key Messages:** Part of our end-to-end Agentic AI observability for agentic apps running in Amazon Bedrock AgentCore
- **Impact:** Large
- **Status:** Tech Preview
- **Owner:** Daniela Tzvetk…
- **Relevant Links:**
  - https://github.com/elastic/obs-integration-team/issues/686
- **TAG** "Agentic Investigations"
- **Feature Tags:** LLM Obs
- **Release:** 9.3

---

## 10. OOTB alert rule templates in integrations

- **Key Messages:** Customers want to set up best practice alerts for their business critical services and resources, but donʼt have the knowledge or observability experience with every service. With alert presets for some of the key integrations, they can now do this with a click of a button and have confidence that they will have adequate observability coverage.
- **Impact:** Large
- **Status:** GA
- **Owner:** Daniela Tzvetk…
- **Relevant Links:**
  - https://github.com/elastic/obs-integration-team/issues/464
- **TAG** "Query, Analysis & Alerting"
- **Feature Tags:** Alerting
- **Release:** 9.3

---

## 11. Supporting Tagging and Bulk Tagging of Alerts

- **Key Messages:** The feature addresses a gap in how users organise and work with alerts. Today, alerts inherit rule tags but cannot be further enriched with metadata after they are created, which limits teams trying to classify alerts by ownership, service, triage state or internal workflows. This proposal introduces first class alert tagging in Kibana and via the API, including adding, removing and bulk editing tags, autocomplete suggestions, persistence on the alert document and full support in search, filters and exports. It preserves existing rule tags and aligns with the Security solutionʼs use of workflow tags, giving users a flexible way to segment and manage alerts without changing permissions or migrating to Kibana tags.
- **Impact:** Small
- **Status:** GA
- **Owner:** Drew Post
- **Relevant Links:**
  - https://github.com/elastic/rna-program/issues/40
- **TAG** "Query, Analysis & Alerting"
- **Feature Tags:** Alerting
- **Release:** 9.3

---

## 12. Improved Muting (Alert-Level Snooze) for Observability Alerts

- **Key Messages:** This feature closes a major operational gap by enabling teams to mute alerts at the individual alert instance level rather than only at the rule level. Many regulated or high discipline environments need to suppress notifications for a specific alert during planned work, expected conditions or noisy periods while still allowing other alerts from the same rule to fire normally. The proposal introduces mute controls in the Alerts table and flyout, stores mute state and audit metadata on the alert document, and ensures muted alerts stop triggering actions but remain visible with clear UI markers. It aligns Elastic with common “snoozeˮ behaviour in competing tools and removes a migration blocker for customers like NSE that rely on fine grained alert suppression.
- **Impact:** Small
- **Status:** GA
- **Owner:** Drew Post
- **Relevant Links:**
  - https://github.com/elastic/rna-program/issues/42
- **TAG** "Query, Analysis & Alerting"
- **Feature Tags:** Alerting
- **Release:** 9.3

---

## 13. EDOT Cloud Forwarder for AWS S3

- **Key Messages:** EDOT Collector runs as an event triggered Lambda function. It removes the need to manage infrastructure that scales with log volume from S3 buckets, and it parses the logs into OTel format.
- **Impact:** Medium
- **Status:** GA
- **Owner:** Miguel Luna
- **Relevant Links:**
  - https://github.com/elastic/observability-dev/issues/4384
- **TAG** "OpenTelemetry"
- **Feature Tags:** OpenTelemetry
- **Release:** 9.3

---

## 14. Find Similar Error Logs for Traces in Discover

- **Key Messages:** When users find a failed transaction within a trace, itʼs very helpful to understand why it happened, how often it happens and when it started happening. In addition to finding the correlated error logs for a span within a trace directly Discover, you will now see a timeline of how often that error happens and simply click through to query those similar errors.
- **Impact:** Small
- **Status:** GA
- **Owner:** Roshan Gonsal…
- **Relevant Links:**
  - https://github.com/elastic/kibana/pull/244665
- **TAG** "Application Performance Monitoring"
- **Feature Tags:** APM
- **Release:** 9.3

---
