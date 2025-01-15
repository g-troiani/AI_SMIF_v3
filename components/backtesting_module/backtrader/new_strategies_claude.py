# File: components/backtesting_module/backtrader/new_strategies_claude.py

import backtrader as bt
import numpy as np

class BollingerBandTrendStrategy(bt.Strategy):
    """
    Bollinger Band Trend Strategy that identifies trends using band crossovers
    with volume confirmation.
    
    Parameters:
    - period (default: 20): The lookback period for SMA and StdDev calculations
    - devfactor (default: 2.0): Number of standard deviations for the bands
    - vol_period (default: 20): Period for volume moving average
    - vol_factor (default: 1.5): Volume must be this times the average for confirmation
    - stop_loss (default: None): Stop loss percentage (e.g., 0.02 for 2%)
    - take_profit (default: None): Take profit percentage (e.g., 0.04 for 4%)
    """
    
    params = (
        ('period', 20),
        ('devfactor', 2.0),
        ('vol_period', 20),
        ('vol_factor', 1.5),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        # Initialize indicators
        self.boll = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.period,
            devfactor=self.params.devfactor
        )
        
        # Volume moving average for confirmation
        self.vol_ma = bt.indicators.SMA(
            self.data.volume,
            period=self.params.vol_period
        )
        
        # Keep track of position entry price
        self.entry_price = None
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
            elif order.issell():
                self.entry_price = None
            
        self.order = None

    def next(self):
        # Don't take new positions if we have a pending order
        if self.order:
            return
            
        # Volume confirmation check
        volume_confirmed = self.data.volume[0] > self.vol_ma[0] * self.params.vol_factor
        
        if not self.position:  # No position - look for entry signals
            # Trend up signal: price crosses above upper band with volume confirmation
            if self.data.close[0] > self.boll.lines.top[0] and volume_confirmed:
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    self.order = self.buy_bracket(
                        size=None,  # Use default position sizing
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                else:
                    self.order = self.buy()
                    
        else:  # Have position - look for exit signals
            if self.data.close[0] < self.boll.lines.top[0]:  # Price falls below upper band
                self.order = self.close()  # Exit position
    
    def stop(self):
        """Callback called when backtesting is finished."""
        # Can be used to print final results or perform cleanup
        pass
    
    
    
    
    
    
    
import backtrader as bt
import numpy as np

class VolumeBreakoutStrategy(bt.Strategy):
    """
    Volume-Confirmed Breakout Strategy that identifies and trades breakouts beyond
    rolling max/min levels with volume confirmation.
    
    Parameters:
    - period (default: 20): Lookback period for calculating price ranges
    - vol_period (default: 20): Period for volume moving average
    - vol_factor (default: 1.5): Volume must be this times average for confirmation
    - stop_loss (default: None): Stop loss percentage (e.g., 0.02 for 2%)
    - take_profit (default: None): Take profit percentage (e.g., 0.04 for 4%)
    - atr_period (default: 14): Period for ATR calculation (for stop placement)
    - atr_multiplier (default: 2.0): Multiplier for ATR-based stops
    """
    
    params = (
        ('period', 20),
        ('vol_period', 20),
        ('vol_factor', 1.5),
        ('stop_loss', None),
        ('take_profit', None),
        ('atr_period', 14),
        ('atr_multiplier', 2.0),
    )

    def __init__(self):
        # Price range indicators
        self.rolling_max = bt.indicators.Highest(
            self.data.high,
            period=self.params.period
        )
        self.rolling_min = bt.indicators.Lowest(
            self.data.low,
            period=self.params.period
        )
        
        # Volume moving average for confirmation
        self.vol_ma = bt.indicators.SMA(
            self.data.volume,
            period=self.params.vol_period
        )
        
        # ATR for dynamic stop placement
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )
        
        # Keep track of entry price and pending orders
        self.entry_price = None
        self.order = None
        self.stop_order = None
        self.profit_order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
            elif order.issell():
                self.entry_price = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # Handle failed orders
            self.order = None
            
        # Reset order reference if this order is done
        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            if order == self.order:
                self.order = None
            elif order == self.stop_order:
                self.stop_order = None
            elif order == self.profit_order:
                self.profit_order = None

    def next(self):
        # Don't take new positions if we have a pending order
        if self.order:
            return
            
        # Volume confirmation check
        volume_confirmed = self.data.volume[0] > self.vol_ma[0] * self.params.vol_factor
        
        if not self.position:  # No position - look for entry signals
            # Bullish breakout with volume confirmation
            if self.data.close[0] > self.rolling_max[-1] and volume_confirmed:
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    # Fixed percentage stops
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    self.order = self.buy_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                else:
                    # ATR-based stops
                    stop_price = entry_price - self.atr[0] * self.params.atr_multiplier
                    self.order = self.buy()
                    if self.order:
                        self.stop_order = self.sell(exectype=bt.Order.Stop,
                                                  price=stop_price)
            
            # Bearish breakout with volume confirmation
            elif self.data.close[0] < self.rolling_min[-1] and volume_confirmed:
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 + self.params.stop_loss)
                    limit_price = entry_price * (1.0 - self.params.take_profit)
                    self.order = self.sell_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                else:
                    # ATR-based stops
                    stop_price = entry_price + self.atr[0] * self.params.atr_multiplier
                    self.order = self.sell()
                    if self.order:
                        self.stop_order = self.buy(exectype=bt.Order.Stop,
                                                 price=stop_price)
        
        else:  # Have position - look for exit signals
            if self.position.size > 0:  # Long position
                if self.data.close[0] < self.rolling_min[-1]:  # Price breaks below range
                    self.close()  # Exit position
            else:  # Short position
                if self.data.close[0] > self.rolling_max[-1]:  # Price breaks above range
                    self.close()  # Exit position

    def stop(self):
        """Callback called when backtesting is finished."""
        # Can be used to print final results or perform cleanup
        pass
    
    
    
    
    
    
    
import backtrader as bt
import numpy as np

class MeanReversionStrategy(bt.Strategy):
    """
    Mean Reversion Strategy based on z-score deviations from moving average.
    Enters positions when price deviates significantly from its mean and
    exits when it reverts back.
    
    Parameters:
    - period (default: 20): Lookback period for SMA and StdDev calculations
    - entry_zscore (default: 2.0): Z-score threshold for entry
    - exit_zscore (default: 0.5): Z-score threshold for exit
    - stop_loss (default: None): Stop loss percentage
    - take_profit (default: None): Take profit percentage
    - max_positions (default: 1): Maximum number of simultaneous positions
    """
    
    params = (
        ('period', 20),
        ('entry_zscore', 2.0),
        ('exit_zscore', 0.5),
        ('stop_loss', None),
        ('take_profit', None),
        ('max_positions', 1)
    )

    def __init__(self):
        # Calculate SMA and Standard Deviation
        self.sma = bt.indicators.SMA(
            self.data.close,
            period=self.params.period
        )
        
        self.stddev = bt.indicators.StandardDeviation(
            self.data.close,
            period=self.params.period
        )
        
        # Calculate Z-Score manually
        self.zscore = bt.indicators.DivByZero(
            numerator=self.data.close - self.sma,
            denominator=self.stddev,
            zero=0.0
        )
        
        # Track orders and positions
        self.orders = {}  # Track orders per position
        self.entry_prices = {}  # Track entry prices
        self.position_count = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_prices[order.ref] = order.executed.price
                self.position_count += 1
            elif order.issell():
                self.position_count -= 1
                if order.ref in self.entry_prices:
                    del self.entry_prices[order.ref]
                    
            # Remove the order from tracking
            if order.ref in self.orders:
                del self.orders[order.ref]
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if order.ref in self.orders:
                del self.orders[order.ref]

    def next(self):
        # Don't trade until we have enough data for z-score calculation
        if len(self.data) < self.params.period:
            return
            
        # Check for exit signals on existing positions
        for position in list(self.entry_prices.keys()):
            if abs(self.zscore[0]) <= self.params.exit_zscore:
                self.close()  # Exit position when price reverts to mean
                
        # Check for new entry signals if we have capacity
        if self.position_count >= self.params.max_positions:
            return
            
        current_zscore = self.zscore[0]
        
        if not self.position:  # No position - look for entry signals
            if current_zscore <= -self.params.entry_zscore:  # Price significantly below mean
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=None,  # Use default sizer
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    
                    # Track the orders
                    for order in orders:
                        self.orders[order.ref] = order
                else:
                    order = self.buy()
                    if order:
                        self.orders[order.ref] = order
                        
            elif current_zscore >= self.params.entry_zscore:  # Price significantly above mean
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 + self.params.stop_loss)
                    limit_price = entry_price * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=None,  # Use default sizer
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    
                    # Track the orders
                    for order in orders:
                        self.orders[order.ref] = order
                else:
                    order = self.sell()
                    if order:
                        self.orders[order.ref] = order

    def stop(self):
        """Calculate and log final strategy statistics."""
        self.zscore_stats = {
            'max_zscore': max(self.zscore.array),
            'min_zscore': min(self.zscore.array),
            'mean_zscore': np.mean(self.zscore.array),
            'std_zscore': np.std(self.zscore.array)
        }
        
        
        
        
        
        
        

import backtrader as bt
import numpy as np

class PriceDiffOscillator(bt.Indicator):
    """
    Custom indicator that calculates an oscillator based on the ratio of
    positive price differences to total absolute differences.
    
    Range is 0 to 1, where:
    - Values near 1 indicate mostly positive price changes (potentially overbought)
    - Values near 0 indicate mostly negative price changes (potentially oversold)
    """
    
    lines = ('oscillator',)
    params = (('period', 20),)
    
    def __init__(self):
        self.addminperiod(self.params.period + 1)
        # Store diff series for performance
        self.diff = bt.indicators.ChangeRate(self.data.close, period=1)
    
    def next(self):
        diffs = [self.diff[i] for i in range(-self.params.period+1, 1)]
        positive_diffs = sum(d for d in diffs if d > 0)
        total_diffs = sum(abs(d) for d in diffs)
        
        if total_diffs != 0:
            self.lines.oscillator[0] = positive_diffs / total_diffs
        else:
            self.lines.oscillator[0] = 0.5  # Neutral when no price changes

class DiffOscillatorStrategy(bt.Strategy):
    """
    Trading strategy based on a custom oscillator calculated from price differences.
    Enters when the oscillator indicates oversold/overbought conditions and exits
    when it returns to neutral levels.
    
    Parameters:
    - period (default: 20): Lookback period for oscillator calculation
    - oversold (default: 0.2): Oversold threshold for long entries
    - overbought (default: 0.8): Overbought threshold for short entries
    - exit_threshold (default: 0.5): Neutral level for exits
    - exit_band (default: 0.1): Band around neutral for exits
    - stop_loss (default: None): Stop loss percentage
    - take_profit (default: None): Take profit percentage
    """
    
    params = (
        ('period', 20),
        ('oversold', 0.2),
        ('overbought', 0.8),
        ('exit_threshold', 0.5),
        ('exit_band', 0.1),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        # Initialize the custom oscillator
        self.oscillator = PriceDiffOscillator(
            self.data,
            period=self.params.period
        )
        
        # Add moving average of the oscillator for trend confirmation
        self.osc_ma = bt.indicators.SMA(
            self.oscillator.oscillator,
            period=self.params.period
        )
        
        # Track orders and positions
        self.order = None
        self.entry_price = None
        
        # Define exit zones
        self.exit_upper = self.params.exit_threshold + self.params.exit_band
        self.exit_lower = self.params.exit_threshold - self.params.exit_band

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
            elif order.issell():
                self.entry_price = None
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.order = None

    def next(self):
        # Don't trade until we have enough data
        if len(self.data) < self.params.period + 1:
            return
            
        # Don't trade if we have pending orders
        if self.order:
            return
            
        current_osc = self.oscillator.oscillator[0]
        
        if not self.position:  # No position - look for entry signals
            if current_osc < self.params.oversold:  # Oversold - potential long
                # Confirm trend with oscillator MA
                if self.osc_ma[0] < self.osc_ma[-1]:  # Trend still down
                    entry_price = self.data.close[0]
                    
                    if self.params.stop_loss and self.params.take_profit:
                        stop_price = entry_price * (1.0 - self.params.stop_loss)
                        limit_price = entry_price * (1.0 + self.params.take_profit)
                        
                        orders = self.buy_bracket(
                            size=None,
                            price=entry_price,
                            stopprice=stop_price,
                            limitprice=limit_price,
                        )
                        self.order = orders[0]  # Main order
                    else:
                        self.order = self.buy()
                        
            elif current_osc > self.params.overbought:  # Overbought - potential short
                # Confirm trend with oscillator MA
                if self.osc_ma[0] > self.osc_ma[-1]:  # Trend still up
                    entry_price = self.data.close[0]
                    
                    if self.params.stop_loss and self.params.take_profit:
                        stop_price = entry_price * (1.0 + self.params.stop_loss)
                        limit_price = entry_price * (1.0 - self.params.take_profit)
                        
                        orders = self.sell_bracket(
                            size=None,
                            price=entry_price,
                            stopprice=stop_price,
                            limitprice=limit_price,
                        )
                        self.order = orders[0]  # Main order
                    else:
                        self.order = self.sell()
                        
        else:  # Have position - look for exit signals
            if self.exit_lower <= current_osc <= self.exit_upper:  # Price returning to neutral
                self.order = self.close()  # Exit position
                
    def stop(self):
        """Calculate and log final strategy statistics."""
        self.oscillator_stats = {
            'max_value': max(self.oscillator.oscillator.array),
            'min_value': min(self.oscillator.oscillator.array),
            'mean_value': np.mean(self.oscillator.oscillator.array),
            'std_value': np.std(self.oscillator.oscillator.array)
        }
        
        
        


import backtrader as bt
import numpy as np

class MLClassificationStrategy(bt.Strategy):
    """
    Strategy that trades based on machine learning classification predictions.
    Expects probability predictions for price movement direction (up/down).
    
    Parameters:
    - prob_threshold (default: 0.6): Minimum probability for trade entry
    - holding_period (default: 1): Number of bars to hold position
    - stop_loss (default: None): Stop loss percentage
    - take_profit (default: None): Take profit percentage
    - use_dynamic_threshold (default: False): Adjust threshold based on rolling performance
    """
    
    params = (
        ('prob_threshold', 0.6),
        ('holding_period', 1),
        ('stop_loss', None),
        ('take_profit', None),
        ('use_dynamic_threshold', False),
        ('dynamic_lookback', 20),
    )

    def __init__(self):
        # Ensure we have the prediction data
        if not hasattr(self.data, 'pred_prob_up'):
            raise ValueError("Data feed must include 'pred_prob_up' line with predictions")
            
        # Store predictions for easier access
        self.predictions = self.data.pred_prob_up
        
        # Track performance for dynamic threshold adjustment
        if self.params.use_dynamic_threshold:
            self.correct_predictions = []
            self.threshold_history = []
            self.current_threshold = self.params.prob_threshold
        
        # Position management
        self.order = None
        self.entry_price = None
        self.entry_bar = None
        self.holding_bars = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.entry_bar = len(self)  # Current bar number
            elif order.issell():
                self.entry_price = None
                self.entry_bar = None
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.order = None

    def update_threshold(self):
        """Dynamically adjust probability threshold based on recent performance"""
        if len(self.correct_predictions) < self.params.dynamic_lookback:
            return
            
        # Calculate recent accuracy
        recent_accuracy = np.mean(self.correct_predictions[-self.params.dynamic_lookback:])
        
        # Adjust threshold: increase if accuracy is low, decrease if high
        if recent_accuracy < 0.5:  # Below random chance
            self.current_threshold = min(0.8, self.current_threshold + 0.02)
        elif recent_accuracy > 0.7:  # Good performance
            self.current_threshold = max(0.5, self.current_threshold - 0.01)
            
        self.threshold_history.append(self.current_threshold)

    def evaluate_prediction(self):
        """Evaluate if the last prediction was correct"""
        if len(self) < 2:  # Need at least 2 bars
            return
            
        prev_close = self.data.close[-1]
        current_close = self.data.close[0]
        actual_up = current_close > prev_close
        
        # Previous prediction probability
        prev_prob_up = self.predictions[-1]
        predicted_up = prev_prob_up > self.current_threshold
        
        # Store prediction accuracy (1 for correct, 0 for incorrect)
        self.correct_predictions.append(float(predicted_up == actual_up))

    def next(self):
        # Update dynamic threshold if enabled
        if self.params.use_dynamic_threshold:
            self.evaluate_prediction()
            self.update_threshold()
            threshold = self.current_threshold
        else:
            threshold = self.params.prob_threshold
        
        # Don't trade if we have pending orders
        if self.order:
            return

        # Check if we need to exit based on holding period
        if self.position and self.entry_bar is not None:
            bars_held = len(self) - self.entry_bar
            if bars_held >= self.params.holding_period:
                self.close()
                return
        
        current_prob = self.predictions[0]
        
        if not self.position:  # No position - look for entry signals
            if current_prob > threshold:  # Strong probability of up move
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]  # Main order
                else:
                    self.order = self.buy()
                    
            elif current_prob < (1 - threshold):  # Strong probability of down move
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 + self.params.stop_loss)
                    limit_price = entry_price * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]  # Main order
                else:
                    self.order = self.sell()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.params.use_dynamic_threshold:
            self.threshold_stats = {
                'final_threshold': self.current_threshold,
                'mean_threshold': np.mean(self.threshold_history),
                'min_threshold': min(self.threshold_history),
                'max_threshold': max(self.threshold_history),
                'mean_accuracy': np.mean(self.correct_predictions)
            }
            
            
            
            

import backtrader as bt
import numpy as np

class MLRegressionStrategy(bt.Strategy):
    """
    Strategy that trades based on machine learning predicted returns.
    Expects continuous return predictions for next period.
    
    Parameters:
    - return_threshold (default: 0.001): Minimum predicted return for trade entry
    - holding_period (default: 1): Number of bars to hold position
    - stop_loss (default: None): Stop loss percentage
    - take_profit (default: None): Take profit percentage
    - volatility_adjust (default: True): Adjust thresholds based on volatility
    - vol_period (default: 20): Period for volatility calculation
    """
    
    params = (
        ('return_threshold', 0.001),
        ('holding_period', 1),
        ('stop_loss', None),
        ('take_profit', None),
        ('volatility_adjust', True),
        ('vol_period', 20),
        ('vol_threshold', 1.5)  # Volatility threshold multiplier
    )

    def __init__(self):
        # Ensure we have the prediction data
        if not hasattr(self.data, 'pred_return'):
            raise ValueError("Data feed must include 'pred_return' line with return predictions")
            
        # Store predictions for easier access
        self.predictions = self.data.pred_return
        
        # Volatility indicator for threshold adjustment
        if self.params.volatility_adjust:
            self.volatility = bt.indicators.StdDev(
                self.data.close,
                period=self.params.vol_period
            )
            self.volatility_ma = bt.indicators.SMA(
                self.volatility,
                period=self.params.vol_period
            )
        
        # Position management
        self.order = None
        self.entry_price = None
        self.entry_bar = None
        self.holding_bars = 0
        
        # Performance tracking
        self.prediction_accuracy = []
        self.trades_info = []

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.entry_bar = len(self)
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            elif order.issell():
                if self.entry_price:
                    # Record trade info
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    self.trades_info.append({
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'bars_held': len(self) - self.entry_bar if self.entry_bar else None,
                        'pred_return': self.predictions[-1]
                    })
                self.entry_price = None
                self.entry_bar = None
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
            
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def get_volatility_adjusted_threshold(self):
        """Adjust return threshold based on current volatility"""
        if not self.params.volatility_adjust:
            return self.params.return_threshold
            
        current_vol = self.volatility[0]
        avg_vol = self.volatility_ma[0]
        
        if current_vol > self.params.vol_threshold * avg_vol:
            # Increase threshold in high volatility
            return self.params.return_threshold * (current_vol / avg_vol)
        else:
            return self.params.return_threshold

    def evaluate_prediction(self):
        """Evaluate accuracy of previous prediction"""
        if len(self) < 2:
            return
            
        actual_return = (self.data.close[0] - self.data.close[-1]) / self.data.close[-1]
        pred_return = self.predictions[-1]
        
        # Calculate prediction error
        error = abs(actual_return - pred_return)
        self.prediction_accuracy.append(error)

    def next(self):
        # Update prediction accuracy
        self.evaluate_prediction()
        
        # Don't trade if we have pending orders
        if self.order:
            return

        # Check if we need to exit based on holding period
        if self.position and self.entry_bar is not None:
            bars_held = len(self) - self.entry_bar
            if bars_held >= self.params.holding_period:
                self.order = self.close()
                return
        
        # Get volatility-adjusted threshold
        current_threshold = self.get_volatility_adjusted_threshold()
        current_pred = self.predictions[0]
        
        if not self.position:  # No position - look for entry signals
            if current_pred > current_threshold:  # Predicted positive return
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]  # Main order
                else:
                    self.order = self.buy()
                    
            elif current_pred < -current_threshold:  # Predicted negative return
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 + self.params.stop_loss)
                    limit_price = entry_price * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]  # Main order
                else:
                    self.order = self.sell()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if len(self.prediction_accuracy) > 0:
            self.prediction_stats = {
                'mean_error': np.mean(self.prediction_accuracy),
                'std_error': np.std(self.prediction_accuracy),
                'max_error': max(self.prediction_accuracy),
                'min_error': min(self.prediction_accuracy)
            }
            
        if len(self.trades_info) > 0:
            returns = [trade['return'] for trade in self.trades_info]
            self.trade_stats = {
                'total_trades': len(self.trades_info),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'avg_bars_held': np.mean([t['bars_held'] for t in self.trades_info if t['bars_held'] is not None])
            }
            
        self.log(f'Strategy finished. Total trades: {len(self.trades_info)}')
        
        
        
        
        
        
        
        
        
        
        
import backtrader as bt
import numpy as np

class MLEnsembleStrategy(bt.Strategy):
    """
    Strategy that uses different ML models based on market regime/volatility.
    Expects predictions from multiple models and regime indicators.
    
    Parameters:
    - vol_period (default: 20): Period for volatility calculation
    - vol_threshold (default: 1.5): Threshold for high/low volatility regime
    - prob_threshold (default: 0.6): Probability threshold for classification models
    - return_threshold (default: 0.001): Return threshold for regression models
    - regime_threshold (default: 0.5): Threshold for regime switching
    - model_type (default: 'classification'): Type of model ('classification' or 'regression')
    """
    
    params = (
        ('vol_period', 20),
        ('vol_threshold', 1.5),
        ('prob_threshold', 0.6),
        ('return_threshold', 0.001),
        ('regime_threshold', 0.5),
        ('model_type', 'classification'),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        # Verify required data lines exist
        required_lines = ['pred_high_vol', 'pred_low_vol']
        for line in required_lines:
            if not hasattr(self.data, line):
                raise ValueError(f"Data feed must include '{line}' line")
        
        # Store model predictions
        self.high_vol_preds = self.data.pred_high_vol
        self.low_vol_preds = self.data.pred_low_vol
        
        # Volatility indicator for regime identification
        self.volatility = bt.indicators.StdDev(
            self.data.close,
            period=self.params.vol_period
        )
        self.volatility_ma = bt.indicators.SMA(
            self.volatility,
            period=self.params.vol_period
        )
        
        # Position management
        self.order = None
        self.entry_price = None
        
        # Performance tracking
        self.regime_changes = []
        self.model_accuracy = {
            'high_vol': [],
            'low_vol': []
        }
        self.trades_info = []
        self.current_regime = None

    def get_regime(self):
        """Determine current market regime based on volatility"""
        if len(self.volatility) < self.params.vol_period:
            return None
            
        current_vol = self.volatility[0]
        avg_vol = self.volatility_ma[0]
        
        new_regime = 'high_vol' if current_vol > self.params.vol_threshold * avg_vol else 'low_vol'
        
        if self.current_regime != new_regime:
            self.regime_changes.append({
                'bar': len(self),
                'old_regime': self.current_regime,
                'new_regime': new_regime,
                'volatility': current_vol,
                'avg_volatility': avg_vol
            })
            self.current_regime = new_regime
        
        return new_regime

    def get_signal_from_predictions(self, regime):
        """Get trading signal based on current regime and corresponding model"""
        if regime == 'high_vol':
            prediction = self.high_vol_preds[0]
        else:
            prediction = self.low_vol_preds[0]
            
        if self.params.model_type == 'classification':
            if prediction > self.params.prob_threshold:
                return 1  # Buy signal
            elif prediction < (1 - self.params.prob_threshold):
                return -1  # Sell signal
            return 0  # No signal
            
        else:  # regression
            if prediction > self.params.return_threshold:
                return 1
            elif prediction < -self.params.return_threshold:
                return -1
            return 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log(f'BUY EXECUTED - Regime: {self.current_regime}, Price: {order.executed.price:.2f}')
            elif order.issell():
                if self.entry_price:
                    # Record trade info
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    self.trades_info.append({
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'regime': self.current_regime
                    })
                self.entry_price = None
                self.log(f'SELL EXECUTED - Regime: {self.current_regime}, Price: {order.executed.price:.2f}')
            
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def evaluate_predictions(self):
        """Evaluate accuracy of previous predictions for each regime"""
        if len(self) < 2:
            return
            
        actual_return = (self.data.close[0] - self.data.close[-1]) / self.data.close[-1]
        
        # Evaluate high volatility model
        high_vol_pred = self.high_vol_preds[-1]
        high_vol_error = self.calculate_prediction_error(high_vol_pred, actual_return)
        self.model_accuracy['high_vol'].append(high_vol_error)
        
        # Evaluate low volatility model
        low_vol_pred = self.low_vol_preds[-1]
        low_vol_error = self.calculate_prediction_error(low_vol_pred, actual_return)
        self.model_accuracy['low_vol'].append(low_vol_error)

    def calculate_prediction_error(self, prediction, actual):
        """Calculate prediction error based on model type"""
        if self.params.model_type == 'classification':
            # Convert prediction to binary and compare with actual direction
            pred_direction = prediction > self.params.prob_threshold
            actual_direction = actual > 0
            return float(pred_direction == actual_direction)
        else:
            # For regression, calculate absolute error
            return abs(prediction - actual)

    def next(self):
        # Update prediction accuracy
        self.evaluate_predictions()
        
        # Don't trade if we have pending orders
        if self.order:
            return
            
        # Get current regime
        regime = self.get_regime()
        if not regime:
            return
            
        # Get trading signal for current regime
        signal = self.get_signal_from_predictions(regime)
        
        if not self.position:  # No position - look for entry signals
            if signal > 0:  # Buy signal
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.buy()
                    
            elif signal < 0:  # Sell signal
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 + self.params.stop_loss)
                    limit_price = entry_price * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.sell()
                    
        else:  # Have position - look for exit signals
            if signal == 0 or (self.position.size > 0 and signal < 0) or (self.position.size < 0 and signal > 0):
                self.order = self.close()

    def stop(self):
        """Calculate and log final strategy statistics."""
        regime_stats = {
            'total_regime_changes': len(self.regime_changes),
            'high_vol_accuracy': np.mean(self.model_accuracy['high_vol']) if self.model_accuracy['high_vol'] else 0,
            'low_vol_accuracy': np.mean(self.model_accuracy['low_vol']) if self.model_accuracy['low_vol'] else 0
        }
        
        if self.trades_info:
            trades_by_regime = {'high_vol': [], 'low_vol': []}
            for trade in self.trades_info:
                trades_by_regime[trade['regime']].append(trade['return'])
                
            for regime, returns in trades_by_regime.items():
                if returns:
                    regime_stats[f'{regime}_avg_return'] = np.mean(returns)
                    regime_stats[f'{regime}_win_rate'] = len([r for r in returns if r > 0]) / len(returns)
        
        self.log(f"Strategy finished - Regime changes: {regime_stats['total_regime_changes']}")
        self.regime_stats = regime_stats
        
        
        
        
        
        
        
import backtrader as bt
import numpy as np

class LSTMStrategy(bt.Strategy):
    """
    Trading strategy based on LSTM/RNN predictions.
    Expects predictions to be pre-calculated using a trained LSTM model.
    
    Parameters:
    - pred_threshold (default: 0.001): Minimum predicted return for trade entry
    - sequence_length (default: 10): Length of sequence used by LSTM
    - confidence_level (default: 0.0): Additional threshold for prediction confidence
    - stop_loss (default: None): Stop loss percentage
    - take_profit (default: None): Take profit percentage
    - trail_stop (default: False): Whether to use trailing stop
    - trail_percent (default: 0.02): Trailing stop percentage
    """
    
    params = (
        ('pred_threshold', 0.001),
        ('sequence_length', 10),
        ('confidence_level', 0.0),
        ('stop_loss', None),
        ('take_profit', None),
        ('trail_stop', False),
        ('trail_percent', 0.02)
    )

    def __init__(self):
        # Verify we have the LSTM predictions data
        if not hasattr(self.data, 'lstm_pred'):
            raise ValueError("Data feed must include 'lstm_pred' line with LSTM predictions")
            
        # LSTM predictions and optional confidence scores
        self.predictions = self.data.lstm_pred
        self.has_confidence = hasattr(self.data, 'pred_confidence')
        if self.has_confidence:
            self.confidence = self.data.pred_confidence
        
        # Additional indicators for confirmation
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.sequence_length)
        self.atr = bt.indicators.ATR(self.data, period=self.params.sequence_length)
        
        # Position management
        self.order = None
        self.stop_order = None
        self.profit_order = None
        self.trail_order = None
        self.entry_price = None
        
        # Performance tracking
        self.trades = []
        self.current_sequence = []

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
                
                if self.params.trail_stop:
                    self.trail_order = self.sell(exectype=bt.Order.StopTrail,
                                               trailpercent=self.params.trail_percent)
                    
            elif order.issell():
                if self.entry_price:
                    # Record trade
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    pred_return = self.predictions[-1]
                    self.trades.append({
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'predicted_return': pred_return,
                        'confidence': self.confidence[-1] if self.has_confidence else None
                    })
                self.entry_price = None
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                
            # Reset orders
            if order == self.order:
                self.order = None
            elif order == self.stop_order:
                self.stop_order = None
            elif order == self.profit_order:
                self.profit_order = None
            elif order == self.trail_order:
                self.trail_order = None
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            if order == self.order:
                self.order = None
            elif order == self.stop_order:
                self.stop_order = None
            elif order == self.profit_order:
                self.profit_order = None
            elif order == self.trail_order:
                self.trail_order = None

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def should_trade(self):
        """Determine if we should trade based on prediction and confidence"""
        if len(self.data) < self.params.sequence_length:
            return False
            
        # Get current prediction
        pred = self.predictions[0]
        
        # Check confidence if available
        if self.has_confidence:
            if self.confidence[0] < self.params.confidence_level:
                return False
                
        # Store prediction for sequence analysis
        self.current_sequence.append(pred)
        if len(self.current_sequence) > self.params.sequence_length:
            self.current_sequence.pop(0)
            
        # Check for consistent predictions
        if len(self.current_sequence) == self.params.sequence_length:
            pred_direction = np.sign(pred)
            sequence_consistency = np.mean([1 if np.sign(x) == pred_direction else 0 
                                         for x in self.current_sequence])
            if sequence_consistency < 0.7:  # At least 70% consistent
                return False
                
        return True

    def next(self):
        # Don't trade until we have enough data
        if not self.should_trade():
            return
            
        # Don't trade if we have pending orders
        if self.order:
            return
            
        current_pred = self.predictions[0]
        
        if not self.position:  # No position - look for entry signals
            if current_pred > self.params.pred_threshold:  # Predicted positive return
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.buy()
                    
            elif current_pred < -self.params.pred_threshold:  # Predicted negative return
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 + self.params.stop_loss)
                    limit_price = entry_price * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.sell()
                    
        else:  # Have position - look for exit signals
            # Exit if prediction changes direction
            if (self.position.size > 0 and current_pred < 0) or \
               (self.position.size < 0 and current_pred > 0):
                self.close()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.trades:
            returns = [t['return'] for t in self.trades]
            pred_returns = [t['predicted_return'] for t in self.trades]
            
            self.stats = {
                'total_trades': len(self.trades),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'prediction_accuracy': np.corrcoef(returns, pred_returns)[0, 1],
                'avg_pred_return': np.mean(pred_returns)
            }
            
            if self.has_confidence:
                confidences = [t['confidence'] for t in self.trades]
                self.stats['avg_confidence'] = np.mean(confidences)
                
            self.log(f"Strategy finished - Total trades: {self.stats['total_trades']}, "
                    f"Win rate: {self.stats['win_rate']:.2%}")
            
            
            
            
            
            
import backtrader as bt
import numpy as np
from enum import Enum

class PatternType(Enum):
    BULLISH = 1
    BEARISH = -1
    NEUTRAL = 0

class CNNPatternStrategy(bt.Strategy):
    """
    Trading strategy based on CNN pattern recognition predictions.
    Expects pre-calculated predictions classifying price patterns.
    
    Parameters:
    - confidence_threshold (default: 0.7): Minimum confidence for pattern signals
    - pattern_length (default: 20): Length of pattern window
    - stop_loss (default: None): Stop loss percentage
    - take_profit (default: None): Take profit percentage
    - confirmation_bars (default: 2): Bars needed to confirm pattern
    """
    
    params = (
        ('confidence_threshold', 0.7),
        ('pattern_length', 20),
        ('stop_loss', None),
        ('take_profit', None),
        ('confirmation_bars', 2),
        ('reset_pattern', True),  # Reset after pattern completion
    )

    def __init__(self):
        # Verify we have the CNN predictions
        required_lines = ['pattern_class', 'pattern_confidence']
        for line in required_lines:
            if not hasattr(self.data, line):
                raise ValueError(f"Data feed must include '{line}' line")
        
        # Store predictions
        self.pattern_class = self.data.pattern_class
        self.pattern_confidence = self.data.pattern_confidence
        
        # Additional indicators for confirmation
        self.volume = bt.indicators.SMA(self.data.volume, period=self.params.pattern_length)
        self.atr = bt.indicators.ATR(self.data, period=self.params.pattern_length)
        
        # Pattern tracking
        self.current_pattern = None
        self.pattern_start_price = None
        self.confirmation_count = 0
        
        # Position management
        self.order = None
        self.entry_price = None
        
        # Performance tracking
        self.pattern_trades = []
        self.active_patterns = []

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log(f'BUY EXECUTED - Pattern: {self.current_pattern}, Price: {order.executed.price:.2f}')
            elif order.issell():
                if self.entry_price:
                    # Record pattern trade
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    self.pattern_trades.append({
                        'pattern': self.current_pattern,
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'confidence': self.pattern_confidence[-1],
                        'pattern_duration': len(self.active_patterns[-1]['prices']) if self.active_patterns else None
                    })
                self.entry_price = None
                if self.params.reset_pattern:
                    self.current_pattern = None
                self.log(f'SELL EXECUTED - Pattern: {self.current_pattern}, Price: {order.executed.price:.2f}')
            
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def get_pattern_type(self):
        """Convert numerical pattern class to PatternType"""
        pattern_class = int(self.pattern_class[0])
        try:
            return PatternType(pattern_class)
        except ValueError:
            return PatternType.NEUTRAL

    def track_pattern(self):
        """Track and validate current pattern formation"""
        if self.current_pattern is None:
            return False
            
        # Store price data for current pattern
        if self.active_patterns:
            self.active_patterns[-1]['prices'].append(self.data.close[0])
            
        # Check if pattern is still valid
        if len(self.active_patterns) > 0:
            pattern_prices = self.active_patterns[-1]['prices']
            if len(pattern_prices) >= self.params.pattern_length:
                # Validate pattern characteristics
                price_range = max(pattern_prices) - min(pattern_prices)
                if price_range < self.atr[0]:  # Pattern not significant enough
                    self.current_pattern = None
                    self.active_patterns.pop()
                    return False
                    
        return True

    def next(self):
        # Don't trade until we have enough data
        if len(self.data) < self.params.pattern_length:
            return
            
        # Don't trade if we have pending orders
        if self.order:
            return
            
        # Get current pattern and confidence
        pattern_type = self.get_pattern_type()
        confidence = self.pattern_confidence[0]
        
        # Update pattern tracking
        if pattern_type != self.current_pattern:
            if confidence >= self.params.confidence_threshold:
                self.current_pattern = pattern_type
                self.pattern_start_price = self.data.close[0]
                self.confirmation_count = 1
                self.active_patterns.append({
                    'type': pattern_type,
                    'start_price': self.data.close[0],
                    'prices': [self.data.close[0]]
                })
            else:
                self.current_pattern = None
        elif self.current_pattern:
            self.confirmation_count += 1
            if not self.track_pattern():
                return

        # Trading logic
        if not self.position:  # No position - look for entry signals
            if self.confirmation_count >= self.params.confirmation_bars:
                if pattern_type == PatternType.BULLISH and confidence >= self.params.confidence_threshold:
                    entry_price = self.data.close[0]
                    
                    if self.params.stop_loss and self.params.take_profit:
                        stop_price = entry_price * (1.0 - self.params.stop_loss)
                        limit_price = entry_price * (1.0 + self.params.take_profit)
                        
                        self.order = self.buy_bracket(
                            size=None,
                            price=entry_price,
                            stopprice=stop_price,
                            limitprice=limit_price,
                        )[0]
                    else:
                        self.order = self.buy()
                        
                elif pattern_type == PatternType.BEARISH and confidence >= self.params.confidence_threshold:
                    entry_price = self.data.close[0]
                    
                    if self.params.stop_loss and self.params.take_profit:
                        stop_price = entry_price * (1.0 + self.params.stop_loss)
                        limit_price = entry_price * (1.0 - self.params.take_profit)
                        
                        self.order = self.sell_bracket(
                            size=None,
                            price=entry_price,
                            stopprice=stop_price,
                            limitprice=limit_price,
                        )[0]
                    else:
                        self.order = self.sell()
                        
        else:  # Have position - look for exit signals
            if ((self.position.size > 0 and pattern_type == PatternType.BEARISH) or 
                (self.position.size < 0 and pattern_type == PatternType.BULLISH)) and \
               confidence >= self.params.confidence_threshold:
                self.order = self.close()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.pattern_trades:
            patterns = [t['pattern'] for t in self.pattern_trades]
            returns = [t['return'] for t in self.pattern_trades]
            confidences = [t['confidence'] for t in self.pattern_trades]
            durations = [t['pattern_duration'] for t in self.pattern_trades if t['pattern_duration']]
            
            self.stats = {
                'total_trades': len(self.pattern_trades),
                'patterns_identified': len(self.active_patterns),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'avg_confidence': np.mean(confidences),
                'avg_pattern_duration': np.mean(durations) if durations else 0,
                'pattern_stats': {
                    PatternType.BULLISH: {
                        'count': sum(1 for p in patterns if p == PatternType.BULLISH),
                        'accuracy': np.mean([r > 0 for p, r in zip(patterns, returns) 
                                          if p == PatternType.BULLISH])
                    },
                    PatternType.BEARISH: {
                        'count': sum(1 for p in patterns if p == PatternType.BEARISH),
                        'accuracy': np.mean([r > 0 for p, r in zip(patterns, returns) 
                                          if p == PatternType.BEARISH])
                    }
                }
            }
            
            self.log(f"Strategy finished - Total patterns: {self.stats['patterns_identified']}, "
                    f"Trades: {self.stats['total_trades']}, "
                    f"Win rate: {self.stats['win_rate']:.2%}")
            
            
            
            
            
            
import backtrader as bt
import numpy as np

class AutoencoderStrategy(bt.Strategy):
    """
    Trading strategy using compressed features from an autoencoder
    combined with predictions from a simple model.
    
    Parameters:
    - n_features (default: 5): Number of compressed features
    - pred_threshold (default: 0.6): Prediction threshold for signals
    - lookback (default: 20): Lookback period for feature stability
    - stop_loss (default: None): Stop loss percentage
    - take_profit (default: None): Take profit percentage
    - feature_stability (default: True): Check feature stability before trading
    """
    
    params = (
        ('n_features', 5),
        ('pred_threshold', 0.6),
        ('lookback', 20),
        ('stop_loss', None),
        ('take_profit', None),
        ('feature_stability', True),
        ('stability_threshold', 0.1)
    )

    def __init__(self):
        # Verify we have the required data
        required_prefix = 'encoded_feature_'
        self.feature_lines = [
            line for line in self.data.lines.getlinealias()
            if line.startswith(required_prefix)
        ]
        
        if len(self.feature_lines) != self.params.n_features:
            raise ValueError(f"Expected {self.params.n_features} encoded features, "
                           f"got {len(self.feature_lines)}")
            
        if not hasattr(self.data, 'model_prediction'):
            raise ValueError("Data feed must include 'model_prediction' line")
        
        # Store features and predictions
        self.features = [getattr(self.data, line) for line in self.feature_lines]
        self.predictions = self.data.model_prediction
        
        # Feature stability tracking
        self.feature_history = []
        
        # Position management
        self.order = None
        self.entry_price = None
        
        # Performance tracking
        self.trades = []
        self.feature_stats = []

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            elif order.issell():
                if self.entry_price:
                    # Record trade
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    current_features = [feature[0] for feature in self.features]
                    self.trades.append({
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'features': current_features,
                        'prediction': self.predictions[-1]
                    })
                self.entry_price = None
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
            
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def check_feature_stability(self):
        """Check if encoded features are stable enough for trading"""
        if len(self.data) < self.params.lookback:
            return False
            
        # Get current feature values
        current_features = [feature[0] for feature in self.features]
        self.feature_history.append(current_features)
        
        if len(self.feature_history) > self.params.lookback:
            self.feature_history.pop(0)
            
        # Calculate feature stability
        feature_changes = []
        for i in range(len(self.features)):
            feature_series = [f[i] for f in self.feature_history]
            stability = np.std(feature_series) / (np.mean(feature_series) + 1e-8)
            feature_changes.append(stability)
            
        # Record feature statistics
        self.feature_stats.append({
            'time': len(self),
            'stabilities': feature_changes,
            'mean_stability': np.mean(feature_changes)
        })
        
        return np.mean(feature_changes) < self.params.stability_threshold

    def next(self):
        # Don't trade until we have enough data
        if len(self.data) < self.params.lookback:
            return
            
        # Don't trade if we have pending orders
        if self.order:
            return
            
        # Check feature stability if enabled
        if self.params.feature_stability and not self.check_feature_stability():
            return
            
        current_pred = self.predictions[0]
        
        if not self.position:  # No position - look for entry signals
            if current_pred > self.params.pred_threshold:  # Strong buy signal
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 - self.params.stop_loss)
                    limit_price = entry_price * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.buy()
                    
            elif current_pred < (1 - self.params.pred_threshold):  # Strong sell signal
                entry_price = self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = entry_price * (1.0 + self.params.stop_loss)
                    limit_price = entry_price * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=None,
                        price=entry_price,
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.sell()
                    
        else:  # Have position - look for exit signals
            # Exit if prediction changes direction significantly
            if (self.position.size > 0 and current_pred < (1 - self.params.pred_threshold)) or \
               (self.position.size < 0 and current_pred > self.params.pred_threshold):
                self.order = self.close()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.trades:
            returns = [t['return'] for t in self.trades]
            predictions = [t['prediction'] for t in self.trades]
            
            # Calculate feature importance
            feature_importance = np.zeros(self.params.n_features)
            for trade in self.trades:
                if trade['return'] > 0:
                    feature_importance += np.abs(trade['features'])
            feature_importance /= len(self.trades)
            
            self.stats = {
                'total_trades': len(self.trades),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'prediction_correlation': np.corrcoef(returns, predictions)[0, 1],
                'feature_importance': feature_importance.tolist(),
                'avg_feature_stability': np.mean([s['mean_stability'] for s in self.feature_stats])
            }
            
            self.log(f"Strategy finished - Total trades: {self.stats['total_trades']}, "
                    f"Win rate: {self.stats['win_rate']:.2%}")
            
            
            
            
            
            
            
import backtrader as bt
import numpy as np
from enum import Enum

class RLAction(Enum):
    """RL Agent actions"""
    HOLD = 0
    BUY = 1
    SELL = 2

class RLAgentStrategy(bt.Strategy):
    """
    Trading strategy that follows pre-trained RL agent signals.
    
    Parameters:
    - confidence_threshold (default: 0.6): Minimum confidence for action execution
    - state_lookback (default: 10): Lookback period for state consistency
    - stop_loss (default: None): Stop loss percentage
    - take_profit (default: None): Take profit percentage
    - position_size_pct (default: 1.0): Position size as percentage of portfolio
    """
    
    params = (
        ('confidence_threshold', 0.6),
        ('state_lookback', 10),
        ('stop_loss', None),
        ('take_profit', None),
        ('position_size_pct', 1.0),
        ('max_positions', 1)
    )

    def __init__(self):
        # Verify we have the required data
        required_lines = ['rl_action', 'action_prob']
        for line in required_lines:
            if not hasattr(self.data, line):
                raise ValueError(f"Data feed must include '{line}' line")
        
        # Store RL signals
        self.actions = self.data.rl_action
        self.probabilities = self.data.action_prob
        
        # Track positions and orders
        self.orders = {}
        self.positions = []
        self.current_action = None
        
        # State tracking
        self.state_history = []
        
        # Performance tracking
        self.action_history = []
        self.trades = []

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: {order.executed.price:.2f}')
                self.positions.append({
                    'entry_price': order.executed.price,
                    'entry_action': self.current_action,
                    'entry_prob': self.probabilities[0],
                    'size': order.executed.size
                })
            elif order.issell():
                self.log(f'SELL EXECUTED: {order.executed.price:.2f}')
                if self.positions:
                    pos = self.positions.pop()
                    returns = (order.executed.price - pos['entry_price']) / pos['entry_price']
                    self.trades.append({
                        'entry_price': pos['entry_price'],
                        'exit_price': order.executed.price,
                        'return': returns,
                        'entry_action': pos['entry_action'],
                        'exit_action': self.current_action,
                        'entry_prob': pos['entry_prob'],
                        'exit_prob': self.probabilities[0],
                        'bars_held': len(self.action_history)
                    })
                    self.action_history = []
            
            if order.ref in self.orders:
                del self.orders[order.ref]
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order {order.ref} failed: {order.status}')
            if order.ref in self.orders:
                del self.orders[order.ref]

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def get_state_consistency(self):
        """Check if recent states have been consistent"""
        if len(self.state_history) < self.params.state_lookback:
            return False
            
        recent_actions = self.state_history[-self.params.state_lookback:]
        most_common = max(set(recent_actions), key=recent_actions.count)
        consistency = recent_actions.count(most_common) / len(recent_actions)
        
        return consistency >= 0.7  # At least 70% consistent

    def next(self):
        # Store current action
        current_action = RLAction(int(self.actions[0]))
        self.current_action = current_action
        current_prob = self.probabilities[0]
        
        # Update state history
        self.state_history.append(current_action)
        if len(self.state_history) > self.params.state_lookback:
            self.state_history.pop(0)
        
        # Don't trade if probabilities are too low
        if current_prob < self.params.confidence_threshold:
            return
            
        # Don't trade if state hasn't been consistent
        if not self.get_state_consistency():
            return
            
        # Update action history for position tracking
        if self.position:
            self.action_history.append(current_action)
        
        # Position sizing
        cash = self.broker.getcash()
        value = self.broker.getvalue()
        position_value = value * self.params.position_size_pct
        
        if not self.position:  # No position - look for entry signals
            if current_action == RLAction.BUY and len(self.positions) < self.params.max_positions:
                size = position_value / self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = self.data.close[0] * (1.0 - self.params.stop_loss)
                    limit_price = self.data.close[0] * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=size,
                        price=self.data.close[0],
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    for order in orders:
                        self.orders[order.ref] = order
                else:
                    order = self.buy(size=size)
                    self.orders[order.ref] = order
                    
            elif current_action == RLAction.SELL and len(self.positions) < self.params.max_positions:
                size = position_value / self.data.close[0]
                
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = self.data.close[0] * (1.0 + self.params.stop_loss)
                    limit_price = self.data.close[0] * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=size,
                        price=self.data.close[0],
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    for order in orders:
                        self.orders[order.ref] = order
                else:
                    order = self.sell(size=size)
                    self.orders[order.ref] = order
                    
        else:  # Have position - look for exit signals
            if current_action == RLAction.HOLD:
                return
                
            if (self.position.size > 0 and current_action == RLAction.SELL) or \
               (self.position.size < 0 and current_action == RLAction.BUY):
                order = self.close()
                if order:
                    self.orders[order.ref] = order

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.trades:
            returns = [t['return'] for t in self.trades]
            probs = [t['entry_prob'] for t in self.trades]
            durations = [t['bars_held'] for t in self.trades]
            
            self.stats = {
                'total_trades': len(self.trades),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'avg_trade_bars': np.mean(durations),
                'avg_confidence': np.mean(probs),
                'sharpe_ratio': np.mean(returns) / np.std(returns) if len(returns) > 1 else 0,
                'max_drawdown': np.min(np.minimum.accumulate(np.array(returns)))
            }
            
            # Action-specific statistics
            for action in RLAction:
                action_trades = [t for t in self.trades if t['entry_action'] == action]
                if action_trades:
                    action_returns = [t['return'] for t in action_trades]
                    self.stats[f'{action.name}_trades'] = len(action_trades)
                    self.stats[f'{action.name}_win_rate'] = len([r for r in action_returns if r > 0]) / len(action_trades)
                    self.stats[f'{action.name}_avg_return'] = np.mean(action_returns)
            
            self.log(f"Strategy finished - Total trades: {self.stats['total_trades']}, "
                    f"Win rate: {self.stats['win_rate']:.2%}")
            
            
            
            
            
            
            
            
import backtrader as bt
import numpy as np
from enum import Enum

class MarketRegime(Enum):
    TRENDING = 0
    MEAN_REVERTING = 1
    HIGH_VOL = 2
    LOW_VOL = 3

class RLAction(Enum):
    HOLD = 0
    BUY = 1
    SELL = 2

class RegimeSwitchingRLStrategy(bt.Strategy):
    """
    Trading strategy that switches between different RL policies based on
    identified market regimes.
    
    Parameters:
    - confidence_threshold (default: 0.6): Minimum confidence for action execution
    - regime_period (default: 20): Period for regime identification
    - vol_threshold (default: 1.5): Volatility threshold for regime change
    - trend_threshold (default: 0.6): Threshold for trend identification
    - regime_change_delay (default: 3): Bars to wait after regime change
    """
    
    params = (
        ('confidence_threshold', 0.6),
        ('regime_period', 20),
        ('vol_threshold', 1.5),
        ('trend_threshold', 0.6),
        ('regime_change_delay', 3),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        # Verify we have regime and action data
        required_prefixes = ['regime_', 'action_']
        for regime in MarketRegime:
            action_line = f'action_{regime.name.lower()}'
            prob_line = f'prob_{regime.name.lower()}'
            if not hasattr(self.data, action_line) or not hasattr(self.data, prob_line):
                raise ValueError(f"Missing required lines: {action_line} and/or {prob_line}")

        # Market regime indicators
        self.volatility = bt.indicators.StdDev(self.data.close, period=self.params.regime_period)
        self.trend = bt.indicators.DirectionalMovement(self.data, period=self.params.regime_period)
        
        # Track current regime and delay counter
        self.current_regime = None
        self.regime_change_count = 0
        self.last_regime_change = 0
        
        # Position management
        self.order = None
        self.entry_price = None
        
        # Performance tracking
        self.regime_changes = []
        self.trades = []
        self.regime_performance = {regime: [] for regime in MarketRegime}

    def identify_regime(self):
        """Identify current market regime based on indicators"""
        if len(self.data) < self.params.regime_period:
            return None
            
        vol_ratio = self.volatility[0] / bt.indicators.SMA(self.volatility, period=self.params.regime_period)[0]
        trend_strength = abs(self.trend.plus[0] - self.trend.minus[0]) / (self.trend.plus[0] + self.trend.minus[0])
        
        if vol_ratio > self.params.vol_threshold:
            return MarketRegime.HIGH_VOL
        elif vol_ratio < 1/self.params.vol_threshold:
            return MarketRegime.LOW_VOL
        elif trend_strength > self.params.trend_threshold:
            return MarketRegime.TRENDING
        else:
            return MarketRegime.MEAN_REVERTING

    def get_regime_action(self, regime):
        """Get action and probability for current regime"""
        action_value = getattr(self.data, f'action_{regime.name.lower()}')[0]
        prob_value = getattr(self.data, f'prob_{regime.name.lower()}')[0]
        
        return RLAction(int(action_value)), prob_value

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log(f'BUY EXECUTED - Regime: {self.current_regime.name}, Price: {order.executed.price:.2f}')
            elif order.issell():
                if self.entry_price:
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    self.trades.append({
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'regime': self.current_regime,
                        'bars_held': len(self) - self.last_regime_change
                    })
                    self.regime_performance[self.current_regime].append(returns)
                self.entry_price = None
                self.log(f'SELL EXECUTED - Regime: {self.current_regime.name}, Price: {order.executed.price:.2f}')
            
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        # Identify current regime
        new_regime = self.identify_regime()
        if not new_regime:
            return
            
        # Handle regime changes
        if new_regime != self.current_regime:
            self.regime_changes.append({
                'bar': len(self),
                'old_regime': self.current_regime,
                'new_regime': new_regime,
                'price': self.data.close[0]
            })
            self.current_regime = new_regime
            self.last_regime_change = len(self)
            self.regime_change_count = 0
            return  # Skip trading on regime change day
            
        self.regime_change_count += 1
        
        # Don't trade until regime change delay is over
        if self.regime_change_count < self.params.regime_change_delay:
            return
            
        # Don't trade if we have pending orders
        if self.order:
            return
            
        # Get action for current regime
        action, probability = self.get_regime_action(self.current_regime)
        
        # Don't trade if probability is too low
        if probability < self.params.confidence_threshold:
            return
            
        if not self.position:  # No position - look for entry signals
            if action == RLAction.BUY:
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = self.data.close[0] * (1.0 - self.params.stop_loss)
                    limit_price = self.data.close[0] * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=None,
                        price=self.data.close[0],
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.buy()
                    
            elif action == RLAction.SELL:
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = self.data.close[0] * (1.0 + self.params.stop_loss)
                    limit_price = self.data.close[0] * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=None,
                        price=self.data.close[0],
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.sell()
                    
        else:  # Have position - look for exit signals
            if ((self.position.size > 0 and action == RLAction.SELL) or 
                (self.position.size < 0 and action == RLAction.BUY)):
                self.order = self.close()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.trades:
            # Overall statistics
            returns = [t['return'] for t in self.trades]
            self.stats = {
                'total_trades': len(self.trades),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'regime_changes': len(self.regime_changes)
            }
            
            # Regime-specific statistics
            for regime in MarketRegime:
                regime_returns = self.regime_performance[regime]
                if regime_returns:
                    self.stats[f'{regime.name}_trades'] = len(regime_returns)
                    self.stats[f'{regime.name}_return'] = np.mean(regime_returns)
                    self.stats[f'{regime.name}_win_rate'] = (
                        len([r for r in regime_returns if r > 0]) / len(regime_returns)
                    )
            
            self.log(f"Strategy finished - Total trades: {self.stats['total_trades']}, "
                    f"Regime changes: {self.stats['regime_changes']}")
            
            # Log regime-specific performance
            for regime in MarketRegime:
                if regime in self.stats:
                    self.log(f"{regime.name}: {self.stats[f'{regime.name}_trades']} trades, "
                            f"Win rate: {self.stats[f'{regime.name}_win_rate']:.2%}")
    
    
    
    
    
import backtrader as bt
import numpy as np

class BetaHedgedStrategy(bt.Strategy):
    """
    CAPM Beta-Hedged Strategy that trades based on alpha and hedges market exposure.
    Requires both stock and market data feeds.
    
    Parameters:
    - beta_period (default: 60): Lookback period for beta calculation
    - alpha_threshold (default: 0.001): Minimum alpha for trade entry
    - hedge_adjustment (default: 0.01): Minimum change in beta to adjust hedge
    - risk_free_rate (default: 0.0): Annual risk-free rate
    """
    
    params = (
        ('beta_period', 60),
        ('alpha_threshold', 0.001),
        ('hedge_adjustment', 0.01),
        ('risk_free_rate', 0.0),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        # Ensure we have market data
        self.market = self.datas[1]  # Market data should be second data feed
        
        # Calculate returns for both stock and market
        self.stock_returns = bt.indicators.PercentChange(self.data.close, period=1)
        self.market_returns = bt.indicators.PercentChange(self.market.close, period=1)
        
        # Daily risk-free rate
        self.daily_rf = (1 + self.params.risk_free_rate) ** (1/252) - 1
        
        # Track beta and positions
        self.current_beta = None
        self.hedge_ratio = None
        self.stock_position = None
        self.hedge_position = None
        
        # Performance tracking
        self.trades = []
        self.betas = []
        self.alphas = []

    def calculate_beta(self):
        """Calculate beta using rolling window"""
        if len(self.data) < self.params.beta_period:
            return None
            
        # Get return series
        stock_rets = np.array(self.stock_returns.get(size=self.params.beta_period))
        market_rets = np.array(self.market_returns.get(size=self.params.beta_period))
        
        # Calculate beta
        covar = np.cov(stock_rets, market_rets)[0][1]
        market_var = np.var(market_rets)
        
        if market_var != 0:
            return covar / market_var
        return None

    def calculate_alpha(self):
        """Calculate alpha using CAPM"""
        if self.current_beta is None:
            return None
            
        # Get most recent returns
        stock_ret = self.stock_returns[0]
        market_ret = self.market_returns[0]
        
        # Calculate expected return using CAPM
        expected_ret = self.daily_rf + self.current_beta * (market_ret - self.daily_rf)
        
        # Alpha is actual minus expected return
        return stock_ret - expected_ret

    def adjust_hedge(self):
        """Adjust market hedge position based on current beta"""
        if self.stock_position and self.current_beta:
            target_hedge = -self.current_beta * abs(self.stock_position.size)
            
            if self.hedge_position:
                current_hedge = self.hedge_position.size
                hedge_diff = target_hedge - current_hedge
                
                # Only adjust if change is significant
                if abs(hedge_diff) > self.params.hedge_adjustment * abs(current_hedge):
                    self.order_target_size(data=self.market, target=target_hedge)
            else:
                self.order_target_size(data=self.market, target=target_hedge)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.data == self.data:  # Stock order
                if order.isbuy():
                    self.stock_position = self.getposition(self.data)
                    self.log(f'STOCK BUY EXECUTED, Price: {order.executed.price:.2f}, Beta: {self.current_beta:.2f}')
                else:
                    self.log(f'STOCK SELL EXECUTED, Price: {order.executed.price:.2f}')
                    if self.stock_position:
                        # Record trade
                        self.trades.append({
                            'entry_price': self.stock_position.price,
                            'exit_price': order.executed.price,
                            'return': (order.executed.price/self.stock_position.price) - 1,
                            'beta': self.current_beta,
                            'alpha': self.alphas[-1] if self.alphas else None
                        })
                    self.stock_position = None
                    
            else:  # Market hedge order
                self.hedge_position = self.getposition(self.market)
                side = "BUY" if order.isbuy() else "SELL"
                self.log(f'HEDGE {side} EXECUTED, Price: {order.executed.price:.2f}')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        # Update beta
        new_beta = self.calculate_beta()
        if new_beta is not None:
            self.current_beta = new_beta
            self.betas.append(new_beta)
            
            # Calculate alpha
            current_alpha = self.calculate_alpha()
            self.alphas.append(current_alpha)
            
            # Adjust hedge if necessary
            self.adjust_hedge()
        else:
            return
            
        # Don't trade without alpha
        if not self.alphas:
            return
            
        current_alpha = self.alphas[-1]
        
        if not self.stock_position:  # No position - look for entry signals
            if abs(current_alpha) > self.params.alpha_threshold:
                # Long stock if positive alpha
                if current_alpha > self.params.alpha_threshold:
                    price = self.data.close[0]
                    if self.params.stop_loss and self.params.take_profit:
                        stop_price = price * (1.0 - self.params.stop_loss)
                        limit_price = price * (1.0 + self.params.take_profit)
                        
                        orders = self.buy_bracket(
                            data=self.data,
                            size=None,
                            price=price,
                            stopprice=stop_price,
                            limitprice=limit_price,
                        )
                    else:
                        self.buy(data=self.data)
                        
                # Short stock if negative alpha
                elif current_alpha < -self.params.alpha_threshold:
                    price = self.data.close[0]
                    if self.params.stop_loss and self.params.take_profit:
                        stop_price = price * (1.0 + self.params.stop_loss)
                        limit_price = price * (1.0 - self.params.take_profit)
                        
                        orders = self.sell_bracket(
                            data=self.data,
                            size=None,
                            price=price,
                            stopprice=stop_price,
                            limitprice=limit_price,
                        )
                    else:
                        self.sell(data=self.data)
                        
        else:  # Have position - look for exit signals
            # Exit if alpha crosses zero or becomes insignificant
            if ((self.stock_position.size > 0 and current_alpha < 0) or
                (self.stock_position.size < 0 and current_alpha > 0) or
                abs(current_alpha) < self.params.alpha_threshold/2):
                self.close(data=self.data)
                self.close(data=self.market)  # Close hedge position

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.trades:
            returns = [t['return'] for t in self.trades]
            betas = [t['beta'] for t in self.trades]
            alphas = [t['alpha'] for t in self.trades]
            
            self.stats = {
                'total_trades': len(self.trades),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'avg_beta': np.mean(betas),
                'avg_alpha': np.mean(alphas),
                'avg_abs_alpha': np.mean([abs(a) for a in alphas]),
                'sharpe_ratio': np.mean(returns) / np.std(returns) if len(returns) > 1 else 0
            }
            
            self.log(f"Strategy finished - Total trades: {self.stats['total_trades']}, "
                    f"Average Beta: {self.stats['avg_beta']:.2f}, "
                    f"Win rate: {self.stats['win_rate']:.2%}")
            
            
            
            
            
            
            
import backtrader as bt
import numpy as np
from datetime import datetime, timedelta

class PaycheckSeasonalityStrategy(bt.Strategy):
    """
    Trading strategy based on seasonality patterns around typical paycheck dates.
    Analyzes historical returns during paycheck periods and trades accordingly.
    
    Parameters:
    - window_size (default: 3): Days around paycheck date to consider
    - month_start_window (default: True): Trade around month start (1st-3rd)
    - month_mid_window (default: True): Trade around month middle (14th-16th)
    - min_history (default: 60): Minimum days of history before trading
    - seasonality_threshold (default: 1.0): Z-score threshold for seasonal effect
    """
    
    params = (
        ('window_size', 3),
        ('month_start_window', True),
        ('month_mid_window', True),
        ('min_history', 60),
        ('seasonality_threshold', 1.0),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        # Track historical returns for each window
        self.window_returns = {
            'month_start': [],
            'month_mid': []
        }
        
        # Track current window status
        self.current_window = None
        self.window_start_date = None
        self.days_in_window = 0
        
        # Position management
        self.order = None
        self.entry_price = None
        
        # Performance tracking
        self.trades = []
        self.seasonal_scores = []

    def is_paycheck_window(self, current_date):
        """Determine if current date is in a paycheck window"""
        day = current_date.day
        
        if self.params.month_start_window and 1 <= day <= 3:
            return 'month_start'
        elif self.params.month_mid_window and 14 <= day <= 16:
            return 'month_mid'
        return None

    def calculate_historical_pattern(self, window_type):
        """Calculate historical seasonal pattern strength"""
        if len(self.window_returns[window_type]) < self.params.min_history:
            return None
            
        returns = self.window_returns[window_type]
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0
            
        z_score = mean_return / std_return
        return z_score

    def update_window_returns(self):
        """Update historical returns for seasonal windows"""
        if len(self.data) < 2:  # Need at least 2 days for returns
            return
            
        current_date = self.data.datetime.datetime(0)
        current_return = (self.data.close[0] / self.data.close[-1]) - 1
        
        window_type = self.is_paycheck_window(current_date)
        if window_type:
            self.window_returns[window_type].append(current_return)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log(f'BUY EXECUTED - Window: {self.current_window}, Price: {order.executed.price:.2f}')
            elif order.issell():
                if self.entry_price:
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    self.trades.append({
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'window_type': self.current_window,
                        'days_held': self.days_in_window
                    })
                self.entry_price = None
                self.log(f'SELL EXECUTED - Window: {self.current_window}, Price: {order.executed.price:.2f}')
            
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        # Update historical returns
        self.update_window_returns()
        
        # Don't trade if we have pending orders
        if self.order:
            return
            
        current_date = self.data.datetime.datetime(0)
        window_type = self.is_paycheck_window(current_date)
        
        # Update window tracking
        if window_type != self.current_window:
            if window_type:  # Entering new window
                self.current_window = window_type
                self.window_start_date = current_date
                self.days_in_window = 1
                
                # Calculate seasonal pattern strength
                z_score = self.calculate_historical_pattern(window_type)
                if z_score is not None:
                    self.seasonal_scores.append({
                        'date': current_date,
                        'window': window_type,
                        'z_score': z_score
                    })
            else:  # Exiting window
                self.current_window = None
                self.window_start_date = None
                self.days_in_window = 0
        else:
            if self.days_in_window is not None:
                self.days_in_window += 1
        
        if not self.position:  # No position - look for entry signals
            if window_type and len(self.window_returns[window_type]) >= self.params.min_history:
                z_score = self.calculate_historical_pattern(window_type)
                
                if z_score is not None and abs(z_score) > self.params.seasonality_threshold:
                    # Trade in direction of seasonal pattern
                    if z_score > 0:  # Historically positive returns
                        if self.params.stop_loss and self.params.take_profit:
                            stop_price = self.data.close[0] * (1.0 - self.params.stop_loss)
                            limit_price = self.data.close[0] * (1.0 + self.params.take_profit)
                            
                            orders = self.buy_bracket(
                                size=None,
                                price=self.data.close[0],
                                stopprice=stop_price,
                                limitprice=limit_price,
                            )
                            self.order = orders[0]
                        else:
                            self.order = self.buy()
                            
                    else:  # Historically negative returns
                        if self.params.stop_loss and self.params.take_profit:
                            stop_price = self.data.close[0] * (1.0 + self.params.stop_loss)
                            limit_price = self.data.close[0] * (1.0 - self.params.take_profit)
                            
                            orders = self.sell_bracket(
                                size=None,
                                price=self.data.close[0],
                                stopprice=stop_price,
                                limitprice=limit_price,
                            )
                            self.order = orders[0]
                        else:
                            self.order = self.sell()
                            
        else:  # Have position - look for exit signals
            if not window_type or self.days_in_window >= self.params.window_size:
                self.order = self.close()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.trades:
            # Overall statistics
            returns = [t['return'] for t in self.trades]
            
            self.stats = {
                'total_trades': len(self.trades),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'avg_days_held': np.mean([t['days_held'] for t in self.trades])
            }
            
            # Window-specific statistics
            for window in ['month_start', 'month_mid']:
                window_trades = [t for t in self.trades if t['window_type'] == window]
                if window_trades:
                    window_returns = [t['return'] for t in window_trades]
                    self.stats[f'{window}_trades'] = len(window_trades)
                    self.stats[f'{window}_return'] = np.mean(window_returns)
                    self.stats[f'{window}_win_rate'] = (
                        len([r for r in window_returns if r > 0]) / len(window_trades)
                    )
            
            self.log(f"Strategy finished - Total trades: {self.stats['total_trades']}, "
                    f"Win rate: {self.stats['win_rate']:.2%}")
            
            # Log window-specific performance
            for window in ['month_start', 'month_mid']:
                if f'{window}_trades' in self.stats:
                    self.log(f"{window}: {self.stats[f'{window}_trades']} trades, "
                            f"Win rate: {self.stats[f'{window}_win_rate']:.2%}")
                    
                    
                    
                    
                    
                    
import backtrader as bt
import numpy as np
from collections import defaultdict

class VWAPIndicator(bt.Indicator):
    """Custom VWAP indicator with optional anchoring"""
    
    lines = ('vwap',)
    params = (('period', 1),)
    
    def __init__(self):
        self.cumvol = bt.indicators.SumN(self.data.volume, period=self.p.period)
        self.cumtyp = bt.indicators.SumN(
            self.data.close * self.data.volume, 
            period=self.p.period
        )
        
        self.lines.vwap = self.cumtyp / self.cumvol

class VolumeProfileVWAPStrategy(bt.Strategy):
    """
    Trading strategy based on VWAP deviations and volume profile support/resistance.
    
    Parameters:
    - vwap_dev_threshold (default: 0.01): VWAP deviation threshold for signals
    - volume_profile_period (default: 20): Period for volume profile calculation
    - num_profile_bins (default: 10): Number of price bins for volume profile
    - min_volume_node (default: 0.1): Minimum relative volume for significant node
    """
    
    params = (
        ('vwap_dev_threshold', 0.01),
        ('volume_profile_period', 20),
        ('num_profile_bins', 10),
        ('min_volume_node', 0.1),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        # Initialize VWAP indicator
        self.vwap = VWAPIndicator(self.data)
        
        # Track volume profile
        self.volume_profile = defaultdict(float)
        self.support_levels = []
        self.resistance_levels = []
        
        # Position management
        self.order = None
        self.entry_price = None
        
        # Performance tracking
        self.trades = []
        self.vwap_distances = []
        self.volume_nodes = []

    def calculate_volume_profile(self):
        """Calculate volume profile for recent period"""
        if len(self.data) < self.params.volume_profile_period:
            return
            
        # Get recent price and volume data
        prices = np.array([self.data.close.get(ago=i)[0] 
                          for i in range(self.params.volume_profile_period)])
        volumes = np.array([self.data.volume.get(ago=i)[0] 
                           for i in range(self.params.volume_profile_period)])
        
        # Create price bins
        price_min, price_max = min(prices), max(prices)
        bin_edges = np.linspace(price_min, price_max, self.params.num_profile_bins + 1)
        
        # Calculate volume profile
        self.volume_profile.clear()
        total_volume = np.sum(volumes)
        
        for i in range(len(bin_edges) - 1):
            mask = (prices >= bin_edges[i]) & (prices < bin_edges[i+1])
            bin_volume = np.sum(volumes[mask])
            if bin_volume > 0:
                price_level = (bin_edges[i] + bin_edges[i+1]) / 2
                self.volume_profile[price_level] = bin_volume / total_volume
        
        # Identify support and resistance levels
        sorted_levels = sorted(self.volume_profile.items(), 
                             key=lambda x: x[1], 
                             reverse=True)
        
        current_price = self.data.close[0]
        self.support_levels = [price for price, vol in sorted_levels 
                             if price < current_price and 
                             vol >= self.params.min_volume_node]
        self.resistance_levels = [price for price, vol in sorted_levels 
                                if price > current_price and 
                                vol >= self.params.min_volume_node]
        
        # Store volume node information
        self.volume_nodes.append({
            'date': self.data.datetime.date(0),
            'price': current_price,
            'nearest_support': min(self.support_levels, default=None),
            'nearest_resistance': min(self.resistance_levels, default=None),
            'profile': dict(self.volume_profile)
        })

    def get_vwap_deviation(self):
        """Calculate current deviation from VWAP"""
        if len(self.data) < 2:
            return 0
            
        current_price = self.data.close[0]
        current_vwap = self.vwap[0]
        
        if current_vwap != 0:
            deviation = (current_price - current_vwap) / current_vwap
            self.vwap_distances.append(deviation)
            return deviation
        return 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, VWAP: {self.vwap[0]:.2f}')
            elif order.issell():
                if self.entry_price:
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    dev_entry = self.vwap_distances[-1] if self.vwap_distances else 0
                    self.trades.append({
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'vwap_deviation': dev_entry
                    })
                self.entry_price = None
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, VWAP: {self.vwap[0]:.2f}')
            
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        # Update volume profile
        self.calculate_volume_profile()
        
        # Don't trade if we have pending orders
        if self.order:
            return
            
        # Calculate VWAP deviation
        vwap_dev = self.get_vwap_deviation()
        
        if not self.position:  # No position - look for entry signals
            # Strong deviation from VWAP with volume support/resistance
            if abs(vwap_dev) > self.params.vwap_dev_threshold:
                if vwap_dev < -self.params.vwap_dev_threshold and self.support_levels:
                    nearest_support = min(self.support_levels)
                    if self.data.close[0] <= nearest_support * 1.01:  # Within 1% of support
                        if self.params.stop_loss and self.params.take_profit:
                            stop_price = self.data.close[0] * (1.0 - self.params.stop_loss)
                            limit_price = self.data.close[0] * (1.0 + self.params.take_profit)
                            
                            orders = self.buy_bracket(
                                size=None,
                                price=self.data.close[0],
                                stopprice=stop_price,
                                limitprice=limit_price,
                            )
                            self.order = orders[0]
                        else:
                            self.order = self.buy()
                            
                elif vwap_dev > self.params.vwap_dev_threshold and self.resistance_levels:
                    nearest_resistance = min(self.resistance_levels)
                    if self.data.close[0] >= nearest_resistance * 0.99:  # Within 1% of resistance
                        if self.params.stop_loss and self.params.take_profit:
                            stop_price = self.data.close[0] * (1.0 + self.params.stop_loss)
                            limit_price = self.data.close[0] * (1.0 - self.params.take_profit)
                            
                            orders = self.sell_bracket(
                                size=None,
                                price=self.data.close[0],
                                stopprice=stop_price,
                                limitprice=limit_price,
                            )
                            self.order = orders[0]
                        else:
                            self.order = self.sell()
                            
        else:  # Have position - look for exit signals
            # Exit when price returns to VWAP
            if abs(vwap_dev) < self.params.vwap_dev_threshold/2:
                self.order = self.close()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.trades:
            returns = [t['return'] for t in self.trades]
            vwap_devs = [t['vwap_deviation'] for t in self.trades]
            
            self.stats = {
                'total_trades': len(self.trades),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'avg_vwap_dev': np.mean([abs(d) for d in vwap_devs]),
                'sharpe_ratio': np.mean(returns) / np.std(returns) if len(returns) > 1 else 0
            }
            
            # Calculate volume profile effectiveness
            profitable_near_support = sum(1 for t in self.trades 
                                        if t['return'] > 0 and t['vwap_deviation'] < 0)
            profitable_near_resistance = sum(1 for t in self.trades 
                                          if t['return'] > 0 and t['vwap_deviation'] > 0)
            
            total_support_trades = sum(1 for t in self.trades if t['vwap_deviation'] < 0)
            total_resistance_trades = sum(1 for t in self.trades if t['vwap_deviation'] > 0)
            
            self.stats.update({
                'support_effectiveness': (profitable_near_support / total_support_trades 
                                       if total_support_trades > 0 else 0),
                'resistance_effectiveness': (profitable_near_resistance / total_resistance_trades 
                                          if total_resistance_trades > 0 else 0)
            })
            
            self.log(f"Strategy finished - Total trades: {self.stats['total_trades']}, "
                    f"Win rate: {self.stats['win_rate']:.2%}")
            
            
            
            
            
            
            
import backtrader as bt
import numpy as np
from enum import Enum

class MarketRegime(Enum):
    """Market regime types identified by clustering"""
    LOW_VOL_TREND = 0
    HIGH_VOL_TREND = 1
    MEAN_REVERSION = 2
    CHOPPY = 3

class RegimeClusterStrategy(bt.Strategy):
    """
    Trading strategy that uses unsupervised learning clusters to identify
    market regimes and applies appropriate trading rules for each regime.
    
    Parameters:
    - regime_shift_delay (default: 2): Bars to wait after regime change
    - volatility_period (default: 20): Period for volatility calculation
    - trend_period (default: 20): Period for trend calculation
    - trend_threshold (default: 0.6): Threshold for trend significance
    """
    
    params = (
        ('regime_shift_delay', 2),
        ('volatility_period', 20),
        ('trend_period', 20),
        ('trend_threshold', 0.6),
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        # Verify we have regime data
        if not hasattr(self.data, 'regime_cluster'):
            raise ValueError("Data feed must include 'regime_cluster' line")
        
        # Store regime data
        self.regime_clusters = self.data.regime_cluster
        
        # Market indicators for regime validation
        self.volatility = bt.indicators.StdDev(
            self.data.close, 
            period=self.params.volatility_period
        )
        self.trend = bt.indicators.DirectionalMovement(
            self.data, 
            period=self.params.trend_period
        )
        
        # Regime tracking
        self.current_regime = None
        self.regime_shift_counter = 0
        self.regime_history = []
        
        # Position management
        self.order = None
        self.entry_price = None
        
        # Strategy components for different regimes
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.trend_period)
        self.atr = bt.indicators.ATR(self.data, period=self.params.volatility_period)
        
        # Performance tracking
        self.trades = []
        self.regime_changes = []

    def validate_regime(self, regime):
        """Validate regime assignment with market indicators"""
        if len(self.data) < max(self.params.volatility_period, self.params.trend_period):
            return False
            
        vol_ratio = self.volatility[0] / bt.indicators.SMA(
            self.volatility, 
            period=self.params.volatility_period
        )[0]
        
        trend_strength = abs(self.trend.plus[0] - self.trend.minus[0]) / (
            self.trend.plus[0] + self.trend.minus[0]
        )
        
        if regime in [MarketRegime.LOW_VOL_TREND, MarketRegime.HIGH_VOL_TREND]:
            return trend_strength > self.params.trend_threshold
        elif regime == MarketRegime.MEAN_REVERSION:
            return trend_strength < self.params.trend_threshold
        return True  # CHOPPY regime doesn't need validation

    def get_position_size(self, regime):
        """Determine position size based on regime"""
        base_size = 1.0
        if regime == MarketRegime.HIGH_VOL_TREND:
            return base_size * 0.5  # Reduce size in high volatility
        elif regime == MarketRegime.CHOPPY:
            return base_size * 0.3  # Minimal size in choppy markets
        return base_size

    def get_regime_signal(self, regime):
        """Get trading signal based on current regime"""
        if regime == MarketRegime.LOW_VOL_TREND:
            # Trend following in low volatility
            if self.data.close[0] > self.sma[0]:
                return 1
            elif self.data.close[0] < self.sma[0]:
                return -1
                
        elif regime == MarketRegime.HIGH_VOL_TREND:
            # Trend following with confirmation
            if (self.data.close[0] > self.sma[0] and 
                self.trend.plus[0] > self.trend.minus[0]):
                return 1
            elif (self.data.close[0] < self.sma[0] and 
                  self.trend.minus[0] > self.trend.plus[0]):
                return -1
                
        elif regime == MarketRegime.MEAN_REVERSION:
            # Mean reversion
            if self.data.close[0] < self.sma[0] - self.atr[0]:
                return 1
            elif self.data.close[0] > self.sma[0] + self.atr[0]:
                return -1
                
        return 0  # No signal or CHOPPY regime

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log(f'BUY EXECUTED - Regime: {self.current_regime.name}, '
                        f'Price: {order.executed.price:.2f}')
            elif order.issell():
                if self.entry_price:
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    self.trades.append({
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'regime': self.current_regime,
                        'bars_held': len(self.data) - self.last_trade_bar
                    })
                self.entry_price = None
                self.log(f'SELL EXECUTED - Regime: {self.current_regime.name}, '
                        f'Price: {order.executed.price:.2f}')
            
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        # Get current regime
        new_regime = MarketRegime(int(self.regime_clusters[0]))
        
        # Handle regime changes
        if new_regime != self.current_regime:
            self.regime_changes.append({
                'date': self.data.datetime.date(0),
                'old_regime': self.current_regime,
                'new_regime': new_regime
            })
            self.current_regime = new_regime
            self.regime_shift_counter = 0
            return
        
        self.regime_shift_counter += 1
        
        # Don't trade during regime transition
        if self.regime_shift_counter < self.params.regime_shift_delay:
            return
            
        # Don't trade if we have pending orders
        if self.order:
            return
            
        # Validate regime
        if not self.validate_regime(self.current_regime):
            return
            
        # Get trading signal for current regime
        signal = self.get_regime_signal(self.current_regime)
        position_size = self.get_position_size(self.current_regime)
        
        if not self.position:  # No position - look for entry signals
            if signal > 0:  # Buy signal
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = self.data.close[0] * (1.0 - self.params.stop_loss)
                    limit_price = self.data.close[0] * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=position_size,
                        price=self.data.close[0],
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.buy(size=position_size)
                    
            elif signal < 0:  # Sell signal
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = self.data.close[0] * (1.0 + self.params.stop_loss)
                    limit_price = self.data.close[0] * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=position_size,
                        price=self.data.close[0],
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.sell(size=position_size)
                    
        else:  # Have position - look for exit signals
            if ((self.position.size > 0 and signal < 0) or 
                (self.position.size < 0 and signal > 0)):
                self.order = self.close()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.trades:
            # Overall statistics
            returns = [t['return'] for t in self.trades]
            self.stats = {
                'total_trades': len(self.trades),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns),
                'regime_changes': len(self.regime_changes)
            }
            
            # Regime-specific statistics
            for regime in MarketRegime:
                regime_trades = [t for t in self.trades if t['regime'] == regime]
                if regime_trades:
                    regime_returns = [t['return'] for t in regime_trades]
                    self.stats[f'{regime.name}_trades'] = len(regime_trades)
                    self.stats[f'{regime.name}_return'] = np.mean(regime_returns)
                    self.stats[f'{regime.name}_win_rate'] = (
                        len([r for r in regime_returns if r > 0]) / len(regime_trades)
                    )
            
            self.log(f"Strategy finished - Total trades: {self.stats['total_trades']}, "
                    f"Win rate: {self.stats['win_rate']:.2%}")
            
            
            
            
            
            
import backtrader as bt
import numpy as np
from typing import Dict, List

class PCAFactorStrategy(bt.Strategy):
    """
    Trading strategy based on PCA-extracted market factors.
    Trades when factors show significant deviations from their means.
    
    Parameters:
    - n_factors (default: 3): Number of PCA factors to use
    - zscore_threshold (default: 2.0): Z-score threshold for factor signals
    - lookback_period (default: 60): Period for factor statistics
    - factor_influence (default: None): Dict mapping factors to their historical influence
    """
    
    params = (
        ('n_factors', 3),
        ('zscore_threshold', 2.0),
        ('lookback_period', 60),
        ('factor_influence', None),  # e.g., {0: 'bullish', 1: 'bearish', 2: 'neutral'}
        ('stop_loss', None),
        ('take_profit', None),
    )

    def __init__(self):
        # Verify we have factor data
        self.factor_lines = []
        for i in range(self.params.n_factors):
            factor_name = f'factor_{i}'
            if not hasattr(self.data, factor_name):
                raise ValueError(f"Missing factor data: {factor_name}")
            self.factor_lines.append(getattr(self.data, factor_name))
        
        # Factor statistics
        self.factor_means = [0] * self.params.n_factors
        self.factor_stds = [0] * self.params.n_factors
        
        # Track factor history
        self.factor_history = {i: [] for i in range(self.params.n_factors)}
        
        # Position management
        self.order = None
        self.entry_price = None
        
        # Performance tracking
        self.trades = []
        self.factor_signals = []

    def calculate_factor_statistics(self):
        """Calculate mean and standard deviation for each factor"""
        if len(self.data) < self.params.lookback_period:
            return
            
        for i in range(self.params.n_factors):
            factor_values = [self.factor_lines[i].get(ago=j)[0] 
                           for j in range(self.params.lookback_period)]
            self.factor_means[i] = np.mean(factor_values)
            self.factor_stds[i] = np.std(factor_values)
            self.factor_history[i].append(factor_values[-1])

    def get_factor_signals(self) -> Dict[int, float]:
        """Calculate z-scores for each factor"""
        signals = {}
        for i in range(self.params.n_factors):
            if self.factor_stds[i] > 0:
                z_score = ((self.factor_lines[i][0] - self.factor_means[i]) / 
                          self.factor_stds[i])
                if abs(z_score) > self.params.zscore_threshold:
                    signals[i] = z_score
        return signals

    def combine_factor_signals(self, signals: Dict[int, float]) -> int:
        """Combine factor signals into trading decision"""
        if not signals or not self.params.factor_influence:
            return 0
            
        signal_strength = 0
        for factor, z_score in signals.items():
            influence = self.params.factor_influence.get(factor, 'neutral')
            if influence == 'bullish':
                signal_strength += z_score
            elif influence == 'bearish':
                signal_strength -= z_score
                
        if abs(signal_strength) > self.params.zscore_threshold:
            return 1 if signal_strength > 0 else -1
        return 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            elif order.issell():
                if self.entry_price:
                    returns = (order.executed.price - self.entry_price) / self.entry_price
                    # Record trade with factor states
                    factor_states = {i: self.factor_lines[i][0] 
                                   for i in range(self.params.n_factors)}
                    self.trades.append({
                        'entry_price': self.entry_price,
                        'exit_price': order.executed.price,
                        'return': returns,
                        'factor_states': factor_states
                    })
                self.entry_price = None
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
            
            self.order = None
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def next(self):
        # Update factor statistics
        self.calculate_factor_statistics()
        
        # Don't trade until we have enough data
        if len(self.data) < self.params.lookback_period:
            return
            
        # Don't trade if we have pending orders
        if self.order:
            return
            
        # Get factor signals
        signals = self.get_factor_signals()
        self.factor_signals.append({
            'date': self.data.datetime.date(0),
            'signals': dict(signals)
        })
        
        # Combine signals into trading decision
        decision = self.combine_factor_signals(signals)
        
        if not self.position:  # No position - look for entry signals
            if decision > 0:  # Buy signal
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = self.data.close[0] * (1.0 - self.params.stop_loss)
                    limit_price = self.data.close[0] * (1.0 + self.params.take_profit)
                    
                    orders = self.buy_bracket(
                        size=None,
                        price=self.data.close[0],
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.buy()
                    
            elif decision < 0:  # Sell signal
                if self.params.stop_loss and self.params.take_profit:
                    stop_price = self.data.close[0] * (1.0 + self.params.stop_loss)
                    limit_price = self.data.close[0] * (1.0 - self.params.take_profit)
                    
                    orders = self.sell_bracket(
                        size=None,
                        price=self.data.close[0],
                        stopprice=stop_price,
                        limitprice=limit_price,
                    )
                    self.order = orders[0]
                else:
                    self.order = self.sell()
                    
        else:  # Have position - look for exit signals
            # Exit if factors return to normal or reverse
            if ((self.position.size > 0 and decision < 0) or 
                (self.position.size < 0 and decision > 0) or
                decision == 0):
                self.order = self.close()

    def stop(self):
        """Calculate and log final strategy statistics."""
        if self.trades:
            returns = [t['return'] for t in self.trades]
            
            # Overall statistics
            self.stats = {
                'total_trades': len(self.trades),
                'avg_return': np.mean(returns),
                'win_rate': len([r for r in returns if r > 0]) / len(returns)
            }
            
            # Factor influence analysis
            for i in range(self.params.n_factors):
                factor_effect = []
                for trade in self.trades:
                    factor_state = trade['factor_states'][i]
                    if factor_state > self.factor_means[i] + self.factor_stds[i]:
                        factor_effect.append((trade['return'], 'high'))
                    elif factor_state < self.factor_means[i] - self.factor_stds[i]:
                        factor_effect.append((trade['return'], 'low'))
                
                if factor_effect:
                    high_returns = [r for r, state in factor_effect if state == 'high']
                    low_returns = [r for r, state in factor_effect if state == 'low']
                    
                    self.stats[f'factor_{i}_high_return'] = (
                        np.mean(high_returns) if high_returns else 0
                    )
                    self.stats[f'factor_{i}_low_return'] = (
                        np.mean(low_returns) if low_returns else 0
                    )
            
            self.log(f"Strategy finished - Total trades: {self.stats['total_trades']}, "
                    f"Win rate: {self.stats['win_rate']:.2%}")
            
            
            
            
            

    
    
    
    
    
    