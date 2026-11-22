#!/bin/bash

# Navigate to the folder containing this script
cd "$(dirname "$0")"

# Terminal Color Codes
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear

echo -e "${CYAN}"
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║                                                              ║"
echo "  ║                ✍️   HANDWRITING STUDIO                       ║"
echo "  ║          Digital Text to Realistic Handwriting               ║"
echo "  ║                                                              ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[Error] Python 3 is not installed or not in PATH.${NC}"
    echo "Please install Python 3 from https://www.python.org/ or via Homebrew: brew install python"
    read -p "Press Enter to exit..."
    exit 1
fi

PYTHON_VER=$(python3 --version)
echo -e "${BLUE}▶ Detected Python:${NC} $PYTHON_VER"

# Check & auto-install dependencies if missing
echo -e "${BLUE}▶ Checking dependencies (Flask, Pillow)...${NC}"
python3 -c "import flask, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}  Required packages missing. Installing Flask and Pillow...${NC}"
    python3 -m pip install flask pillow
    if [ $? -ne 0 ]; then
        echo -e "${RED}[Error] Failed to install required packages.${NC}"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi
echo -e "${GREEN}✓ All dependencies ready!${NC}\n"

# Port Selection (macOS AirPlay uses 5000, so we use 5050 by default)
PORT=5050

# Check if port 5050 is busy; if so, find next free port
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; do
    PORT=$((PORT + 1))
done

export PORT=$PORT

echo -e "${CYAN}==============================================================${NC}"
echo -e "${GREEN}${BOLD}  🚀 Starting Handwriting Studio Server...${NC}"
echo -e "  🌐 Web Address: ${BOLD}http://localhost:${PORT}${NC}"
echo -e "${CYAN}==============================================================${NC}"
echo -e "\n${YELLOW}💡 Press [ Ctrl + C ] in this terminal window to stop the server.${NC}\n"

# Automatically open the browser after 1.5 seconds in background
(sleep 1.5 && open "http://localhost:${PORT}") &

# Start Flask Web App in foreground
python3 app.py
