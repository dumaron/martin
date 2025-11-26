#!/bin/bash

# Script to upload Berkeley Mono fonts from macOS to Fly.io volume
# Usage: ./scripts/upload-berkeley-mono.sh

set -e  # Exit on error

# Configuration
APP_NAME="martin-duma"
LOCAL_FONT_DIR="$HOME/Library/Fonts"
REMOTE_FONT_DIR="/storage/fonts"
TEMP_DIR=$(mktemp -d)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Berkeley Mono Font Upload Script${NC}"
echo "=================================="
echo ""

# Check if fly CLI is installed
if ! command -v fly &> /dev/null; then
	echo -e "${RED}Error: fly CLI is not installed${NC}"
	echo "Install it from: https://fly.io/docs/hands-on/install-flyctl/"
	exit 1
fi

# Check if logged in to Fly.io
if ! fly auth whoami &> /dev/null; then
	echo -e "${RED}Error: Not logged in to Fly.io${NC}"
	echo "Run: fly auth login"
	exit 1
fi

# Create temporary directory for fonts
FONT_TEMP_DIR="$TEMP_DIR/berkeley-mono"
mkdir -p "$FONT_TEMP_DIR"

# Copy Berkeley Mono fonts to temp directory
echo -e "${YELLOW}Copying Berkeley Mono fonts...${NC}"
FONT_COUNT=$(ls "$LOCAL_FONT_DIR"/BerkeleyMono* 2>/dev/null | wc -l | tr -d ' ')

if [ "$FONT_COUNT" -eq 0 ]; then
	echo -e "${RED}Error: No Berkeley Mono fonts found in $LOCAL_FONT_DIR${NC}"
	rm -rf "$TEMP_DIR"
	exit 1
fi

cp "$LOCAL_FONT_DIR"/BerkeleyMono* "$FONT_TEMP_DIR/"
echo -e "${GREEN}Found and copied $FONT_COUNT font files${NC}"

# Create tarball
TARBALL="$TEMP_DIR/berkeley-mono-fonts.tar.gz"
echo -e "${YELLOW}Creating tarball...${NC}"
tar -czf "$TARBALL" -C "$TEMP_DIR" berkeley-mono
echo -e "${GREEN}Tarball created: $TARBALL${NC}"

# Get the first running machine or start one if none are running
echo -e "${YELLOW}Finding Fly.io machine...${NC}"
MACHINE_ID=$(fly machines list --app "$APP_NAME" --json | jq -r '.[0].id' 2>/dev/null)

if [ -z "$MACHINE_ID" ] || [ "$MACHINE_ID" == "null" ]; then
	echo -e "${RED}Error: No machines found for app $APP_NAME${NC}"
	rm -rf "$TEMP_DIR"
	exit 1
fi

echo -e "${GREEN}Using machine: $MACHINE_ID${NC}"

# Upload tarball to Fly.io machine
echo -e "${YELLOW}Uploading fonts to Fly.io...${NC}"
fly ssh sftp shell --app "$APP_NAME" --machine "$MACHINE_ID" <<EOF
put $TARBALL /tmp/berkeley-mono-fonts.tar.gz
EOF

# Extract and move fonts on the remote machine
echo -e "${YELLOW}Extracting fonts on remote machine...${NC}"
fly ssh console --app "$APP_NAME" --machine "$MACHINE_ID" --command "
	set -e
	mkdir -p $REMOTE_FONT_DIR
	cd /tmp
	tar -xzf berkeley-mono-fonts.tar.gz
	mv berkeley-mono/* $REMOTE_FONT_DIR/
	rm -rf berkeley-mono berkeley-mono-fonts.tar.gz
	ls -lh $REMOTE_FONT_DIR | head -10
	echo ''
	echo 'Total fonts installed:'
	ls -1 $REMOTE_FONT_DIR | wc -l
"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}✓ Berkeley Mono fonts successfully uploaded to $REMOTE_FONT_DIR${NC}"
echo ""
echo "To verify the fonts, run:"
echo "  fly ssh console --app $APP_NAME -C 'ls -lh $REMOTE_FONT_DIR'"
