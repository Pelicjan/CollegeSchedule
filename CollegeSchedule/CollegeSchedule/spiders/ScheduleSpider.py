import scrapy
from scrapy.http import FormRequest
from scrapy.http import Request
import login_credentials

class ScheduleSpider(scrapy.Spider):
    name = 'ScheduleSpider'
    start_urls = ['https://s1.wcy.wat.edu.pl/ed1/']
    output = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_callback = kwargs.get('args').get('callback')

    def parse(self, response, **kwargs):
        return FormRequest.from_response(
            response,
            formdata={
                'userid': login_credentials.login,
                'password': login_credentials.password
            },
            callback=self.go_to_schedule)

    def go_to_schedule(self, response):
        url = response.url + "&mid=328&iid=20204&exv=I8J5S1&pos=0&rdo=1"
        return Request(url=url, callback=self.get_schedule)

    def get_schedule(self, response):
        self.output = (response.xpath("//table[@class='tableFormList2SheTeaGrpHTM']").get(),
                       response.xpath("//table[@class='tableGrayWhite']").get())

    def close(self, spider, reason):
        self.output_callback(self.output)
