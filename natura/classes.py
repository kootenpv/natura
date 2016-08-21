from collections import namedtuple
from natura.classes import *


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


class Abbrev(Base):
    pass


class Skipper(Base):
    pass


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
