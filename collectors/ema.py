"""Collect EMA 200"""


import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import datetime
import time
import logging
import fire
import requests
from influxdb import InfluxDBClient
import configs.alphaconf
import configs.influx
import configs.fxit


def get_ema200(symbol, age=23*3600):

    influx_client = InfluxDBClient(
        configs.influx.HOST,
        configs.influx.PORT,
        configs.influx.DBUSER,
        configs.influx.DBPWD,
        configs.influx.DBNAME,
        timeout=5
    )
    query = 'SELECT last("ema200") FROM "ema200" WHERE ("symbol"=~ /^' + symbol + '$/)'
    result = influx_client.query(query)
    ema200_date = result.raw['series'][0]['values'][0][0]
    tmp = ema200_date.split('.')
    ema200_date = tmp[0]
    ema200_date = datetime.datetime.strptime(ema200_date, '%Y-%m-%dT%H:%M:%S')
    now = datetime.datetime.utcnow()
    diff = now - ema200_date
    if diff.total_seconds() < age:
        ema200 = result.raw['series'][0]['values'][0][1]
    else:
        ema200 = None
    return ema200


def fetch_ema200_alpha(symbol, key=configs.alphaconf.key):
    url = 'https://www.alphavantage.co/query?function=' + \
          'EMA&symbol={}&interval=daily&time_period=200&series_type=close&apikey={}'.format(symbol, key)
    retry = 0

    # Check cache
    try:
        ema200 = get_ema200(symbol)
    except:
        ema200 = None

    if ema200:
        logging.info(symbol + ' Got EMA200 from InfluxDB: ' + str(ema200))
    else:
        # Try to fetch from the WEB
        while True:
            try:
                r = requests.get(url=url)
                data = r.json()
                last = data['Meta Data']['3: Last Refreshed']
                ema200 = float(data['Technical Analysis: EMA'][last]['EMA'])
                if ema200:
                    break
            except:
                retry += 1
                if retry > 10:
                    logging.error('Can not fetch ' + symbol)
                    logging.error(url)
                    break
                logging.info(symbol + ' retry ' + str(retry))
                time.sleep(retry*3)
                continue

    return ema200


def fetch_ema200_fxit(write_to_influx=True):
    if write_to_influx:
        influx_client = InfluxDBClient(
            configs.influx.HOST,
            configs.influx.PORT,
            configs.influx.DBUSER,
            configs.influx.DBPWD,
            configs.influx.DBNAME,
            timeout=5
        )

    symbols = configs.fxit.holdings
    for symbol in symbols:
        ema200 = fetch_ema200_alpha(symbol=symbol)
        logging.info(symbol + ' ' + str(ema200))
        if type(ema200) != float:
            logging.error(symbol + ' ' + str(ema200) + ' not float')
            continue

        if write_to_influx:
            json_body = [
                {
                    "measurement": "ema200",
                    "tags": {
                        "symbol": symbol,
                    },
                    "fields": {
                        "ema200": ema200,
                    }
                }
            ]
            influx_client.write_points(json_body)


def fetch_ema200_portfolio(write_to_influx=True):
    if write_to_influx:
        influx_client = InfluxDBClient(
            configs.influx.HOST,
            configs.influx.PORT,
            configs.influx.DBUSER,
            configs.influx.DBPWD,
            configs.influx.DBNAME,
            timeout=5
        )

    symbols = configs.alphaconf.symbols

    for item in symbols:
        symbol = list(item.keys())[0]
        ema200 = fetch_ema200_alpha(symbol=symbol)
        logging.info(symbol + ' ' + str(ema200))
        if type(ema200) != float:
            logging.error(symbol + ' ' + str(ema200) + ' not float')
            continue

        if write_to_influx:
            json_body = [
                {
                    "measurement": "ema200",
                    "tags": {
                        "symbol": symbol,
                    },
                    "fields": {
                        "ema200": ema200,
                    }
                }
            ]
            influx_client.write_points(json_body)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s',
                        level='INFO',
                        stream=sys.stderr)
    if "PYCHARM_HOSTED" in os.environ:
        print(get_ema200('C'))
        # fetch_ema200_portfolio(write_to_influx=False)
    else:
        fire.Fire()

