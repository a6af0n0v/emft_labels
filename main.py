# The script lays out small labels on A4 page in a grid
# the label may contain datamatrix code, article number, date and lot
# User can change basic features of the layout/labels in the preferences dialog
# User preferences are persisted between sessions
# Denis Agafonov 2020/12/05

import pylibdmtx.pylibdmtx as dmtx
import shelve, os
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.Qt import QApplication, QMainWindow, QWidget, QMenu, QFormLayout, QDialog, QLineEdit, QPushButton, QSpinBox, QHBoxLayout, QComboBox, QLabel
from PyQt5.QtGui import QPicture, QPainter, QImage, QFont, QBrush, QPen
from PyQt5.QtCore import QUrl
from PyQt5 import  Qt
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView

def mmToPixels(mm):
    #converts mm to pixels
    return int(float(mm/25.4)*ppi)
def pixelsToMm(pixels):
    #converts pixels to mm
    return float(pixels/ppi*25.4)

ppi = 94            #printer resolution
mw = None           #MainWindow
label_size = (129, 55)   #size of the label in pixels
spacing = (5,5)     #spacing between labels
n_columns = 5       #number of columns of the label layout
show_alignmnet_marks = True
first_alignment_mark_position = (25, 15)  #position of the top left alignment mark
alignment_mark_size = (7, 7)
qr_size = (37,37)   #qr code size
n_rows_per_page = 17
distance_between_alignament_marks = (int(mmToPixels(185)), int(mmToPixels(270)))
first_label_offset = (30, 35)
generate_settings = {
    'defaultNumberOfLabels':10,
    'firstLabelArticleNumber': 0000,
    'weekNrYear':"40/20",
    'lotName': "X000"
}
font = {
    'family': 'Segoe UI',
    'size': 9,
    'weight': 400
}
item_positions = {
    'article': (45, 20),    #p1
    'week': (45, 50),       #p2
    'lot': (45, 35),        #p3
    'code': (5,10),         #p4
    'logo': (10,10)         #no logo anymore
}
frame_options = {
    'pen-width': 0,
    'pen-color': Qt.Qt.black,
    'radius': 5
}

def saveValues():
    #saves user preferences in shelve file parms
    with shelve.open(r'parms.dat') as config:
        config['size'] = label_size
        config['spacing'] = spacing
        config['n_columns'] = n_columns
        config['qr_size'] = qr_size
        config['offset'] = first_label_offset
        config['font'] = font
        config['item_positions'] = item_positions
        config['frame_options'] = frame_options
        config['generate_settings'] = generate_settings


def readValues():
    #reads user preferences from shelve file parms
    global label_size
    global spacing
    global n_columns
    global first_label_offset
    global qr_size
    global item_positions
    global font
    global frame_options
    global generate_settings
    print('reading config from file')
    with shelve.open(r'parms.dat') as config:
        label_size = config['size']
        spacing = config['spacing']
        n_columns = config['n_columns']
        qr_size = config['qr_size']
        first_label_offset = config['offset']
        font = config['font']
        item_positions = config['item_positions']
        frame_options = config['frame_options']
        generate_settings = config['generate_settings']


def generateCode(article, week, lot):
    #function returns QPicture object containing DataMatrix code with given article, week, lot
    toBeEncoded = 'S/N %s, Lot %s, Date %s'%(article, lot, week)
    bar = toBeEncoded.encode('utf-8')
    encoded_bar = dmtx.encode(bar)
    img = Image.frombytes('RGB', (encoded_bar.width, encoded_bar.height), encoded_bar.pixels)
    img = img.resize(qr_size)
    qimg = ImageQt(img)

    picture = QPicture()
    painter = QPainter()
    painter.begin(picture)

    if frame_options['pen-color'] != Qt.Qt.white:
        painter.setBrush(QBrush(Qt.Qt.white))
    painter.setFont(QFont(font['family'], font['size'], font['weight']))
    if frame_options['pen-color'] != Qt.Qt.white:
        old_pen = painter.pen()
        painter.setPen(QPen(frame_options['pen-color'], frame_options['pen-width']))
        painter.drawRoundedRect(0, 0, *label_size, frame_options['radius'], frame_options['radius'])
        painter.setPen(old_pen)
    painter.drawText(*item_positions['article'], "S/N " + article)
    painter.drawText(*item_positions['week'], "Date " + week)
    painter.drawText(*item_positions['lot'], "Lot " + lot)
    painter.drawImage(*item_positions['code'], qimg)

    painter.end()
    return picture


def generateFromUI():
    #event handler which is triggered when user selects 'Generate labels' menu item
    class GenerateLabelsDialog (QDialog):
        #Generate labels dialog class
        def __init__(self, p = None):
            QDialog.__init__(self, p)
            self.setWindowTitle("Generate page layout...")
            self.layout = QFormLayout()

            self.numberOfLabelsSpinBox = QSpinBox()
            self.numberOfLabelsSpinBox.setRange(1, 200)
            self.numberOfLabelsSpinBox.setValue(generate_settings['defaultNumberOfLabels'])
            self.layout.addRow("Number of labels", self.numberOfLabelsSpinBox)

            self.firstLabelArticleNumberSB = QSpinBox()
            self.firstLabelArticleNumberSB.setRange(0,9999)
            self.firstLabelArticleNumberSB.setValue(generate_settings['firstLabelArticleNumber'])
            self.layout.addRow("First label article number", self.firstLabelArticleNumberSB)

            self.weekNrYearLE = QLineEdit()
            self.weekNrYearLE.setText(generate_settings['weekNrYear'])
            self.layout.addRow("Week nr/ year", self.weekNrYearLE)

            self.lotNameLE = QLineEdit()
            self.lotNameLE.setText(generate_settings['lotName'])
            self.layout.addRow("Lot", self.lotNameLE)

            self.generatePB = QPushButton("Generate")
            self.generatePB.clicked.connect(self.onGenerate)
            self.layout.addRow("", self.generatePB)
            self.cancelPB = QPushButton("Cancel")
            self.cancelPB.clicked.connect(self.close)
            self.layout.addRow("", self.cancelPB)
            self.setLayout(self.layout)

        def onGenerate(self):
            generate_settings['defaultNumberOfLabels'] = self.numberOfLabelsSpinBox.value()
            generate_settings['firstLabelArticleNumber'] = self.firstLabelArticleNumberSB.value()
            generate_settings['weekNrYear'] = self.weekNrYearLE.text()
            generate_settings['lotName'] = self.lotNameLE.text()
            self.accept()

    generateLabelsDlg = GenerateLabelsDialog()
    if generateLabelsDlg.exec() == QDialog.Accepted:
        mw.labels = []
        saveValues()
        for i in range(generate_settings['defaultNumberOfLabels']):
            article = "%s-%d" % (generate_settings['lotName'], generate_settings['firstLabelArticleNumber']+i)
            print("Generating ", article)
            picture = generateCode(article, generate_settings['weekNrYear'], generate_settings['lotName'])
            if mw !=None:
                mw.labels.append(picture)

def drawLabels(painter, labels, _printer=None):
    #function lays out the given labels on the _printer canvas using the given painter
    #if the _printer is None, screen canvas is used
    row = 0
    column = 0
    page = [0,0]

    def drawAlignmentMarks():
        if show_alignmnet_marks==True:
            old_brush = painter.brush()
            painter.setBrush(QBrush(Qt.Qt.black))
            painter.drawEllipse(*first_alignment_mark_position, *alignment_mark_size)
            painter.drawEllipse(first_alignment_mark_position[0] + distance_between_alignament_marks[0], first_alignment_mark_position[1], *alignment_mark_size)
            painter.drawEllipse(first_alignment_mark_position[0], first_alignment_mark_position[1] + distance_between_alignament_marks[1], *alignment_mark_size)
            painter.setBrush(old_brush)
    drawAlignmentMarks()

    for label in labels:

        painter.drawPicture(first_label_offset[0] + column * (label_size[0] + spacing[0]), first_label_offset[1] + row * (label_size[1] + spacing[1]),
                            label)
        column = column + 1
        if column % n_columns == 0:
            column = 0
            row = row + 1
            if row% n_rows_per_page == 0:
                if _printer!=None:
                    page[1] = _printer.pageRect(QPrinter.DevicePixel).height()
                    _printer.newPage()
                    row = 0
                    drawAlignmentMarks()

def printCodes():
    #action which is triggered when the user selects 'Print' menu item
    if mw== None:
        raise Exception('Mainwindow is not initialized')
    else:
        print('printing...')

    printer = QPrinter()
    dlg = QPrintDialog(printer)
    if dlg.exec() == QDialog.Accepted:
        painter = QPainter()
        painter.begin(printer)
        drawLabels(painter, mw.labels, printer)
        painter.end()

class DoubleSpin(QWidget):
    #a custom widget containing 2 QSpinBoxes in a row
    #is used for pair user input (like x,y or width, height)
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        self.sbx = QSpinBox()
        self.sby = QSpinBox()
        self.sbx.setRange(0,1000)
        self.sby.setRange(0,1000)
        lb = QLabel('x')
        lb.setSizePolicy(Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Minimum)
        layout.addWidget(lb)
        self.sbx.setSizePolicy(Qt.QSizePolicy.Maximum,Qt.QSizePolicy.Maximum)
        layout.addWidget(self.sbx)
        lby = QLabel('y')
        lby.setSizePolicy(Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Minimum)
        layout.addWidget(lby)
        layout.setAlignment(Qt.Qt.AlignLeft)
        layout.addWidget(self.sby)
        self.setLayout(layout)
    def setX(self, x):
        self.sbx.setValue(x)
    def setY(self, y):
        self.sby.setValue(y)
    def getValues(self):
        return (self.sbx.value(), self.sby.value())

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent) #Qt.Qt.MSWindowsFixedSizeDialogHint
        self.labels = []
        self.logo = QImage(r'logo.PNG')


    def paintEvent(self, a0):
        QMainWindow.paintEvent(self, a0)
        painter = QPainter()
        painter.begin(self)
        if len(self.labels)>0:
            drawLabels(painter, self.labels)
        else:

            painter.drawImage(self.width()/2 - self.logo.width()/2 ,self.height()/2 - self.logo.height()/2, self.logo)
        painter.end()

def showPreferences():
    #the action is triggered when the user selects 'Preferences' menu item
    class Preview(QWidget):
        #Left side of the Preferences dialog with the sketch of the layout
        def __init__(self, parent=None):
            QWidget.__init__(self, parent)
            self.pic = QImage(r'pic1.png')
        def paintEvent(self, a0):
            QWidget.paintEvent(self, a0)
            painter = QPainter()
            painter.begin(self)
            painter.drawImage(0,0, self.pic)
            painter.end()

    class PreferencesDialog(QDialog):
        #the user preferences itself
        def __init__(self, parent=None):
            QDialog.__init__(self, parent)
            self.setWindowTitle('Preferences')
            self.resize(600,240)
            layout = QHBoxLayout()
            preview = Preview(self)
            form = QFormLayout()
            self.widthSB = QSpinBox()
            self.heightSB = QSpinBox()
            self.widthSB.setRange(1,1000)
            self.heightSB.setRange(1, 1000)
            self.widthSB.setValue(label_size[0])
            self.heightSB.setValue(label_size[1])
            form.addRow('Width', self.widthSB)
            form.addRow('Height', self.heightSB)
            self.spacingDS = DoubleSpin()
            self.spacingDS.setX(spacing[0])
            self.spacingDS.setY(spacing[1])
            form.addRow('Spacing',self.spacingDS)
            self.offsetDS = DoubleSpin()
            self.offsetDS.setX(first_label_offset[0])
            self.offsetDS.setY(first_label_offset[1])
            form.addRow('Offset', self.offsetDS)
            self.p1 = DoubleSpin()
            self.p1.setX(item_positions['article'][0])
            self.p1.setY(item_positions['article'][1])
            form.addRow('p1', self.p1)
            self.p2 = DoubleSpin()
            self.p2.setX(item_positions['week'][0])
            self.p2.setY(item_positions['week'][1])
            form.addRow('p2', self.p2)
            self.p3 = DoubleSpin()
            self.p3.setX(item_positions['lot'][0])
            self.p3.setY(item_positions['lot'][1])
            form.addRow('p3', self.p3)
            self.p4 = DoubleSpin()
            self.p4.setX(item_positions['code'][0])
            self.p4.setY(item_positions['code'][1])
            form.addRow('p4', self.p4)
            self.qr_sizeDS = DoubleSpin()
            self.qr_sizeDS.setX(qr_size[0])
            self.qr_sizeDS.setY(qr_size[1])
            form.addRow('QR size', self.qr_sizeDS)
            self.alignament_mark = DoubleSpin()
            self.alignament_mark.setX(item_positions['logo'][0]) #instead of logo, position of alignment_mark is used
            self.alignament_mark.setY(item_positions['logo'][1])
            form.addRow('Alignment mark', self.alignament_mark)

            self.numberofColumnsSB = QSpinBox()
            self.numberofColumnsSB.setRange(1, 10)
            self.numberofColumnsSB.setValue(n_columns)
            form.addRow('Number of columns', self.numberofColumnsSB)

            self.numberofRowsSB = QSpinBox()
            self.numberofRowsSB.setRange(1, 50)
            self.numberofRowsSB.setValue(n_rows_per_page)
            form.addRow('Number of rows', self.numberofRowsSB)

            self.fontSizeSB = QSpinBox()
            self.fontSizeSB.setRange(4, 25)
            self.fontSizeSB.setValue(font['size'])
            form.addRow('Font size', self.fontSizeSB)
            self.frame_visible = QComboBox()
            self.frame_visible.addItem('True')
            self.frame_visible.addItem('False')

            form.addRow('Frame visible?', self.frame_visible)
            pbOk = QPushButton('OK')
            pbOk.clicked.connect(self.accept)
            form.addRow('', pbOk)
            pbCancel = QPushButton('Cancel')
            pbCancel.clicked.connect(self.reject)
            form.addRow('', pbCancel)
            layout.addWidget(preview)
            layout.addLayout(form)
            self.setLayout(layout)

    dlg = PreferencesDialog()

    if dlg.exec() == QDialog.Accepted:
        updateValues(dlg)

def updateValues(dlg):
    #the function persists all user preferences made in dialog dlg
    #and finally saves them in shelve file
    global  label_size
    global  spacing
    global  n_columns
    global  first_label_offset
    global  qr_size
    global  item_positions
    global font
    global frame_options
    global n_rows_per_page

    label_size = (dlg.widthSB.value(), dlg.heightSB.value())
    spacing = dlg.spacingDS.getValues()
    n_columns = dlg.numberofColumnsSB.value()
    n_rows_per_page = dlg.numberofRowsSB.value()
    first_label_offset = dlg.offsetDS.getValues()
    item_positions['article'] = dlg.p1.getValues()
    item_positions['week'] = dlg.p2.getValues()
    item_positions['lot'] = dlg.p3.getValues()
    item_positions['code'] = dlg.p4.getValues()
    item_positions['logo'] = dlg.alignament_mark.getValues()
    qr_size = dlg.qr_sizeDS.getValues()
    font['size'] = dlg.fontSizeSB.value()

    if dlg.frame_visible.currentText() == 'True':
        frame_options['pen-color'] = Qt.Qt.black
    else:
        frame_options['pen-color'] = Qt.Qt.white
    saveValues()

helpdlg = None
def showQuickStart():
    global helpdlg
    helpdlg = QWebEngineView()
    url = QUrl.fromLocalFile(os.getcwd() + r"/readme.html")
    helpdlg.load(url)
    helpdlg.show()


if __name__ == '__main__':
    print('The app for printing labels on A4 paper')
    if os.path.exists(r'parms.dat.dat'):
        readValues()

    app = QApplication([])
    mw = MainWindow()
    mw.setWindowTitle('Security foils label generator')
    fileMenu = mw.menuBar().addMenu("File")
    fileMenu.addAction("Preferences...", showPreferences)
    fileMenu.addAction("Generate labels...", generateFromUI)
    fileMenu.addAction("Print...", printCodes)
    fileMenu.addAction("Close", app.quit)
    helpMenu = mw.menuBar().addMenu("Help")
    helpMenu.addAction("Quick start", showQuickStart)
    mw.resize(300,300)
    mw.show()
    app.exec()


