#!/usr/bin/env bash
# AgentAudit Skill — One-Line Installer
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/starbuck100/agentaudit-skill/main/install.sh | bash
#
# Or with a specific platform:
#   curl -sSL https://raw.githubusercontent.com/starbuck100/agentaudit-skill/main/install.sh | bash -s -- --platform claude
#
# Platforms: claude, cursor, windsurf, copilot, openclaw

set -euo pipefail

# Colors (disabled if not a terminal)
if [ -t 1 ]; then
  GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; BLUE=''; NC=''
fi

info()  { echo -e "${BLUE}ℹ${NC}  $*"; }
ok()    { echo -e "${GREEN}✅${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠️${NC}  $*" >&2; }
fail()  { echo -e "${RED}❌${NC} $*" >&2; exit 1; }

# ── Dependencies ──
for cmd in git curl jq; do
  command -v "$cmd" &>/dev/null || fail "Required: $cmd — install it first."
done

# ── Parse args ──
PLATFORM=""
AGENT_NAME=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform|-p) PLATFORM="$2"; shift 2 ;;
    --agent|-a)    AGENT_NAME="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: install.sh [--platform <claude|cursor|windsurf|copilot|openclaw>] [--agent <name>]"
      exit 0 ;;
    *) shift ;;
  esac
done

# ── Detect platform if not specified ──
if [ -z "$PLATFORM" ]; then
  if [ -d "$HOME/.claude" ]; then
    PLATFORM="claude"
  elif [ -d "$HOME/.cursor" ]; then
    PLATFORM="cursor"
  elif [ -d "$HOME/.windsurf" ]; then
    PLATFORM="windsurf"
  else
    PLATFORM="claude"  # Default
  fi
  info "Auto-detected platform: $PLATFORM"
fi

# ── Determine install directory ──
case "$PLATFORM" in
  claude)   SKILLS_DIR="$HOME/.claude/skills" ;;
  cursor)   SKILLS_DIR="$HOME/.cursor/skills" ;;
  windsurf) SKILLS_DIR="$HOME/.windsurf/skills" ;;
  copilot)  SKILLS_DIR=".github/skills" ;;
  openclaw)
    if command -v clawhub &>/dev/null; then
      info "Installing via ClawHub..."
      clawhub install agentaudit
      ok "Installed via ClawHub."
      exit 0
    else
      fail "ClawHub not found. Install OpenClaw first or use --platform claude"
    fi ;;
  *) fail "Unknown platform: $PLATFORM. Use: claude, cursor, windsurf, copilot, openclaw" ;;
esac

INSTALL_DIR="$SKILLS_DIR/agentaudit"

# ── Check if already installed ──
if [ -d "$INSTALL_DIR" ] || [ -L "$INSTALL_DIR" ]; then
  warn "AgentAudit already installed at $INSTALL_DIR"
  echo "  To update: cd $INSTALL_DIR && git pull"
  echo "  To reinstall: rm -rf $INSTALL_DIR && re-run this script"
  exit 0
fi

# ── Clone ──
info "Cloning agentaudit-skill..."
CLONE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/agentaudit-skill"
mkdir -p "$(dirname "$CLONE_DIR")"

if [ -d "$CLONE_DIR" ]; then
  info "Updating existing clone..."
  git -C "$CLONE_DIR" pull --quiet
else
  git clone --depth 1 https://github.com/starbuck100/agentaudit-skill.git "$CLONE_DIR"
fi
ok "Cloned to $CLONE_DIR"

# ── Symlink ──
mkdir -p "$SKILLS_DIR"
ln -sf "$CLONE_DIR" "$INSTALL_DIR"
ok "Linked to $INSTALL_DIR"

# ── Verify integrity ──
info "Verifying skill integrity..."
if bash "$CLONE_DIR/scripts/verify.sh" agentaudit 2>/dev/null; then
  ok "Integrity verified"
else
  warn "Integrity check failed or registry unreachable — verify manually later"
fi

# ── Register agent ──
if [ -z "$AGENT_NAME" ]; then
  # Generate default name from hostname + platform
  AGENT_NAME="${PLATFORM}-$(hostname -s 2>/dev/null || echo 'agent')"
  AGENT_NAME=$(echo "$AGENT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9._-]/-/g' | head -c 64)
fi

CRED_FILE="$CLONE_DIR/config/credentials.json"
USER_CRED="${XDG_CONFIG_HOME:-$HOME/.config}/agentaudit/credentials.json"

if [ -f "$CRED_FILE" ] || [ -f "$USER_CRED" ]; then
  ok "Already registered (credentials found)"
else
  info "Registering agent '$AGENT_NAME'..."
  if bash "$CLONE_DIR/scripts/register.sh" "$AGENT_NAME"; then
    ok "Registered as '$AGENT_NAME'"
  else
    warn "Registration failed — register manually: bash $CLONE_DIR/scripts/register.sh your-name"
  fi
fi

# ── Done ──
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  AgentAudit installed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "  Platform:  $PLATFORM"
echo "  Location:  $INSTALL_DIR → $CLONE_DIR"
echo "  Agent:     $AGENT_NAME"
echo ""
echo "  Test it:"
echo "    bash $INSTALL_DIR/scripts/check.sh lodash"
echo ""
echo "  Restart your agent ($PLATFORM) to activate the security gate."
echo ""
