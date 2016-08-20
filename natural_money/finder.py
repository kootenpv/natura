import os
import json
import re
from collections import namedtuple
from natural_money.utils import guess_currency
from natural_money.utils import find_non_overlapping_results
from natural_money.conversion_backends import FixerIOExchangeRate

package_dir = os.path.join(os.path.dirname(__file__), "../data/money")

LOCALES = {}
for fname in os.listdir(package_dir):
    if fname.endswith(".json"):
        with open(os.path.join(package_dir, fname)) as f:
            name = fname.split(".")[0].upper()
            LOCALES[name] = json.load(f)

Money = namedtuple("Money", ["value", "currency", "spans",
                             "matches", "base", "base_amount", "last_modified_base"])

LOCALE_NL = {
    'symbol': u'\u20AC',
    'currency': r'euro[s]*',
    'units': [('miljoen', 10**6), ('milj', 10**6), ('m', 10**6), ('mil', 10**6),
              ('duizend', 10**3),
              ('miljard', 10**9),
              ('honderd', 10**2),
              ('cent', 0.01),
              ('\\b', 1), ('', 1)]
}

ReMatch = namedtuple("ReMatch", ["x", "span"])


class Base():

    def __init__(self, x, span):
        self.x = x
        self.span = span

    def __repr__(self):
        return "{}(x={}, span={})".format(self.__class__.__name__, self.x, self.span)


class Symbol(Base):
    pass


class Currency(Base):
    pass


class Amount(Base):
    pass


class TextAmount(Base):
    pass


class Keyword():

    def __init__(self, x, converted, span):
        self.x = x
        self.span = span
        self.converted = converted

    def __repr__(self):
        msg = "{}(x={}, span={}, converted={})"
        return msg.format(self.__class__.__name__, self.x, self.span, self.converted)


class Abbrev(Base):
    pass


class Skipper(Base):
    pass


def pipe(ls, pre=r'(?<![^0-9 -])', post=r'(?![^0-9 -])'):
    # this is flipped
    p = post + "|" + pre
    return pre + p.join(sorted(ls, key=len, reverse=True)) + post


class Finder(object):

    def __init__(self, language="US", locale=None, base_currency="EUR", converter=FixerIOExchangeRate()):
        if locale is None:
            locale = LOCALES[language]
        self.locale = locale
        self.scanner = None
        self.converter = converter
        self.base_currency = base_currency

    def set_scanner(self, scanner=None):
        if self.scanner is None and scanner is None:
            scanner = re.Scanner([
                (pipe(self.locale['keywords'], pre=r'', post=r'\b'), self.handle_keyword),
                (pipe(self.locale['currencies'], pre=r'', post=r's?\b'), self.currency_regex),
                (pipe(self.locale['abbrevs']), lambda y, x: Abbrev(x, y.match.span())),
                (self.symbols_to_regex(), self.symbol_regex),
                (r'-?[0-9.,]+', self.to_number_regex),
                (r' |-', self.echo_regex),
                (pipe(self.locale['units']), self.units_regex),
                (r'.', lambda y, x: Skipper(x, y.match.span()))
            ])
        if scanner is not None:
            self.scanner = scanner

    def symbols_to_regex(self):
        escape_dollars = [x.replace("$", r"\$") for x in self.locale['symbols']]
        return pipe(escape_dollars)

    def findall(self, text, min_amount=-float("inf"), max_amount=float("inf"),
                numeric_to_money=False, single=False):
        self.set_scanner()
        sm, _ = self.scanner.scan(text)
        results = []
        for s, c in [(sm, Abbrev), (reversed(sm), Abbrev), (sm, Symbol),
                     (reversed(sm), Symbol), (reversed(sm), Currency)]:
            for x in self.get_money(s, c, text):
                if not min_amount < x.value < max_amount:
                    continue
                if single:
                    return x
                results.append(x)

        results.sort(key=lambda x: x.spans)
        results = find_non_overlapping_results(results)

        if not results and numeric_to_money:
            results = self._find_always(sm, text)

        if single:
            if results:
                return results[0]
            return None

        return sorted(results, key=lambda x: x.spans)

    def find(self, text, min_amount=-float("inf"), max_amount=float("inf"),
             numeric_to_money=False):
        return self.findall(text, min_amount, max_amount, numeric_to_money, single=True)

    def currency_regex(self, scanner, x):
        span = scanner.match.span()
        if x in self.locale['currencies']:
            return Currency(x, span=span)
        else:
            return Currency(x[:-1], span=span)

    def _find_always(self, scan_matches, text):
        return [self.make_money(sm.x, self.base_currency, [sm.span], text)
                for sm in scan_matches
                if isinstance(sm, Amount)]

    @staticmethod
    def symbol_regex(scanner, x):
        return Symbol(x.strip(), span=scanner.match.span())

    @staticmethod
    def echo_regex(scanner, x):
        return ReMatch(x, span=scanner.match.span())

    def units_regex(self, scanner, x):
        return TextAmount(float(self.locale['units'][x]), scanner.match.span())

    def handle_keyword(self, scanner, x):
        return Keyword(x, self.locale['keywords'][x], scanner.match.span())

    @staticmethod
    def to_number_regex(scanner, x):
        result = None
        if re.match("^-?[0-9]+$", x):
            result = float(x)
        elif re.match("^-?[0-9]{1,3}(,[0-9]{3})*([.][0-9]+)*$", x):
            result = float(x.replace(",", ""))
        elif re.match(r"^-?[0-9]+\.[0-9]+$", x):
            result = float(x)
        result = Amount(result, scanner.match.span()) if result else None
        return result

    def get_money(self, scan_matches, currency_symbol_abbrev, text):
        scan_matches = list(scan_matches)
        strike = 10000
        amounts = []
        start_ends = []
        currencies = []
        clues = [x for x in scan_matches if isinstance(x, Keyword)]
        for m in scan_matches:
            if isinstance(m, currency_symbol_abbrev):
                amounts.append(None)
                start_ends.append([m.span])
                if isinstance(m, Abbrev):
                    currency = m.x
                else:
                    keyword, currency = guess_currency(m, clues, self.locale)
                    if keyword is not None:
                        start_ends[-1].append(keyword.span)
                currencies.append(currency)
                strike = 0
            elif isinstance(m, Skipper):
                strike += 1
            elif strike < 2 and isinstance(m, (Amount, TextAmount)):
                amounts[-1] = amounts[-1] * m.x if amounts[-1] is not None else m.x
                strike = 0 if isinstance(m, TextAmount) else 100
                start_ends[-1].append(m.span)
        # sort inner spans
        for se in start_ends:
            se.sort()
        return [self.make_money(amount, currency, spans, text)
                for amount, currency, spans in zip(amounts, currencies, start_ends)
                if amount is not None]

    def make_money(self, amount, currency, spans, text):
        if self.converter:
            base = self.base_currency
            base_amount, last_mod = self.converter.convert(currency, self.base_currency, amount)
        else:
            base = None
            base_amount, last_mod = None, None
        text_matches = [text[z[0]:z[1]] for z in spans]
        return Money(amount, currency, spans, text_matches, base, base_amount, last_mod)
