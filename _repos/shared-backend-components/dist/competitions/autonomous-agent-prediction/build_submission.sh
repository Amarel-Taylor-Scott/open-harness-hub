#!/usr/bin/env bash
# Package the ADK Agent Config into submission.zip with agent.yaml at the archive ROOT.
set -e
cd "$(dirname "$0")"
rm -f submission.zip
zip -r submission.zip agent.yaml prompts skills -x '*/__pycache__/*' '*.pyc'
echo "built: $(pwd)/submission.zip"
unzip -l submission.zip
