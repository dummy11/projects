#coding=utf-8
import tushare as ts
import datetime

class my_filter(object):

    def __init__(self,  code):
        super(my_filter,self).__init__()
        self.restrict_code = []
        self.expect_loss_code = []
        self.valid_code = code

    @property
    def filter_code(self):
        self.restrict_share()
        self.forecast()
        return self.valid_code, self.restrict_code, self.expect_loss_code

    def restrict_share(self):
        data = ts.xsg_data()
        ratio = list(data.ratio)
        restrict_code = list(data.code)
        for index in range(len(ratio)):
            if ratio[index] > 5 and restrict_code[index] in self.valid_code:
                self.restrict_code.append(restrict_code[index])
                self.valid_code.remove(restrict_code[index])

    def forecast(self):
        today = datetime.date.today()
        year = int(today.strftime('%Y'))
        month = int(today.strftime('%m'))
        if month > 3:
            quarter = month/3
        else:
            quarter = 1 if month == 3 else 4
        data = ts.forecast_data(year, quarter)
        code_list = list(data.code)
        type_list = list(data.type)
        for code in self.valid_code:
            if code in code_list:
                index = code_list.index(code)
                if type_list[index] in ['预降'.decode('utf-8'), '预减'.decode('utf-8'), '预亏'.decode('utf-8')]:
                    self.valid_code.remove(code)
                    self.expect_loss_code.append(code)

if __name__ == "__main__":
    all_company = ts.get_stock_basics()
    valid_code = list(all_company.index)
    f = my_filter(valid_code)
    valid_code, restrict_code, expect_loss_code = f.filter_code
    f.forecast()