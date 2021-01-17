import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QTextEdit, QPushButton
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from scrapy.crawler import CrawlerProcess
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


def onBtnClicked():
    print('pushbutton clicked')


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "MainWindow.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file, self)
        ui_file.close()

        self.textEdit = self.window.findChild(QTextEdit, 'textEdit')
        self.pushButton = self.window.findChild(QPushButton, 'pushButton')

        out = crawl(ScheduleSpider)
        print(out)
        self.textEdit.setText(out[0])
        self.pushButton.clicked.connect(onBtnClicked)


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
