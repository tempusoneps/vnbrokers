from abc import ABC, abstractmethod
import pandas as pd

LONG_DEAL_TYPE = "NB"
SHORT_DEAL_TYPE = "NS"


class BaseBroker(ABC):
    TRADING_FEE = 0.0

    def __init__(self, symbol, trading_fee=None):
        self.symbol = symbol
        self.trading_fee = self.TRADING_FEE if trading_fee is None else trading_fee
        self.do_date = ''
        self.opened_qty = 0
        self.entry_price = 0
        self.exit_price = 0
        self.entry_time = ''
        self.is_long_open = False
        self.is_short_open = False
        self.history = []
        self._trades = pd.DataFrame(columns=("EntryTime", "EntryPrice", "ExitTime", "ExitPrice", "Type", "Profit"))
        self.mode = 'live'
        self.number_of_deal = 0
        self.qty = 0
        self.profit = 0
        self.total_profit = 0
        self.stoploss = 0
        self.force_stoploss = 0
        self.take_profit = 0
        self.deal_id = 0
        self.trigger = False
        self.logs = []

    def set_qty(self, new_qty):
        self.qty = new_qty

    def set_stoploss(self, price):
        self.stoploss = price

    def set_force_stoploss(self, price):
        self.force_stoploss = price

    def set_take_profit(self, price):
        self.take_profit = price

    def set_trigger(self, is_trigger):
        self.trigger = is_trigger

    def open_long_deal(self, price, order_type="LO"):
        self.trigger_before()
        if self.mode == 'live':
            self.opened_qty = self.qty
            self.entry_price = price
            self.is_long_open = True
            self.history.append('(Long) with price {} at {}'.format(price, self.do_date))
        self.open_deal(LONG_DEAL_TYPE, price, order_type)
        self.trigger_after()

    def open_short_deal(self, price, order_type="LO"):
        self.trigger_before()
        if self.mode == 'live':
            self.opened_qty = self.qty
            self.entry_price = price
            self.is_short_open = True
            self.history.append('(Short) with price {} at {}'.format(price, self.do_date))
        self.open_deal(SHORT_DEAL_TYPE, price, order_type)
        self.trigger_after()

    def close_all_open_deal(self, expected_price):
        self.trigger_before()
        if self.has_opened_deal():
            self.qty = self.opened_qty
            if self.is_long_open:
                self.close_long_deal(expected_price, "MTL")
            elif self.is_short_open:
                self.close_short_deal(expected_price, "MTL")
        self.trigger_after()
        return False

    def close_long_deal(self, price, order_type="LO"):
        self.trigger_before()
        self.exit_price = price
        profit = price - self.entry_price - self.trading_fee
        profit = round(profit, 1)
        self.profit = profit
        self.opened_qty = 0
        self.is_long_open = False
        if self.mode == 'live':
            self.history.append(
                '  --- (Close - Long) with price {} at {}, profit: {}'.format(price, self.do_date, profit))
        if self.mode == 'dev':
            self.total_profit += profit
            self.history.append(
                '  --- (Close - Long) with price {} at {}, profit: {}, total profit: {}'.format(
                    price, self.do_date, profit, self.total_profit))
            self._trades.loc[len(self._trades)] = [
                self.entry_time, self.entry_price, self.do_date, price, "Long", profit
            ]
        self.open_deal(SHORT_DEAL_TYPE, price, order_type)
        self.trigger_after()

    def close_short_deal(self, price, order_type="LO"):
        self.trigger_before()
        self.exit_price = price
        profit = self.entry_price - price - self.trading_fee
        profit = round(profit, 1)
        self.profit = profit
        self.opened_qty = 0
        self.is_short_open = False
        if self.mode == 'live':
            self.history.append(
                '  --- (Close - Short) with price {} at {}, profit: {}'.format(price, self.do_date, profit))
        if self.mode == 'dev':
            self.total_profit += profit
            self.history.append(
                '  --- (Close - Short) with price {} at {}, profit: {}, total profit: {}'.format(
                    price, self.do_date, profit, self.total_profit))
            self._trades.loc[len(self._trades)] = [
                self.entry_time, self.entry_price, self.do_date, price, "Short", profit
            ]
        self.open_deal(LONG_DEAL_TYPE, price, order_type)
        self.trigger_after()

    @abstractmethod
    def open_deal(self, deal_type, price, order_type="LO"):
        pass

    @abstractmethod
    def close_all_orders(self):
        pass

    @abstractmethod
    def cancel_order(self, order_id):
        pass

    @abstractmethod
    def pull_deal_data(self):
        pass

    def set_risk_reward(self):
        return

    def has_opened_deal(self):
        return self.opened_qty > 0

    def trigger_before(self):
        if not self.trigger:
            return
        order_type = "Long" if self.is_long_open else ("Short" if self.is_short_open else "None")
        msg = (
            f"Before. Ordered qty: {self.opened_qty}, order_type: {order_type}, "
            f"entry_price: {self.entry_price}, entry_time: {self.entry_time}"
        )
        self.log(msg)

    def trigger_after(self):
        if not self.trigger:
            return
        msg = f"After. Ordered qty: {self.opened_qty}."
        self.log(msg)

    def log(self, msg):
        if self.mode == 'live':
            self.logs.append(msg)
