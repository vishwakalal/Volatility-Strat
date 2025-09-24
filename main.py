from AlgorithmImports import *
from math import *

class VolatilityShield(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2019, 1,1)  # Backtesting dates
        self.SetEndDate(2025, 1, 1)
        self.SetCash(100000)  # Starting capital

        # Defining the symbols
        self.crypto_symbols = ["BTCUSD", "ETHUSD"]
        self.stock_symbols = ["AAPL","META", "NVDA","TSM","INTU","BX", "TSLA", "PWR", "NUE","ZM", "NIO", "BRKR", "AXON", "ODFL", "PINS", "EFX","BLDR","ENPH","PLTR"]
        self.fx_symbols = ["GBPUSD", "EURUSD", "USDJPY"]
        self.SetBenchmark("SPY")
        self.spy_symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.spy_ema200 = self.EMA(self.spy_symbol, 200, Resolution.Daily)

        # Adding cryptocurrency, and stock
        self.active_symbols = []
        for symbol in self.crypto_symbols:
            try:
                self.AddCrypto(symbol, Resolution.Daily)
                self.active_symbols.append(symbol)
            except Exception as e:
                self.Debug(f"Unable to add symbol: {symbol}. Exception: {e}")
       

        for symbol in self.stock_symbols:
            try:
                self.AddEquity(symbol, Resolution.Daily)
                self.active_symbols.append(symbol)
            except Exception as e:
                self.Debug(f"Unable to add symbol: {symbol}. Exception: {e}")



        # Define the technical indicators
        self.supertrend1 = {}
        self.supertrend2 = {}
        self.rsi = {}
        self.ema100 = {}
        self.weekly_twap = {}
        self.entry_prices = {}
        self.atr = {}
        self.exposure_cap = 0.95
        self.target_portfolio_volume = 0.12
        self.min_weight = 0.05
        self.max_weight = 0.20


        for symbol in self.active_symbols:
            self.supertrend1[symbol] = self.STR(symbol, 10, 2.5, MovingAverageType.Wilders)
            self.supertrend2[symbol] = self.STR(symbol, 10, 3, MovingAverageType.Wilders)
            self.rsi[symbol] = self.RSI(symbol, 10, MovingAverageType.Wilders, Resolution.Daily)
            self.ema100[symbol] = self.EMA(symbol, 100, Resolution.Daily)
            self.weekly_twap[symbol] = self.WeeklyTwap(symbol, 5)
            self.entry_prices[symbol] = None
            self.atr[symbol] = self.ATR(symbol, 14, MovingAverageType.Wilders, Resolution.Daily)

        self.SetWarmUp(100, Resolution.Daily)  # 100 day EMA period

    def WeeklyTwap(self, symbol, num_weeks):
        twap = self.SMA(symbol, num_weeks * 5, Resolution.Daily)  # Assuming 5 trading days per week
        return twap
    
    def ExposureCap(self):
        pv = self.Portfolio.TotalPortfolioValue
        if pv <= 0:
            return 0.0
        long_value = sum(max(0.0, sec.HoldingsValue) for sec in self.Portfolio.Values)
        return float(long_value / pv)
    
    def VolatilityWeight(self, symbol, price):
        atr_indicator = self.atr.get(symbol, None)
        if atr_indicator is None or not atr_indicator.IsReady or price <= 0:
            return None

        atr_value = atr_indicator.Current.Value
        if atr_value <= 0:
            return None

        daily_volume = atr_value / price
        annual_volume = daily_volume * sqrt(252)
        raw_weight = self.target_portfolio_volume / (annual_volume * 3.0)
        return max(self.min_weight, min(self.max_weight, raw_weight))

    def OnData(self, data):
        if self.IsWarmingUp:
            return

        for symbol in self.active_symbols:
            if symbol in self.fx_symbols:
                if not data.QuoteBars.ContainsKey(symbol):
                    continue
                qbar = data.QuoteBars[symbol]
                current_price = (qbar.Bid.Close + qbar.Ask.Close) / 2.0 if qbar.Bid and qbar.Ask else qbar.Close
            else:
                if not data.Bars.ContainsKey(symbol):
                    continue

                bar = data.Bars[symbol]
                current_price = bar.Close

            # Get current values
            supertrend1 = self.supertrend1[symbol].Current.Value
            supertrend2 = self.supertrend2[symbol].Current.Value
            rsi = self.rsi[symbol].Current.Value
            ema100 = self.ema100[symbol].Current.Value
            weekly_twap = self.weekly_twap[symbol].Current.Value

            # Define factor based on asset type
            factor = 1.1 if symbol in self.crypto_symbols else 1.02

            # Entry condition
            if symbol in self.stock_symbols:
                if (not self.spy_ema200.IsReady) or (self.Securities[self.spy_symbol].Price < self.spy_ema200.Current.Value):
                    continue
            if self.entry_prices[symbol] is None:
                if self.ExposureCap() >= self.exposure_cap:
                    continue
                if (current_price > supertrend1 and 
                    current_price > supertrend2 and 
                    rsi > 55 and 
                    current_price > ema100 and 
                    current_price < factor * weekly_twap):  # Use appropriate factor
                    self.Debug(f"{symbol}: Supertrend1={supertrend1}, Supertrend2={supertrend2}, RSI={rsi},EMA100={ema100}, Weekly TWAP={weekly_twap}")
                    weight = self.VolatilityWeight(symbol, current_price)
                    if weight is None:
                        weight = 0.1
                    self.SetHoldings(symbol, float(weight))
                    self.entry_prices[symbol] = current_price

            # Exit condition
            elif current_price < supertrend1 and current_price < supertrend2:
                self.Liquidate(symbol)
                self.entry_prices[symbol] = None
