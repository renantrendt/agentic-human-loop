#!/bin/bash
set -e

echo "=========================================="
echo "  Content Agent Claw — OpenShell Setup"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POLICIES_DIR="$SCRIPT_DIR/policies"

# Verify OpenShell is installed
if ! command -v openshell &> /dev/null; then
    echo "Installing OpenShell..."
    curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "OpenShell: $(openshell --version 2>/dev/null || echo 'installed')"

# Verify Docker is running
if ! docker info &> /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Start Docker first."
    exit 1
fi

echo ""
echo "Step 1: Setting up credential providers..."

# Create providers for each subagent (credentials injected as env vars, never on disk)
if [ -n "$ANTHROPIC_API_KEY" ]; then
    openshell provider create --type anthropic --from-existing 2>/dev/null || true
    echo "  ✓ Anthropic provider"
fi

if [ -n "$YOUTUBE_API_KEY" ]; then
    openshell provider create --type custom --name youtube \
        --env YOUTUBE_API_KEY="$YOUTUBE_API_KEY" 2>/dev/null || true
    echo "  ✓ YouTube provider"
fi

if [ -n "$RESEND_API_KEY" ]; then
    openshell provider create --type custom --name resend \
        --env RESEND_API_KEY="$RESEND_API_KEY" 2>/dev/null || true
    echo "  ✓ Resend provider"
fi

if [ -n "$FRAMER_API_KEY" ]; then
    openshell provider create --type custom --name framer \
        --env FRAMER_API_KEY="$FRAMER_API_KEY" 2>/dev/null || true
    echo "  ✓ Framer provider"
fi

echo ""
echo "Step 2: Creating sandboxes..."

# Monitor agent — Reddit + YouTube scraping (no credentials)
echo "  Creating monitor-agent sandbox..."
openshell sandbox create --name monitor-agent \
    --policy "$POLICIES_DIR/monitor-agent.yaml" 2>/dev/null || true

# Analyst agent — clustering + gap detection (Claude only)
echo "  Creating analyst-agent sandbox..."
openshell sandbox create --name analyst-agent \
    --policy "$POLICIES_DIR/analyst-agent.yaml" 2>/dev/null || true

# Writer agent — article generation (Claude only)
echo "  Creating writer-agent sandbox..."
openshell sandbox create --name writer-agent \
    --policy "$POLICIES_DIR/writer-agent.yaml" 2>/dev/null || true

# Publisher agent — Framer CMS (Framer key only, no Claude)
echo "  Creating publisher-agent sandbox..."
openshell sandbox create --name publisher-agent \
    --policy "$POLICIES_DIR/publisher-agent.yaml" 2>/dev/null || true

# Reviewer agent — email digest + Gmail polling (Resend + Gmail)
echo "  Creating reviewer-agent sandbox..."
openshell sandbox create --name reviewer-agent \
    --policy "$POLICIES_DIR/reviewer-agent.yaml" 2>/dev/null || true

echo ""
echo "Step 3: Verifying sandboxes..."
openshell sandbox list

echo ""
echo "=========================================="
echo "  Claw setup complete!"
echo "=========================================="
echo ""
echo "  Run the claw:  python3 openshell/claw.py"
echo "  Monitor:       openshell term"
echo "  Logs:          openshell logs <sandbox-name> --tail"
echo ""
