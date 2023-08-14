import asyncio
import telebot
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import csv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


def sendmsg(symbol, api_key, user_id):
    global today
    file_date = f'{today.year}_{today.month}_{today.day}'
    file_name = f'{symbol}_{file_date}'
    api_key = api_key
    user_id = user_id

    bot = telebot.TeleBot(api_key)

    FIG_FILE_PATH = f'data/{file_name}.png'
    with open(FIG_FILE_PATH, 'rb') as photo:
        bot.send_photo(chat_id=user_id, photo=photo)

def LiquidityScore():
    global today
    file_date = f'{today.year}_{today.month}_{today.day}'
    url = "https://api.coinmarketcap.com/data-api/v3/exchange/market-pairs/latest?slug=binance&category=spot&start=1&limit=5"
    current_time = datetime.now()
    response = requests.get(url)

    data = response.json()
    if data is not None:

        for pair in data['data']['marketPairs']:
            symbol = pair['marketPair']
            liquid = pair['effectiveLiquidity']
            print(f"Time: {current_time}, Symbol: {symbol}, Liquidity:{liquid}")

            if symbol == 'BTC/USDT':
                with open(f'data/BTC_{file_date}.csv', 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['',current_time,liquid])
            elif symbol == 'ETH/USDT':
                with open(f'data/ETH_{file_date}.csv', 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['',current_time,liquid])

def NewCSV():
    global today
    today = datetime.today()
    file_date = f'{today.year}_{today.month}_{today.day}'
    df_BTC = pd.DataFrame(columns=['Time', 'Liquidity'])
    df_BTC.to_csv(f'data/BTC_{file_date}.csv')
    print(f'{file_date} Generate New CSV file.')

def visualization(symbol):
    global today
    file_date = f'{today.year}_{today.month}_{today.day}'
    file_name = f'{symbol}_{file_date}'
    CSV_FILE_PATH = f'data/{file_name}.csv'
    df = pd.read_csv(CSV_FILE_PATH).iloc[:,1:]
    df['Time'] = df['Time'].apply(pd.to_datetime)
    df.set_index('Time',inplace=True)
    df['diff'] = df.Liquidity.diff()
    drop_num = len(df[(df['diff'] != 0) & (df['diff'] < -100)])
    plt.figure(figsize=(16,8))
    plt.plot(df.Liquidity)
    plt.title(f'{file_date} Drop times: {drop_num}')
    plt.savefig(f'data/{file_name}.png')
    plt.close()

if __name__ == '__main__':
    today = datetime.today()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(NewCSV, CronTrigger(hour=0, minute=0,second=2))
    scheduler.add_job(LiquidityScore, 'interval', seconds=30)
    scheduler.add_job(visualization, CronTrigger(hour=23, minute=59, second=50),args=['BTC'])
    scheduler.add_job(visualization, CronTrigger(hour=23, minute=59, second=52),args=['ETH'])
    scheduler.add_job(sendmsg, CronTrigger(hour=23, minute=59,second=55),args=['BTC'])
    scheduler.add_job(sendmsg, CronTrigger(hour=23, minute=59, second=57), args=['ETH'])
    scheduler.start()

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()

