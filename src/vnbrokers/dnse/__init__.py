import pandas as pd
import requests

from vnbrokers.base import BaseBroker, LONG_DEAL_TYPE, SHORT_DEAL_TYPE

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
DEFAULT_DNSE_LOAN_PACKAGE_ID = 1306
TRADING_FEE = 0.3


class Broker(BaseBroker):
    TRADING_FEE = TRADING_FEE

    def __init__(self, symbol, account_no, bearer_token, trading_token, loan_package_id=None):
        super().__init__(symbol)
        self.loan_package_id = loan_package_id or DEFAULT_DNSE_LOAN_PACKAGE_ID
        self.account_no = account_no
        self.bearer_token = bearer_token
        self.trading_token = trading_token

    def set_loan_package_id(self, new_id):
        self.loan_package_id = new_id

    def open_deal(self, deal_type, price, order_type="LO"):
        if not self.qty:
            self.qty = 1
        url = "https://services.entrade.com.vn/dnse-order-service/derivative/orders"
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Trading-Token': self.trading_token,
            'Authorization': 'Bearer ' + self.bearer_token
        }

        price = round(price, 1)

        data = {
            'symbol': self.symbol,
            'side': deal_type,
            'orderType': order_type,
            'price': price,
            'quantity': self.qty,
            'loanPackageId': self.loan_package_id,
            'accountNo': self.account_no
        }

        res = requests.post(url, json=data, headers=header)
        if res.status_code != 200:
            raise Exception(res.json())

    def set_risk_reward(self):
        deal_id = self.deal_id
        risk = abs(self.entry_price - self.force_stoploss)
        reward = abs(self.take_profit - self.entry_price)
        if not deal_id or not risk or not reward:
            print("Error(*) while setting stoploss & take profit.")
            exit()
        url = "https://services.entrade.com.vn/dnse-derivative-deal-risk/pnl-configs/" + str(deal_id)
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Trading-Token': self.trading_token,
            'Authorization': 'Bearer ' + self.bearer_token
        }

        data = {
            'takeProfitEnabled': True,
            'stopLossEnabled': True,
            'takeProfitStrategy': 'DELTA_PRICE',
            'takeProfitOrderType': 'FASTEST',
            'takeProfitDeltaPrice': reward,
            'stopLossStrategy': 'DELTA_PRICE',
            'stopLossOrderType': 'FASTEST',
            'stopLossDeltaPrice': risk
        }

        try:
            res = requests.post(url, json=data, headers=header)
            if res.status_code != 200:
                print(res.json())
        except:
            print("Error(**) while setting stoploss & take profit.")
            exit()

    def close_all_orders(self):
        url = "https://services.entrade.com.vn/dnse-order-service/derivative/orders?accountNo=" + self.account_no
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Authorization': 'Bearer ' + self.bearer_token
        }

        res = requests.get(url, headers=header)
        if "orders" in res.json():
            orders = res.json()['orders']
            if len(orders) > 0:
                for order in orders:
                    if order['orderStatus'] == 'New' and order['id']:
                        self.cancel_order(order['id'])

    def cancel_order(self, order_id):
        url = "https://services.entrade.com.vn/dnse-order-service/derivative/orders/" + str(
            order_id) + "?accountNo=" + self.account_no
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Trading-Token': self.trading_token,
            'Authorization': 'Bearer ' + self.bearer_token
        }
        try:
            requests.delete(url, headers=header)
        except:
            print("Error while open deal.")
            exit()

    def pull_deal_data(self):
        url = 'https://services.entrade.com.vn/dnse-derivative-core/deals?accountNo=' + self.account_no
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Authorization': 'Bearer ' + self.bearer_token
        }

        try:
            x = requests.get(url, headers=header)
        except:
            print("Error while pulling deal.")
            exit()
        data = []
        if "data" in x.json():
            data = x.json()['data']
        if len(data) > 0:
            for deal in data:
                self.number_of_deal += 1
                if deal['status'] == 'OPEN' and deal['costPrice'] and deal['loanPackageId'] == self.loan_package_id:
                    self.opened_qty = int(deal['openQuantity'])
                    self.entry_price = deal['costPrice']
                    self.deal_id = deal['id']
                    entry_time = pd.to_datetime(deal['modifiedDate']) + pd.DateOffset(hours=7)
                    entry_time = entry_time.strftime("%Y-%m-%d %H:%M:%S")
                    self.entry_time = entry_time
                    if deal['side'] == LONG_DEAL_TYPE:
                        self.is_long_open = True
                    if deal['side'] == SHORT_DEAL_TYPE:
                        self.is_short_open = True
                    break
        else:
            self.opened_qty = 0
            self.is_long_open = False
            self.is_short_open = False
            self.entry_time = ''
