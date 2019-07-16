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
from find_continue_red import *
from find_two_three_low import *
from find_break_through_average import *
from send_mail import *

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--day_before', action='store', help='parse code data between (today - day_before) ~ today, the day all mean trade day', default='3')
parser.add_argument('-n', '--num', action='store', help='at least codes num to be picked out', default='5')
parser.add_argument('-r', '--real_time', action='store_true', help='real time parse data, otherwise just parse hist data')
parser.add_argument('-c', '--clean', action='store_true', help='clean the local data')
parser.add_argument('-s', '--send_mail', action='store_true', help='send the mathch code mail to me')
parser.add_argument('-w', '--wait_minute', action='store', help='wait minutes to start the program')
parser.add_argument('-nl', '--no_loss', action='store_true', help='get the no loss shares')
parser.add_argument('-po','--parse_only', action='store_true', help='only parse data, not get data')
parser.add_argument('-lo','--limit_up_only', action='store_true', help='only parse limit up code')
args = parser.parse_args()

reload(sys)
sys.setdefaultencoding('utf-8')

code_time_region = {}
printed_code = []
limit_up_match_list = []
yesterday_limit_up_list = []
up_down_match_list = []
continue_red_match_list = []
two_three_low_match_list = []
break_through_average_match_list = []
loss_code_list = []
limit_up_match_queue = Queue()
yesterday_limit_up_queue = Queue()
up_down_match_queue = Queue()
continue_red_match_queue = Queue()
two_three_low_match_queue = Queue()
break_through_average_match_queue = Queue()
limit_up_match_queue_temp = Queue()
threshold = 0.03
yesterday_limit_up_threshold = 1

def filter_code(all_company):
    valid_code = []
    for i in range(0, len(all_company.pe)):
        if args.no_loss:
            if int(all_company.pe[i]) > 0 and int(all_company.pe[i]) < 500:
                code = '%06d'%all_company.code[i]
                valid_code.append(code)        
        else:
            code = '%06d'%all_company.code[i]
            if int(all_company.pe[i]) <= 0 and int(all_company.pe[i]) > 500:
                loss_code_list.append(code)
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
        if today.date() > saved_latest_day.date():
            time_update = 1
            hour = int(today.strftime('%H'))
            minute = int(today.strftime('%M'))
            if (hour > 15) or (hour == 15 and minute > 15): #only after 15:05 will get today's code data
                current_latest_day = today
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
    #try:
    pro = ts.pro_api()
    code_pro = code + '.SH' if code[0] == '6' else code + '.SZ'
    print (code_pro, get_hist_start, get_hist_end)
    data = ts.pro_bar(pro_api=pro, ts_code=code_pro, start_date=get_hist_start.replace('-', ''), end_date=get_hist_end.replace('-', ''))
    #data = ts.get_hist_data(code, get_hist_start, get_hist_end)
    if data is not None:
        if not data.pct_chg.empty:
            time_region = []
            time_region.append(region_start)
            time_region.append(region_end)
            code_time_region[code] = time_region   #only when get hist back would update the time region
    return data
    # except:
    #     #pass
    #     print ('failed to get %s history data'%code)

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
    #map(get_code_data, valid_code, day_before_list)
    for i in range(0, len(valid_code)):
        if not args.parse_only:
            get_code_data(valid_code[i], day_before)
        if (i%199 == 0 and i > 0 and (not args.parse_only)):
            time.sleep(55)

    with open('local_data/time_region', 'w') as f:
        f.write(str(code_time_region))

def parse_code_data(code, day_before, retry_num):
    index = 0
    up_down = find_up_down()
    continue_red = find_continue_red()
    two_three_low = find_two_three_low()
    break_through = find_break_through_average()
    if os.path.exists("local_data/%s.csv"%code):
        data = pd.read_csv("local_data/%s.csv"%code)
    else:
        saved_latest_day, saved_pre_day, today, pre_day, current_latest_day, current_pre_day = get_time_region(code, day_before)
        start = current_pre_day.strftime('%Y-%m-%d')
        end = current_latest_day.strftime('%Y-%m-%d')
        data = get_hist_data(code, start, end, current_pre_day.strftime('%Y-%m-%d'), current_latest_day.strftime('%Y-%m-%d'))
        if data is not None:
            data.to_csv("local_data/%s.csv"%code)
    p_change = data.pct_chg
    if (data is not None) and (not p_change.empty):
        #below is for find yesterday limit up
        if p_change[1] >= 9.9 and p_change[0] <= yesterday_limit_up_threshold and not code in loss_code_list:
            yesterday_limit_up_queue.put(code)

        #below is for limit up
        time_range = (day_before+retry_num) if len(p_change) > (day_before+retry_num) else len(p_change)
        for i in range(time_range): #find the first zhang ting, smaller index means later day
            if p_change[i] >= 9.9 and data.close[i] == data.high[i]:
                if i + 1 <= len(p_change) - 1:
                    if p_change[i+1] <= 8:  #should not continual zhangting
                        index = i
                else:
                    index = i
        if index != 0: #and data.close[index] < 1.15*data.ma20[index]:  #index 0 means today, zhangting close not exceed ma20 15%
            low = list(data.low)
            close = list(data.close)
            open = list(data.open)
            #p_change = list(data.p_change)
            if  (close[0] >  close[index]*0.9*(1-threshold - 0.02) and close[0] < close[index]*0.9*(1+threshold)): #\
                #or (low[0] >  close[index]*0.9*(1-threshold+0.005) and low[0] < close[index]*0.9*(1+threshold-0.005)):
                if not code in limit_up_match_list:
                    #match_code.append(code)
                    limit_up_match_queue.put(code)
                    limit_up_match_queue_temp.put(code)
                    # if match_cnt >= int(args.num):
                    #     break
        index = 0
        match_up_down = up_down.is_hist_up_down(data)
        match_continue_red = continue_red.is_continue_red(data)
        match_two_three_low = two_three_low.is_two_three_low(data)
        match_break_through_average = break_through.is_break_through_average(data)
        if match_up_down:
            up_down_match_queue.put(code)
        if match_continue_red:
            continue_red_match_queue.put(code)
        if match_two_three_low:
            two_three_low_match_queue.put(code)
        if match_break_through_average:
            break_through_average_match_queue.put(code)

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
    while not continue_red_match_queue.empty():
        code = continue_red_match_queue.get()
        continue_red_match_list.append(code)
    while not two_three_low_match_queue.empty():
        code = two_three_low_match_queue.get()
        two_three_low_match_list.append(code)
    while not yesterday_limit_up_queue.empty():
        code = yesterday_limit_up_queue.get()
        yesterday_limit_up_list.append(code)
    while not break_through_average_match_queue.empty():
        code = break_through_average_match_queue.get()
        break_through_average_match_list.append(code)

    if not args.limit_up_only:
        filter_match_code(up_down_match_list, 'up_down')
        filter_match_code(continue_red_match_list, 'continue_red')
        filter_match_code(two_three_low_match_list, 'two_three_low')
        filter_match_code(break_through_average_match_list, 'break_through_average')
        filter_match_code(yesterday_limit_up_list, 'yesterday_limit_up')
    filter_match_code(limit_up_match_list, 'limit_up')

def filter_match_code(match_code, match_type):
    msg=""
    has_new_code=0
    f = my_filter(match_code)
    match_code, restrict_code, expect_loss_code = f.filter_code
    print ('') # to align the display
    if match_code:
        msg += '%s match code are : \n'%match_type
    for code in match_code:
        if code not in printed_code:
            has_new_code = 1
            msg += code+"\n"
            printed_code.append(code)
    if restrict_code:
        msg += 'restrict code are : \n'
    for code in restrict_code:
        if code not in printed_code:
            has_new_code = 1
            msg += code+"\n"
            printed_code.append(code)
    if expect_loss_code:
        msg += 'expect loss code are : \n'
    for code in expect_loss_code:
        if code not in printed_code:
            has_new_code = 1
            msg += code+"\n"
            printed_code.append(code)
    print(msg)
    if args.send_mail and has_new_code:
        send_mail(msg)

def parse_real_time_data(valid_code, day_before):
    #threshold = 0.045
    index = 0
    retry_num = 0
    match_code = []
    today = datetime.datetime.today()
    hour = int(today.strftime('%H'))
    minute = int(today.strftime('%M'))
    up_down = find_up_down()
    if (hour > 9 or (hour == 9 and minute >= 30)) and hour < 15:
        while (hour < 15):
            retry_num += 1
            print ('retry %d:'%retry_num)
            # try:
            all_data = ts.get_today_all()
            print ('')  # to align the display
            for code in valid_code:
                all_code = list(all_data.code)
                try:
                    i = all_code.index(code)
                except:
                    print ('%s is not in list'%code)
                    continue
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
                p_change = data.pct_chg
                if (data is not None) and (not p_change.empty):
                    time_range = day_before if len(p_change) > day_before else len(p_change)
                    for i in range(time_range): #find the first zhang ting, smaller index means later day
                        if p_change[i] >= 9.9 and data.close[i] == data.high[i]:
                            if i + 1 <= len(p_change) - 1:
                                if p_change[i+1] <= 8:  #should not continual zhangting
                                    index = i
                            else:
                                index = i
                    if index != 0:# and data.close[index] < 1.15*data.ma20[index]:  #index 0 means today, zhangting close not exceed ma20 15%
                        low = list(data.low)
                        close = list(data.close)
                        open = list(data.open)
                        #p_change = list(data.p_change)
                        if  (trade >  close[index]*0.9*(1-threshold - 0.02) and trade < close[index]*0.9*(1+threshold)): #\
                            #or (low[0] >  close[index]*0.9*(1-threshold+0.005) and low[0] < close[index]*0.9*(1+threshold-0.005)):
                            if not code in match_code:
                                #print (code)
                                match_code.append(code)
                    index = 0
                    match_up_down = up_down.is_real_time_up_down(data, trade, real_open, real_high, real_low)
                    if match_up_down:
                        up_down_match_list.append(code)
            # except:
            #     print ("failed to get today all data")
            filter_match_code(match_code, 'limit_up')
            #filter_match_code(up_down_match_list, 'up_down')
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

    if args.wait_minute:
        time.sleep(int(args.wait_minute)*60)

    if args.real_time:
        parse_real_time_data(valid_code, 3)  # only choose zhangting share in 3 days
    else:
        parse_hist_data(valid_code, day_before)

if __name__ == "__main__":
    ts.set_token('b105dd8b37494c895f838c4cf657a0c80352815b72f877ebaa507f37')
    main()
