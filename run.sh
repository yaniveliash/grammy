#!/bin/bash
cd "$(dirname "$0")"

# Prevent parallel execution
if pgrep -f "python3 grammy.py" > /dev/null; then
  exit 0
fi

# Activate virtualenv and run
source .venv/bin/activate
python3 grammy.py "$@"
