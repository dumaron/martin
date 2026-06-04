from toolz import curry


@curry
def lmap(f, seq):
	"""Curried, data-last, non-lazy map for Python iterables.

	`lmap(f, seq)` returns a list immediately;
	`lmap(f)` returns a reusable function awaiting the sequence — handy for composing data-last pipelines.
	"""
	return list(map(f, seq))


@curry
def lfilter(pred, seq):
	"""Curried, data-last, non-lazy filter for Python iterables.

	`lfilter(pred, seq)` returns a list immediately;
	`lfilter(pred)` returns a reusable function awaiting the sequence — handy for composing data-last pipelines.
	"""
	return list(filter(pred, seq))


@curry
def separate(pred, seq):
	"""Curried, data-last, non-lazy partitioning for Python iterables."""

	# I actually wanted to use toolz.partition here, but it seems it inherits the weird python's groupby implementation
	# that will actually create a new entry for the final result when the predicate changes... so you need to sort the
	# initial array. I wonder why they went down that path, it seems very unconfortable to use - and slow, since it
	# requires sorting first. Mah.

	is_true = []
	is_false = []
	for item in seq:
		if pred(item):
			is_true.append(item)
		else:
			is_false.append(item)
	return is_true, is_false


@curry
def ternary(partial_pred, true_value, false_value, value):
	return true_value if partial_pred(value) else false_value


@curry
def eq(value_1, value_2):
	return value_1 == value_2

@curry
def first(array):
	if array is None:
		return None
	return array[0]

@curry
def last(array):
	if array is None:
		return None
	return array[-1]

key = first
value = last