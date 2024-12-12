# File: components/backtesting_module/backtrader/strategies.py
# Type: py

import backtrader as bt

class MovingAverageCrossoverStrategy(bt.Strategy):
    params = (
        ('short_window', 10),
        ('long_window', 20),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.short_ma = bt.indicators.SMA(self.data.close, period=self.params.short_window)
        self.long_ma = bt.indicators.SMA(self.data.close, period=self.params.long_window)
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)

    def next(self):
        if self.crossover > 0 and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.crossover < 0 and self.position:
            self.close()

class RSIStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('overbought', 70),
        ('oversold', 30),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)

    def next(self):
        if self.rsi < self.params.oversold and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.rsi > self.params.overbought and self.position:
            self.close()

class MACDStrategy(bt.Strategy):
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )

    def next(self):
        if self.macd.macd[0] > self.macd.signal[0] and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.macd.macd[0] < self.macd.signal[0] and self.position:
            self.close()

class BollingerBandsStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('devfactor', 2),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.period,
            devfactor=self.params.devfactor
        )

    def next(self):
        if self.data.close[0] < self.boll.lines.bot[0] and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.data.close[0] > self.boll.lines.top[0] and self.position:
            self.close()

class MomentumStrategy(bt.Strategy):
    params = (
        ('momentum_period', 10),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.momentum = bt.indicators.MomentumOscillator(
            self.data.close,
            period=self.params.momentum_period
        )

    def next(self):
        if len(self.data) > self.params.momentum_period:
            past_price = self.data.close[-self.params.momentum_period]
            current_price = self.data.close[0]
            momentum = (current_price / past_price) - 1.0

            if momentum > 0 and not self.position:
                entry_price = self.data.close[0]
                if self.params.stop_loss and self.params.take_profit and self.params.stop_loss > 0 and self.params.take_profit > 0:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
                else:
                    self.buy()
            elif momentum <= 0 and self.position:
                self.close()



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
        self.trades_executed = 0  # Track number of trades

    def next(self):
        self.bar_count += 1
        
        if not self.position:
            # Buy immediately on the first bar
            self.buy()
            self.log("BUY ORDER SENT")
        else:
            # Close the position on the next bar
            self.log("CLOSING POSITION")
            self.close()

    def notify_order(self, order):
        # When an order completes, increment trades_executed if it was a completed trade
        if order.status in [order.Completed]:
            # Count both buy and sell completions as trade executions
            self.trades_executed += 1

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()} {txt}')
