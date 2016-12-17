import re
from natura.classes import *


def pipe(ls, pre=r'(?<![a-zA-Z])', post=r'(?![a-zA-Z])'):
    # this is flipped
    p = post + "|" + pre
    return pre + p.join(sorted(ls, key=len, reverse=True)) + post


class Scanner():

    def __init__(self, locale):
        self.locale = locale
        # hacky
        self.scan = re.Scanner([
            (pipe(self.locale['keywords'], pre=r'', post=r'\b'), self.handle_keyword),
            (pipe(self.locale['currencies'], pre=r'', post=r's?\b'), self.currency_regex),
            (pipe(self.locale['abbrevs']), lambda y, x: Abbrev(x, y.match.span())),
            (self.symbols_to_regex(), self.symbol_regex),
            (r'-?[0-9.,]+', self.to_number_regex),
            (r' |-', self.echo_regex),
            (pipe(self.locale['units']), self.units_regex),
            (r'.', lambda y, x: Skipper(x, y.match.span())),
            (r'\n', lambda y, x: Skipper(x, y.match.span()))
        ], re.MULTILINE | re.IGNORECASE).scan

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

    @staticmethod
    def echo_regex(scanner, x):
        return None

    def units_regex(self, scanner, x):
        return TextAmount(float(self.locale['units'][x.lower()]), scanner.match.span())

    def handle_keyword(self, scanner, x):
        if x not in self.locale['keywords']:
            return None
        return Keyword(x, self.locale['keywords'][x], scanner.match.span())

    @staticmethod
    def to_number_regex(scanner, x):
        result = None
        if re.match("^[+-]?[0-9]{1,3}(?:,?[0-9]{3})*[.]$", x):
            result = float(x.replace(",", ""))
        elif not re.match("^[+-]?[0-9]{1,3}(?:,?[0-9]{3})*(\.[0-9]{2})?$", x):
            result = None
        elif re.match("^-?[0-9]+[.]?$", x):
            result = float(x)
        elif re.match("^-?[0-9]{1,3}(,[0-9]{3})*([.][0-9]+)*$", x):
            result = float(x.replace(",", ""))
        elif re.match(r"^-?[0-9]+\.[0-9]+[.]?$", x):
            result = float(x)
        return Amount(result, scanner.match.span()) if result else None
