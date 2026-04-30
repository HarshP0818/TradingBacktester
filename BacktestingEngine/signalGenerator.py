

# now we are going to generate the buy/sell/hold signals
# we will take an input of a DataFrame object containing columns date, open, high, low, close, volume
# we will output a pd.series object of signals. 1 = buy, 0 = hold, -1 = sell
# we will not track money, positions, or execute trades here
# ONLY generate signals
import pandas as pd

class Strategy:
    # we will create a constructor for the strategy class that takes in the parameters for the strategy, such as the fast and slow window for the moving average crossover strategy
    def __init__(self, fast_window=20, slow_window=50):
        self.fast_window = fast_window
        self.slow_window = slow_window

    # this function will take in the cleaned data and generate the signals based on the strategy parameters
    def generate_signals(self, data):
        # we will populate signal with all 0s so we dont need to calculations for hold signals, we will only update the buy/sell signals
        signal = pd.Series(0, index=data.index)
        # we will use a simple moving average crossover strategy for demonstration
        fast = data['close'].rolling(window=self.fast_window).mean()
        slow = data['close'].rolling(window=self.slow_window).mean()
        # signal will be when fast > slow, we buy, when fast < slow we sell, otherwise we hold
        # the signal should be a pd.series of 1, 0, -1
        # now we will compare the fast and slow to determine what the current signal should be
        signal[fast > slow] = 1
        signal[fast < slow] = -1
        return signal