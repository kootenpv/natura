import re
from natura.classes import *
from natura.utils import to_number_regex


def pipe(ls, pre=r'(?<![a-zA-Z])', post=r'(?![a-zA-Z])'):
    # this is flipped
    p = post + "|" + pre
    return pre + p.join(sorted(ls, key=len, reverse=True)) + post


class Scanner():

    def __init__(self, locale):
        self.locale = locale
        # hacky
        self.scan = re.Scanner([
            (pipe(self.locale['currencies'], pre=r'', post=r's?\b'), self.currency_regex),
            (pipe(self.locale['abbrevs']), lambda y, x: Abbrev(x, y.match.span())),
            (self.symbols_to_regex(), self.symbol_regex),
            (pipe(self.locale['keywords'], pre=r'', post=r'\b'), self.handle_keyword),
            (r'[., ]', None),
            (r'-?[0-9., ]*[0-9]+', self.to_number),
            (r'-', None),
            (pipe(self.locale['unit_abbrevs']), self.unit_abbrevs_regex),
            (pipe(self.locale['units'], post=r'\w*\b'), self.units_regex),
            (r'.', lambda y, x: Skipper(x, y.match.span())),
            (r'\n', lambda y, x: Skipper(x, y.match.span()))
        ], re.MULTILINE | re.IGNORECASE | re.UNICODE).scan

    def symbols_to_regex(self):
        esc = [x.replace("$", r"\$").replace(".", r"\.") for x in self.locale['symbols']]
        return pipe(esc)

    def currency_regex(self, scanner, x):
        span = scanner.match.span()
        if x in self.locale['currencies']:
            return Currency(x, span=span)
        elif x.lower() in self.locale['currencies']:
            return Currency(x.lower(), span=span)
        else:
            return Currency(x[:-1].lower(), span=span)

    @staticmethod
    def symbol_regex(scanner, x):
        return Symbol(x.strip(), span=scanner.match.span())

    def unit_abbrevs_regex(self, scanner, x):
        return TextAmount_Abbrev(self.locale['unit_abbrevs'][x.lower()], scanner.match.span())

    def units_regex(self, scanner, x):
        return TextAmount(x.lower(), scanner.match.span())

    def handle_keyword(self, scanner, x):
        if x not in self.locale['keywords']:
            return None
        return Keyword(x, self.locale['keywords'][x], scanner.match.span())

    @staticmethod
    def to_number(scanner, x):
        result = to_number_regex(x)
        return Amount(result, scanner.match.span()) if result else None
