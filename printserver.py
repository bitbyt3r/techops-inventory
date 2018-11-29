import sys
import os
import io
import time
import win32print
import win32ui
import win32con
import threading
from PIL import Image, ImageWin, ImageQt
from PyQt5 import QtCore, QtGui, QtWidgets, QtPrintSupport
from PyQt5.QtGui import QColor, QPainter, QFont, QBitmap, QImage, QPen
from PyQt5.QtCore import QThread, pyqtSignal, QSizeF, Qt, QBuffer
from cloudant.client import CouchDB

DEFAULT_TEXT = {
    "font": "Helvetica",
    "size": 0,
    "x": 0,
    "y": 0,
    "width": 1,
    "height": 1,
    "text": "Placeholder",
    "align": "center"
}

running = True
renderLock = threading.Lock()

class DBThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        def format(data):
            document = {
                "lines": [
                    [0.2,0.125,0.2,0.875],
                    [0,0.875,1,0.875],
                    [0.5,0.875,0.5,1],
                ],
                "text": [
                    {
                        "x": 0,
                        "y": 0,
                        "width": 1,
                        "height": 0.125,
                        "text": data["department"]
                    },
                    {
                        "x": 0.525,
                        "y": 0.875,
                        "width": 0.45,
                        "height": 0.125,
                        "text": data["date"]
                    },
                    {
                        "x": 0.025,
                        "y": 0.875,
                        "width": 0.45,
                        "height": 0.125,
                        "text": data["bin"]
                    }
                ]
            }
            n = 8
            if len(data["items"]) > n:
                n = len(data["items"])
            for i in range(n):
                if i < len(data["items"]):
                    document["text"].append({
                        "x": 0,
                        "y": 0.125+0.75/n*i,
                        "width": 0.2,
                        "height": 0.75/n,
                        "text": data["items"][i][0]
                    })
                    document["text"].append({
                        "x": 0.2,
                        "y": 0.125+0.75/n*i,
                        "width": 0.8,
                        "height": 0.75/n,
                        "text": data["items"][i][1]
                    })
                document["lines"].append([0,0.125+0.75/n*i,1,0.125+0.75/n*i])
            
            for idx in range(len(document["text"])):
                defaults = dict(DEFAULT_TEXT)
                text = document["text"][idx]
                defaults.update(document["text"][idx])
                document["text"][idx] = defaults
            self.signal.emit((document, data['copies']))
        client = CouchDB("printer", "FEEDMEPAPER", url="http://localhost:5984", connect=True)
        session = client.session()
        if not 'magfest' in client.all_dbs():
            client.create_database('magfest')
        magfest = client['magfest']
                
        since = 0
        while running:
            changes = magfest.changes(since=since, feed='continuous')
            for change in changes:
                if 'deleted' in change:
                    if change['deleted']:
                        continue
                document = magfest[change['id']]
                document.fetch()
                if 'print_status' in document.keys():
                    if document['print_status'] == "pending":
                        print("Printing {}".format(document['label']['bin']))
                        format(document)
                        document['print_status'] = "printed"
                        document.save()
            since = changes.last_seq
            time.sleep(1)

        client.disconnect()
        return

class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.document = {"lines": [], "text": []}
        self.setWindowTitle('Label Printer Daemon')
        self.dbThread = DBThread()
        self.dbThread.signal.connect(self.handlePrint)
        
        self.size = 807, 1199
        self.resize(*self.size)

        self.dbThread.start()

    def paintEvent(self, event):
        black, white = QColor(0,0,0), QColor(255,255,255)
        paint = QPainter(self)
        paint.setRenderHint(QPainter.Antialiasing, False)
        paint.setRenderHint(QPainter.TextAntialiasing, False)
        paint.setRenderHint(QPainter.HighQualityAntialiasing, False)
        paint.setBrush(white)
        paint.setPen(white)
        paint.drawRect(0,0,self.size[0], self.size[1])

        pen = QPen()
        pen.setWidth(2)
        paint.setPen(pen)
        paint.setBrush(black)

        for line in self.document['lines']:
            paint.drawLine(line[0]*self.size[0], line[1]*self.size[1], line[2]*self.size[0], line[3]*self.size[1])
        for text in self.document['text']:
            if not text['text']:
                continue
            flags = 0
            if text['align'] == "center":
                flags |= Qt.AlignCenter
            else:
                flags |= Qt.AlignLeft
            if text['size'] == 0:
                fits = True
                last_size = 1
                current_size = 1
                while fits:
                    last_size = current_size
                    current_size += 1
                    paint.setFont(QFont(text['font'], current_size))
                    rect = paint.boundingRect(text['x']*self.size[0], text['y']*self.size[1], text['width']*self.size[0], text['height']*self.size[1], flags, text['text'])
                    if rect.width() >= text['width']*self.size[0] or rect.height() >= text['height']*self.size[1]:
                        fits = False
                paint.setFont(QFont(text['font'], last_size))
            else:
                paint.setFont(QFont(text['font'], text['size']))
            paint.drawText(text['x']*self.size[0], text['y']*self.size[1], text['width']*self.size[0], text['height']*self.size[1], flags, text['text'])
        paint.end()

    def handlePrint(self, data):
        with renderLock:
            self.document, copies = data
            self.update()
            printerName = win32print.GetDefaultPrinter()
            deviceContext = win32ui.CreateDC()
            deviceContext.CreatePrinterDC(printerName)
            pix = self.grab()
            bmp = QImage(pix)
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            bmp.save(buffer, "BMP")
            img = Image.open(io.BytesIO(buffer.data()))
            deviceContext.StartDoc("Inventory Label")
            for i in range(copies):
                deviceContext.StartPage()
                dib = ImageWin.Dib(img)
                dib.draw(deviceContext.GetHandleOutput(), (0,0,self.size[0],self.size[1]))
                deviceContext.EndPage()
            deviceContext.EndDoc()
            deviceContext.DeleteDC()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    res = app.exec_()
    running = False
    sys.exit(res)