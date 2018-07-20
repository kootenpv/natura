import os
import re
import sqlite3
from datetime import datetime
import requests
from dateutil.relativedelta import relativedelta


class NoneExchangeRate():

    def convert(self, from_currency, to_currency, amount):
        return None, None


class BaseExchangeRate():

    def __init__(self):
        self.conn, self.c, self.path = self.get_connection_cursor()

    def convert(self, from_currency, to_currency, amount):
        if from_currency == to_currency:
            return amount, None
        factor, last_modified = self.get(from_currency, to_currency)
        if factor < 0:
            return None, None
        return amount * factor, last_modified

    def get(self, from_currency, to_currency):
        now = datetime.now()
        query = "SELECT factor,last_updated FROM {} \
                 WHERE currency_from=? AND currency_to=? ORDER BY last_updated DESC"
        query = query.format(self.__class__.__name__)
        res = self.c.execute(query, (from_currency, to_currency)).fetchone()
        # either new or too old
        if res is None or res[1] + relativedelta(days=1) < now:
            # fetch
            res = self.update_conversion(from_currency, to_currency)
        factor, last_modified = res
        return factor, last_modified

    def save_double(self, from_currency, to_currency, factor1, dt):
        # make it upsert instead
        sql = "INSERT INTO {} VALUES (?, ?, ?, ?), (?, ?, ?, ?)"
        sql = sql.format(self.__class__.__name__)
        self.c.execute(sql, (dt, from_currency, to_currency, factor1,
                             dt, to_currency, from_currency, 1 / factor1))
        try:
            self.conn.commit()
        except sqlite3.OperationalError:
            print("cannot write")

    def update_conversion(self, from_currency, to_currency):
        raise NotImplementedError()

    def get_connection_cursor(self, base_path=os.path.expanduser("~/natura")):
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        path = os.path.join(base_path, "conversions.db")
        conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        c = conn.cursor()
        try:
            sql = "CREATE TABLE {} \
                   (last_updated timestamp, currency_from text, currency_to text, factor real)"
            sql = sql.format(self.__class__.__name__)
            c.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass
        return conn, c, path

    def drop_all(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        self.conn, self.c, self.path = self.get_connection_cursor()


class FxExchangeRate(BaseExchangeRate):

    def update_conversion(self, from_currency, to_currency):
        url = "http://{}.fxexchangerate.com/{}.xml"
        url = url.format(from_currency, to_currency)
        resp = requests.get(url)
        if resp.status_code == 200:
            xml = resp.text
            factor1 = self.get_conversion_factor(from_currency, to_currency, xml)
            dt = self.get_last_updated(xml)
        else:
            factor1, dt = -1, datetime.now() + relativedelta(months=1)
        self.save_double(from_currency, to_currency, factor1, dt)
        return factor1, dt

    @staticmethod
    def get_last_updated(xml):
        date_match = re.search("<lastBuildDate>([^<]+)</lastBuildDate>", xml)
        if not date_match:
            raise TypeError()
        date_value = date_match.groups()[0].strip()
        date = datetime.strptime(date_value, "%a %b %d %Y %H:%M:%S %Z")
        return date

    @staticmethod
    def get_conversion_factor(from_currency, to_currency, xml):
        conversion_regex = "1.00 {} = (.+) {}".format(from_currency, to_currency)
        conversion_match = re.search(conversion_regex, xml)
        if not conversion_match:
            raise TypeError()
        conversion_factor = float(conversion_match.groups()[0])
        return conversion_factor


class FixerIOExchangeRate(BaseExchangeRate):

    def __init__(self, key):
        BaseExchangeRate.__init__(self)
        self.key = key

    def update_conversion(self, from_currency, to_currency):
        resp = requests.get(" http://data.fixer.io/api/latest?access_key={}&base={}".format(self.key, to_currency))
        resp.raise_for_status()
        table_name = self.__class__.__name__
        rates = resp.json().get('rates', None)
        if rates is None:
            msg = "{}: Rates not available for '{}'"
            raise TypeError(msg.format(table_name, to_currency))
        dt = datetime.now()
        for curr, factor in rates.items():
            self.save_double(to_currency, curr, factor, dt)

        factor1 = rates.get(from_currency, None)
        if factor1 is None:
            msg = "{}: Pair '{}':'{}' is unknown, trying again in 1 month"
            print(msg.format(table_name, from_currency, to_currency))
            factor1, dt = -1, dt + relativedelta(months=1)
            self.save_double(to_currency, from_currency, factor1, dt)
        else:
            factor1 = float(factor1)
        return 1 / factor1, dt
