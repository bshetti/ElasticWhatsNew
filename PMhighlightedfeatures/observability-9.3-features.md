# Elastic Observability 9.3 — Release Features

Release date: 1/27/2026
Feature freeze: 12/16/2025

---

## 1. Workflows

- **Key Messages:** Workflows help SREs manage the known operational processes that keep services healthy: correlating signals, escalating known failure modes, updating metadata, and orchestrating remediation steps. But performance degradations and system regressions rarely follow a predictable path. Teams often chase symptoms across dashboards without clarity on where to start.
- **Impact:** Large (Note: for 9.3 this item will only be included in the Platform section of the Tear Sheet)
- **Status:** Preview
- **Owner:** Tinsae Erkailo
- **Relevant Links:** (none listed)
- **TAG** "Agentic Investigations"

---

## 2. Amazon Bedrock AgentCore Integration

- **Key Messages:** Part of our end-to-end Agentic AI observability for agentic apps running in Amazon Bedrock AgentCore.
- **Impact:** Large
- **Status:** Tech Preview
- **Owner:** Daniela Tzvetkova
- **Relevant Links:**
  - https://www.elastic.co/docs/reference/integrations/aws_bedrock_agentcore
- **TAG** "Agentic Investigations"


---

## 3. OOTB Alert Rule Templates in Integrations

- **Key Messages:** Customers want to set up best practice alerts for their business critical services and resources, but don't have the knowledge or observability experience with every service. With alert presets for some of the key integrations, they can now do this with a click of a button and have confidence that they will have adequate observability coverage.
- **Impact:** Large
- **Status:** GA
- **Owner:** Daniela Tzvetkova
- **Relevant Links:**
  - https://github.com/elastic/obs-integration-team/issues/464
- **TAG** "Query, Analysis & Alerting"


---

## 5. Streams — Generate Processing Pipeline

- **Key Messages:** Parse logs from the message field in a log document with the click of a button. An Agentic workflow will use the available processors in Streams to extract data like the timestamp, log level and more from a users logs and put it into either ECS or OTel fields. Separately the dissect processor now also has AI suggestions.
- **Impact:** Medium
- **Status:** Tech Preview
- **Tier:** Enterprise
- **Competitive Differentiator:** Unique against OpenSearch, Grafana
- **Owner:** Luca Wintergerst
- **Relevant Links:**
  - https://github.com/elastic/kibana/pull/243950
- **TAG** "Log Analytics & Streams"

---

## 6. Streams — Improved Processing Capabilities

- **Key Messages:** New Processors: Drop, Remove, Remove by prefix, Convert, Replace, Append. YAML mode for expert users and more complex pipelines. Autocomplete for fields/value. Autocomplete for Ingest Pipeline JSON config.
- **Impact:** Medium
- **Status:** GA
- **Owner:** Luca Wintergerst
- **Relevant Links:**
  - https://github.com/elastic/kibana/pull/242743
- **TAG** "Log Analytics & Streams"

---

## 9. Find Similar Error Logs for Traces in Discover

- **Key Messages:** When users find a failed transaction within a trace, it's very helpful to understand why it happened, how often it happens and when it started happening. In addition to finding the correlated error logs for a span within a trace directly in Discover, you will now see a timeline of how often that error happens and simply click through to query those similar errors.
- **Impact:** Small
- **Status:** GA
- **Owner:** Roshan Gonsalkorale
- **Relevant Links:**
  - https://github.com/elastic/kibana/pull/244665
- **TAGS** "APM"
---

## 10. Supporting Tagging and Bulk Tagging of Alerts

- **Key Messages:** The feature addresses a gap in how users organise and work with alerts. Today, alerts inherit rule tags but cannot be further enriched with metadata after they are created, which limits teams trying to classify alerts by ownership, service, triage state or internal workflows. This proposal introduces first class alert tagging in Kibana and via the API, including adding, removing and bulk editing tags, autocomplete suggestions, persistence on the alert document and full support in search, filters and exports. It preserves existing rule tags and aligns with the Security solution's use of workflow tags, giving users a flexible way to segment and manage alerts without changing permissions or migrating to Kibana tags.
- **Impact:** Small
- **Status:** GA
- **Owner:** Drew Post
- **Relevant Links:**
  - https://github.com/elastic/rna-program/issues/40
- **TAG** "Query, Analysis & Alerting"



---

## 12. ES|QL TS Command Enhancements

- **Key Messages:** The TS command in ES|QL now supports more time series aggregations, making it possible to do richer and more comprehensive analytics on metrics data. TRANGE, clamp, percentile, stddev, stdvar, deriv, and better extrapolation for rate are supported. Step functions, similar to the PromQL step functions, will help users control the resolution and execution time of their analytics. Note: This will also be repeated in platform.
- **Impact:** Medium
- **Status:** Tech Preview
- **Owner:** Vinay Chandrasekhar
- **Relevant Links:**
  - https://github.com/elastic/elasticsearch/issues/136250
  - https://github.com/elastic/elasticsearch/issues/135599
  - https://github.com/elastic/elasticsearch/issues/136281
  - https://github.com/elastic/metrics-program/issues/270
  - https://github.com/elastic/elasticsearch/issues/136251
  - https://github.com/elastic/elasticsearch/issues/136272
  - https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/conditional-functions-and-expressions#esql-clamp
- **TAG** "Infrastructure Monitoring"

---

## 13. Exponential Histogram Field Support in TSDB, ES|QL

- **Key Messages:** OpenTelemetry Exponential Histograms are an advanced metric type designed to capture the distribution of values, like request latency, using automatically adjusting, exponentially-sized buckets. They are crucial for time series analytics by significantly reducing storage overhead and improving the accuracy of calculated percentiles (e.g., p99 latency), especially for long-tail distributions common in microservices. This release adds support for ingesting exponential histograms, and querying them via ES|QL. In addition, downsampling exponential histograms will also be supported. Note: This will also be repeated in platform.
- **Impact:** Small
- **Status:** Tech Preview
- **Owner:** Vinay Chandrasekhar
- **Relevant Links:**
  - https://github.com/elastic/elasticsearch/issues/128622
- **TAG** "Infrastructure Monitoring"

---

## 14. Downsampling Enhancements

- **Key Messages:** Metrics downsampling introduces an enhancement to retain the last value per downsampling interval, exchanging accuracy for performance and results in a downsampled index with the same mapping as the raw data making analytics on downsampled data consistent with analytics on raw data. Note: This will also be repeated in platform.
- **Impact:** Small
- **Status:** Tech Preview
- **Tier:** Platinum
- **Owner:** Vinay Chandrasekhar
- **Relevant Links:**
  - https://github.com/elastic/elasticsearch/issues/128357
- **TAG** "Infrastructure Monitoring"

---

## 15. ES|QL TS Query Performance Improvements

- **Key Messages:** Multiple improvements to ES|QL query performance result in significant reduction in query latency (5x+) when wildcarding/filtering by dimensions as part of the query.
- **Impact:** Small
- **Status:** Tech Preview
- **Owner:** Vinay Chandrasekhar
- **Relevant Links:**
  - https://github.com/elastic/elasticsearch/issues/136252
- **TAG** "Infrastructure Monitoring"

---

## 16. EDOT Cloud Forwarder for AWS S3

- **Key Messages:** EDOT Collector runs as an event triggered Lambda function. It removes the need to manage infrastructure that scales with log volume from S3 buckets, and it parses the logs into OTel format.
- **Impact:** Medium
- **Status:** GA
- **Owner:** Miguel Luna
- **Relevant Links:**
  - https://github.com/elastic/observability-dev/issues/4384
- **TAG** "OpenTelemetry"


