from pathlib import WindowsPath
import sys
import os
import math
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/pyG5")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtGui import QKeySequence, QAction

from pyG5.pyG5View import pyG5HSIWidget, g5Width, g5Height

def reciprocal(heading):
    if heading < 180:
        return heading + 180
    else:
        return heading - 180

def getWCA(course, tas, winddir, windspeed):
    windangle = math.radians(winddir-course)
    xwc = math.sin(windangle)*windspeed
    wca = math.degrees(math.atan(xwc/tas))
    return round(wca)

def normalize(heading):
    if heading > 360:
        return heading-360
    if heading < 0:
        return heading+360
    return heading

class HoldingSim:

    def nextCallback(self):

        if self.solutionVisible:
            self.refresh()
            self.solutionVisible = False
        else:
            self.showSolution()
            self.solutionVisible = True

    def showSolution(self):
        self.solutionLabel.setText(self.solution)

    def getEntry(self, angle, direction):
        if angle <= 70 or angle >= 290:
            return "direct"

        if direction:        
            if angle > 70 and angle <= 180:
                return "parallel"
            if angle > 180 and angle <= 250:
                return "offset"
            if angle > 250 and angle <= 290: 
                return "special direct"
        else:
            if angle > 70 and angle <= 110:
                return "special direct"
            if angle > 110 and angle < 180:
                return "offset"
            if angle > 180 and angle < 290: 
                return "parallel"


    def refresh(self):
        radial = random.randint(0, 35) * 10
        direction = random.randint(0, 1)
        winddir = random.uniform(0.0, 359.0)
        qdr = random.uniform(0.0, 359.0)
        heading = reciprocal(round(qdr))
        outboundcourse = radial
        windspeed = random.uniform(5.0, 25.0)

        track = heading-getWCA(heading, 120, winddir, windspeed)
        wca = getWCA(outboundcourse, 120, winddir, windspeed)

        outboundwindangle = math.radians(winddir-outboundcourse)
        xwc = math.sin(outboundwindangle)*windspeed
        twc_hwc = math.cos(outboundwindangle)*windspeed

        outboundtime = 60+round(twc_hwc)
        outboundheading = outboundcourse + 3*wca    

        self.HSI.nav1crs(reciprocal(radial))
        self.HSI.windDirection(winddir)
        self.HSI.windSpeed(windspeed/1.94384)
        self.HSI.magHeading(heading)
        self.HSI.bearing1avail(True)
        self.HSI.bearing1(reciprocal(qdr))
        self.HSI.headingBug(heading)
        self.HSI.groundTrack(track)

        task = "radial: {:03d}\n".format(radial)
        task += "qdr: {:03d}\n".format(round(qdr))
        task += "turns: " + ("left" if direction else "right") + "\n"
        task += "wind: " + str(round(winddir)) + " at " + str(round(windspeed)) + "\n"

        self.taskLabel.setText(task)
        
        angle = qdr-radial
        angle = angle if angle > 0 else angle+360

        entry = self.getEntry(angle, direction)

        self.solution = ""
        self.solution += "Entry: " + entry+ "\n"

        if entry == "offset":
            entrycourse = (outboundcourse+30 if direction else outboundcourse-30)
            entrycourse = normalize(entrycourse)
            self.solution += "   Entry course {:03d}\n".format(entrycourse)

            entryheading = entrycourse+2*getWCA(entrycourse, 120, winddir, windspeed)
            entryheading = normalize(entryheading)
            self.solution += "   Entry heading (2xWCA) {:03d}\n".format(entryheading)

        
        if entry == "parallel":
            entrycourse = outboundcourse
            self.solution += "   Entry course {:03d}\n".format(entrycourse)

            entryheading = entrycourse+getWCA(entrycourse, 120, winddir, windspeed)
            entryheading = normalize(entryheading)
            self.solution += "   Entry heading (1xWCA) {:03d}\n".format(entryheading)

        self.solution += "Inbound course: {:03d}\n".format(reciprocal(outboundcourse))
        self.solution += "Outbound heading: {:03d}\n".format(round(outboundheading))
        self.solution += "Outbound time: " + str(round(outboundtime)) + "\n"

        if xwc < 0:
            self.solution += "Crosswind component is: " + str(abs(round(xwc))) + " L" + "\n"
        else:
            self.solution += "Crosswind component is: " + str(abs(round(xwc)))+ " R"+ "\n"

        if (twc_hwc < 0):
            self.solution += "Headwind component is: " + str(-round(twc_hwc)) + "\n"
        else:
            self.solution += "Tailwind component is: " + str(round(twc_hwc)) + "\n"

        self.solutionLabel.setText("")
       

    def __init__(self):

        self.app = QApplication(sys.argv)

        self.window = QMainWindow()

        self.window.resize(750, 500)
        self.window.move(0, 0)
        self.window.setWindowTitle("Holding Sim")
        file_menu = QMenu("&File", self.window)

        quitAction = QAction("&Quit", self.window)
        quitAction.setShortcut(QKeySequence("Ctrl+w"))
        quitAction.triggered.connect(self.window.close)
        file_menu.addAction(quitAction)
        
        quitAction = QAction("&Next", self.window)
        quitAction.setShortcut(QKeySequence("space"))
        quitAction.triggered.connect(self.nextCallback)
        file_menu.addAction(quitAction)

        menuBar = self.window.menuBar()
        menuBar.addMenu(file_menu)

        hlayout = QHBoxLayout()
        mainWidget = QWidget()
        mainWidget.setLayout(hlayout)

        labelWidget = QWidget(self.window)
        labelLayout = QVBoxLayout()
        labelWidget.setLayout(labelLayout)
        labelWidget.setFixedWidth(200)
        labelWidget.setMinimumHeight(300)
        
        self.taskLabel = QLabel(self.window)
        self.taskLabel.setWordWrap(True)
        labelLayout.addWidget(self.taskLabel)

        self.solutionLabel = QLabel(self.window)
        self.solutionLabel.setWordWrap(True)
        labelLayout.addWidget(self.solutionLabel)

        labelLayout.addStretch()

        vlayout = QVBoxLayout()

        hlayout.addLayout(vlayout)
        self.HSI = pyG5HSIWidget()
        hlayout.addWidget(self.HSI)
        hlayout.addWidget(labelWidget)
        
        self.solutionVisible = False
        self.refresh()        

        self.window.setCentralWidget(mainWidget)
        # Show window
        self.window.show()

        sys.exit(self.app.exec())


if __name__ == "__main__":

    h = HoldingSim()