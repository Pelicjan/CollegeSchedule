import pickle
from pathlib import Path
import login_credentials
import urllib3
import requests
from scrapy import Selector
from block import Block
from data import Data


class Scraper:
    formdata = {'formname': 'login',
                'default_fun': '1',
                'userid': login_credentials.login.encode('iso-8859-2'),
                'password': login_credentials.password.encode('iso-8859-2')
                }

    def __init__(self, callback, group):
        self.raw_schedule = tuple()
        self.schedule_selector = None
        self.group_selector = None
        self.data = Data()
        self.s = requests.Session()
        urllib3.disable_warnings()
        self.load_data()
        if self.data.blank:
            callback('')
            self.init_scrap(group)
        else:
            callback(self.data.current_group)

    def log_in(self):
        print("Logowanie do e-Dziekanatu")
        r = self.s.get('https://s1.wcy.wat.edu.pl/ed1/', verify=False)
        selector = Selector(text=r.text)
        self.data.sid = selector.xpath("//form[@name='aaa']/@action").get().partition('=')[2]
        self.s.post('https://s1.wcy.wat.edu.pl/ed1/index.php?sid=' + self.data.sid, data=self.formdata,
                    verify=False, headers={"Content-Type": "application/x-www-form-urlencoded; charset=ISO-8859-2"})

    def scrap(self, group):
        if self.data.sid == '':
            self.log_in()
        r = self.s.get('https://s1.wcy.wat.edu.pl/ed1/logged_inc.php?sid={}&mid=328&iid=20201&exv={}&pos=0&rdo=1'
                       .format(self.data.sid, group), verify=False)
        if r.url == 'https://wcy.wat.edu.pl/':
            self.data.sid = ''
            self.scrap(group)
            return
        sel = Selector(text=r.text)
        self.raw_schedule = (sel.xpath("//table[@class='tableFormList2SheTeaGrpHTM']").get(),
                             sel.xpath("//td[@class='tdFormEdit2']//table[@class='tableGrayWhite']").get())
        self.schedule_selector = Selector(text=self.raw_schedule[0])
        self.group_selector = Selector(text=self.raw_schedule[1])

    def init_scrap(self, group):
        if group == '':
            group = 'WCY18IJ5S1'
        self.data.current_group = group
        self.scrap(group)
        self.set_all_blocks(group)
        self.set_all_dates()
        self.data.groups = self.group_selector.xpath("//a[@class='aMenu' and contains(@href, 'showGroupPlan')]/text()")\
            .getall()

    def set_all_blocks(self, group):
        all_blocks = list()
        for i in range(1, 23):
            all_blocks += self.get_week_blocks_from_selector(group, i)
        self.data.blocks[group] = all_blocks

    def set_all_dates(self):
        self.data.dates.clear()
        for i in range(22):
            first_day = self.schedule_selector \
                .xpath("//th[position()={} and @class='thFormList1HSheTeaGrpHTM3']/nobr/text()"
                       .format(4 + i)).getall()
            next_days = self.schedule_selector \
                .xpath("//td[position()={} and @class='tdFormList1DDSheTeaGrpHTM3']/nobr/text()"
                       .format(4 + i)).getall()
            self.data.dates += first_day + next_days

    def get_week_blocks_from_selector(self, group, week) -> list:  # week indexed from 1
        block_list = list()
        blocks_data = self.schedule_selector.xpath("//td[position()={} and @class='tdFormList1DSheTeaGrpHTM3']//table "
                                                   "| //td[position()={} and @class='tdFormList1DSheTeaGrpHTM3' "
                                                   "and count(*)=0]/text() "
                                                   .format(2 + week, 2 + week)).getall()
        for i, block_data in enumerate(blocks_data):
            if block_data != '\xa0':
                selector = Selector(text=block_data)
                block = Block(index=i + (week - 1) * 49,
                              blank=False,
                              group=group,
                              hide=False,
                              note='',
                              subject=selector.xpath("//tr[1]/td/nobr/b[1]/text()").get(),
                              category=selector.xpath("//tr[1]/td/nobr/b[2]/text()").get(),
                              room=selector.xpath("//tr[1]/td/nobr/text()[last()]").get(),
                              teacher=selector.xpath("//tr[2]/td/nobr/a/text()").get(),
                              number=selector.xpath("//tr[3]/td/nobr/text()").get())
                block_list.append(block)
            else:
                block_list.append(Block(index=i + (week - 1) * 49,
                                        blank=True,
                                        group=group))
        return block_list

    def get_week_blocks(self, group, week) -> list:  # week indexed from 1
        self.data.current_group = group
        block_list = list()
        if group in self.data.blocks:
            start_index = (week - 1) * 49
            end_index = start_index + 49
            for block in self.data.blocks[group][start_index:end_index]:
                block_list.append(block)
            return block_list
        self.scrap(group)
        self.set_all_blocks(group)
        return self.get_week_blocks(group, week)

    def get_week_dates(self, week) -> list:  # week indexed from 0
        if len(self.data.dates) == 0:
            self.init_scrap(self.data.current_group)
        dates = list()
        for i, date in enumerate(self.data.dates):
            if i // 14 == week:
                dates.append(date)
        return dates

    def get_groups(self) -> list:
        if len(self.data.groups) == 0:
            self.init_scrap(self.data.current_group)
        return self.data.groups

    def save_data(self):
        with open('schedule.data', 'wb') as f:
            pickle.dump(self.data, f)

    def load_data(self):
        data_file = Path("schedule.data")
        if data_file.is_file():
            with open('schedule.data', 'rb') as f:
                self.data = pickle.load(f)
                self.data.blank = False
