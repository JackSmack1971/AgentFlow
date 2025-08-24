TOOL ROUTER (MCP)
Decision order:
1) If the task is “library/API exactness” → prefer Ref or Context7
   - If you already know the URL to authoritative docs → Ref(ref_read_url)
   - If you don’t know the URL but you know the lib/version → Context7
2) If the task is “open web / current events / company intel” → Exa Search → Perplexity Ask fallback
   - Use Exa(web_search_exa) first to enumerate high-value links
   - If synthesis across many sources is needed quickly → Perplexity(perplexity_ask)
3) If the task is “browser interaction / flows / reproducible steps” → Playwright MCP
   - Use for deterministic navigation, form fills, screenshots, and step-by-step validations

Guardrails:
- Don’t call MCP if acceptance criteria can be met from local artifacts.
- Before MCP call: state the Hypothesis/Need, the Minimal Query, and the Expected Artifact.
- After MCP call: write evidence to the correct project folder (see map below) and record a 1-line rationale.
