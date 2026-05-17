def months_back(year, month, n):
	"""Return the n most recent months (oldest first) ending with (year, month)."""
	months = []
	y, m = year, month
	for _ in range(n):
		months.append((y, m))
		m -= 1
		if m == 0:
			m, y = 12, y - 1
	return list(reversed(months))
