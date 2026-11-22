from vnbrokers.base import BaseBroker

TRADING_FEE = 0.0


class Broker(BaseBroker):
    TRADING_FEE = TRADING_FEE

    def __init__(self, symbol, trading_fee=None):
        super().__init__(symbol, trading_fee=trading_fee)

    def open_deal(self, deal_type, price, order_type="LO"):
        if not self.qty:
            self.qty = 1
        self.number_of_deal += 1
        self.log(
            f"[Simulator] open_deal: symbol={self.symbol}, side={deal_type}, "
            f"order_type={order_type}, price={round(price, 1)}, qty={self.qty}"
        )

    def close_all_orders(self):
        self.log(f"[Simulator] close_all_orders: symbol={self.symbol}")

    def cancel_order(self, order_id):
        self.log(f"[Simulator] cancel_order: order_id={order_id}")

    def pull_deal_data(self):
        self.log(f"[Simulator] pull_deal_data: symbol={self.symbol}, opened_qty={self.opened_qty}")
