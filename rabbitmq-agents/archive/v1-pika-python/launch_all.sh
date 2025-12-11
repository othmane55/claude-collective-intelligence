#!/bin/bash
#
# RabbitMQ Multi-Agent System Launcher
# ====================================
# ULTRATHINK Implementation - ETK Compliant
#
# Opens 3 VS Code terminals:
# - Terminal 1: Guardian Agent (Team Leader)
# - Terminal 2: Plugin Lifecycle Worker
# - Terminal 3: Plugin Manifest Worker
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  RabbitMQ Multi-Agent System Launcher"
echo "=============================================="
echo ""
echo "Working directory: $SCRIPT_DIR"
echo ""

# Check RabbitMQ is running
echo "[1/4] Checking RabbitMQ..."
if ! pgrep -x "rabbitmq-server" > /dev/null && ! pgrep -x "beam.smp" > /dev/null; then
    echo "WARNING: RabbitMQ may not be running!"
    echo "Start with: brew services start rabbitmq"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "[OK] RabbitMQ appears to be running"
fi

# Check Python dependencies
echo ""
echo "[2/4] Checking Python dependencies..."
python3 -c "import pika; import colorama" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt --user
fi
echo "[OK] Dependencies ready"

# Launch VS Code terminals using osascript
echo ""
echo "[3/4] Opening VS Code terminals..."

# Use osascript directly with escaped characters
osascript -e 'tell application "Visual Studio Code" to activate' -e 'delay 0.5'

osascript -e '
tell application "System Events"
    tell process "Code"
        keystroke "`" using {command down, shift down}
    end tell
end tell
'
sleep 2

# Now open Terminal app for easier management
open -a Terminal "$SCRIPT_DIR"
sleep 1

echo ""
echo "Terminal opened. Run these commands in separate tabs:"
echo ""
echo "  Tab 1: python3 guardian_leader.py"
echo "  Tab 2: python3 worker_lifecycle.py"
echo "  Tab 3: python3 worker_manifest.py"
echo ""

echo "[OK] Terminals launched"
echo ""
echo "[4/4] Setup complete!"
echo ""
echo "=============================================="
echo "  Multi-Agent System Ready"
echo "=============================================="
echo ""
echo "Terminal 1: Guardian Agent (Team Leader)"
echo "Terminal 2: Plugin Lifecycle Worker"
echo "Terminal 3: Plugin Manifest Worker"
echo ""
echo "Guardian Commands:"
echo "  > help                    - Show all commands"
echo "  > validate plugin <name>  - Validate plugin"
echo "  > health <plugin>         - Check health"
echo "  > diagnose <plugin>       - Diagnose issues"
echo "  > list workers            - Show workers"
echo "  > quit                    - Exit"
echo ""
