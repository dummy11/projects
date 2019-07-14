import pandas as pd
import tushare as ts
import numpy as np

class find_breakthrough_average(object):
    def __init__(self):
        super(find_breakthrough_average, self).__init__()

    def caculate_average_line(self, data):
        close = list(data.close)
        close_5 = close[0:5]
        close_10 = close[0:10]
        close_20 = close[0:20]
        close_55 = close[0:55]
        mean_5 = np.mean(close_5)
        mean_10 = np.mean(close_10)
        mean_20 = np.mean(close_20)
        mean_55 = np.mean(close_55)

if __name__ == "__main__":
    break_average = find_breakthrough_average()
    data = ts.get_hist_data('300056', '2019-04-01', '2019-07-12')
    break_average.caculate_average_line(data)
