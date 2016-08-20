import re
from natural_money.utils import guess_currency
from natural_money.utils import load_locale
from natural_money.utils import find_non_overlapping_results
from natural_money.conversion_backends import FixerIOExchangeRate
from natural_money.classes import *
from natural_money.scanner import Scanner


class Finder(object):

    def __init__(self, language="US", locale=None, base_currency="EUR", converter=FixerIOExchangeRate()):
        if locale is None:
            locale = load_locale(language)
        self.locale = locale
        self.scanner = None
        self.converter = converter
        self.base_currency = base_currency

    def set_scanner(self, scanner=None):
        if self.scanner is None and scanner is None:
            scanner = Scanner(self.locale)
        if scanner is not None:
            self.scanner = scanner

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

    def _find_always(self, scan_matches, text):
        return [self.make_money(sm.x, self.base_currency, [sm.span], text)
                for sm in scan_matches
                if isinstance(sm, Amount)]

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
