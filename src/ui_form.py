# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDial, QFrame,
    QGraphicsView, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSlider, QVBoxLayout, QWidget)

class Ui_Widget(object):
    def setupUi(self, Widget):
        if not Widget.objectName():
            Widget.setObjectName(u"Widget")
        Widget.resize(800, 600)
        self.qGraphicsView = QGraphicsView(Widget)
        self.qGraphicsView.setObjectName(u"qGraphicsView")
        self.qGraphicsView.setGeometry(QRect(0, 0, 800, 600))
        self.qGraphicsView.setFrameShape(QFrame.Shape.NoFrame)
        self.qGraphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.qGraphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.labelActuatorControls = QLabel(Widget)
        self.labelActuatorControls.setObjectName(u"labelActuatorControls")
        self.labelActuatorControls.setGeometry(QRect(60, 190, 200, 24))
        self.labelSequences = QLabel(Widget)
        self.labelSequences.setObjectName(u"labelSequences")
        self.labelSequences.setGeometry(QRect(300, 190, 200, 24))
        self.labelAct1 = QLabel(Widget)
        self.labelAct1.setObjectName(u"labelAct1")
        self.labelAct1.setGeometry(QRect(0, 250, 180, 18))
        self.labelAct2 = QLabel(Widget)
        self.labelAct2.setObjectName(u"labelAct2")
        self.labelAct2.setGeometry(QRect(100, 305, 180, 18))
        self.angle2 = QSlider(Widget)
        self.angle2.setObjectName(u"angle2")
        self.angle2.setGeometry(QRect(100, 325, 140, 50))
        self.angle2.setMinimum(-45)
        self.angle2.setMaximum(45)
        self.angle2.setOrientation(Qt.Orientation.Horizontal)
        self.labelAct3 = QLabel(Widget)
        self.labelAct3.setObjectName(u"labelAct3")
        self.labelAct3.setGeometry(QRect(240, 430, 180, 18))
        self.scrollArea = QScrollArea(Widget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(QRect(300, 230, 200, 200))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 198, 198))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.homeButton = QPushButton(Widget)
        self.homeButton.setObjectName(u"homeButton")
        self.homeButton.setGeometry(QRect(550, 190, 175, 75))
        self.checkBox = QCheckBox(Widget)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setGeometry(QRect(550, 290, 175, 75))
        self.pushButton = QPushButton(Widget)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(550, 390, 175, 75))
        self.titleLabel = QLabel(Widget)
        self.titleLabel.setObjectName(u"titleLabel")
        self.titleLabel.setGeometry(QRect(0, 80, 800, 31))
        self.logo = QLabel(Widget)
        self.logo.setObjectName(u"logo")
        self.logo.setGeometry(QRect(0, 0, 63, 20))
        self.angle1 = QSlider(Widget)
        self.angle1.setObjectName(u"angle1")
        self.angle1.setGeometry(QRect(40, 280, 18, 160))
        self.angle1.setMinimum(-45)
        self.angle1.setMaximum(45)
        self.angle1.setOrientation(Qt.Orientation.Vertical)
        self.angle3 = QDial(Widget)
        self.angle3.setObjectName(u"angle3")
        self.angle3.setGeometry(QRect(240, 450, 128, 128))
        self.angle3.setMaximum(180)

        self.retranslateUi(Widget)

        QMetaObject.connectSlotsByName(Widget)
    # setupUi

    def retranslateUi(self, Widget):
        Widget.setWindowTitle(QCoreApplication.translate("Widget", u"Motion Simulator User Interface", None))
        self.labelActuatorControls.setText(QCoreApplication.translate("Widget", u"Actuator Controls:", None))
        self.labelSequences.setText(QCoreApplication.translate("Widget", u"Sequences:", None))
        self.labelAct1.setText(QCoreApplication.translate("Widget", u"Actuator 1 Angle:", None))
        self.labelAct2.setText(QCoreApplication.translate("Widget", u"Actuator 2 Angle:", None))
        self.labelAct3.setText(QCoreApplication.translate("Widget", u"Actuator 3 Angle:", None))
        self.homeButton.setText(QCoreApplication.translate("Widget", u"Reset Actuator Angles", None))
        self.checkBox.setText(QCoreApplication.translate("Widget", u"Enable All Motors", None))
        self.pushButton.setText(QCoreApplication.translate("Widget", u"E-Stop", None))
        self.titleLabel.setText(QCoreApplication.translate("Widget", u"Motion Simulator Design Team", None))
        self.logo.setText("")
    # retranslateUi

