from collections import namedtuple


def node(name):
    return namedtuple(name, "x,span")


Symbol     = node("Symbol")
Currency   = node("Currency")
Amount     = node("Amount")
TextAmount = node("TextAmount")
Abbrev     = node("Abbrev")
Skipper    = node("Skipper")


class Keyword():

    def __init__(self, x, converted, span):
        self.x = x
        self.span = span
        self.converted = converted

    def __repr__(self):
        msg = "{}(x={}, span={}, converted={})"
        return msg.format(self.__class__.__name__, self.x, self.span, self.converted)

Money = namedtuple("Money", ["value", "currency", "spans",
                             "matches", "base", "base_amount", "last_modified_base"])
