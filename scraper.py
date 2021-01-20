import login_credentials
import urllib3
import requests
from scrapy import Selector


class Scraper:
    formdata = {'formname': 'login',
                'default_fun': '1',
                'userid': login_credentials.login.encode('iso-8859-2'),
                'password': login_credentials.password.encode('iso-8859-2')
                }

    def __init__(self):
        self.sid = ''
        self.raw_schedule = tuple()
        self.schedule_selector = None
        self.group_selector = None
        self.s = requests.Session()
        urllib3.disable_warnings()

    def login(self):
        print("Logowanie do e-Dziekanatu")
        r = self.s.get('https://s1.wcy.wat.edu.pl/ed1/', verify=False)
        selector = Selector(text=r.text)
        self.sid = selector.xpath("//form[@name='aaa']/@action").get().partition('=')[2]
        self.s.post('https://s1.wcy.wat.edu.pl/ed1/index.php?sid=' + self.sid, data=self.formdata,
                    verify=False, headers={"Content-Type": "application/x-www-form-urlencoded; charset=ISO-8859-2"})

    def scrap(self, group):
        if self.sid == '':
            self.login()
        r = self.s.get('https://s1.wcy.wat.edu.pl/ed1/logged_inc.php?sid={}&mid=328&iid=20201&exv={}&pos=0&rdo=1'
                       .format(self.sid, group))
        if r.url == 'https://wcy.wat.edu.pl/':
            self.sid = ''
            self.scrap(group)
            return
        sel = Selector(text=r.text)
        self.raw_schedule = (sel.xpath("//table[@class='tableFormList2SheTeaGrpHTM']").get(),
                             sel.xpath("//td[@class='tdFormEdit2']//table[@class='tableGrayWhite']").get())
        self.schedule_selector = Selector(text=self.raw_schedule[0])
        self.group_selector = Selector(text=self.raw_schedule[1])

    def get_groups(self) -> list:
        return self.group_selector.xpath("//a[@class='aMenu' and contains(@href, 'showGroupPlan')]/text()").getall()

    def get_days(self, position) -> list:
        first_day = self.schedule_selector \
            .xpath("//th[position()={} and @class='thFormList1HSheTeaGrpHTM3']/nobr/text()"
                   .format(4 + position)).getall()
        next_days = self.schedule_selector \
            .xpath("//td[position()={} and @class='tdFormList1DDSheTeaGrpHTM3']/nobr/text()"
                   .format(4 + position)).getall()
        return first_day + next_days

    def get_blocks(self, number) -> list:
        return self.schedule_selector.xpath("//td[position()={} and @class='tdFormList1DSheTeaGrpHTM3']//table "
                                            "| //td[position()={} and @class='tdFormList1DSheTeaGrpHTM3' "
                                            "and count(*)=0]/text() "
                                            .format(2 + number, 2 + number)).getall()

    def get_block_data(self, block) -> dict:
        block_data = dict()
        selector = Selector(text=block)
        block_data['subject'] = selector.xpath("//tr[1]/td/nobr/b[1]/text()").get()
        block_data['category'] = selector.xpath("//tr[1]/td/nobr/b[2]/text()").get()
        block_data['room'] = selector.xpath("//tr[1]/td/nobr/text()[last()]").get()
        block_data['teacher'] = selector.xpath("//tr[2]/td/nobr/a/text()").get()
        block_data['number'] = selector.xpath("//tr[3]/td/nobr/text()").get()
        return block_data
