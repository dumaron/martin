import csv
import tablib


def import_fineco_xlsx(file):
    data = tablib.Dataset().load(file, format='xlsx', skip_lines=6)
    return data.dict


def parse_csv(file):
    with open(file.path, 'r') as text_mode_file:
        f = csv.DictReader(text_mode_file, delimiter=';')
        return [i for i in f]


def get_file_rows(file, file_type):
    if file_type == 'FINECO_BANK_ACCOUNT_XLSX_EXPORT': # cannot import the enums because of circular imports... mmh
        return import_fineco_xlsx(file)
    else:
        return parse_csv(file)
