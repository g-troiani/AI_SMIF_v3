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



# class PAUL_RSIStrategy(bt.Strategy):
#     """
#     PAUL_RSI Strategy:
#     Detects bullish and bearish divergences on RSI and trades accordingly.
#     """
#     params = (
#         ('rsi_period', 14),
#         ('overbought', 70),
#         ('oversold', 30),
#         ('target_rsi', 50),
#         ('risk_percent', 0.02),  # e.g., 2% risk management
#     )

#     def __init__(self):
#         self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
#         self.bullish_divergence = False
#         self.bearish_divergence = False
#         self.entry_price = None

#     def detect_divergence(self):
#         lows = self.data.low
#         highs = self.data.high
#         rsi = self.rsi

#         # Detect Bullish Divergence: price lower lows, RSI higher highs
#         if lows[-1] < lows[-2] and rsi[-1] > rsi[-2]:
#             self.bullish_divergence = True
#             self.bearish_divergence = False

#         # Detect Bearish Divergence: price higher highs, RSI lower lows
#         elif highs[-1] > highs[-2] and rsi[-1] < rsi[-2]:
#             self.bullish_divergence = False
#             self.bearish_divergence = True

#     def next(self):
#         self.detect_divergence()

#         # Entry logic
#         if self.bullish_divergence and not self.position:
#             self.entry_price = self.data.close[0]
#             stop_loss = self.entry_price * (1 - self.params.risk_percent)
#             target_price = self.entry_price * (1 + self.params.risk_percent)

#             # Enter long
#             self.buy()
#             self.stop_loss = stop_loss
#             self.target_price = target_price

#         elif self.bearish_divergence and not self.position:
#             self.entry_price = self.data.close[0]
#             stop_loss = self.entry_price * (1 + self.params.risk_percent)
#             target_price = self.entry_price * (1 - self.params.risk_percent)

#             # Enter short
#             self.sell()
#             self.stop_loss = stop_loss
#             self.target_price = target_price

#         # Exit logic
#         if self.position:
#             # For a long position
#             if self.position.size > 0:
#                 if self.data.close[0] >= self.target_price or self.data.close[0] <= self.stop_loss:
#                     self.close()
#             # For a short position
#             elif self.position.size < 0:
#                 if self.data.close[0] <= self.target_price or self.data.close[0] >= self.stop_loss:
#                     self.close()



import backtrader as bt
import math

class PAUL_RSIStrategy(bt.Strategy):
    params = (
        ('period', 14),
        ('overbought', 70),
        ('oversold', 30),
        ('target_rsi', 50),
        ('stop_loss_pct', 0.02),   # example 2% stop loss
        ('take_profit_pct', 0.05), # example 5% take profit
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.period)

        # Flags for whether a divergence-based trade was entered
        self.bullish_divergence_detected = False
        self.bearish_divergence_detected = False
        self.entry_price = None

        # We'll store recent highs and lows for divergence detection
        self.price_highs = []
        self.price_lows = []
        self.rsi_highs = []
        self.rsi_lows = []

        # Track last divergence type
        self.last_divergence_type = None

    def next(self):
        # Update lists of recent highs/lows (windowed approach)
        # In a real scenario, you'd implement logic to detect swing points.
        # Here, we just keep a rolling window and try to detect patterns.
        window = 10  # look back over last 10 bars to detect divergence
        self.price_highs = [self.data.high[-i] for i in range(1, window+1)]
        self.price_lows = [self.data.low[-i] for i in range(1, window+1)]
        self.rsi_highs = [self.rsi[-i] for i in range(1, window+1)]
        self.rsi_lows = [self.rsi[-i] for i in range(1, window+1)]

        current_rsi = self.rsi[0]

        # Detect Divergence
        divergence_status = self.detect_divergence()

        # Entry Conditions
        if divergence_status == "Bullish Divergence" and not self.position:
            self.bullish_divergence_detected = True
            self.bearish_divergence_detected = False
            self.last_divergence_type = "bullish"
            self.buy()
            self.entry_price = self.data.close[0]

        if divergence_status == "Bearish Divergence" and not self.position:
            self.bearish_divergence_detected = True
            self.bullish_divergence_detected = False
            self.last_divergence_type = "bearish"
            self.sell()
            self.entry_price = self.data.close[0]

        # Exit Conditions
        if self.position:
            # Check RSI target exit
            if self.bullish_divergence_detected and current_rsi >= self.params.target_rsi:
                self.close()
                self.bullish_divergence_detected = False
                self.entry_price = None

            if self.bearish_divergence_detected and current_rsi <= self.params.target_rsi:
                self.close()
                self.bearish_divergence_detected = False
                self.entry_price = None

            # Stop Loss / Take Profit
            if self.entry_price:
                if self.position.size > 0: # Long
                    if self.data.close[0] <= self.entry_price * (1.0 - self.params.stop_loss_pct):
                        self.close()  # stop loss hit
                    elif self.data.close[0] >= self.entry_price * (1.0 + self.params.take_profit_pct):
                        self.close()  # take profit hit
                else: # Short
                    if self.data.close[0] >= self.entry_price * (1.0 + self.params.stop_loss_pct):
                        self.close()  # stop loss hit
                    elif self.data.close[0] <= self.entry_price * (1.0 - self.params.take_profit_pct):
                        self.close()  # take profit hit

    def detect_divergence(self):
        # Simple Divergence Detection:
        # Bullish divergence: price makes lower lows, RSI makes higher lows
        # Bearish divergence: price makes higher highs, RSI makes lower highs

        if len(self.price_lows) < 2 or len(self.rsi_lows) < 2 or len(self.price_highs) < 2 or len(self.rsi_highs) < 2:
            return "No Divergence"

        price_low1 = min(self.price_lows[:5])   # recent low
        price_low2 = min(self.price_lows[5:])   # previous low
        rsi_low1 = min(self.rsi_lows[:5])
        rsi_low2 = min(self.rsi_lows[5:])

        price_high1 = max(self.price_highs[:5]) # recent high
        price_high2 = max(self.price_highs[5:]) # previous high
        rsi_high1 = max(self.rsi_highs[:5])
        rsi_high2 = max(self.rsi_highs[5:])

        # Bullish divergence check
        # Price making lower lows: price_low1 < price_low2
        # RSI making higher lows: rsi_low1 > rsi_low2
        if (price_low1 < price_low2) and (rsi_low1 > rsi_low2):
            return "Bullish Divergence"

        # Bearish divergence check
        # Price making higher highs: price_high1 > price_high2
        # RSI making lower highs: rsi_high1 < rsi_high2
        if (price_high1 > price_high2) and (rsi_high1 < rsi_high2):
            return "Bearish Divergence"

        return "No Divergence"
