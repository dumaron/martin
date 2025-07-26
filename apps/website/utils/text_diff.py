import difflib
from html import escape


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
			highlighted_text.append(escape(modified_text[j1:j2]))
		elif tag == 'replace':
			# Characters are different, highlight in red
			highlighted_text.append(
				f'<span style="background-color: #ffcccc; color: #cc0000;">{escape(modified_text[j1:j2])}</span>'
			)
		elif tag == 'insert':
			# Character exists in modified but not in original, highlight in red
			highlighted_text.append(
				f'<span style="background-color: #ffcccc; color: #cc0000;">{escape(modified_text[j1:j2])}</span>'
			)
		elif tag == 'delete':
			# Character exists in original but not in modified - show deletion marker
			highlighted_text.append(
				f'<span style="background-color: #ffcccc; color: #cc0000; font-family: Berkeley Mono, monospace; padding:0 2px;">D</span>'
			)
	
	return ''.join(highlighted_text)