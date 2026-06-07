#!/usr/bin/env python3
"""Upload report fonts (Berkeley Mono, Public Sans) from macOS to Fly.io volume.

`fly sftp put` refuses to overwrite existing files, so already-uploaded fonts are skipped.
"""

import subprocess
import sys
from pathlib import Path

LOCAL_FONT_DIR = Path.home() / 'Library' / 'Fonts'
REMOTE_FONT_DIR = '/storage/fonts'
FONT_GLOBS = ('BerkeleyMono*', 'PublicSans*')


def run(cmd, capture=False):
	"""Execute shell command, optionally returning captured stdout."""
	return subprocess.run(cmd, check=True, capture_output=capture, text=True)


def find_fonts(font_dir):
	"""Find all report fonts in directory."""
	fonts = [font for glob in FONT_GLOBS for font in font_dir.glob(glob)]
	if not fonts:
		sys.exit(f'Error: No fonts matching {FONT_GLOBS} found in {font_dir}')
	return fonts


def create_remote_directory(remote_dir):
	"""Ensure remote font directory exists."""
	run(['fly', 'ssh', 'console', '--command', f'mkdir -p {remote_dir}'])


def remote_font_names(remote_dir):
	"""Names of files already present in the remote font directory."""
	result = run(['fly', 'ssh', 'console', '--command', f'ls -1 {remote_dir}'], capture=True)
	return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def upload_font(font_path, remote_dir):
	"""Upload a single font file to Fly.io."""
	run(['fly', 'sftp', 'put', font_path, f'{remote_dir}/{font_path.name}'])


def main():
	fonts = find_fonts(LOCAL_FONT_DIR)
	create_remote_directory(REMOTE_FONT_DIR)
	existing = remote_font_names(REMOTE_FONT_DIR)

	pending = [f for f in fonts if f.name not in existing]
	skipped = len(fonts) - len(pending)
	if skipped:
		print(f'Skipping {skipped} font(s) already present on the volume')

	for i, font in enumerate(pending, 1):
		print(f'  [{i}/{len(pending)}] {font.name}')
		upload_font(font, REMOTE_FONT_DIR)

	print(f'\nSuccessfully uploaded {len(pending)} fonts to {REMOTE_FONT_DIR}')


if __name__ == '__main__':
	main()
