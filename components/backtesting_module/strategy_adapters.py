# File: components/backtesting_module/backtrader/strategy_adapters.py
# Type: py

import backtrader as bt


class BaseStrategyWithSLTP(bt.Strategy):
    params = (
        ('stop_loss', 0.0),
        ('take_profit', 0.0),
    )
    
    # If you don’t provide stop_loss and take_profit, the strategy will just place simple buy/sell orders without bracket orders.
    # cerebro.addstrategy(BollingerBandsStrategy, period=20, devfactor=2, stop_loss=0.05, take_profit=0.10)


    def __init__(self):
        self.entry_price = None

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
            elif order.issell():
                self.entry_price = None

    def check_sl_tp(self):
        if self.position and self.entry_price:
            current_price = self.data.close[0]
            pct_change = (current_price - self.entry_price) / self.entry_price * 100.0
            # Check stop loss
            if self.params.stop_loss and pct_change <= -abs(self.params.stop_loss):
                self.close()
            # Check take profit
            elif self.params.take_profit and pct_change >= abs(self.params.take_profit):
                self.close()


class MovingAverageCrossoverStrategy(bt.Strategy):
    """Moving Average Crossover Strategy Implementation"""
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
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.crossover < 0 and self.position:
            self.sell()






class RSIStrategy(bt.Strategy):
    """RSI Strategy Implementation"""
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
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.rsi > self.params.overbought and self.position:
            self.sell()







class MACDStrategy(bt.Strategy):
    """MACD Strategy Implementation"""
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
        if self.macd.macd > self.macd.signal and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.macd.macd < self.macd.signal and self.position:
            self.sell()





class BollingerBandsStrategy(bt.Strategy):
    """Bollinger Bands Strategy Implementation"""
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
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.data.close[0] > self.boll.lines.top[0] and self.position:
            self.sell()






class MomentumStrategy(bt.Strategy):
    """Simple Momentum Strategy Implementation"""
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
        if self.momentum > 0 and not self.position:
            entry_price = self.data.close[0]
            if self.params.stop_loss is not None and self.params.take_profit is not None:
                stop_price = entry_price * (1.0 - self.params.stop_loss)
                limit_price = entry_price * (1.0 + self.params.take_profit)
                self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
            else:
                self.buy()
        elif self.momentum < 0 and self.position:
            self.sell()


# (2) define VolumeToggleStrategy here (before referencing it)
class VolumeToggleStrategy(bt.Strategy):
    params = (
        ('volume_threshold', 100),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        pass

    def next(self):
        current_volume = self.data.volume[0]
        if current_volume > self.params.volume_threshold:
            # toggle positions
            if not self.position:
                # open (buy)
                entry_price = self.data.close[0]
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
                else:
                    self.buy()
            else:
                # close (sell)
                self.sell()



class StrategyAdapter:
    """
    Strategy adapter that maps strategy names to their implementations.
    """
    
    STRATEGIES = {
        'MovingAverageCrossover': MovingAverageCrossoverStrategy,
        'RSI': RSIStrategy,
        'MACD': MACDStrategy,
        'BollingerBands': BollingerBandsStrategy,
        'Momentum': MomentumStrategy,
        'VolumeToggleStrategy': VolumeToggleStrategy,
    }

    @staticmethod
    def get_strategy(name):
        if name not in StrategyAdapter.STRATEGIES:
            raise ValueError(
                f"Strategy '{name}' not found. "
                f"Available strategies: {list(StrategyAdapter.STRATEGIES.keys())}"
            )
        return StrategyAdapter.STRATEGIES[name]