import sys
import os
from _datetime import datetime
from pathlib import Path
import roman
import pickle
from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QPushButton, QVBoxLayout, QLabel, \
    QTableWidget, QComboBox
from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from scrapy.crawler import CrawlerProcess
from scrapy import Selector
from qt_material import apply_stylesheet
from CollegeSchedule.CollegeSchedule.spiders.ScheduleSpider import ScheduleSpider


class MyCrawler:

    def __init__(self):
        self.group = 'I8J5S1'
        self.output = None
        self.process = CrawlerProcess(settings={'LOG_ENABLED': False})

    def yield_output(self, data):
        self.output = data

    def crawl(self, cls):
        self.process.crawl(cls, args={'callback': self.yield_output, 'group': self.group})
        self.process.start()


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "main_window.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file, self)
        ui_file.close()
        self.data = dict()
        self.raw_schedule = tuple()
        self.schedule_selector = None
        self.week = 1
        self.selected_block = (-1, -1)

        self.load_data()

        self.main_widget = self.window.findChild(QWidget, 'college_schedule')
        self.table_widget = self.window.findChild(QTableWidget, 'table_widget')
        self.next_week = self.window.findChild(QPushButton, 'next_week')
        self.previous_week = self.window.findChild(QPushButton, 'previous_week')
        self.save_note_button = self.window.findChild(QPushButton, 'save_note')
        self.group_box = self.window.findChild(QComboBox, 'group_box')
        self.download_button = self.window.findChild(QPushButton, 'download_data')
        self.note = self.window.findChild(QTextEdit, 'note')

        self.next_week.clicked.connect(lambda: self.get_week(self.week + 1))
        self.previous_week.clicked.connect(lambda: self.get_week(self.week - 1))
        self.save_note_button.clicked.connect(self.save_note)
        self.download_button.clicked.connect(self.download_schedule)
        self.table_widget.cellClicked.connect(self.block_clicked)

        self.get_groups()
        self.download_schedule()
        today = (datetime.today().day, datetime.today().month)
        weeks = self.get_all_weeks()
        for i, week in enumerate(weeks, start=1):
            if today in week:
                self.get_week(i)
                break

    def get_groups(self):
        pass

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

    def get_all_weeks(self) -> list:
        weeks = list()
        for i in range(22):
            first_day = self.schedule_selector \
                .xpath("//th[position()={} and @class='thFormList1HSheTeaGrpHTM3']/nobr/text()"
                       .format(4 + i)).getall()
            next_days = self.schedule_selector \
                .xpath("//td[position()={} and @class='tdFormList1DDSheTeaGrpHTM3']/nobr/text()"
                       .format(4 + i)).getall()
            days = first_day + next_days
            dates = list()
            for j in range(0, len(days), 2):
                dates += [(int(days[j]), roman.fromRoman(days[j + 1]))]
            weeks += [dates]
        return weeks

    def get_week(self, number):
        if 1 <= number <= 22:
            self.week = number
            self.note.setPlainText('')

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
                self.add_block(row, column, subject, category, room, teacher, number)
            else:
                self.table_widget.removeCellWidget(row, column)
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
        if self.get_index(row, column) in self.data:
            block.setProperty('Note', 'true')
            block.setStyle(block.style())
        block.setLayout(layout)
        block.setProperty('class', 'block')
        self.table_widget.setCellWidget(row, column, block)

    def get_index(self, row, column) -> int:
        return row + column * 7 + (self.week - 1) * 49

    def block_clicked(self, row, column):
        if self.selected_block[0] != row or self.selected_block[1] != column:
            if self.selected_block[0] != -1 and self.selected_block[1] != -1:
                previous_block = self.table_widget.cellWidget(self.selected_block[0], self.selected_block[1])
                if previous_block is not None:
                    previous_block.setProperty('Selected', 'false')
                    previous_block.setStyle(previous_block.style())
            self.selected_block = (row, column)
            block = self.table_widget.cellWidget(row, column)
            if block is not None:
                block.setProperty('Selected', 'true')
                block.setStyle(block.style())
            self.load_note(self.get_index(row, column))

    def load_data(self):
        data_file = Path("schedule.data")
        if data_file.is_file():
            with open('schedule.data', 'rb') as f:
                self.data = pickle.load(f)

    def save_data(self):
        with open('schedule.data', 'wb') as f:
            pickle.dump(self.data, f)

    def load_note(self, index):
        if index in self.data:
            self.note.setPlainText(self.data[index])
        else:
            self.note.setPlainText('')

    def save_note(self):
        if self.note.toPlainText() == '':
            self.data.pop(self.get_index(self.selected_block[0], self.selected_block[1]), None)
            block = self.table_widget.cellWidget(self.selected_block[0], self.selected_block[1])
            block.setProperty('Note', 'false')
            block.setStyle(block.style())
        else:
            self.data[self.get_index(self.selected_block[0], self.selected_block[1])] = self.note.toPlainText()
            block = self.table_widget.cellWidget(self.selected_block[0], self.selected_block[1])
            block.setProperty('Note', 'true')
            block.setStyle(block.style())

    def closeEvent(self, event):
        self.save_data()
        event.accept()


group = 'I8J5S1'


def crawl(cls):
    crawler = MyCrawler()
    crawler.group = group
    crawler.crawl(cls)
    return crawler.output


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    apply_stylesheet(app, theme='dark_green.xml')
    stylesheet = app.styleSheet()
    with open('custom.css') as file:
        app.setStyleSheet(stylesheet + file.read())
    widget.show()
    sys.exit(app.exec_())
