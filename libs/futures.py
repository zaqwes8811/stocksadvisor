"""Working with Moex Futures
https://iss.moex.com/iss/reference/
https://iss.moex.com/iss/engines/futures/markets.xml
https://iss.moex.com/iss/engines/futures/markets/forts.xml
https://iss.moex.com/iss/engines/futures/markets/forts/securities.xml
"""

import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import pandas_datareader as pdr
from datetime import datetime, timedelta
from pprint import pprint
import matplotlib.pyplot as plt

class FUTURES(object):
    """Single futures"""

    def __init__(self, symbol=''):
        self.symbol = symbol
        self.df = None

    def fetch_moex(self, days=100, timeout=1, boardid='RFUD'):
        date_N_days_ago = datetime.now() - timedelta(days=days)
        start = date_N_days_ago.strftime('%m/%d/%Y')

        df = pdr.get_data_moex(self.symbol, pause=timeout, start=start)
        df = df.reset_index()
        df = df.query('BOARDID == @boardid')
        filtered = pd.DataFrame()
        filtered['date'] = df['TRADEDATE']
        filtered['Open'] = df['OPEN']
        filtered['Low'] = df['LOW']
        filtered['High'] = df['HIGH']
        filtered['Close'] = df['CLOSE']
        filtered['Volume'] = df['VOLUME']
        # filtered['Openpositions'] = df['OPENPOSITION']
        # filtered['Openpositionsvalue'] = df['OPENPOSITIONVALUE']

        return filtered

    def get_data_from_moex(self, cachedir='cache-m', cacheage=3600*24*8, timeout=3, days=100):
        if not os.path.isdir(cachedir):
            os.mkdir(cachedir)
        filename = self.symbol + '.csv'
        filepath = os.path.join(cachedir, filename)
        if os.path.isfile(filepath):
            age = time.time() - os.path.getmtime(filepath)
            if age > cacheage:
                os.remove(filepath)
            else:
                data = pd.read_csv(filepath)
                self.df = data
                return data

        data = self.fetch_moex(days=days, timeout=timeout)
        self.df = data
        filepath = os.path.join(cachedir, filename)
        data.to_csv(filepath, index=False)

        time.sleep(timeout)

        return data

    def plot(self):
        df = self.df
        df.pop('Open')
        df.pop('High')
        df.pop('Low')
        df.date = pd.to_datetime(df['date'], format='%Y-%m-%d')
        df = df.set_index('date')
        df.plot(subplots=True, grid=True, figsize=(15, 5), title=self.symbol)
        plt.show()
