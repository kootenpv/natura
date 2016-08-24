# note that when mentioned Rupee it is usually Indian. However, the rupee
# symbol '₨' mostly means 'Pakistan Rupee'
# similar story with the China Yuan symbol which is the same as Yen

import json
from collections import defaultdict
from collections import Counter
import lxml.html

default_symbols = {'Philippines', 'Netherlands Antilles', 'India', 'Costa Rica', 'United States',
                   'Sweden', 'Russia', 'Kyrgyzstan',  'United Kingdom', 'Korea (South)', 'Iran',
                   'China Yuan', 'Pakistan'}

default_currencies = {'Denmark', 'Netherlands Antilles', 'India', 'Saudi Arabia', 'Costa Rica', 'United States',
                      'Sweden', 'Russia', 'Kyrgyzstan', 'Mexico',  'United Kingdom', 'Korea (South)', 'Iran',
                      'China Yuan', 'Pakistan'}

currencies = defaultdict(set)
symbols = defaultdict(set)
blacklist = set(["of", "and", "New", "new", "St.", "Saint", "South", "East", "West", "Central"])
keywords = {}
with open("google_money.html") as f:
    google = {x.split(",")[0]: {"name": x.split(",")[1]} for x in f.read().split("\n") if x}
    for key in google:
        name_parts = google[key]['name'].split()
        google[key]['currency'] = name_parts[-1]
        keywords[" ".join(name_parts[:-1])] = key
        # for name_part in name_parts[:-1]:
        #     if len(name_part) < 2:
        #         continue
        #     if name_part not in blacklist:
        #         keywords[name_part] = key


def unijoin(x):
    return "".join(["\\u" + y.zfill(4) for y in x.split(", ")])

with open("xe_data.json", "w") as f2:
    f2.write("{")
    with open("money.html") as f:
        data = lxml.html.fromstring(f.read())
        rows = data.xpath("//tr")[1:]
        for row in rows:
            cells = [cell for cell in row.xpath("./td/text()")]
            abbrev, symbol = cells[:2]
            symbol = symbol.strip()
            if not symbol:
                continue
            if len(row.xpath("./td/text()")) != 6:
                continue
            f2.write('"{}": "{}",\n'.format(abbrev, unijoin(row.xpath("./td/text()")[-2])))
            name = row.xpath("./td/a/text()")[0]
            currency_type = name.split()[-1].lower()
            currency_prefix = " ".join(name.split()[:-1])
            info = (abbrev, currency_prefix)
            currencies[currency_type].add(info)
            symbols[symbol].add(info)
            keywords[currency_prefix.split("(")[0]] = abbrev
            # for cp in currency_prefix.split():
            #     cp = cp.strip("(").strip(")")
            #     if cp not in blacklist:
            #         keywords[cp].add(abbrev)
    f2.write('"": ""}')

with open("xe_data.json") as f:
    xe_data = json.load(f)

with open("MicroPyramid_forex-python.json") as f:
    forex = json.load(f)

for k, v in symbols.items():
    symbols[k] = set([(row[0], len(v) == 1 or row[1] in default_symbols) for row in v])

for k, v in currencies.items():
    currencies[k] = set([(row[0], len(v) == 1 or row[1] in default_currencies) for row in v])

currencies['bitcoin'] = {('BTC', True)}

new_symbols = defaultdict(set)

for k, v in symbols.items():
    for x in v:
        if x[0] in xe_data:
            new_symbols[xe_data[x[0]]].add(x)
        else:
            print(x[0])

default_abbrevs = set()
for k, v in new_symbols.items():
    for x in v:
        if x[1]:
            default_abbrevs.add(x[0])

for k, v in currencies.items():
    for x in v:
        if x[1]:
            default_abbrevs.add(x[0])

#ignored_symbols = 'abcdefghijklmnopqrstuvwxyz'.upper()
symcounts = Counter([x['symbol'] for x in forex])
for s in forex:
    if s['symbol'] not in new_symbols and (symcounts[s['symbol']] == 1 or s['cc'] in default_abbrevs):
        new_symbols[s['symbol']].add((s['cc'], True))

new_symbols['Ƀ'] = {('BTC', True)}

for row in forex:
    key = row['cc']
    name_parts = row['name'].split()
    keywords[" ".join(name_parts[:-1])] = key
    # for name_part in name_parts[:-1]:
    #     if len(name_part) < 2:
    #         continue
    #     if name_part not in blacklist:
    #         keywords[name_part] = key

currencies['euro'] = currencies.pop('countries')

# assert all default
assert all([sum([x[-1] for x in v]) == 1 for v in currencies.values()])
assert all([sum([x[-1] for x in v]) == 1 for v in new_symbols.values()])
# http://www.fileformat.info/info/unicode/category/Sc/list.htm


def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

units = {
    'trillion': 10**12, 'b': 10**9, 'bn': 10**9,
    'billion': 10**9, 'b': 10**9, 'bn': 10**9,
    'million': 10**6, 'm': 10**6, 'mn': 10**6, 'mil': 10**6,
    'thousand': 10**3, 'k': 10**3,
    'hundred': 10**2,
    'ninety': 90, 'eighty': 80, 'seventy': 70, 'sixty': 60, 'fifty': 50,
    'fourty': 40, 'thirty': 30, 'twenty': 20,
    'nineteen': 19, 'eighteen': 18, 'seventeen': 17, 'sixteen': 16,
    'fifteen': 15, 'fourteen': 14, 'thirteen': 17, 'twelve': 16, 'eleven': 11,
    'ten': 10, 'nine': 9, 'eight': 8, 'seven': 7, 'six': 6,
    'five': 5, 'four': 4, 'three': 3, 'two': 2, 'one': 1,
    'half': 0.5,
    'cent': 0.01
}


if '' in keywords:
    keywords.pop("")

for m in ['m', 'M']:
    if m in new_symbols:
        new_symbols.pop(m)

abbrevs = set()
for vs in new_symbols.values():
    for v in vs:
        abbrevs.add(v[0])
for vs in currencies.values():
    for v in vs:
        abbrevs.add(v[0])

abbrevs.update(keywords.values())

for k, v in list(new_symbols.items()):
    k = k.upper()
    if k not in new_symbols:
        new_symbols[k] = v

# add known missing
new_symbols['$US'] = [["USD", True]]
new_symbols['$A'] = [["AUD", True]]


data = {'symbols': new_symbols,
        'currencies': currencies,
        'keywords': keywords,
        'units': units,
        'abbrevs': set([x.upper() for x in abbrevs])}

with open("../data/money/us.json", "w") as f:
    json.dump(data, f, default=set_default)
