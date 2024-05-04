import csv


def parse_unicredit_csv(file):
    with open(file.path, 'r') as text_mode_file:
        f = csv.DictReader(text_mode_file, delimiter=';')
        return [i for i in f]
