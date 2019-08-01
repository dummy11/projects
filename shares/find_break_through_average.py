import pandas as pd
import tushare as ts
import numpy as np

class find_break_through_average(object):
    def __init__(self):
        super(find_break_through_average, self).__init__()

    def caculate_average_line(self, data):
        line_list = []
        close = list(data.close)
        close_5 = close[0:5]
        close_10 = close[0:10]
        close_20 = close[0:20]
        close_55 = close[0:55]
        close_89 = close[0:89]
        close_144 = close[0:144]
        close_233 = close[0:233]
        line_list.append(np.mean(close_5)   if len(close) >= 5 else 0)
        line_list.append(np.mean(close_10)  if len(close) >= 10 else 0)
        line_list.append(np.mean(close_20)  if len(close) >= 20 else 0)
        line_list.append(np.mean(close_55)  if len(close) >= 55 else 0)
        line_list.append(np.mean(close_89)  if len(close) >= 89 else 0)
        line_list.append(np.mean(close_144) if len(close) >= 144 else 0)
        line_list.append(np.mean(close_233) if len(close) >= 233 else 0)
        return line_list
       
    def is_break_through_average(self, data):
        open = list(data.open)
        close = list(data.close)
        line_list = self.caculate_average_line(data)
        line_list.append(close[0])
        line_list.append(open[0])
        sort_list = sorted(line_list)
        open_index = sort_list.index(open[0])
        close_index = sort_list.index(close[0])
        if close_index - open_index > 5:
            return 1
        else:
            return 0

    def is_average_sorted(self, data):
        line_list = self.caculate_average_line(data)
        if line_list[0] >= line_list[1] and line_list[1] >= line_list[2] and line_list[2] >= line_list[3] and line_list[3] >= line_list[4] and line_list[4] >= line_list[5] and line_list[5] != 0 and line_list[0] <= line_list[5]*(1+0.15):
            return 1
        else:
            return 0

    def is_break_through_average_real(self, data, real_open, trade):
        open = list(data.open)
        close = list(data.close)
        line_list = self.caculate_average_line(data)
        line_list.append(trade)
        line_list.append(real_open)
        sort_list = sorted(line_list)
        open_index = sort_list.index(real_open)
        close_index = sort_list.index(trade)
        if close_index - open_index > 5:
            return 1
        else:
            return 0

if __name__ == "__main__":
    break_average = find_break_through_average()
    data = ts.get_hist_data('300056', '2019-04-01', '2019-07-28')
    print data
    print break_average.is_break_through_average(data)
