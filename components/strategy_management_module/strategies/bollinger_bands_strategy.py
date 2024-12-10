class BollingerBandsStrategy(BaseStrategyWithSLTP):
    params = (
        ('period', 20),
        ('devfactor', 2),
        ('stop_loss', 0.0),
        ('take_profit', 0.0),
    )

    def __init__(self):
        # Initialize parent class to ensure it sets up stop_loss and take_profit
        super().__init__()
        self.boll = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.period,
            devfactor=self.params.devfactor
        )

    def next(self):
        self.check_sl_tp()  # This checks for stop loss / take profit
        if self.data.close[0] < self.boll.lines.bot[0] and not self.position:
            self.buy()
        elif self.data.close[0] > self.boll.lines.top[0] and self.position:
            self.sell()
