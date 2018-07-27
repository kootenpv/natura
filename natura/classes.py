from collections import namedtuple


def node(name):
    return namedtuple(name, "x,span")


Symbol = node("Symbol")
Currency = node("Currency")
Amount = node("Amount")
TextAmount = node("TextAmount")
TextAmount_Abbrev = node("TextAmount_Abbrev")
Abbrev = node("Abbrev")
Skipper = node("Skipper")


class Keyword():

    def __init__(self, x, converted, span):
        self.x = x
        self.span = span
        self.converted = converted

    def __repr__(self):
        msg = "{}(x={}, span={}, converted={})"
        return msg.format(self.__class__.__name__, self.x, self.span, self.converted)


class Money():

    def __init__(self, value, currency, spans, matches, base, base_amount, last_modified_base):
        self.names = ["value", "currency", "spans", "matches",
                      "base", "base_amount", "last_modified_base"]
        self.value = value
        self.currency = currency
        self.spans = spans
        self.matches = matches
        self.base = base
        self.base_amount = base_amount
        self.last_modified_base = last_modified_base

    def __repr__(self):
        msg = "{}({})"
        values = ', '.join(["{}={}".format(x, getattr(self, x)) for x in self.names])
        return msg.format(self.__class__.__name__, values)

    def to_dict(self):
        result = {k: getattr(self, k) for k in self.names}
        result['spans'] = [{"begin": x[0], "end": x[1]} for x in self.spans]
        return result
