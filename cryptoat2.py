import ccxt
import datetime
import FinanceDataReader as fdr
import pyupbit
import time
import requests

p_exchange = 1150  # 환율 초기값
binance = ccxt.binance({
    'apiKey': '',
    'secret': '',
})  # 바이낸스 API
upbit = pyupbit.Upbit('', '')
myToken = ''  # slack
ticker = 'EOS'  # 종목
count = 19  # 주문 수량
mount = 100000  # 주문 금액
status = 1.01  # 프리미엄 기준
gap = 0.74  # 갭
p_cnt = 299
p_exchange = 1165.1


def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )


def get_exchange():
    try:
        today = str(datetime.date.today())
        today = int(today.replace('-', ''))
        today = str(today)
        exchange = fdr.DataReader('USD/KRW', today).iloc[-1, 0]
        post_message(myToken, "#stock", exchange)

    except:
        today = 210817
        exchange = fdr.DataReader('USD/KRW', today).iloc[-1, 0]
        post_message(myToken, "#stock", '환율 날짜 오류: ' + str(exchange))
    print('환율: ' + str(exchange))
    return exchange


def binance_balance(tk):
    balance = binance.fetch_balance()  # 잔고 조회
    b_balance = balance[tk]['free']
    # print(tk + ' Binance 잔고: ' + str(b_balance))
    return b_balance


def binance_price(tk, p_exchange):
    b_ticker = binance.fetch_ticker(tk+'/USDT')  # 현재가 조회
    price = b_ticker['close']
    price2 = price * p_exchange # 원화 계산
    # print(tk + ' Binance 현재가: ' + str(price2))
    return price2


def binance_usd_price(tk):
    b_ticker = binance.fetch_ticker(tk+'/USDT')  # 현재가 조회
    price = b_ticker['close']
    return price


def binance_buy(tk, cnt):
    order = binance.create_market_buy_order(tk + '/USDT', cnt)  # 시장가 매수 주문
    print(order)
    # post_message(myToken, "#stock", order)
    print('바이낸스 시장가 매수')


def binance_sell(tk, cnt):
    order = binance.create_market_sell_order(tk + '/USDT', cnt)  # 시장가 매도 주문
    print(order)
    # post_message(myToken, "#stock", print(order))
    print('바이낸스 시장가 매도')


def upbit_price(tk):
    u_price = pyupbit.get_current_price('KRW-' + tk)
    # print(tk + ' Upbit 현재가: ' + str(u_price))
    return u_price


def upbit_buy(tk, mnt):  # 업비트 시장가 매수는 금액 기준
    u_ticker = 'KRW-' + tk
    market_price_buy = upbit.buy_market_order(u_ticker, mnt)
    print(market_price_buy)
    # post_message(myToken, "#stock", print(market_price_buy))
    print('업비트 시장가 매수')


def upbit_sell(tk, cnt):
    u_ticker = 'KRW-' + tk
    market_price_sell = upbit.sell_market_order(u_ticker, cnt)
    print(market_price_sell)
    # post_message(myToken, "#stock", print(market_price_sell))
    print('업비트 시장가 매도')


def get_premium(b_price, u_price, tk):
    premium = 100*(u_price-b_price)/u_price
    # print(tk + ' 프리미엄: ' + str(round(premium, 3)) + '%')
    return premium


def get_premium(b_price, u_price, tk):
    premium = 100*(u_price-b_price)/u_price
    # print(tk + ' 프리미엄: ' + str(round(premium, 3)) + '%')
    return premium



while True:
    try:

        if binance_balance('USDT') > (count*binance_usd_price(ticker)+5) and upbit.get_balance('KRW-' + ticker) > count:
            # print('프리미엄 잔고 가능')
            if get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker) > (status+gap):
                upbit_sell(ticker, count)
                binance_buy(ticker, count)
                post_message(myToken, "#stock", ticker + ' 프리미엄 체결: ' + str(round(get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker), 2)))

                if binance_balance('USDT') < (count * binance_usd_price(ticker) + 10):
                    p_exchange = get_exchange()
                    status = get_premium((binance_usd_price(ticker) * p_exchange), upbit_price(ticker), ticker)


        #     else:
        #         print('프리미엄 Pass')
        # else:
        #     print('바이낸스 USDT 부족')

        if upbit.get_balance('KRW') > mount + 5000 and binance_balance(ticker) > mount/binance_price(ticker, p_exchange):
            # print('역프리미엄 잔고 가능')
            if get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker) < (status+gap):
                count2 = round(mount / (upbit_price(ticker) + 5), 2)
                upbit_buy(ticker, mount)
                binance_sell(ticker, count2)
                post_message(myToken, "#stock", ticker + ' 역프리미엄 체결: ' + str(round(get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker), 2)))
        #     else:
        #         print('역프리미엄 Pass')
        # else:
        #     print('업비트 KRW 부족')

        p_cnt = p_cnt + 1

        if p_cnt == 300:
            p_cnt = 0
            status = (status * 0.97) + (get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker) * 0.03)
            post_message(myToken, "#stock", ticker + ' 프리미엄 기준: ' + str(round(status, 2)))

        time.sleep(7)

    except Exception as e:
        post_message(myToken, "#stock", e)
        time.sleep(30)
