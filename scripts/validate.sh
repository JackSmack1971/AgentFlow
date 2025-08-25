#!/usr/bin/env bash
set -euo pipefail
if ! command -v ajv >/dev/null 2>&1; then
  echo "Installing ajv-cli and yaml-js locally..."
  npm i -g ajv-cli yaml-js
fi
ajv validate -s docs/contracts/state_v1.schema.json -d project/sample-app/control/state.json
node -e "console.log(JSON.stringify(require('yaml-js').load(require('fs').readFileSync('project/sample-app/control/backlog.yaml','utf8'))))" > /tmp/backlog.json
ajv validate -s docs/contracts/backlog_v1.schema.json -d /tmp/backlog.json
node -e "console.log(JSON.stringify(require('yaml-js').load(require('fs').readFileSync('project/sample-app/control/sprint.yaml','utf8'))))" > /tmp/sprint.json
ajv validate -s docs/contracts/sprint_v1.schema.json -d /tmp/sprint.json
echo "All good âœ…"
