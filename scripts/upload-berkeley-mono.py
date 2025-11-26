#!/usr/bin/env python3
"""Upload Berkeley Mono fonts from macOS to Fly.io volume."""

import subprocess
import sys
from pathlib import Path

LOCAL_FONT_DIR = Path.home() / 'Library' / 'Fonts'
REMOTE_FONT_DIR = '/storage/fonts'


def run(cmd, check=True, capture=False):
	"""Execute shell command with optional output capture."""
	return subprocess.run(
		cmd,
		check=check,
		capture_output=capture,
		text=True
	)


def find_fonts(font_dir):
	"""Find all Berkeley Mono fonts in directory."""
	fonts = list(font_dir.glob('BerkeleyMono*'))
	if not fonts:
		sys.exit(f'Error: No Berkeley Mono fonts found in {font_dir}')
	return fonts


def create_remote_directory(remote_dir):
	"""Ensure remote font directory exists."""
	run(['fly', 'ssh', 'console', '--command', f'mkdir -p {remote_dir}'])


def upload_font(font_path, remote_dir):
	"""Upload a single font file to Fly.io."""
	run(['fly', 'sftp', 'put', font_path, f'{remote_dir}/{font_path.name}'])


def main():
	fonts = find_fonts(LOCAL_FONT_DIR)
	create_remote_directory(REMOTE_FONT_DIR)

	for i, font in enumerate(fonts, 1):
		print(f'  [{i}/{len(fonts)}] {font.name}')
		upload_font(font, REMOTE_FONT_DIR)

	print(f'\nSuccessfully uploaded {len(fonts)} fonts to {REMOTE_FONT_DIR}')


if __name__ == '__main__':
	main()
