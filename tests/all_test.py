#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import pytest
from natura import Finder
from natura.utils import load_locale

LOCALES = {}
for name in os.listdir("data/money"):
    if name.endswith(".json"):
        language = name.split(".json")[0]
        LOCALES[language] = load_locale(language)

default_money = Finder(converter=None)

CURRENT_BAD = [u'.د.ب', u'US$']


def proove(x, y):
    value, currency, spans = y
    return x.value == value and x.currency == currency and len(x.spans) == spans


def get_default(symbols):
    for s in symbols:
        if s[1]:
            return s[0]


def generic_test(money_string, _money, *results):
    money = _money or default_money
    mp = money.findall(money_string)
    assert len(mp) == len(results)
    assert all([proove(match, result) for match, result in zip(mp, results)])
    return mp


def test_beginning2():
    generic_test("USD500", None, [500, 'USD', 2])


def test_negative():
    generic_test("-500 USD", None, [-500, 'USD', 2])


def test_beginning3():
    generic_test("500$", None, [500, 'USD', 2])


def test_beginning4():
    generic_test("$500", None, [500, 'USD', 2])


def test_beginning5():
    generic_test("500dollars", None, [500, 'USD', 2])


def test_beginning6_not():
    generic_test("dollars 500", None)


def test_multiple():
    t = "500dollars 500dollars 500dollars"
    generic_test(t, None, [500, 'USD', 2], [500, 'USD', 2], [500, 'USD', 2])


def test_multiple2():
    t = "500 EUR $500 and five hundred yen"
    generic_test(t, None, [500, 'EUR', 2], [500, 'USD', 2], [500, 'JPY', 3])


def test_not():
    generic_test("500", None)


def test_numeric():
    mp = default_money.find("500", numeric_to_money=True)
    assert mp


def test_keyword_aud():
    t = "3 people at most Australia 500 dollars june 2018"
    generic_test(t, None, [500, 'AUD', 3])


def test_textual_amount():
    t = "3 people at most five hundred dollars june 2018"
    generic_test(t, None, [500, 'USD', 3])


def test_textual_amount2():
    t = "3 people at most five hundred billion dollars 2018"
    generic_test(t, None, [5 * 100 * 1000000000, 'USD', 4])


def test_duplicate():
    t = "3 people at most $500 dollars june 2018"
    generic_test(t, None, [500, 'USD', 2])


def test_yen():
    t = "3 people at most 500 yen in 2018"
    generic_test(t, None, [500, 'JPY', 2])


def test_pre_abbrev():
    t = "3 people at most 500 JPY in 2018"
    generic_test(t, None, [500, 'JPY', 2])


def test_pre_abbrev2():
    t = "3 people at most 500JPY in 2018"
    generic_test(t, None, [500, 'JPY', 2])


def test_post_abbrev():
    t = "3 people at most JPY 500 in 2018"
    generic_test(t, None, [500, 'JPY', 2])


def test_double_pre_abbrev():
    t = "3 people at most JPY 500 in JPY two hundred ok"
    generic_test(t, None, [500, 'JPY', 2], [200, 'JPY', 3])


# def test_double_comma():
#     t = "3 people at most JPY 500, JPY two hundred ok"
#     generic_test(t, None, [500, 'JPY', 2], [200, 'JPY', 3])


def test_symbol1():
    t = "3 people at most $500 june 2018"
    generic_test(t, None, [500, 'USD', 2])


def test_symbol2():
    t = u"3 people at most £500 june 2018"
    generic_test(t, None, [500, 'GBP', 2])


def test_symbol3():
    t = "3 people at most Z$500 june 2018"
    generic_test(t, None, [500, 'ZWD', 2])


def test_symbol4():
    t = "3 people at most 500Z$ june 2018"
    generic_test(t, None, [500, 'ZWD', 2])


def test_symbol5():
    t = "3 people at most Z$ 500 june 2018"
    generic_test(t, None, [500, 'ZWD', 2])


def test_symbol6():
    t = "3 people at most 500 Z$ june 2018"
    generic_test(t, None, [500, 'ZWD', 2])


def test_symbol7():
    t = "3 people at most Z$ 500 june 2018"
    generic_test(t, None, [500, 'ZWD', 2])


def test_symbol7():
    t = u"(£2,386)"
    generic_test(t, None, [2386, 'GBP', 2])


def test_symbol8():
    t = u"'£2,386'"
    generic_test(t, None, [2386, 'GBP', 2])


def test_new_symbol():
    t = "$US10"
    generic_test(t, None, [10, 'USD', 2])


def test_new_symbol2():
    t = "$A10"
    generic_test(t, None, [10, 'AUD', 2])


def test_numeric_then_unit():
    t = "$US10b"
    generic_test(t, None, [10**10, 'USD', 3])


def test_from_to1():
    t = "from 500 Z$ to 500 USD"
    generic_test(t, None, [500, 'ZWD', 2], [500, 'USD', 2])


def test_misformed1():
    t = "500-Z$"
    generic_test(t, None, [500, 'ZWD', 2])


def test_misformed2():
    t = "500-dollars"
    generic_test(t, None, [500, 'USD', 2])


def test_comma():
    t = "5,000 dollars"
    generic_test(t, None, [5000, 'USD', 2])


def test_decimal_points():
    t = "5.50 dollars"
    generic_test(t, None, [5.50, 'USD', 2])


currency_types = ['symbols', 'currencies']
money_strings = [u"500{ms}", u"500 {ms}", u"asdf500 {ms}"]


@pytest.mark.parametrize("locale_name", LOCALES)
@pytest.mark.parametrize("currency_type", currency_types)
@pytest.mark.parametrize("money_string", money_strings)
def test_symbols(locale_name, money_string, currency_type):
    locale = LOCALES[locale_name]
    money = Finder(locale_name, converter=None)
    for ct in locale[currency_type]:
        if ct not in CURRENT_BAD:
            y_sim = get_default(locale[currency_type][ct])
            generic_test(money_string.format(ms=ct), money, [500, y_sim, 2])

currency_types = ['symbols', 'currencies']
money_strings = [u"500{ms} to 50{ms2}", u"500 {ms} to 50 {ms2}"]


@pytest.mark.parametrize("locale_name", LOCALES)
@pytest.mark.parametrize("currency_type", currency_types)
@pytest.mark.parametrize("money_string", money_strings)
def test_symbols2(locale_name, money_string, currency_type):
    locale = LOCALES[locale_name]
    money = Finder(locale_name, converter=None)
    keys1 = list(locale[currency_type])[:-1]
    keys2 = list(locale[currency_type])[1:]
    for ct, ct2 in zip(keys1, keys2):
        if ct not in CURRENT_BAD and ct2 not in CURRENT_BAD:
            y_sim = get_default(locale[currency_type][ct])
            y_sim2 = get_default(locale[currency_type][ct2])
            mons = money_string.format(ms=ct, ms2=ct2)
            generic_test(mons, money, [500, y_sim, 2], [50, y_sim2, 2])

currency_types = ['currencies']
money_strings = [u"500 {ms} to {ms2} 50"]


@pytest.mark.parametrize("locale_name", LOCALES)
@pytest.mark.parametrize("currency_type", currency_types)
@pytest.mark.parametrize("money_string", money_strings)
def test_symbols3(locale_name, money_string, currency_type):
    locale = LOCALES[locale_name]
    money = Finder(locale_name, converter=None)
    keys1 = list(locale[currency_type])[:-1]
    keys2 = list(locale[currency_type])[1:]
    for ct, ct2 in zip(keys1, keys2):
        if ct not in CURRENT_BAD and ct2 not in CURRENT_BAD:
            y_sim = get_default(locale[currency_type][ct])
            y_sim2 = get_default(locale[currency_type][ct2])
            mons = money_string.format(ms=ct, ms2=ct2)
            generic_test(mons, money, [500, y_sim, 2])

money_strings = [u"500 {ms} to 50 {ms2}", u"500 {ms} and 50 {ms2}"]


@pytest.mark.parametrize("locale_name", LOCALES)
@pytest.mark.parametrize("money_string", money_strings)
def test_mix1(locale_name, money_string):
    locale = LOCALES[locale_name]
    money = Finder(locale_name, converter=None)
    for ct, ct2 in zip(locale['symbols'], locale['currencies']):
        if ct not in CURRENT_BAD and ct2 not in CURRENT_BAD:
            y_sim = get_default(locale['symbols'][ct])
            y_sim2 = get_default(locale['currencies'][ct2])
            mons = money_string.format(ms=ct, ms2=ct2)
            generic_test(mons, money, [500, y_sim, 2], [50, y_sim2, 2])


def test_default_exchange():
    from_currency = "USD"
    to_currency = "EUR"
    money = Finder(base_currency=to_currency)
    import sqlite3
    try:
        mp = money.findall("500{}".format(from_currency))
        assert mp[0].base is not None
        assert mp[0].last_modified_base is not None
    except sqlite3.OperationalError:
        print("skipping sqlite on remote")
