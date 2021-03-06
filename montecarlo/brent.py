"""Working with Moex Brent
https://www.moex.com/ru/contract.aspx?code=Si-12.18
https://www.moex.com/ru/derivatives/
https://www.moex.com/ru/derivatives/contracts.aspx
"""

import time
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import pandas as pd
import matplotlib.pyplot as plt
import libs.futures
import pandas_montecarlo
from pprint import pprint
import math
import numpy as np

symbol = 'GMKN'  # 'SiZ8'  # 'SBER'  # 'BRZ8'

futures = libs.futures.FUTURES(symbol=symbol, boardid='TQBR')  # boardid='TQBR'
futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))

futures.get_atr(period=5)
futures.get_ema(period=5)
futures.get_kc()

futures.df.pop('Open')
futures.df.pop('High')
futures.df.pop('Low')
# futures.df.pop('Openpositionsvalue')

# futures.plot()

futures.df.pop('KC_LOW')
futures.df.pop('KC_HIGH')

print(futures.df.corr())
print()

# Stop loss
futures.df['StopLoss'] = futures.df['Close'] - 5 * futures.df['ATR']
futures.df['StopLossPercent'] = 1 - futures.df['StopLoss'] / futures.df['Close']
bust = futures.df['StopLossPercent'].max()

print('Last price:', round(futures.df.Close[-1:].values[0], 2))
print('Bust:', bust)
print('StopLoss:', round(futures.df.Close[-1:].values[0]*(1-bust), 2))
print()

bust_chance, goal_chance = futures.get_bust_chance(bust=bust, sims=10000)
print('Bust chance:', round(bust_chance, 2))
print('Goal chance:', round(goal_chance, 2))
print()

# Reward-risk ratio
for i in range(1, 10):
    goal = i * 0.1
    futures.df['RewardRiskRatio'] = (goal_chance/i) * goal * futures.df['Close'] / \
        (bust_chance * (futures.df['Close'] - futures.df['StopLoss']))
    if futures.df['RewardRiskRatio'].mean() > 2:
        print('Reward-Risk ratio:', futures.df['RewardRiskRatio'].mean())
        print('Goal:', goal)
        break

if goal > 0.1:
    bust_chance, goal_chance = futures.get_bust_chance(bust=bust, goal=goal)
    print('Bust chance:', round(bust_chance, 2))
    print('Goal chance:', round(goal_chance, 2))
    print()
