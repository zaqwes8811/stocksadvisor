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
import talib
import pandas_montecarlo
from alpha_vantage.timeseries import TimeSeries

class FUTURES(object):
    """Single futures"""

    def __init__(self, symbol='', boardid='RFUD', volumefield='VOLUME', cacheage=3600*24*5):
        self.symbol = symbol
        self.df = None
        self.boardid = boardid
        self.volumefield = volumefield
        self.cacheage = cacheage

        self.trend = ''

    def get_prices_from_alpha(self, key='', cachedir='cache'):
        if not os.path.isdir(cachedir):
            os.mkdir(cachedir)
        filename = self.symbol + '.csv'
        filepath = os.path.join(cachedir, filename)
        if os.path.isfile(filepath):
            age = time.time() - os.path.getmtime(filepath)
            if age > self.cacheage:
                os.remove(filepath)
            else:
                data = pd.read_csv(filepath, index_col='date')
                self.df = data
                return data

        data = self.fetch_alpha(key=key, size='compact')
        data.to_csv(filepath)

        self.df = data
        return data

    def fetch_alpha(self, key='demo', size='compact', timeout=5):
        ts = TimeSeries(key=key, output_format='pandas')
        retry = 0
        while True:
            try:
                data, meta_data = ts.get_daily_adjusted(symbol=self.symbol, outputsize=size)
                break
            except:
                retry += 1
                if retry > 10:
                    exit('Can not fetch ' + self.symbol)
                time.sleep(timeout)
                continue
        return data

    def fix_alpha_columns(self):
        df = self.df
        df = df.rename(index=str, columns={'3. low': 'Low'})
        df = df.rename(index=str, columns={'2. high': 'High'})
        df = df.rename(index=str, columns={'1. open': 'Open'})
        df = df.rename(index=str, columns={'4. close': 'Close'})
        df = df.rename(index=str, columns={'6. volume': 'Volume'})
        df = df.rename(index=str, columns={'5. adjusted close': 'Adjusted close'})

        self.df = df
        self.df = df.reset_index()

    def fetch_moex(self, days=100, timeout=1):
        date_N_days_ago = datetime.now() - timedelta(days=days)
        start = date_N_days_ago.strftime('%m/%d/%Y')

        df = pdr.get_data_moex(self.symbol, pause=timeout, start=start)
        df = df.reset_index()
        df = df.query('BOARDID == @self.boardid')
        filtered = pd.DataFrame()
        filtered['date'] = df['TRADEDATE']
        filtered['Open'] = df['OPEN']
        filtered['Low'] = df['LOW']
        filtered['High'] = df['HIGH']
        filtered['Close'] = df['CLOSE']
        filtered['Volume'] = df[self.volumefield]
        if self.boardid =='RFUD':
            filtered['Openpositions'] = df['OPENPOSITION']
            filtered['Openpositionsvalue'] = df['OPENPOSITIONVALUE']

        return filtered

    def get_data_from_moex(self, cachedir='cache-m', timeout=3, days=100):
        if not os.path.isdir(cachedir):
            os.mkdir(cachedir)
        filename = self.symbol + '.csv'
        filepath = os.path.join(cachedir, filename)
        if os.path.isfile(filepath):
            age = time.time() - os.path.getmtime(filepath)
            if age > self.cacheage:
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
        columns = self.df.columns
        df = pd.concat([self.df['date'], self.df['Close'], self.df['Volume']], axis=1)
        df.date = pd.to_datetime(df['date'], format='%Y-%m-%d')
        df = df.set_index('date')
        df['Close'] = df.Close.replace(to_replace=0, method='ffill')
        df['Volume'] = df.Volume.replace(to_replace=0, method='ffill')
        fig = plt.figure(figsize=(15, 8))
        plt.subplot(3, 1, 1)
        plt.title(self.symbol)

        plt.plot(df.index, df.Close, 'k', label='Price')

        if 'ATR' in columns:
            df['ATR'] = self.df.ATR.values

        if 'EMA5' in columns:
            df['EMA5'] = self.df.EMA5.values
            plt.plot(df.index, df.EMA5, 'b', label='EMA5')

        if 'EMA20' in columns:
            df['EMA20'] = self.df.EMA20.values
            plt.plot(df.index, df.EMA20, 'r', label='EMA20')

        if 'KC_LOW' in columns:
            df['KC_LOW'] = self.df.KC_LOW.values

        if 'KC_HIGH' in columns:
            df['KC_HIGH'] = self.df.KC_HIGH.values

        if 'KC_LOW' in columns and 'KC_HIGH' in columns:
            plt.fill_between(df.index, df.KC_LOW, df.KC_HIGH, color='b', alpha=0.2)

        plt.legend()
        plt.grid()

        ax1 = plt.subplot(3, 1, 2)
        ax2 = ax1.twinx()

        ax1.plot(df.index, df.Volume, 'g', label='Volume')
        ax1.set_ylabel('Volume', color='g')

        if 'Openpositions' in columns:
            df['Openpositions'] = self.df.Openpositions.values
            ax2.plot(df.index, df.Openpositions, 'b', label='Openpositions')
            ax2.legend()

        ax1.grid()

        if 'ATR' in columns:
            plt.subplot(3, 1, 3)
            plt.plot(df.index, df.ATR, 'r', label='ATR')
            plt.legend()
            plt.grid()

        fig.tight_layout()
        plt.show()

    def get_atr(self, period=5):
        pricedata = self.df
        high = pricedata['High'].values
        low = pricedata['Low'].values
        close = pricedata['Close'].values
        low = low.astype(float)
        high = high.astype(float)
        close = close.astype(float)
        output = talib.ATR(high, low, close, timeperiod=period)
        self.df['ATR'] = output
        return output

    def get_ema(self, period=5):
        pricedata = self.df
        close = pricedata['Close'].values
        close = close.astype(float)
        output = talib.EMA(close, timeperiod=period)
        self.df['EMA' + str(period)] = output
        return output

    def get_kc(self, period=5):
        self.df['KC_LOW'] = self.df['EMA' + str(period)] - 2 * self.df['ATR']
        self.df['KC_HIGH'] = self.df['EMA' + str(period)] + 2 * self.df['ATR']

    def get_bust_chance(self, sims=1000, bust=0.1, goal=0.1, plot=False):
        # Monte-Carlo
        self.df['Return'] = self.df['Close'].pct_change().fillna(0)

        # print('Real returns stats:')
        # pprint(self.df['Return'].describe())
        # print()

        mc = self.df['Return'].montecarlo(sims=sims, bust=-1 * bust, goal=goal)

        # pprint(mc.stats)
        bust_chance = mc.stats['bust']
        goal_chance = mc.stats['goal']

        # print(mc.data[1].describe())
        # print(mc.data)

        if plot:
            mc.plot(title=self.symbol, figsize=(15, 5))

        return bust_chance, goal_chance

    def count_anomalies(self, period=5, ratio=2):
        low = self.df['Low'].values
        low = low.astype(float)
        high = self.df['High'].values
        high = high.astype(float)
        close = self.df['Close'].values
        close = close.astype(float)
        atr = talib.ATR(high, low, close, timeperiod=period)
        ema = talib.EMA(close, timeperiod=period)

        ema = ema[period:]
        atr = atr[period:]
        close = close[period:]

        count = (close < (ema - ratio * atr)).sum()
        count += (close > (ema + ratio * atr)).sum()

        return count

    def detect_trend(self):
        # EMA5 > EMA20 means up trend
        self.df['UpTrend'] = self.df.EMA5.fillna(0) >= self.df.EMA20.fillna(0)
        self.df['DownTrend'] = self.df.EMA5.fillna(0) <= self.df.EMA20.fillna(0)

        if self.df['UpTrend'].sum() >= 0.85 * len(self.df['UpTrend']):
            trend = 'Up'
        elif self.df['DownTrend'].sum() >= 0.85 * len(self.df['DownTrend']):
            trend = 'Down'
        else:
            trend = 'Sideways'

        self.trend = trend
        return trend
