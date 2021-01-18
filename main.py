import sys
import os

from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QPushButton, QGridLayout, QVBoxLayout, QLabel, \
    QTableWidget, QCheckBox
from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from scrapy.crawler import CrawlerProcess
from scrapy import Selector
from CollegeSchedule.CollegeSchedule.spiders.ScheduleSpider import ScheduleSpider


class MyCrawler:

    def __init__(self):
        self.output = None
        self.process = CrawlerProcess(settings={'LOG_ENABLED': False})

    def yield_output(self, data):
        self.output = data

    def crawl(self, cls):
        self.process.crawl(cls, args={'callback': self.yield_output})
        self.process.start()


def crawl(cls):
    crawler = MyCrawler()
    crawler.crawl(cls)
    return crawler.output


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "main_window.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file, self)
        ui_file.close()
        self.raw_schedule = tuple
        self.schedule_selector = None

        self.main_widget = self.window.findChild(QWidget, 'CollegeSchedule')
        self.table_widget = self.window.findChild(QTableWidget, 'tableWidget')
        self.next_week = self.window.findChild(QPushButton, 'nextWeek')
        self.previous_week = self.window.findChild(QPushButton, 'previousWeek')
        self.check = self.window.findChild(QCheckBox, 'check')

        self.next_week.clicked.connect(self.download_schedule)
        self.download_schedule()

    def download_schedule(self):
        # self.raw_schedule = crawl(ScheduleSpider)
        # OFFLINE TEST
        f = open("plan.txt", "r", encoding="utf8")
        html = f.read()
        sel = Selector(text=html)
        self.raw_schedule = (sel.xpath("//table[@class='tableFormList2SheTeaGrpHTM']").get(),
                             sel.xpath("//table[@class='tableGrayWhite']").get())
        # OFFLINE TEST
        self.schedule_selector = Selector(text=self.raw_schedule[0])
        self.get_week(1)

    def get_week(self, number):
        first_day = self.schedule_selector \
            .xpath("//th[position()={} and @class='thFormList1HSheTeaGrpHTM3']/nobr/text()"
                   .format(3 + number)).getall()

        next_days = self.schedule_selector \
            .xpath("//td[position()={} and @class='tdFormList1DDSheTeaGrpHTM3']/nobr/text()"
                   .format(3 + number)).getall()

        self.set_headers(first_day + next_days)

        blocks = self.schedule_selector \
            .xpath("//td[position()={} and @class='tdFormList1DSheTeaGrpHTM3']//table "
                   "| //td[position()={} and @class='tdFormList1DSheTeaGrpHTM3' and count(*)=0]/text()"
                   .format(2 + number, 2 + number)).getall()
        print(blocks)
        self.set_blocks(blocks)

    def set_headers(self, days):
        dates = list()
        weekdays = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
        for i in range(0, len(days), 2):
            dates += [days[i] + ' ' + days[i + 1] + '\n' + weekdays[i // 2]]
        self.table_widget.setHorizontalHeaderLabels(dates)

    def set_blocks(self, blocks):
        row = 0
        column = 0
        for i, block in enumerate(blocks, start=1):
            if block != '\xa0':
                selector = Selector(text=block)
                subject = selector.xpath("//tbody/tr[1]/td/nobr/b[1]/text()").get()
                category = selector.xpath("//tbody/tr[1]/td/nobr/b[2]/text()").get()
                room = selector.xpath("//tbody/tr[1]/td/nobr/text()[last()]").get()
                teacher = selector.xpath("//tbody/tr[2]/td/nobr/a/text()").get()
                number = selector.xpath("//tbody/tr[3]/td/nobr/text()").get()
                print(subject, category, room, teacher, number)
                self.add_block(row, column, subject, category, room, teacher, number)
            row += 1
            if i % 7 == 0:
                row = 0
                column += 1

    def add_block(self, row, column, subject, category, room, teacher, number):
        block = QWidget()
        layout = QVBoxLayout()
        subject_label = QLabel(subject, alignment=Qt.AlignCenter)
        subject_label.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
        layout.addWidget(subject_label)
        layout.addWidget(QLabel(category, alignment=Qt.AlignCenter))
        layout.addWidget(QLabel(room, alignment=Qt.AlignCenter))
        layout.addWidget(QLabel(teacher, alignment=Qt.AlignCenter))
        layout.addWidget(QLabel(number, alignment=Qt.AlignCenter))
        block.setLayout(layout)
        self.table_widget.setCellWidget(row, column, block)


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
