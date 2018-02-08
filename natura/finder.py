#prevent ['$', '1', 'M', '2', 'M']
import re
from natura.utils import guess_currency
from natura.utils import load_locale
from natura.utils import find_non_overlapping_results
from natura.conversion_backends import FixerIOExchangeRate
from natura.classes import *
from natura.scanner import Scanner


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
        for entity, check_class in [(sm, Abbrev), (reversed(sm), Abbrev), (sm, Symbol),
                                    (reversed(sm), Symbol), (reversed(sm), Currency)]:
            for x in self.get_money(entity, check_class, text):
                if not min_amount < x.value < max_amount:
                    continue
                if single:
                    return x
                results.append(x)

        # better match in reverse, e.g. "L6001 3WJ 807934 $123.12"
        results.sort(key=lambda x: x.spans, reverse=True)
        results = find_non_overlapping_results(results)

        if not results and numeric_to_money:
            results = self._find_always(sm, text)

        if single:
            if results:
                return results[0]
            return None

        return sorted(results, key=lambda x: x.spans)

    def replace(self, text, replace_with="NATURA", min_amount=-float("inf"), max_amount=float("inf"),
                numeric_to_money=False, single=False):
        found = self.findall(text, min_amount, max_amount, numeric_to_money, single)
        if single:
            found = [found]
        spans = []
        if not found:
            return text
        for x in found:
            spans.append((x.spans[0][0], x.spans[-1][1]))
        spans.sort()
        news = ''
        lbound = 0
        for s in spans:
            news += text[lbound:s[0]]
            news += replace_with
            lbound = s[1]
        news += text[spans[-1][1]:]
        return news

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
                # issuematic... here be dragons
                strike += 10
            elif strike < 2 and isinstance(m, (Amount, TextAmount)):
                amounts[-1] = amounts[-1] * m.x if amounts[-1] is not None else m.x
                strike = 0
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
