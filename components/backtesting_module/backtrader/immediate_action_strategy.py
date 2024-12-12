import backtrader as bt

class ImmediateActionStrategy(bt.Strategy):
    """
    A simple strategy that:
    - Buys as soon as the first bar is received.
    - Closes the position on the following bar.
    Ensures almost immediate execution once data comes in.
    """

    def __init__(self):
        self.bar_count = 0
        self.bars_received = False  # Track if we received any bars
        self.trades_made = False    # Track if any trades were executed

    def next(self):
        self.bar_count += 1
        self.bars_received = True   # We have at least one bar

        if not self.position:
            # Buy immediately on the first bar
            self.buy()
            self.log("BUY ORDER SENT")
            self.trades_made = True
        else:
            # Close position on the next bar
            self.log("CLOSING POSITION")
            self.close()
            self.trades_made = True

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()} {txt}')
