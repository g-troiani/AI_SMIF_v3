import backtrader as bt

class BollingerBandTrendStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('devfactor', 2.0),
    )

    def __init__(self):
        # Initialize Bollinger Bands indicator
        self.boll = bt.indicators.BollingerBands(
            self.data.close, 
            period=self.params.period, 
            devfactor=self.params.devfactor
        )
        
        # For convenience, alias upper and lower bands
        self.upper_band = self.boll.lines.top
        self.mid_band = self.boll.lines.mid
        self.lower_band = self.boll.lines.bot

    def next(self):
        current_close = self.data.close[0]
        
        # Check if we have an open position
        if not self.position:
            # No position: Check for entry signals
            if current_close > self.upper_band[0]:
                # Trend up: Go LONG
                self.buy()
            elif current_close < self.lower_band[0]:
                # Trend down: Go SHORT
                self.sell()
        else:
            # We have a position: Check for exit conditions based on position direction
            if self.position.size > 0:
                # Currently LONG
                # Exit if price falls back below upper band
                if current_close < self.upper_band[0]:
                    self.close()
            else:
                # Currently SHORT
                # Exit if price rises back above lower band
                if current_close > self.lower_band[0]:
                    self.close()







import backtrader as bt

class BollingerBandTrendStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('devfactor', 2.0),
        ('stop_loss', None),      # decimal form, e.g. 0.05 for 5%
        ('take_profit', None),    # decimal form, e.g. 0.10 for 10%
    )

    def __init__(self):
        # Initialize Bollinger Bands
        self.boll = bt.indicators.BollingerBands(
            self.data.close, 
            period=self.params.period, 
            devfactor=self.params.devfactor
        )
        
        self.upper_band = self.boll.lines.top
        self.mid_band = self.boll.lines.mid
        self.lower_band = self.boll.lines.bot

    def next(self):
        current_close = self.data.close[0]
        
        # Determine if we will use bracket orders
        use_bracket = (
            self.params.stop_loss is not None and self.params.stop_loss > 0 and
            self.params.take_profit is not None and self.params.take_profit > 0
        )

        if not self.position:
            # No position: Check for entry signals
            if current_close > self.upper_band[0]:
                # Trend up: Go LONG
                if use_bracket:
                    entry_price = current_close
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
                else:
                    self.buy()

            elif current_close < self.lower_band[0]:
                # Trend down: Go SHORT
                if use_bracket:
                    entry_price = current_close
                    stop_price = entry_price * (1.0 + self.params.stop_loss)
                    limit_price = entry_price * (1.0 - self.params.take_profit)
                    self.sell_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
                else:
                    self.sell()

        else:
            # If we are using bracket orders, we rely on them for exits, no manual close needed.
            if not use_bracket:
                # Manual exit conditions (if not using bracket)
                if self.position.size > 0:
                    # LONG position
                    if current_close < self.upper_band[0]:
                        self.close()
                else:
                    # SHORT position
                    if current_close > self.lower_band[0]:
                        self.close()









import backtrader as bt

class VolumeConfirmedBreakoutStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('stop_loss', None),     # e.g. 0.05 for 5%
        ('take_profit', None),   # e.g. 0.10 for 10%
    )

    def __init__(self):
        # Rolling max/min indicators
        self.highest = bt.indicators.Highest(self.data.close, period=self.params.period)
        self.lowest = bt.indicators.Lowest(self.data.close, period=self.params.period)
        
        # Average volume
        self.avg_volume = bt.indicators.SMA(self.data.volume, period=self.params.period)

    def next(self):
        current_close = self.data.close[0]
        current_volume = self.data.volume[0]
        rolling_max = self.highest[0]
        rolling_min = self.lowest[0]
        avg_vol = self.avg_volume[0]

        # Determine if we will use bracket orders
        use_bracket = (
            self.params.stop_loss is not None and self.params.stop_loss > 0 and
            self.params.take_profit is not None and self.params.take_profit > 0
        )

        if not self.position:
            # No current position, look for breakouts
            if current_close > rolling_max and current_volume > avg_vol:
                # Bullish breakout
                if use_bracket:
                    entry_price = current_close
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
                else:
                    self.buy()
            
            elif current_close < rolling_min and current_volume > avg_vol:
                # Bearish breakout
                if use_bracket:
                    entry_price = current_close
                    stop_price = entry_price * (1.0 + self.params.stop_loss)
                    limit_price = entry_price * (1.0 - self.params.take_profit)
                    self.sell_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
                else:
                    self.sell()

        else:
            # If we are using bracket orders, no manual exit needed.
            if not use_bracket:
                # Manual exit logic
                if self.position.size > 0:  
                    # Long position: exit if price falls back below rolling_max
                    if current_close < rolling_max:
                        self.close()
                else:
                    # Short position: exit if price rises back above rolling_min
                    if current_close > rolling_min:
                        self.close()











import backtrader as bt

class MeanReversionSMAZScoreStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.period)
        self.std = bt.indicators.StdDev(self.data.close, period=self.params.period)

    def next(self):
        current_close = self.data.close[0]
        sma_val = self.sma[0]
        std_val = self.std[0] if self.std[0] != 0 else 1e-9  # Prevent division by zero
        z_score = (current_close - sma_val) / std_val

        # Determine if bracket orders will be used
        use_bracket = (
            self.params.stop_loss is not None and self.params.stop_loss > 0 and
            self.params.take_profit is not None and self.params.take_profit > 0
        )

        if not self.position:
            # Look for extreme deviations
            if z_score > 2:
                # Overbought, go SHORT
                if use_bracket:
                    entry_price = current_close
                    stop_price = entry_price * (1.0 + self.params.stop_loss)   # stop above entry
                    limit_price = entry_price * (1.0 - self.params.take_profit) # tp below entry
                    self.sell_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
                else:
                    self.sell()

            elif z_score < -2:
                # Oversold, go LONG
                if use_bracket:
                    entry_price = current_close
                    stop_price = entry_price * (1.0 - self.params.stop_loss)   # stop below entry
                    limit_price = entry_price * (1.0 + self.params.take_profit) # tp above entry
                    self.buy_bracket(price=entry_price, stopprice=stop_price, limitprice=limit_price)
                else:
                    self.buy()

        else:
            # If using bracket orders, exit is handled by them.
            if not use_bracket:
                # Manual exit when Z-score is near zero (|z_score| < 0.5)
                if abs(z_score) < 0.5:
                    self.close()









