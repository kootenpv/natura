import re
import json
import pkgutil


def abs_span_dist(m1, m2):
    s1 = m1.span
    s2 = m2.span
    return abs(s1[0] - s2[0]) + abs(s1[1] - s2[1])


def get_keyword(m, clues):
    if clues:
        return min(clues, key=lambda x: abs_span_dist(x, m))
    return None


def get_default_currency(options):
    return [opt[0] for opt in options if opt[1]][0]


def guess_currency(m, clues, locale):
    keyword = get_keyword(m, clues)

    if m.x in locale['currencies']:
        options = locale['currencies'][m.x]
    elif m.x.lower() in locale['currencies']:
        options = locale['currencies'][m.x]
    elif m.x in locale['symbols']:
        options = locale['symbols'][m.x]
    elif m.x.upper() in locale['symbols']:
        options = locale['symbols'][m.x.upper()]
    else:
        options = []
    if keyword is not None and options:
        for opt in options:
            if opt[0] == keyword.converted:
                currency = opt[0]
                return keyword, currency

    keyword = None
    return keyword, get_default_currency(options)


def find_non_overlapping_results(matches):
    results = []
    spans = set()
    for result in matches:
        if not any(any(a <= x < b or a < y < b for a, b in spans) for x, y in result.spans):
            spans.update(result.spans)
            results.append(result)
    return results


def load_locale(language):
    locale = pkgutil.get_data("data.money", "{}.json".format(language.lower()))
    return json.loads(locale.decode('utf-8'))


seps = [",", "."]

def to_number_regex(x):
    x = x.replace(" ", "")
    result = None
    for decimal_sep in seps:
        for thousand_sep in seps:
            if decimal_sep == thousand_sep:
                continue
            regex = "^[+-]?"
            regex += "[0-9]{1,3}"
            regex += "(?:[" + thousand_sep + "]?[0-9]{3})*"
            regex += "([" + decimal_sep + "][0-9]{1,2})?"
            regex += "$"
            if re.match(regex, x):
                try:
                    result = float(x.replace(thousand_sep, "").replace(decimal_sep, "."))
                except ValueError:
                    continue
                return result
    return result
