import scrapy


class ScheduleSpider(scrapy.Spider):
    name = 'ScheduleSpider'
    start_urls = [
        'https://wcy.wat.edu.pl/pl/rozklad?grupa_id=WCY18IJ5S1',
    ]
    output = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_callback = kwargs.get('args').get('callback')

    def parse(self, response, **kwargs):
        self.output = response.xpath("//div[@id='navbar']").get()

    def close(self, spider, reason):
        self.output_callback(self.output)
