import pandas as pd
import tushare as ts

class find_two_three_low(object):
    def __init__(self):
        super(find_two_three_low, self).__init__()

    def is_two_low(self, data):
        threshold = 0.03
        continue_day = 20
        day_before = 3
        low = list(data.low)
        if len(low) >= continue_day:
            lowest_value = min(low)
            lowest_index = low.index(lowest_value)
            if lowest_index > day_before and (low[0] <= lowest_value*(1+threshold) and low[0] >= lowest_value*(1-threshold)):
                return 1
            else:
                return 0
        else:
            return 0

    def is_three_low(self, data):
        threshold = 0.02
        continue_day = 20
        day_before = 3
        low = list(data.low)
        high = list(data.high)
        highest_value = max(high)
        if len(low) >= continue_day:
            lowest_value = min(low)
            lowest_index = low.index(lowest_value)
            second_low = low
            del second_low[lowest_index]
            second_lowest_value = min(second_low)
            second_lowest_index = low.index(second_lowest_value)
            if highest_value >= lowest_value*(1+0.2) and abs(second_lowest_index - lowest_index) > 3 and (second_lowest_value <= lowest_value*(1+threshold)):
                if lowest_index > day_before and second_lowest_index > day_before and (low[0] <= lowest_value*(1+threshold) and low[0] >= lowest_value*(1-threshold)):
                    return 1
                else:
                    return 0
            else:
                return 0
        else:
            return 0

    def is_two_three_low(self, data):
        if self.is_two_low(data) or self.is_three_low(data):
            return 1
        else:
            return 0

if __name__ == "__main__":
    two_three = find_two_three_low()
    data = ts.get_hist_data('300056', '2019-05-11', '2019-07-11')
    print two_three.is_two_three_low(data)
