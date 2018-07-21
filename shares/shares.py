import pandas as pd
import tushare as ts
import time
import datetime
import os
import sys
import argparse
from multiprocessing import Pool, Queue
from my_filter import *
from find_up_down import *

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--day_before', action='store', help='parse code data between (today - day_before) ~ today, the day all mean trade day', default='3')
parser.add_argument('-n', '--num', action='store', help='at least codes num to be picked out', default='5')
parser.add_argument('-r', '--real_time', action='store_true', help='real time parse data, otherwise just parse hist data')
parser.add_argument('-c', '--clean', action='store_true', help='clean the local data')
args = parser.parse_args()

code_time_region = {}
printed_code = []
limit_up_match_list = []
up_down_match_list = []
limit_up_match_queue = Queue()
up_down_match_queue = Queue()
limit_up_match_queue_temp = Queue()

def filter_code(all_company):
    valid_code = []
    for i in range(0, len(all_company.pe)):
        if int(all_company.pe[i]) > 0 and int(all_company.pe[i]) < 500:
            code = '%06d'%all_company.code[i]
            valid_code.append(code)
    return valid_code

# def date_handler(date):
#     if hasattr(date, 'isoformat'):
#         return date.isoformat()
#     else:
#         raise TypeError

def get_time_region(code, day_before):
    time_empty = 0
    time_update = 0
    today = datetime.datetime.today()
    pre_day = today - datetime.timedelta(day_before)
    saved_latest_day = datetime.datetime(year=1900,month=1,day=1)
    saved_pre_day = datetime.datetime(year=1900,month=1,day=1)
    current_latest_day = datetime.datetime
    current_pre_day = datetime.datetime

    if not code_time_region.has_key(code):
        time_empty = 1
        current_latest_day = today
        current_pre_day = pre_day
    else:
        time_region = code_time_region[code]
        saved_latest_day = datetime.datetime.strptime(time_region[1], '%Y-%m-%d')
        weekday = today.isoweekday()
        if today.date() > saved_latest_day.date() and weekday not in [6,7]:
            time_update = 1
            hour = int(today.strftime('%H'))
            minute = int(today.strftime('%M'))
            if (hour > 15) or (hour == 15 and minute > 15): #only after 15:05 will get today's code data
                current_latest_day = today
            else:
                if weekday == 1:
                    current_latest_day = today - datetime.timedelta(3)
                else:
                    current_latest_day = today - datetime.timedelta(1)
        else:
            current_latest_day = saved_latest_day
        saved_pre_day = datetime.datetime.strptime(time_region[0], '%Y-%m-%d')
        if pre_day.date() < saved_pre_day.date():
            time_update = 1
            current_pre_day = pre_day
        else:
            current_pre_day = saved_pre_day

    # if time_empty or time_update:
    #     time_region = []
    #     time_region.append(current_pre_day.strftime('%Y-%m-%d'))
    #     time_region.append(current_latest_day.strftime('%Y-%m-%d'))
    #     code_time_region[code] = time_region
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    pre_day = pre_day.replace(hour=0, minute=0, second=0, microsecond=0)
    current_pre_day = current_pre_day.replace(hour=0, minute=0, second=0, microsecond=0)
    current_latest_day = current_latest_day.replace(hour=0, minute=0, second=0, microsecond=0)
    return saved_latest_day, saved_pre_day, today, pre_day, current_latest_day, current_pre_day

def get_hist_data(code, get_hist_start, get_hist_end, region_start, region_end):
    try:
        data = ts.get_hist_data(code, get_hist_start, get_hist_end)
        if data is not None:
            if not data.p_change.empty:
                time_region = []
                time_region.append(region_start)
                time_region.append(region_end)
                code_time_region[code] = time_region   #only when get hist back would update the time region
        return data
    except:
        #pass
        print ('failed to get %s history data'%code)

def get_code_data(code, day_before):
    saved_latest_day, saved_pre_day, today, pre_day, current_latest_day, current_pre_day = get_time_region(code, day_before)
    if today < saved_latest_day:  # this path temply not used, as today is always >= saved latest day
        if pre_day >= saved_pre_day:
            pass
        else:
            data = get_hist_data(code, pre_day.strftime('%Y-%m-%d'), (saved_pre_day-datetime.timedelta(1)).strftime('%Y-%m-%d'), current_pre_day.strftime('%Y-%m-%d'), current_latest_day.strftime('%Y-%m-%d'))
            data.to_csv("local_data/%s.csv"%code)
    else:
        if pre_day > saved_latest_day:
            start = pre_day.strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
            data = get_hist_data(code, start, end, current_pre_day.strftime('%Y-%m-%d'), current_latest_day.strftime('%Y-%m-%d'))
            if data is not None:
                data.to_csv("local_data/%s.csv"%code)
        elif pre_day >= saved_pre_day and pre_day <= saved_latest_day:
            if current_latest_day == saved_latest_day:
                pass
            else:
                if os.path.exists("local_data/%s.csv" % code):
                    local_data = pd.read_csv("local_data/%s.csv" % code)
                start = (saved_latest_day+datetime.timedelta(1)).strftime('%Y-%m-%d')
                end = today.strftime('%Y-%m-%d')
                data = get_hist_data(code, start, end, current_pre_day.strftime('%Y-%m-%d'), current_latest_day.strftime('%Y-%m-%d'))
                if data is not None:
                    data.to_csv("local_data/%s.csv"%code)
                local_data.to_csv("local_data/%s.csv"%code, mode='a', header=None, index=False)
        else:
            if os.path.exists("local_data/%s.csv"%code):
                local_data = pd.read_csv("local_data/%s.csv"%code)
            if today > saved_latest_day:
                start = (saved_latest_day+datetime.timedelta(1)).strftime('%Y-%m-%d')
                end = today.strftime('%Y-%m-%d')
                data2 = get_hist_data(code, start, end, current_pre_day.strftime('%Y-%m-%d'), current_latest_day.strftime('%Y-%m-%d'))
                if data2 is not None:
                    data2.to_csv("local_data/%s.csv"%code)
            start = pre_day.strftime('%Y-%m-%d')
            end = (saved_pre_day-datetime.timedelta(1)).strftime('%Y-%m-%d')
            data1 = get_hist_data(code, start, end, current_pre_day.strftime('%Y-%m-%d'), current_latest_day.strftime('%Y-%m-%d'))
            if today > saved_latest_day:
                local_data.to_csv("local_data/%s.csv"%code, mode='a', header=None, index=False)
            else:
                local_data.to_csv("local_data/%s.csv"%code, index=False)
            if data1 is not None:
                data1.to_csv("local_data/%s.csv"%code, mode='a', header=None)

def get_data(valid_code, day_before):
    global code_time_region
    print ('getting code data...')
    if os.path.exists('local_data/time_region'):
        with open('local_data/time_region', 'r') as f:
            str_time_region = f.read()
            if str_time_region != '':
                code_time_region = eval(str_time_region)
    day_before_list = [day_before]*len(valid_code)
    map(get_code_data, valid_code, day_before_list)
    with open('local_data/time_region', 'w') as f:
        f.write(str(code_time_region))

def parse_code_data(code, day_before, retry_num):
    threshold = 0.03
    index = 0
    up_down = find_up_down()
    if os.path.exists("local_data/%s.csv"%code):
        data = pd.read_csv("local_data/%s.csv"%code)
    else:
        saved_latest_day, saved_pre_day, today, pre_day, current_latest_day, current_pre_day = get_time_region(code, day_before)
        start = current_pre_day.strftime('%Y-%m-%d')
        end = current_latest_day.strftime('%Y-%m-%d')
        data = get_hist_data(code, start, end, current_pre_day.strftime('%Y-%m-%d'), current_latest_day.strftime('%Y-%m-%d'))
        if data is not None:
            data.to_csv("local_data/%s.csv"%code)
    if (data is not None) and (not data.p_change.empty):
        time_range = (day_before+retry_num) if len(data.p_change) > (day_before+retry_num) else len(data.p_change)
        for i in range(time_range): #find the first zhang ting, smaller index means later day
            if data.p_change[i] >= 9.92 and data.close[i] == data.high[i]:
                index = i
        if index != 0 and data.close[index] < 1.15*data.ma20[index]:  #index 0 means today, zhangting close not exceed ma20 15%
            low = list(data.low)
            close = list(data.close)
            open = list(data.open)
            p_change = list(data.p_change)
            if  (close[0] >  close[index]*0.9*(1-threshold) and close[0] < close[index]*0.9*(1+threshold)): #\
                #or (low[0] >  close[index]*0.9*(1-threshold+0.005) and low[0] < close[index]*0.9*(1+threshold-0.005)):
                if not code in limit_up_match_list:
                    #match_code.append(code)
                    limit_up_match_queue.put(code)
                    limit_up_match_queue_temp.put(code)
                    # if match_cnt >= int(args.num):
                    #     break
        index = 0
        match_up_down = up_down.is_hist_up_down(data)
        if match_up_down:
            up_down_match_queue.put(code)
    else:
        #print ('%s has no local data'%code)
        pass

def parse_hist_data(valid_code, day_before):

    global limit_up_match_list
    retry_num = 0
    #match_code = []
    day_before_list = [day_before]*len(valid_code)
    print ('#####################################')
    print ('The codes match the condition are as follow : ')
    while (limit_up_match_queue.qsize() < int(args.num)):
        pool = Pool(30)
        #retry_num_list = [retry_num]*len(valid_code)
        #map(parse_code_data, valid_code, day_before_list, retry_num_list)
        for code in valid_code:
            pool.apply_async(parse_code_data, args=(code, day_before, retry_num))
        pool.close()
        pool.join()

        #limit_up_match_list = []
        while not limit_up_match_queue_temp.empty():
            code = limit_up_match_queue_temp.get()
            limit_up_match_list.append(code)
        retry_num += 1
        if retry_num > 10:
            break
    # while (not limit_up_match_queue.empty()):
    #     code = limit_up_match_queue.get()
    #     match_code.append(code)
    while not up_down_match_queue.empty():
        code = up_down_match_queue.get()
        up_down_match_list.append(code)
    filter_match_code(limit_up_match_list, 'limit_up')
    filter_match_code(up_down_match_list, 'up_down')

def filter_match_code(match_code, match_type):
    f = my_filter(match_code)
    match_code, restrict_code, expect_loss_code = f.filter_code
    print ('') # to align the display
    print ('%s match code are :'%match_type)
    for code in match_code:
        if code not in printed_code:
            print (code)
            printed_code.append(code)
    print ('restrict code are : ')
    for code in restrict_code:
        if code not in printed_code:
            print (code)
            printed_code.append(code)
    print ('expect loss code are : ')
    for code in expect_loss_code:
        if code not in printed_code:
            print (code)
            printed_code.append(code)

def parse_real_time_data(valid_code, day_before):
    threshold = 0.03
    index = 0
    retry_num = 0
    match_code = []
    today = datetime.datetime.today()
    hour = int(today.strftime('%H'))
    minute = int(today.strftime('%M'))
    up_down = find_up_down()
    if (hour > 9 or (hour == 9 and minute > 30)) and hour < 15:
        while (hour < 15):
            retry_num += 1
            print ('retry %d:'%retry_num)
            all_data = ts.get_today_all()
            print ('')  # to align the display
            for code in valid_code:
                all_code = list(all_data.code)
                i = all_code.index(code)
                trade = all_data.trade[i]
                real_low = all_data.low[i]
                real_high = all_data.high[i]
                real_open = all_data.open[i]

                if os.path.exists("local_data/%s.csv"%code):
                    data = pd.read_csv("local_data/%s.csv"%code)
                else:
                    saved_latest_day, saved_pre_day, today, pre_day, current_latest_day, current_pre_day = get_time_region(code, day_before)
                    start = current_pre_day.strftime('%Y-%m-%d')
                    end = current_latest_day.strftime('%Y-%m-%d')
                    data = get_hist_data(code, start, end, current_pre_day.strftime('%Y-%m-%d'), current_latest_day.strftime('%Y-%m-%d'))
                    if data is not None:
                        data.to_csv("local_data/%s.csv"%code)
                if (data is not None) and (not data.p_change.empty):
                    time_range = day_before if len(data.p_change) > day_before else len(data.p_change)
                    for i in range(time_range): #find the first zhang ting, smaller index means later day
                        if data.p_change[i] >= 9.92 and data.close[i] == data.high[i]:
                            index = i
                    if index != 0 and data.close[index] < 1.15*data.ma20[index]:  #index 0 means today, zhangting close not exceed ma20 15%
                        low = list(data.low)
                        close = list(data.close)
                        open = list(data.open)
                        p_change = list(data.p_change)
                        if  (trade >  close[index]*0.9*(1-threshold) and trade < close[index]*0.9*(1+threshold)): #\
                            #or (low[0] >  close[index]*0.9*(1-threshold+0.005) and low[0] < close[index]*0.9*(1+threshold-0.005)):
                            if not code in match_code:
                                #print (code)
                                match_code.append(code)
                    index = 0
                    match_up_down = up_down.is_real_time_up_down(data, trade, real_open, real_high, real_low)
                    if match_up_down:
                        up_down_match_list.append(code)
            filter_match_code(match_code, 'limit_up')
            filter_match_code(up_down_match_list, 'up_down')
            time.sleep(300) #every 5 minutes get real time data
            today = datetime.datetime.today()
            hour = int(today.strftime('%H'))
            minute = int(today.strftime('%M'))

    else:
        parse_hist_data(valid_code, day_before)

def main():
    day_before = int(args.day_before)
    if args.clean:
        cmd = 'rm local_data/*.csv local_data/time_region'
        os.system(cmd)
    try:
        all_company = ts.get_stock_basics()
        if not os.path.exists('local_data'):
            os.mkdir('local_data')
        all_company.to_csv('local_data/code_list.csv')
        all_company = pd.read_csv('local_data/code_list.csv')
    except:
        if os.path.exists('local_data/code_list.csv'):
            print ('failed to get the company code list, use local code list')
            all_company = pd.read_csv('local_data/code_list.csv')
        else:
            print ('failed to get the company code list, please retry')
            sys.exit()

    valid_code = filter_code(all_company)
    try:
        get_data(valid_code, day_before+10) #get more data
    except KeyboardInterrupt:
        sys.exit()

    if args.real_time:
        parse_real_time_data(valid_code, 3)  # only choose zhangting share in 3 days
    else:
        parse_hist_data(valid_code, day_before)

if __name__ == "__main__":
    main()
