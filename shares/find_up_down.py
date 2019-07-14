import pandas as pd
import tushare as ts

class find_up_down(object):
    def __init__(self):
        super(find_up_down, self).__init__()

    def is_real_time_up_down(self, data, trade, real_open, real_high, real_low):
        threshold = 0.03
        close_threshold = 0.015
        low = list(data.low)
        close = list(data.close)
        high = list(data.high)
        open = list(data.open)
        if high[0] >= close[0]*(1+threshold) and high[0] >= open[0]*(1+threshold):
            if real_low <= trade*(1-threshold) and real_low <= real_open*(1-threshold):
                if trade >= close[0]*(1-close_threshold) and trade <=  close[0]*(1+close_threshold):
                    return 1
        elif low[0] <= close[0]*(1-threshold) and low[0] <= open[0]*(1-threshold):
            if real_high >= trade*(1+threshold) and real_high >= real_open*(1+threshold):
                if trade >= close[0]*(1-close_threshold) and trade <=  close[0]*(1+close_threshold):
                    return  1
        else:
            return 0

    def is_hist_up_down(self, data):
        threshold = 0.035
        close_threshold = 0.015
        low = list(data.low)
        close = list(data.close)
        high = list(data.high)
        open = list(data.open)
        if high[1] >= close[1]*(1+threshold) and high[1] >= open[1]*(1+threshold): #yesterday
            if low[0] <= close[0]*(1-threshold) and low[0] <= open[0]*(1-threshold): #today
                if close[0] >= close[1]*(1-close_threshold) and close[0] <= close[1]*(1+close_threshold):
                    return 1
        elif low[1] <= close[1]*(1-threshold) and low[1] <= open[1]*(1-threshold):
            if high[0] >= close[0]*(1+threshold) and high[0] >= open[0]*(1+threshold):
                if close[0] >= close[1]*(1-close_threshold) and close[0] <= close[1]*(1+close_threshold):
                    return 1
        else:
            return 0

# if __name__ == "__main__":
#     up_down = find_up_down()
#     all_data = ts.get_today_all()
#     all_code = list(all_data.code)
