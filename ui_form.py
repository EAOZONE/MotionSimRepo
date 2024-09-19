# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDial, QGraphicsView,
    QPushButton, QScrollArea, QSizePolicy, QSlider,
    QWidget)

class Ui_Widget(object):
    def setupUi(self, Widget):
        if not Widget.objectName():
            Widget.setObjectName(u"Widget")
        Widget.resize(800, 600)
        self.pushButton = QPushButton(Widget)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(310, 400, 171, 71))
        self.graphicsView = QGraphicsView(Widget)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setGeometry(QRect(270, 210, 256, 192))
        self.scrollArea = QScrollArea(Widget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(QRect(530, 210, 171, 191))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 169, 189))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.Actuator1 = QDial(Widget)
        self.Actuator1.setObjectName(u"Actuator1")
        self.Actuator1.setGeometry(QRect(130, 250, 50, 64))
        self.Actuator2 = QDial(Widget)
        self.Actuator2.setObjectName(u"Actuator2")
        self.Actuator2.setGeometry(QRect(180, 280, 50, 64))
        self.Actuator3 = QDial(Widget)
        self.Actuator3.setObjectName(u"Actuator3")
        self.Actuator3.setGeometry(QRect(70, 280, 50, 64))
        self.pushButton_2 = QPushButton(Widget)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(100, 340, 111, 51))
        self.checkBox = QCheckBox(Widget)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setGeometry(QRect(310, 470, 171, 51))
        self.horizontalSlider = QSlider(Widget)
        self.horizontalSlider.setObjectName(u"horizontalSlider")
        self.horizontalSlider.setGeometry(QRect(110, 240, 71, 20))
        self.horizontalSlider.setOrientation(Qt.Orientation.Horizontal)

        self.retranslateUi(Widget)

        QMetaObject.connectSlotsByName(Widget)
    # setupUi

    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QCoreApplication.translate("Widget", u"Widget", None))
        self.pushButton.setText(QCoreApplication.translate("Widget", u"E-Stop", None))
        self.pushButton_2.setText(QCoreApplication.translate("Widget", u"Home", None))
        self.checkBox.setText(QCoreApplication.translate("Widget", u"Enable All", None))
    # retranslateUi

