"""
Portfolio class
"""

import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import json
import pandas as pd
import libs.assets
import configs.alphaconf


class PORTFOLIO(object):
    """PORTFOLIO class"""

    def __init__(self, name='No name', money=100000, caching=True, cacheage=3600 * 48):
        self.name = name
        self.initial_money = money
        self.money = money
        self.value = money
        self.profit = 0
        self.data = dict()
        self.key = configs.alphaconf.key
        self.caching = caching
        self.cacheage = cacheage

        pd.options.display.max_rows = 200
        self.df = pd.DataFrame()
        self.values = pd.DataFrame()

    def add(self, symbol='', asset_type='etf', source='moex', share=0):
        """
        Add an asset to the portfolio

        Args:
            symbol: Asset ticker
            asset_type: Type, ETF
            source: Data source, MOEX
            share: The asset share in the portfolio, %
        """
        asset = libs.assets.ASSET(symbol=symbol, source=source, asset_type=asset_type, key=self.key,
                                  cacheage=self.cacheage, caching=self.caching)
        self.data[symbol] = dict()
        self.data[symbol]['asset'] = asset
        self.data[symbol]['share'] = share

        asset.get_data()

        if self.df.empty:
            self.df = pd.concat([asset.df['date'], asset.df['Close']], axis=1)
            self.df.date = pd.to_datetime(self.df['date'], format='%Y-%m-%d')
            self.df = self.df.set_index('date')
            self.df = self.df.rename(columns={'Close': symbol})
        else:
            tmp_df = asset.df
            tmp_df.date = pd.to_datetime(tmp_df['date'], format='%Y-%m-%d')
            tmp_df = tmp_df.set_index('date')
            tmp_df = tmp_df[~tmp_df.index.duplicated()]
            self.df[symbol] = tmp_df['Close']

        price = float(round(self.df[symbol][0:1].values[0], 2))
        self.data[symbol]['count'] = int(self.initial_money * (share / 100) / price)
        self.data[symbol]['value'] = round(self.data[symbol]['count'] * price, 2)
        self.money = round(self.money - self.data[symbol]['value'], 2)

    def run(self):
        """
        Calculate performance of the portfolio
        """

        value_names = list()
        for symbol in self.data.keys():
            value_names.append(symbol + '_value')
            self.df[symbol + '_value'] = self.df[symbol] * self.data[symbol]['count']

        self.df['Total'] = self.df[value_names].sum(axis=1)

        self.value = round(self.money + self.df['Total'][-1:].values[0], 2)
        self.profit = round(self.value - self.initial_money, 2)

    def walk(self):
        """
        Simulate something
        """

        symbols = self.data.keys()
        money = 0

        for index, row in self.df.iterrows():

            total = 0
            # Get total value of the portfolio
            for symbol in symbols:
                self.data[symbol]['value'] = round(row[symbol] * self.data[symbol]['count'], 2)
                total += self.data[symbol]['value']

            # Get current asset weight
            for symbol in symbols:
                self.data[symbol]['weight'] = round(100 * self.data[symbol]['value'] / total, 2)
                self.data[symbol]['diff'] = self.data[symbol]['weight'] - self.data[symbol]['share']

            # Rebalance?
            for symbol in symbols:
                if self.data[symbol]['diff'] > 2:
                    print(symbol, row[symbol], self.data[symbol]['value'], self.data[symbol]['weight'],
                          self.data[symbol]['share'], total)
                    for symbol2 in symbols:
                        if symbol == symbol2:
                            continue
                        if self.data[symbol2]['diff'] < -1:
                            print(symbol2, self.data[symbol2]['diff'])

                            # Sell
                            amount = int(self.data[symbol]['value'] * self.data[symbol]['diff'] * 0.01 / row[symbol])
                            if amount > 0:
                                print(symbol, 'to sell:', amount)
                                self.data[symbol]['count'] -= amount
                                gain = amount * row[symbol]

                                # Buy
                                amount = int(gain / row[symbol2])
                                print(symbol2, 'to buy:', amount)
                                self.data[symbol2]['count'] += amount
                                pay = amount * row[symbol2]

                                money += gain - pay
                                break
                    else:
                        continue
                    break

        profit = round(self.money + money + total - self.initial_money, 2)
        print(profit)

    def print_stats(self):
        if 'Total' in self.df:
            print(self.df['Total'].describe())

    def __str__(self):
        data = dict()
        data[self.name] = dict()
        data[self.name]['value'] = self.value
        data[self.name]['money'] = self.money
        data[self.name]['profit'] = self.profit
        data[self.name]['profit_pct'] = round(100 * self.profit / self.initial_money, 1)

        symbols = self.data.keys()

        for symbol in symbols:
            data[self.name][symbol] = dict()
            data[self.name][symbol]['share'] = self.data[symbol]['share']
            data[self.name][symbol]['count'] = self.data[symbol]['count']
            data[self.name][symbol]['value'] = self.data[symbol]['value']

        rez = json.dumps(data, indent=4)
        return rez
