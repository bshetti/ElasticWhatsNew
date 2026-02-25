# Elastic Observability: Key Capabilities

---

## Log Analytics and Streams

Elastic handles log data at petabyte scale with full-text search, automatic pattern detection, and AI-driven categorization. **Streams** eliminates the need to build and maintain fragile ingest pipelines — it uses AI to automatically parse, partition, and structure your logs, manage retention, and surface **Significant Events** like critical errors and anomalies without requiring you to predefine every alert rule. The logsdb index mode delivers up to 70% storage compression without sacrificing query speed.

**Observability Labs:** [Introducing Streams](https://www.elastic.co/observability-labs/blog/elastic-observability-streams-ai-logs-investigations) · [Fixing a fundamental flaw in observability](https://www.elastic.co/observability-labs/blog/reimagine-observability-elastic-streams) · [Streams Processing: Stop Fighting with Grok](https://www.elastic.co/observability-labs/blog/elastic-streams-processing) · [Streams Data Quality and Failure Store](https://www.elastic.co/observability-labs/blog/data-quality-and-failure-store-in-streams) · [Retention Management with Streams](https://www.elastic.co/observability-labs/blog/simplifying-retention-management-with-streams) · [AI-driven incident response with logs](https://www.elastic.co/observability-labs/blog/ai-driven-incident-response-with-logs) · [Getting more from logs with OTel](https://www.elastic.co/observability-labs/blog/getting-more-from-your-logs-with-opentelemetry)

**Docs:** [Log monitoring](https://www.elastic.co/observability/log-monitoring) · [Streams](https://www.elastic.co/docs/solutions/observability/streams/streams) · [Significant Events](https://www.elastic.co/docs/solutions/observability/streams/management/significant-events)

### What's New in Streams — 9.2 / 9.3

**AI-suggested processing pipelines** — Streams analyzes sample documents from your log stream and suggests ingest pipeline configurations automatically, with parse rate previews and simulated output so you can validate before committing. ([#243950](https://github.com/elastic/kibana/pull/243950))

**AI-suggested partitioning** — Streams can now recommend how to partition your log data into logical sub-streams using AI analysis of your data patterns. ([#235759](https://github.com/elastic/kibana/pull/235759))

**Cell-level routing conditions** — Create routing conditions directly from values in the data preview table, making it faster to set up stream partitioning from actual log data. ([#235560](https://github.com/elastic/kibana/pull/235560))

**Manual field mapping from Schema tab** — You can now map new fields directly from the Schema tab without editing index templates, including support for `geo_point` fields that auto-detect flattened lat/lon pairs. ([#235919](https://github.com/elastic/kibana/pull/235919), [#244356](https://github.com/elastic/kibana/pull/244356))

**Persistent field mappings for processors** — Field mappings created by processing rules now persist across pipeline changes, so you don't lose schema work when editing processors. ([#233799](https://github.com/elastic/kibana/pull/233799))

**Ingest pipeline processor templates** — The manual pipeline editor now suggests processor templates and supports triple-quoted strings for complex patterns. ([#236919](https://github.com/elastic/kibana/pull/236919), [#236595](https://github.com/elastic/kibana/pull/236595))

**Improved processing warnings** — Clearer warnings when processing rules encounter issues, making it easier to diagnose pipeline problems. ([#239188](https://github.com/elastic/kibana/pull/239188))

**Guided onboarding tour** — A new interactive walkthrough guides first-time users through the Streams UI covering the streams list, retention, processing, attachments, and advanced configuration. ([#244808](https://github.com/elastic/kibana/pull/244808))

**Per-space permissions** — Streams visibility can now be configured per Kibana space, giving admins control over which teams see the Streams app. ([#244285](https://github.com/elastic/kibana/pull/244285))

**Better missing stream handling** — Navigating to a deleted stream now shows a clear message with a link back instead of a blank screen. ([#244366](https://github.com/elastic/kibana/pull/244366))

**Log events without ML** — The shared logs overview now shows all available log events even when ML features are not available in your tier. ([#225785](https://github.com/elastic/kibana/pull/225785))

---

## Infrastructure Monitoring

Collect logs, metrics, and events from 450+ sources — AWS, Azure, GCP, Kubernetes, Prometheus, databases, network gear — through lightweight agents, OTel collectors, or agentless cloud-native ingestion. The Hosts view gives you real-time CPU, memory, disk, and network metrics across your fleet with alert hotspots and historical trends. For Kubernetes, Elastic auto-discovers ephemeral workloads and enriches metadata at ingest so you can filter by cluster, node, pod, or namespace through prebuilt dashboards. Zero-config ML automatically detects anomalies in resource usage and traffic patterns.

**Observability Labs:** [Explore and Analyze Metrics with ES|QL](https://www.elastic.co/observability-labs/blog/metrics-explore-analyze-with-esql-discover) · [Metrics analytics gets 5x faster](https://www.elastic.co/observability-labs/blog/elastic-metrics-analytics) · [The observability gap](https://www.elastic.co/observability-labs/blog/modern-observability-opentelemetry-correlation-ai) · [Unified K8s Observability with EDOT](https://www.elastic.co/docs/solutions/observability/get-started/quickstart-unified-kubernetes-observability-with-elastic-distributions-of-opentelemetry-edot)

**Docs:** [Infrastructure monitoring](https://www.elastic.co/observability/infrastructure-monitoring) · [Hosts view](https://www.elastic.co/docs/solutions/observability/infra-and-hosts/analyze-compare-hosts) · [Anomaly detection](https://www.elastic.co/docs/solutions/observability/infra-and-hosts/detect-metric-anomalies)

### What's New in Infrastructure Monitoring — 9.2 / 9.3

**ES|QL TS command enhancements** — The `TS` command now supports a much richer set of time series aggregations: `TRANGE`, `clamp`, `percentile`, `stddev`, `stdvar`, `deriv`, and improved `rate` extrapolation. New step functions (similar to PromQL step functions) let you control the resolution and execution time of your metrics analytics. ([elasticsearch#136250](https://github.com/elastic/elasticsearch/issues/136250), [elasticsearch#135599](https://github.com/elastic/elasticsearch/issues/135599), [elasticsearch#136281](https://github.com/elastic/elasticsearch/issues/136281), [elasticsearch#136251](https://github.com/elastic/elasticsearch/issues/136251), [elasticsearch#136272](https://github.com/elastic/elasticsearch/issues/136272)) · [Docs: clamp function](https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/conditional-functions-and-expressions#esql-clamp)

**Exponential histogram field support** — OpenTelemetry exponential histograms can now be ingested, queried via ES|QL, and downsampled in TSDB. These histograms capture value distributions (like request latency) with automatically adjusting exponential buckets, significantly reducing storage overhead while improving percentile accuracy for long-tail distributions common in microservices. ([elasticsearch#128622](https://github.com/elastic/elasticsearch/issues/128622))

**Downsampling enhancements** — Metrics downsampling now retains the last value per interval, producing a downsampled index with the same mapping as raw data. This means analytics on downsampled data are consistent with analytics on raw data — you don't need separate queries for different retention tiers. ([elasticsearch#128357](https://github.com/elastic/elasticsearch/issues/128357))

**ES|QL TS query performance (~5x faster)** — Multiple query execution improvements result in approximately 5x reduction in query latency when wildcarding or filtering by dimensions, making interactive metrics exploration significantly more responsive. ([elasticsearch#136252](https://github.com/elastic/elasticsearch/issues/136252))

**Supported schemas in Infrastructure inventory** — The inventory view now shows which schemas (ECS, OTel) are in use across your hosts, making it easier to understand data compatibility. ([#244481](https://github.com/elastic/kibana/pull/244481))

**Schema detection API** — A new API detects existing schemas in your infrastructure data, helping with migration planning and data consistency checks. ([#226597](https://github.com/elastic/kibana/pull/226597))

**Host chart filtering fix** — Charts now correctly filter by `host.name`, and CPU queries use a gap policy that includes zeros for more accurate visualization. ([#242673](https://github.com/elastic/kibana/pull/242673), [#239596](https://github.com/elastic/kibana/pull/239596))

---

## Application Performance Monitoring (APM)

Elastic APM is OpenTelemetry-native — instrument with OTel SDKs or Elastic's production-ready EDOT distributions (Java, .NET, Python, Node.js, PHP, iOS, Android) and get distributed tracing, live service dependency maps, and latency/error correlation without proprietary agents or data formats. Head- and tail-based sampling captures the critical traces without the performance tax. ML-driven correlation automatically identifies which specific attribute combinations — a deployment, a browser version, a user segment — are behind intermittent failures, going beyond simple threshold alerts.

**Observability Labs:** [EDOT Now GA](https://www.elastic.co/observability-labs/blog/elastic-distributions-opentelemetry-ga) · [Frontend Instrumentation with OTel](https://www.elastic.co/observability-labs/blog/web-frontend-instrumentation-with-opentelemetry) · [APM for iOS and Android](https://www.elastic.co/observability-labs/blog/apm-ios-android-native-apps)

**Docs:** [APM](https://www.elastic.co/observability/application-performance-monitoring) · [EDOT docs](https://elastic.github.io/opentelemetry/) · [Transaction sampling](https://www.elastic.co/docs/solutions/observability/apm/transaction-sampling)

### What's New in APM — 9.2

**Trace timeline in Discover** — The trace timeline view is now available directly in the Discover flyout, so you can see distributed trace context without leaving your ad-hoc exploration. ([#234072](https://github.com/elastic/kibana/pull/234072))

**Errors in trace context** — Errors are now shown in the context of their parent traces with error counts, badges, and span type support, making it easier to understand failures within a request flow. ([#234178](https://github.com/elastic/kibana/pull/234178), [#227413](https://github.com/elastic/kibana/pull/227413), [#227208](https://github.com/elastic/kibana/pull/227208))

**Span links with APM indices** — Span links now display when APM indices are available, giving you visibility into async and cross-service relationships. ([#232135](https://github.com/elastic/kibana/pull/232135))

**Mobile service support** — APM parameters now include mobile services, extending coverage to iOS and Android instrumented via EDOT. ([#237500](https://github.com/elastic/kibana/pull/237500))

---

## Digital Experience Monitoring

Backend metrics can look fine while your users are having a terrible time. **Synthetic monitoring** simulates user journeys from global test locations to catch problems before users hit them — with a point-and-click recorder, GitOps-managed test scripts, and failed-vs-successful run comparison. **Real user monitoring (RUM)** captures performance on actual devices, networks, and geographies with Core Web Vitals tracking and full distributed trace correlation from browser to backend. SLO dashboards track availability, latency, error budgets, and burn rates in real time.

**Observability Labs:** [Automating Synthetic Monitoring with MCP](https://www.elastic.co/observability-labs/blog/mcp-elastic-synthetics) · [From Uptime to Synthetics migration guide](https://www.elastic.co/observability-labs/blog/uptime-to-synthetics-guide) · [Synthetics GitOps](https://www.elastic.co/observability-labs/blog/synthetics-git-ops-observability)

**Docs:** [Digital experience monitoring](https://www.elastic.co/observability/digital-experience-monitoring) · [Synthetics](https://www.elastic.co/docs/solutions/observability/synthetics/) · [SLOs](https://www.elastic.co/docs/solutions/observability/incident-management/service-level-objectives-slos)

### What's New in Digital Experience — 9.2

**Sub-feature privileges for Synthetics** — Synthetics global parameters now have their own sub-feature privileges, giving admins finer control over who can view and edit monitor configurations. ([#243821](https://github.com/elastic/kibana/pull/243821))

**Public endpoint for manual test runs** — A new public API endpoint lets you trigger synthetic monitor test runs on demand, useful for CI/CD validation and ad-hoc checks. ([#227760](https://github.com/elastic/kibana/pull/227760))

**Monitor recovery alerts** — Monitor status rules now support automatic alert recovery when the monitor comes back up or when the alerting condition is no longer met. ([#229962](https://github.com/elastic/kibana/pull/229962))

**View in Discover from Synthetics alerts** — Alert details pages for Synthetics Monitor Status and TLS rules now include a "View in Discover" link for deeper investigation. ([#234104](https://github.com/elastic/kibana/pull/234104))

**Linked dashboards for SLOs** — You can now link dashboards directly to SLOs, and the alert details page shows both linked and suggested dashboards with tags for faster triage. ([#233265](https://github.com/elastic/kibana/pull/233265), [#228902](https://github.com/elastic/kibana/pull/228902))

---

## AI-Assisted Investigations

The **Elastic AI Agent** — including the **Observability Agent** — is grounded in your actual observability data and your organization's knowledgebases (runbooks, past incidents) via RAG. Ask questions in plain English, get ES|QL queries, interpreted results, and next steps specific to your environment. It also works inline, proactively annotating logs, traces, and errors with context during triage without requiring you to start a conversation. Through **Agent Builder**, you can create custom agents that execute investigative workflows, generate charts, and connect to external systems via MCP and A2A protocols.

**Observability Labs:** [Modern AIOps & Log Intelligence](https://www.elastic.co/observability-labs/blog/modern-aiops-elastic-observability) · [AI-driven incident response with logs](https://www.elastic.co/observability-labs/blog/ai-driven-incident-response-with-logs) · [Agent Builder & OTel for Observability](https://www.elastic.co/observability-labs/blog/agent-builder-opentelemetry) · [Context-aware agentic workflows](https://www.elastic.co/search-labs/blog/series/context-aware-ai-agentic-workflows-with-elastic) · [Unifying data with OTel and GenAI](https://www.elastic.co/observability-labs/blog/the-next-evolution-of-observability-unifying-data-with-opentelemetry-and-generative-ai)

**Docs:** [AIOps](https://www.elastic.co/observability/aiops) · [Agent Builder](https://www.elastic.co/elasticsearch/agent-builder) · [Built-in Agents](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/builtin-agents-reference)

### What's New in AI-Assisted Investigations — 9.2

**Integration-aware knowledge base** — The AI Agent is now aware of LLM-facing documentation for integrations installed in your cluster, so it can reference integration-specific context during investigations. ([#237085](https://github.com/elastic/kibana/pull/237085))

**Unified knowledge base settings** — Installation settings for Knowledge Base and Product Docs are now consolidated into a single location, simplifying setup. ([#232559](https://github.com/elastic/kibana/pull/232559), [#228695](https://github.com/elastic/kibana/pull/228695))

**Native function calling for self-managed LLMs** — The AI Agent now supports native function calling for self-managed LLMs and OpenAI-compatible providers, expanding beyond hosted model support. ([#232109](https://github.com/elastic/kibana/pull/232109), [#232097](https://github.com/elastic/kibana/pull/232097))

**Improved Gemini prompts** — Prompts for Google Gemini models have been refined for better response quality in observability investigations. ([#223476](https://github.com/elastic/kibana/pull/223476))

**GenAI Settings in Stack Management** — AI Agent visibility and configuration settings are now centralized under a new GenAI Settings page in Stack Management. ([#227289](https://github.com/elastic/kibana/pull/227289), [#233727](https://github.com/elastic/kibana/pull/233727))

**Raw request tracing for LLM connectors** — The `raw_request` field is now included in traces for `.gen-ai`, `.gemini`, and `.bedrock` connectors, giving you full visibility into what's being sent to your LLM providers. ([#232229](https://github.com/elastic/kibana/pull/232229))

---

## LLM and GenAI Observability

If you're running AI-powered applications in production, you need to monitor them like any other critical service. Elastic provides prebuilt dashboards for OpenAI, Amazon Bedrock, Azure AI Foundry, and Google Vertex AI — tracking invocation counts, error rates, latency, token usage, and cost by model. For agentic workflows, instrument LangChain and other frameworks via EDOT or third-party libraries (LangTrace, OpenLIT, OpenLLMetry) to get step-by-step tracing of the full LLM execution path. Guardrails monitoring covers prompt injection detection, sensitive data leakage, and content safety policy adherence.

**Observability Labs:** [LLM observability with Elastic](https://www.elastic.co/observability-labs/blog/llm-observability-elastic) · [OpenAI integration](https://www.elastic.co/observability-labs/blog/llm-observability-openai) · [Amazon Bedrock AgentCore](https://www.elastic.co/observability-labs/blog/llm-agentic-ai-observability-amazon-bedrock-agentcore) · [Azure AI Foundry](https://www.elastic.co/observability-labs/blog/llm-observability-azure-ai-foundry) · [Tracing OpenAI with OTel](https://www.elastic.co/observability-labs/blog/elastic-opentelemetry-openai) · [LangChain tracing with LangTrace](https://www.elastic.co/observability-labs/blog/elastic-opentelemetry-langchain-tracing-langtrace)

**Docs:** [LLM monitoring](https://www.elastic.co/observability/llm-monitoring) · [LLM observability docs](https://www.elastic.co/docs/solutions/observability/applications/llm-observability)

---

## Query, Analysis, and Machine Learning

**ES|QL** is Elastic's piped query language for ad-hoc investigation — chain filter, transform, join, and aggregate operations across logs, metrics, and traces in a single query. Recent additions include time series functions (RATE, window functions), LOOKUP JOIN for enriching data at query time without denormalizing at ingest, and native OTel exponential histogram support. **Machine learning** runs 100+ preconfigured anomaly detection jobs out of the box across all your data, with guided workflows for custom forecasting, classification, and regression when you need them. Together they give you two investigation modes: the intentional query when you know what you're looking for, and always-on detection for the things you didn't.

**Observability Labs:** [ES|QL Joins for Observability](https://www.elastic.co/observability-labs/blog/elastic-esql-join-observability) · [Metrics with ES|QL + Discover](https://www.elastic.co/observability-labs/blog/metrics-explore-analyze-with-esql-discover) · [Metrics analytics 5x faster](https://www.elastic.co/observability-labs/blog/elastic-metrics-analytics)

**Docs:** [ES|QL](https://www.elastic.co/docs/explore-analyze/query-filter/languages/esql) · [Machine Learning](https://www.elastic.co/elasticsearch/machine-learning) · [Anomaly detection jobs](https://www.elastic.co/docs/explore-analyze/machine-learning/anomaly-detection/ml-anomaly-detection-job-types)

### What's New in Query, Analysis, and Alerting — 9.2

**View in Discover from alert details** — Alert details pages now include "View in Discover" links across SLO burn rate, ES query, Synthetics, and other rule types, giving you one click from alert to full investigation context. ([#233259](https://github.com/elastic/kibana/pull/233259), [#233855](https://github.com/elastic/kibana/pull/233855), [#234104](https://github.com/elastic/kibana/pull/234104))

**Time-ranged dashboard links from alerts** — Links from alert details to related dashboards now include the relevant time range, so dashboards open scoped to the incident window. ([#230601](https://github.com/elastic/kibana/pull/230601))

**Filters and saved queries in custom threshold rules** — Custom threshold alert rules now support saved queries and filters, making it easier to reuse complex conditions. ([#229453](https://github.com/elastic/kibana/pull/229453))

**API key deletion warnings** — Deleting API keys that are currently in use by alerting rules now shows a warning to prevent accidentally breaking active alerts. ([#243353](https://github.com/elastic/kibana/pull/243353))

**Improved case management** — You can now paste screenshots directly into case markdown comments, attach any event (not just alerts) to cases, and case observables are automatically extracted when attaching alerts. ([#226077](https://github.com/elastic/kibana/pull/226077), [#230970](https://github.com/elastic/kibana/pull/230970), [#233027](https://github.com/elastic/kibana/pull/233027))

---

## OpenTelemetry

Elastic is built on OpenTelemetry as its primary data collection standard — not as an add-on. **EDOT** (Elastic Distributions of OpenTelemetry) is a production-ready, fully open OTel distribution with the Collector and auto-instrumentation SDKs for Java, .NET, Python, Node.js, PHP, iOS, and Android, backed by enterprise-grade support with all enhancements contributed upstream. OTel data flows into Elasticsearch in its native format — no schema conversions — so semantic conventions are preserved and you can correlate any signal using standard resource attributes. Elastic is a top-three contributor to the OTel project, having donated ECS to OTel Semantic Conventions and its Universal Profiling agent.

**Observability Labs:** [EDOT Now GA](https://www.elastic.co/observability-labs/blog/elastic-distributions-opentelemetry-ga) · [OTel Data Quality with Instrumentation Score](https://www.elastic.co/observability-labs/blog/otel-instrumentation-score) · [Correlate OTel traces with ECS logs](https://www.elastic.co/observability-labs/blog/otel-ecs-unification-elastic) · [EDOT SDK config with OpAmp](https://www.elastic.co/observability-labs/blog/elastic-distribution-opentelemetry-sdk-central-configuration-opamp) · [EDOT PHP joins OTel](https://www.elastic.co/observability-labs/blog/opentelemetry-accepts-elastics-donation-of-edot) · [A day in the life of an OTel maintainer](https://www.elastic.co/observability-labs/blog/day-opentelemetry-maintainer)

**Docs:** [OpenTelemetry](https://www.elastic.co/observability/opentelemetry) · [EDOT docs](https://elastic.github.io/opentelemetry/) · [EDOT quickstart](https://elastic.github.io/opentelemetry/quickstart/)

### What's New in OpenTelemetry — 9.2

**EDOT Node.js agent configuration** — New `send_traces`, `send_metrics`, and `send_logs` settings let you selectively control which signal types the EDOT Node.js agent sends, reducing noise when you only need specific telemetry. ([#233798](https://github.com/elastic/kibana/pull/233798))

**OpAmp central config for EDOT agents** — `opamp_polling_interval` and `sampling_rate` settings are now available in central configuration for EDOT application agents, enabling fleet-wide tuning without redeploying. ([#231835](https://github.com/elastic/kibana/pull/231835))
