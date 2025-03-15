def fix_unicredit_floating_point(string):
    return (string
            .replace('.', '')
            .replace(',', '.'))
