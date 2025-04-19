#!/bin/bash
cd "$(dirname "$0")"

# Prevent parallel execution
if pgrep -f "python3 -m grammy" > /dev/null; then
  exit 0
fi

# Create .venv if it doesn't exist
if [ ! -d .venv ]; then
  echo "🛠️ Creating virtual environment..."
  python3 -m venv .venv || {
    echo "❌ Failed to create virtual environment." >&2
    exit 1
  }
fi

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies if needed
if ! python3 -c "import instagrapi" &> /dev/null; then
  echo "📦 Installing dependencies..."
  pip install --break-system-packages -r requirements.txt || {
    echo "❌ Failed to install dependencies." >&2
    exit 1
  }
fi

# Ensure root project directory is in PYTHONPATH
export PYTHONPATH="$PWD"

exec python3 -m grammy "$@"