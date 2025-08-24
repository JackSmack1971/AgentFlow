# MCP Playbook — SPARC Autonomous Adversary

Goal: surface **high-impact risks** fast, prove them with evidence, and validate mitigations.

## When to Use What
- **Real-world incidents / attack patterns / regulatory actions** → **Exa** (enumerate) → **Perplexity** (synthesize)
- **Reproducible risky flows** (abuse paths, rate limits, upload bypass) → **Playwright**
- **API/library edge behavior** (security-critical) → **Ref** (exact docs), optionally **Context7** for version-specific info

## Outputs (always)
- Adversarial scenarios: `project/<projectId>/adversarial/<scenario-id>/*`
- Risk register deltas: `project/<projectId>/risk-assessment/<date>-<topic>.md`
- Playwright evidence (screens/har): see directories below

## Query Templates

### Exa Search
```json
{
  "tool": "web_search_exa",
  "args": {
    "query": "S3 presigned URL security bypass upload malware 2024..2025",
    "freshness": "365d",
    "site_filters": ["aws.amazon.com", "portswigger.net", "owasp.org", "hackerone.com"]
  },
  "expected_artifact": "project/<projectId>/evidence/research/exa/s3-presigned-bypass/results.json"
}
Perplexity Ask
json
Copy
Edit
{
  "tool": "perplexity_ask",
  "args": {
    "messages": [
      { "role": "system", "content": "Cite sources; enumerate exploit preconditions and mitigations." },
      { "role": "user", "content": "Synthesize common bypasses against presigned S3 uploads (≤365d). Prioritize these sources: <urls from Exa>." }
    ]
  },
  "expected_artifact": "project/<projectId>/evidence/research/perplexity/s3-presigned-bypass.md"
}
Playwright MCP (abuse flow reproduction)
json
Copy
Edit
{
  "scenario": "upload-content-type-bypass",
  "steps": [
    { "tool": "navigate", "args": { "url": "https://example.com/upload" } },
    { "tool": "type", "args": { "selector": "#file", "text": "/path/to/eicar.txt" } },
    { "tool": "evaluate", "args": { "script": "window.fetchInterceptor=1" } },
    { "tool": "screenshot", "args": { "path": "project/<projectId>/adversarial/playwright/upload-content-type-bypass/01.png" } }
  ],
  "artifacts_dir": "project/<projectId>/adversarial/playwright/upload-content-type-bypass/"
}
Ref (ref-tools)
json
Copy
Edit
{
  "tool": "ref_read_url",
  "args": { "url": "https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-streaming.html" },
  "expected_artifact": "project/<projectId>/evidence/research/ref/aws/s3-sigv4-streaming.md"
}
Context7 (optional)
json
Copy
Edit
{
  "tool": "context7_inject",
  "args": {
    "library": "@aws-sdk/client-s3",
    "version": "3.x",
    "topics": ["PutObject", "SignatureV4", "content-type validation"]
  },
  "expected_artifact": "project/<projectId>/evidence/research/context7/@aws-sdk/client-s3@3.x.md"
}
Evidence & Paths
Exa: project/<projectId>/evidence/research/exa/<topic>/{results.json,notes.md}

Perplexity: project/<projectId>/evidence/research/perplexity/<topic>.md

Ref/Context7: project/<projectId>/evidence/research/(ref|context7)/<topic>.md

Playwright:

Steps JSON: project/<projectId>/adversarial/playwright/<scenario>/steps.json

Screens: project/<projectId>/adversarial/playwright/<scenario>/*.png

Logs/HAR (if captured): project/<projectId>/adversarial/playwright/<scenario>/*.har

Logging & Compliance
Append every MCP interaction to: project/<projectId>/control/mcp-usage.log.jsonl

Scrub secrets and PII from logs and screenshots

Maintain allowed origins for Playwright in project/<projectId>/control/playwright-origins.json

Go/No-Go Gate (default)
Do not approve if mitigations < 95% coverage of discovered high-risk issues.

Include detection & response checks (metrics, alerts) in every scenario write-up.