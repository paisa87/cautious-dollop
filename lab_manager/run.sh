#!/bin/bash
# ─────────────────────────────────────────────
#  VG Lab Manager — Mac / Linux launcher
# ─────────────────────────────────────────────

cd "$(dirname "$0")"

echo ""
echo "  VG Lab Manager — Starting up..."
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "  ERROR: Python 3 is not installed."
    echo "  Download it from https://www.python.org/downloads/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "  First-time setup: creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install/update dependencies quietly
echo "  Checking dependencies..."
pip install -q -r requirements.txt

echo ""
echo "  ✓ Ready! Open your browser to:  http://localhost:5000"
echo ""
echo "  Default login:  username = admin   password = labadmin"
echo "  (Change the password after your first login!)"
echo ""
echo "  Press Ctrl+C to stop the server."
echo ""

# Open browser after a short delay (background)
(sleep 2 && open "http://localhost:5000" 2>/dev/null || xdg-open "http://localhost:5000" 2>/dev/null) &

python3 app.py
