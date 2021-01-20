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
from qt_material import apply_stylesheet
from scraper import Scraper


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "main_window.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file, self)
        ui_file.close()
        self.data = {'notes': dict(), 'hidden': list()}
        self.week = 1
        self.sel_block = (-1, -1)
        self.group = 'WCY18IJ5S1'

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
        self.download_button.clicked.connect(lambda: self.download_data(self.group))
        self.table_widget.cellClicked.connect(self.block_clicked)
        self.table_widget.cellDoubleClicked.connect(self.block_double_clicked)
        self.group_box.currentTextChanged.connect(self.change_group)

        self.scraper = Scraper()
        self.download_data(self.group)
        self.set_groups()
        self.group_box.setCurrentIndex(self.group_box.findText(self.group))

    def set_groups(self):
        groups = self.scraper.get_groups()
        self.group_box.blockSignals(True)
        self.group_box.addItems(groups)
        self.group_box.blockSignals(False)

    def download_data(self, group):
        self.scraper.scrap(group)
        self.table_widget.clearContents()
        self.get_days()

    def get_days(self):
        today = (datetime.today().day, datetime.today().month)
        weeks = self.get_all_weeks()
        for i, week in enumerate(weeks, start=1):
            if today in week:
                self.get_week(i)
                break

    def get_all_weeks(self) -> list:
        weeks = list()
        for i in range(22):
            days = self.scraper.get_days(i)
            dates = list()
            for j in range(0, len(days), 2):
                dates += [(int(days[j]), roman.fromRoman(days[j + 1]))]
            weeks += [dates]
        return weeks

    def get_week(self, number):
        if 1 <= number <= 22:
            self.week = number
            self.note.setPlainText('')
        self.set_headers(self.scraper.get_days(number - 1))
        self.set_blocks(self.scraper.get_blocks(number))

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
                block_data = self.scraper.get_block_data(block)
                self.add_block(row, column,
                               block_data['subject'],
                               block_data['category'],
                               block_data['room'],
                               block_data['teacher'],
                               block_data['number'])
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
        if self.get_index(row, column) in self.data['notes']:
            block.setProperty('Note', 'true')
            block.setStyle(block.style())
        if self.get_index(row, column) in self.data['hidden']:
            block.setProperty('Hide', 'true')
            block.setStyle(block.style())
        block.setLayout(layout)
        block.setProperty('class', 'block')
        self.table_widget.setCellWidget(row, column, block)

    def get_index(self, row, column) -> int:
        return row + column * 7 + (self.week - 1) * 49

    def block_clicked(self, row, column):
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

    def block_double_clicked(self, row, column):
        block = self.table_widget.cellWidget(row, column)
        if block is not None:
            visible = block.property('Hide') if block.property('Hide') is not None else False
            block.setProperty('Hide', not visible)
            block.setStyle(block.style())
            children = block.findChildren(QLabel)
            for child in children:
                child.setStyle(child.style())
            if not visible:
                self.data['hidden'].append(self.get_index(row, column))
            else:
                if self.get_index(row, column) in self.data['hidden']:
                    self.data['hidden'].remove(self.get_index(row, column))

    def change_group(self, group):
        self.group = group

    def load_data(self):
        data_file = Path("schedule.data")
        if data_file.is_file():
            with open('schedule.data', 'rb') as f:
                self.data = pickle.load(f)

    def save_data(self):
        with open('schedule.data', 'wb') as f:
            pickle.dump(self.data, f)

    def load_note(self, index):
        if index in self.data['notes']:
            self.note.setPlainText(self.data['notes'][index])
        else:
            self.note.setPlainText('')

    def save_note(self):
        block = self.table_widget.cellWidget(self.sel_block[0], self.sel_block[1])
        if block is not None:
            if self.note.toPlainText() == '':
                self.data['notes'].pop(self.get_index(self.sel_block[0], self.sel_block[1]), None)
                block.setProperty('Note', 'false')
                block.setStyle(block.style())
            else:
                self.data['notes'][self.get_index(self.sel_block[0], self.sel_block[1])] = self.note.toPlainText()
                block.setProperty('Note', 'true')
                block.setStyle(block.style())

    def closeEvent(self, event):
        self.save_data()
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
