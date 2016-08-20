def abs_span_dist(m1, m2):
    s1 = m1.span
    s2 = m2.span
    return abs(s1[0] - s2[0]) + abs(s1[1] - s2[1])


def get_keyword(m, clues):
    if clues:
        return sorted(clues, key=lambda x: abs_span_dist(x, m))[0]
    else:
        return None


def get_default_currency(options):
    return [opt[0] for opt in options if opt[1]][0]


def guess_currency(m, clues, locale):
    keyword = get_keyword(m, clues)

    if m.x in locale['currencies']:
        options = locale['currencies'][m.x]
    elif m.x in locale['symbols']:
        options = locale['symbols'][m.x]
    else:
        options = locale['symbols'][m.x.upper()]

    if keyword is not None:
        for opt in options:
            if opt[0] == keyword.converted:
                currency = opt[0]
                return keyword, currency
                break

    keyword = None
    return keyword, get_default_currency(options)


def find_non_overlapping_results(matches):
    results = []
    spans = set()
    for result in matches:
        if not any([any([a <= x < b or a <= y < b for a, b in spans]) for x, y in result.spans]):
            for span in result.spans:
                spans.add(span)
            results.append(result)
    return results
