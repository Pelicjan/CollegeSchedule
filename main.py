import sys
import os
import threading
from _datetime import datetime
import roman
from PySide6 import QtGui
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QPushButton, QVBoxLayout, QLabel, \
    QTableWidget, QComboBox
from PySide6.QtCore import QFile, Qt, QSize, Signal
from PySide6.QtUiTools import QUiLoader
from qt_material import apply_stylesheet
from scraper import Scraper


class MainWindow(QWidget):
    loading_signal = Signal(bool, str, bool)
    set_blocks_signal = Signal(list, int)

    def __init__(self):
        super(MainWindow, self).__init__()
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "main_window.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file, self)
        ui_file.close()
        self.week = 1
        self.sel_block = (-1, -1)
        self.group = 'WCY18IJ5S1'
        self.blocks = list()
        self.loading_widget = None

        self.main_widget = self.window.findChild(QWidget, 'college_schedule')
        self.table_widget = self.window.findChild(QTableWidget, 'table_widget')
        self.next_week = self.window.findChild(QPushButton, 'next_week')
        self.previous_week = self.window.findChild(QPushButton, 'previous_week')
        self.save_note_button = self.window.findChild(QPushButton, 'save_note')
        self.group_box = self.window.findChild(QComboBox, 'group_box')
        self.download_button = self.window.findChild(QPushButton, 'download_data')
        self.note = self.window.findChild(QTextEdit, 'note')

        self.next_week.clicked.connect(lambda: self.get_week_click(self.week + 1))
        self.previous_week.clicked.connect(lambda: self.get_week_click(self.week - 1))
        self.save_note_button.clicked.connect(self.save_note_click)
        self.download_button.clicked.connect(lambda: self.load_data(True))
        self.table_widget.cellClicked.connect(self.block_click)
        self.table_widget.cellDoubleClicked.connect(self.block_double_click)
        self.group_box.currentTextChanged.connect(self.group_change)
        self.loading_signal.connect(self.loading_slot)
        self.set_blocks_signal.connect(self.set_blocks_slot)

        self.scraper = Scraper()
        t = threading.Thread(target=lambda: self.scraper.start(self, self.group))
        t.start()

    def load_data(self, force_download=False):
        self.get_days(force_download)
        self.set_groups()
        self.group_box.setCurrentIndex(self.group_box.findText(self.group))

    def get_days(self, force_download):
        today = (datetime.today().day, datetime.today().month)
        weeks = self.get_all_weeks()
        for i, week in enumerate(weeks, start=1):
            if today in week:
                if 1 <= i <= 22:
                    t = threading.Thread(target=lambda: self.set_blocks_thread_func(i, force_download))
                    t.start()
                break

    def get_all_weeks(self) -> list:
        weeks = list()
        for i in range(22):
            days = self.scraper.get_week_dates(i)
            dates = list()
            for j in range(0, len(days), 2):
                dates += [(int(days[j]), roman.fromRoman(days[j + 1]))]
            weeks += [dates]
        return weeks

    def get_week(self, number):
        if 1 <= number <= 22:
            self.week = number
            self.note.setPlainText('')
            self.set_headers(self.scraper.get_week_dates(number - 1))
            self.clear_blocks()
            self.set_blocks()

    def set_headers(self, days):
        dates = list()
        weekdays = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
        for i in range(0, len(days), 2):
            dates += [days[i] + ' ' + days[i + 1] + '\n' + weekdays[i // 2]]
        self.table_widget.setHorizontalHeaderLabels(dates)

    def clear_blocks(self):
        for row in range(self.table_widget.rowCount()):
            for column in range(self.table_widget.columnCount()):
                self.table_widget.removeCellWidget(row, column)

    def set_blocks(self):
        row = 0
        column = 0
        for i, block in enumerate(self.blocks, start=1):
            self.add_block(row, column, block)
            row += 1
            if i % 7 == 0:
                row = 0
                column += 1

    def add_block(self, row, column, block):
        block_widget = QWidget()
        if block.hide:
            block_widget.setProperty('Hide', 'true')
            block_widget.setStyle(block_widget.style())
        if block.note != '':
            block_widget.setProperty('Note', 'true')
            block_widget.setStyle(block_widget.style())
        if not block.blank:
            layout = QVBoxLayout()
            subject_label = QLabel(block.subject, alignment=Qt.AlignCenter)
            subject_label.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Bold))
            layout.addWidget(subject_label)
            layout.addWidget(QLabel(block.category, alignment=Qt.AlignCenter))
            layout.addWidget(QLabel(block.room, alignment=Qt.AlignCenter))
            layout.addWidget(QLabel(block.teacher, alignment=Qt.AlignCenter))
            layout.addWidget(QLabel(block.number, alignment=Qt.AlignCenter))
            block_widget.setLayout(layout)
            block_widget.setProperty('class', 'block')
        else:
            block_widget.setProperty('class', 'invisible_block')
        self.table_widget.setCellWidget(row, column, block_widget)

    def set_groups(self):
        groups = self.scraper.get_groups()
        self.group_box.blockSignals(True)
        self.group_box.addItems(groups)
        self.group_box.blockSignals(False)

    def get_index(self, row, column) -> int:
        return row + column * 7 + (self.week - 1) * 49

    def load_note(self, index):
        for block in self.blocks:
            if block.index == index:
                self.note.setPlainText(block.note)
                return
        self.note.setPlainText('')

    def show_loading(self):
        self.loading_widget = QWidget(self)
        self.loading_widget.setGeometry(279, 323, 200, 200)
        label = QLabel(self.loading_widget)
        movie = QMovie("Icons/loading.gif")
        label.setMovie(movie)
        label.setGeometry(30, 30, 140, 140)
        movie.setScaledSize(QSize(140, 140))
        movie.start()
        self.loading_widget.setStyleSheet("QWidget {border-radius: 100px; background-color: #222222;}")
        self.loading_widget.show()

    def block_click(self, row, column):
        if self.sel_block[0] != row or self.sel_block[1] != column:
            if self.sel_block[0] != -1 and self.sel_block[1] != -1:
                previous_block = self.table_widget.cellWidget(self.sel_block[0], self.sel_block[1])
                if previous_block is not None:
                    previous_block.setProperty('Selected', 'false')
                    previous_block.setStyle(previous_block.style())
            self.sel_block = (row, column)
            block = self.table_widget.cellWidget(row, column)
            if block is not None:
                block.setProperty('Selected', 'true')
                block.setStyle(block.style())
            self.load_note(self.get_index(row, column))

    def block_double_click(self, row, column):
        block = self.table_widget.cellWidget(row, column)
        if block is not None:
            hide = not block.property('Hide') if block.property('Hide') is not None else True
            block.setProperty('Hide', hide)
            block.setStyle(block.style())
            children = block.findChildren(QLabel)
            for child in children:
                child.setStyle(child.style())
            for block in self.blocks:
                if block.index == self.get_index(row, column):
                    block.hide = hide

    def group_change(self, group):
        self.group = group
        self.load_data()

    def save_note_click(self):
        block_widget = self.table_widget.cellWidget(self.sel_block[0], self.sel_block[1])
        if block_widget is not None:
            if self.note.toPlainText() == '':
                for block in self.blocks:
                    if block.index == self.get_index(self.sel_block[0], self.sel_block[1]):
                        block.note = ''
                block_widget.setProperty('Note', 'false')
                block_widget.setStyle(block_widget.style())
            else:
                for block in self.blocks:
                    if block.index == self.get_index(self.sel_block[0], self.sel_block[1]):
                        block.note = self.note.toPlainText()
                block_widget.setProperty('Note', 'true')
                block_widget.setStyle(block_widget.style())

    def get_week_click(self, week):
        t = threading.Thread(target=lambda: self.set_blocks_thread_func(week, False))
        t.start()

    def loading_slot(self, show, group, load_data):
        if show:
            self.show_loading()
        else:
            self.group = group
            if self.loading_widget is not None:
                self.loading_widget.close()
        if load_data:
            self.load_data()

    def set_blocks_thread_func(self, week, force_download):
        blocks = self.scraper.get_week_blocks(self, week, force_download)
        self.set_blocks_signal.emit(blocks, week)

    def set_blocks_slot(self, blocks, week):
        self.blocks = blocks
        self.get_week(week)

    def closeEvent(self, event):
        self.scraper.save_data()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    apply_stylesheet(app, theme='dark_green.xml')
    stylesheet = app.styleSheet()
    with open('custom.css') as file:
        app.setStyleSheet(stylesheet + file.read())
    widget.setWindowTitle("College Schedule")
    widget.setWindowIcon(QtGui.QIcon("Icons/timetable.png"))
    widget.move(QtGui.QGuiApplication.primaryScreen().geometry().center() - widget.window.rect().center())
    widget.show()
    sys.exit(app.exec_())
