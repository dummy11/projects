import pandas as pd
import tushare as ts

class find_continue_red(object):
    def __init__(self):
        super(find_continue_red, self).__init__()

    def is_continue_red(self, data):
        threshold = 0.08
        continue_day = 7
        open = list(data.open)
        close = list(data.close)
        if len(open) >= continue_day:
            for index in range(continue_day):
                if not close[index] > open[index]:
                    return 0
            if close[0] <= close[continue_day-1]*(1+threshold):
                return 1
            else:
                return 0
        else:
            return 0

if __name__ == "__main__":
    continue_red = find_continue_red()
    data = ts.get_hist_data('300056', '2018-07-11', '2018-07-20')
    print continue_red.is_continue_red(data)
    print data
