import pandas as pd
import requests

from vnbrokers.base import BaseBroker, LONG_DEAL_TYPE, SHORT_DEAL_TYPE

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
BANK_MARGIN_PORTFOLIO_ID = 123
TRADING_FEE = 0.7


class Broker(BaseBroker):
    TRADING_FEE = TRADING_FEE

    def __init__(self, symbol, investor_id, investor_account_id, bearer_token, bank_margin_portfolio_id=None):
        super().__init__(symbol)
        self.bankMarginPortfolioId = bank_margin_portfolio_id or BANK_MARGIN_PORTFOLIO_ID
        self.investorId = investor_id
        self.investorAccountId = investor_account_id
        self.bearer_token = bearer_token

    def open_deal(self, deal_type, price, order_type="LO"):
        if not self.qty:
            self.qty = 1
        url = "https://services.entrade.com.vn/entrade-api/derivative/orders"
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Authorization': 'Bearer ' + self.bearer_token
        }
        data = {
            'symbol': self.symbol,
            'side': deal_type,
            'orderType': order_type,
            'quantity': self.qty,
            'bankMarginPortfolioId': self.bankMarginPortfolioId,
            'investorId': self.investorId
        }
        if order_type != "MTL":
            price = round(price, 1)
            data['price'] = price

        try:
            res = requests.post(url, json=data, headers=header)
            if res.status_code != 200:
                raise Exception(res.json())
        except Exception as e:
            print(f"Error opening deal ({deal_type}): {e}")

    def close_all_orders(self):
        url = "https://services.entrade.com.vn/entrade-api/derivative/orders?startIndex=1&endIndex=100&investorId=" + self.investorId
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Authorization': 'Bearer ' + self.bearer_token
        }

        res = requests.get(url, headers=header)
        if "data" in res.json():
            orders = res.json()['data']
            if len(orders) > 0:
                for order in orders:
                    if (order['orderStatus'] == 'New' or order['orderStatus'] == 'Pending') and order['id']:
                        self.cancel_order(order['id'])

    def cancel_order(self, order_id):
        url = "https://services.entrade.com.vn/entrade-api/derivative/orders/" + str(order_id)
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Authorization': 'Bearer ' + self.bearer_token
        }
        try:
            requests.delete(url, headers=header)
        except:
            print("Error while cancelling deal.")
            exit()

    def pull_deal_data(self):
        url = 'https://services.entrade.com.vn/entrade-api/derivative/deals?endIndex=100&startIndex=1&investorId=' + self.investorId
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
                if deal['status'] == 'ACTIVE' and deal['averageCostPrice']:
                    self.opened_qty = int(deal['openQuantity'])
                    self.entry_price = deal['averageCostPrice']
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

    def set_risk(self):
        deal_id = self.deal_id
        if not deal_id or not self.take_profit or not self.force_stoploss:
            print("Error(*) while setting stoploss & take profit.")
            exit()
        url = "https://services.entrade.com.vn/entrade-api/risk_configs?investorAccountId=" + self.investorId
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Authorization': 'Bearer ' + self.bearer_token
        }
        data = {
            'cutLossRate': 0.05,
            'investorId': self.investorId,
            'investorAccountId': self.investorAccountId,
            'trailingEnabled': False
        }
        try:
            res = requests.patch(url, json=data, headers=header)
            if res.status_code != 200:
                print(res.json())
        except:
            print("Error(**) while setting stoploss & take profit.")
            exit()

    def set_reward(self):
        deal_id = self.deal_id
        if not deal_id or not self.take_profit or not self.force_stoploss:
            print("Error(*) while setting stoploss & take profit.")
            exit()
        url = "https://services.entrade.com.vn/entrade-api/deal_risks"
        header = {
            'User-Agent': USER_AGENT,
            'ContentType': 'application/json',
            'Authorization': 'Bearer ' + self.bearer_token
        }
        data = {
            'id': deal_id,
            'takeProfitPrice': self.take_profit
        }
        try:
            res = requests.post(url, json=data, headers=header)
            if res.status_code != 200:
                print(res.json())
        except:
            print("Error(**) while setting stoploss & take profit.")
            exit()
