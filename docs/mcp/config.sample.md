# MCP Config (sample)

Set these environment variables before using MCP-enabled modes:

- `REF_API_KEY`        # Ref (ref-tools)
- `CONTEXT7_API_KEY`   # Context7 (Upstash)
- `EXA_API_KEY`        # Exa MCP
- `SONAR_API_KEY`      # Perplexity (Sonar)

Playwright MCP:
- Ensure Node 18+ and a runnable browser environment
- Maintain an allowlist in `project/<id>/control/playwright-origins.json`
