#coding=utf-8
import tushare as ts

def get_block_share():
    pro = ts.pro_api()
    #return pro.daily(ts_code="603657.SH", start_date="20181101", end_date="20181108")
    return ts.pro_bar(pro_api=pro, ts_code="600093.SH", start_date="20181101", end_date="20181120", ma=[5, 10, 20])

if __name__ == "__main__":
    ts.set_token('b105dd8b37494c895f838c4cf657a0c80352815b72f877ebaa507f37')
    data = ts.get_today_all()
    #data=get_block_share()
    print(data)
    data=ts.get_concept_classified()
    # for code in range(0, len(data['c_name'])):
    #     if (data['c_name'][code] == "融资融券"):
    #         print (data['code'][code])