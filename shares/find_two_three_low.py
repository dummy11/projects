import pandas as pd
import tushare as ts

class find_two_three_low(object):
    def __init__(self):
        super(find_two_three_low, self).__init__()

    def is_two_low(self, data):
        threshold = 0.03
        high_low_threshold = 0.20
        continue_day = 30
        day_before = 3
        low = list(data.low)[0:continue_day]
        high = list(data.high)[0:continue_day]
        highest_value = max(high)
        highest_index = high.index(highest_value)        
        lowest_value = min(low)
        lowest_index = low.index(lowest_value)
        if len(low) >= continue_day:
            if highest_value >= lowest_value*(1+high_low_threshold) and abs(highest_index - lowest_index) > 3:
                if lowest_index > day_before and (low[0] <= lowest_value*(1+threshold) and low[0] >= lowest_value*(1-threshold)):
                    return 1
                else:
                    return 0
            else:
                return 0
        else:
            return 0

    def is_three_low(self, data):
        threshold = 0.03
        high_low_threshold = 0.20
        continue_day = 30
        day_before = 3
        low = list(data.low)[0:continue_day]
        high = list(data.high)[0:continue_day]
        real_lowest_value = min(list(data.low))
        highest_value = max(high)
        highest_index = high.index(highest_value)
        lowest_value = min(low)
        lowest_index = low.index(lowest_value)
        second_low = low
        del second_low[lowest_index]
        second_lowest_value = min(second_low)
        second_lowest_index = low.index(second_lowest_value)
        index_list = sorted([lowest_index, second_lowest_index])
        if lowest_value <= real_lowest_value*(1+0.15) and highest_index >= index_list[0]+3 and highest_index <= index_list[1]-3 and lowest_index < continue_day-1 and second_lowest_value < continue_day-1:
            if highest_value >= lowest_value*(1+high_low_threshold) and (second_lowest_value <= lowest_value*(1+threshold)):
                if (low[0] <= lowest_value*(1+threshold+0.02)):
                    return 1
                else:
                    return 0
            else:
                return 0
        else:
            return 0

    def is_two_three_low(self, data):
        if self.is_three_low(data):
            return 1
        else:
            return 0

if __name__ == "__main__":
    two_three = find_two_three_low()
    data = ts.get_hist_data('600744', '2019-05-11', '2019-07-11')
    print two_three.is_two_three_low(data)
