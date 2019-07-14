import pandas as pd
import tushare as ts

class find_yesterday_limit_up(object):
    def __init__(self):
        super(find_yesterday_limit_up, self).__init__()

    def is_yesterday_limit_up(self, data):
        p_change = data.p_change
        print p_change
        if p_change[1] >= 9.9 and (p_change[0] <= 1):
            return 1
        else:
            return 0

if __name__ == "__main__":
    limit_up = find_yesterday_limit_up()
    data = ts.get_hist_data('300056', '2019-03-20', '2019-03-22')
    print limit_up.is_yesterday_limit_up(data)