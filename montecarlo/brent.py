"""Working with Moex Brent
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
import matplotlib.pyplot as plt
import libs.futures

# symbol = 'BRZ8'
symbol = 'SiZ8'
futures = libs.futures.FUTURES(symbol=symbol)
futures.get_data_from_moex(cachedir=os.path.join('..', 'cache-m'))
df = futures.df
df.pop('Open')
df.pop('High')
df.pop('Low')
df.date = pd.to_datetime(df['date'], format='%Y-%m-%d')
df = df.set_index('date')
print(df.tail(10))

df.plot(subplots=True, grid=True, figsize=(15,5))
plt.show()
