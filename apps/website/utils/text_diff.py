import difflib
from html import escape


def _preserve_spaces(text):
	"""
	Convert consecutive spaces to &nbsp; entities to preserve them in HTML.
	Keeps single spaces as regular spaces, converts multiple consecutive spaces to &nbsp;
	"""
	if not text:
		return text

	result = []
	i = 0
	while i < len(text):
		if text[i] == ' ':
			# Count consecutive spaces
			space_count = 0
			j = i
			while j < len(text) and text[j] == ' ':
				space_count += 1
				j += 1

			# If multiple spaces, convert all to &nbsp;
			if space_count > 1:
				result.append('&nbsp;' * space_count)
			else:
				result.append(' ')

			i = j
		else:
			result.append(text[i])
			i += 1

	return ''.join(result)


def highlight_text_differences(original_text, modified_text):
	"""
	Highlight character-level differences between two texts.

	Returns the modified_text with differences highlighted in red spans.
	Different/inserted characters are highlighted, equal characters remain unchanged.
	Deleted characters are shown as 'D' markers.

	Args:
		original_text (str): The original text to compare against
		modified_text (str): The modified text to highlight differences in

	Returns:
		str: HTML string with differences highlighted in <span> elements
	"""
	if not original_text or not modified_text:
		return escape(modified_text) if modified_text else ''

	# Use SequenceMatcher to find character-level differences
	matcher = difflib.SequenceMatcher(None, original_text, modified_text)
	highlighted_text = []

	for tag, i1, i2, j1, j2 in matcher.get_opcodes():
		if tag == 'equal':
			# Characters are the same, add them without highlighting
			escaped_text = escape(modified_text[j1:j2])
			highlighted_text.append(_preserve_spaces(escaped_text))
		elif tag == 'replace':
			# Characters are different, highlight in red
			escaped_text = escape(modified_text[j1:j2])
			highlighted_text.append(
				f'<span style="background-color: #ffcccc; color: #cc0000;">{_preserve_spaces(escaped_text)}</span>'
			)
		elif tag == 'insert':
			# Character exists in modified but not in original, highlight in red
			escaped_text = escape(modified_text[j1:j2])
			highlighted_text.append(
				f'<span style="background-color: #ffcccc; color: #cc0000;">{_preserve_spaces(escaped_text)}</span>'
			)
		elif tag == 'delete':
			# Character exists in original but not in modified - show deletion marker
			# Count how many characters were deleted to show the right number of markers
			deleted_count = i2 - i1
			deleted_text = original_text[i1:i2]

			# If all deleted characters are spaces, show them as visible markers
			if deleted_text.strip() == '':
				# All spaces - show each space as a visible marker
				for _ in range(deleted_count):
					highlighted_text.append(
						'<span style="background-color: #ffcccc; color: #cc0000; font-family: Berkeley Mono, monospace; padding:0 2px;">D</span>'
					)
			else:
				# Mixed content - just show D markers
				for _ in range(deleted_count):
					highlighted_text.append(
						'<span style="background-color: #ffcccc; color: #cc0000; font-family: Berkeley Mono, monospace; padding:0 2px;">D</span>'
					)

	return ''.join(highlighted_text)
