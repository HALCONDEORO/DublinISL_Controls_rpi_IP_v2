#!/usr/bin/env python3
#--------------------------------------------------------
#
#Name: LBD-Sign Language Camera Controls - IP RPI Version
#
#Author: Isaac Urwin - IP & ISL revision by Simon Laban
#
#Date: November 2025
#
#Camera facing platform prefered address 1 - Default IP 192.168.1.251/24 stored in PTZ1IP.txt [ID 1 (81)]
#Camera facing audience prefered address 2 - Default IP 192.168.1.252/24 stored in PTZ2IP.txt [ID 2 (82)]
#
#--------------------------------------------------------
import os
import sys
import socket
import binascii
import PyQt5

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QLabel, QMessageBox, QHBoxLayout, QButtonGroup, QInputDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSlot

#os.chdir ("/home/pi/BSL_Controls")

IPAddress= open('PTZ1IP.txt','r').read()
IPAddress2= open('PTZ2IP.txt','r').read()
Cam1ID= open('Cam1ID.txt','r').read()
Cam2ID= open('Cam2ID.txt','r').read()
Contact= open('Contact.txt', 'r').read()
ButtonColor= "black"

#PTZ Address Check
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    s.connect((IPAddress, 5678))
    Cam1DataString= binascii.unhexlify(Cam1ID+"090400FF")
    s.send(Cam1DataString)
    reply = s.recv(131072)
    Cam1Check= "Green"
except (socket.timeout, socket.error, OSError):
    Cam1Check= "Red"

try:
    global Cam2Check
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    s.connect((IPAddress2, 5678))
    Cam2DataString= binascii.unhexlify(Cam2ID+"090400FF")
    s.send(Cam2DataString)
    reply = s.recv(131072)
    Cam2Check= "Green"
except (socket.timeout, socket.error, OSError):
    Cam2Check= "Red"


class MainWindow(QMainWindow):
            
    def __init__(self):
        super().__init__()
        self.WindowtTitle = 'Eccles Camera Controls'
        self.left = 0
        self.top = 0
        self.width = 1280
        self.height = 1024  
            
    #def initUI(self):
        self.setGeometry(self.left, self.top, self.width, self.height)
        pixmap = QPixmap("Background_ISL_v1.png")
        background = QLabel(self)
        background.setPixmap(pixmap)
        background.move(0,0)
        background.resize(1280,1024)
                       
#Camera Control Buttons
        Home = QPushButton('HOME', self)
        Home.setGeometry(1025,640,120,120)
        Home.clicked.connect(self.HomeButton)
        Home.setStyleSheet("background-color: blue; border: 5px yellow; border-radius: 60px; font: bold 20px; color: white")
        
        UpLeft = QPushButton(self)
        UpLeft.setGeometry(905,520,120,120)
        UpLeft.pressed.connect(self.UpLeft)
        UpLeft.released.connect(self.Stop)
        UpLeft.setStyleSheet("background-image: url(UpLeftArrow_120.png); border: none")

        Up = QPushButton(self)
        Up.setGeometry(1025,520,120,120)
        Up.pressed.connect(self.Up)
        Up.released.connect(self.Stop)
        Up.setStyleSheet("background-image: url(UpArrow_120.png); border: none")

        UpRight = QPushButton(self)
        UpRight.setGeometry(1145,520,120,120)
        UpRight.pressed.connect(self.UpRight)
        UpRight.released.connect(self.Stop)
        UpRight.setStyleSheet("background-image: url(UpRightArrow_120.png); border: none")
       
        Left = QPushButton(self)
        Left.setGeometry(905,640,120,120)
        Left.pressed.connect(self.Left)
        Left.released.connect(self.Stop)
        Left.setStyleSheet("background-image: url(LeftArrow_120.png); border: none")
        
        Right = QPushButton(self)
        Right.setGeometry(1145,640,120,120)
        Right.pressed.connect(self.Right)
        Right.released.connect(self.Stop)       
        Right.setStyleSheet("background-image: url(RightArrow_120.png); border: none")

        DownLeft = QPushButton(self)
        DownLeft.setGeometry(905,760,120,120)
        DownLeft.pressed.connect(self.DownLeft)
        DownLeft.released.connect(self.Stop)
        DownLeft.setStyleSheet("background-image: url(DownLeftArrow_120.png); border: none")
       
        Down = QPushButton(self)
        Down.setGeometry(1025,760,120,120)
        Down.pressed.connect(self.Down)
        Down.released.connect(self.Stop)
        Down.setStyleSheet("background-image: url(DownArrow_120.png); border: none")

        DownRight = QPushButton(self)
        DownRight.setGeometry(1145,760,120,120)
        DownRight.pressed.connect(self.DownRight)
        DownRight.released.connect(self.Stop)
        DownRight.setStyleSheet("background-image: url(DownRightArrow_120.png); border: none")
       
        ZoomIn = QPushButton(self)
        ZoomIn.setGeometry(1135,370,120,120)
        ZoomIn.pressed.connect(self.ZoomIn)
        ZoomIn.released.connect(self.ZoomStop)
        ZoomIn.setStyleSheet("background-image: url(ZoomIn_120.png); border: none")

        ZoomOut = QPushButton(self)
        ZoomOut.setGeometry(915,370,120,120)
        ZoomOut.pressed.connect(self.ZoomOut)
        ZoomOut.released.connect(self.ZoomStop)
        ZoomOut.setStyleSheet("background-image: url(ZoomOut_120.png); border: none")
        
#Configuration buttons                
        Cam1Address = QPushButton('Platform [Cam1]  -  '+IPAddress, self)
        Cam1Address.setGeometry(905,960,320,20)
        Cam1Address.setStyleSheet("font: bold 15px; color:"+Cam1Check)
        Cam1Address.clicked.connect(self.PTZ1Address)

        Cam2Address = QPushButton('Comments [Cam2]  -  '+IPAddress2, self)
        Cam2Address.setGeometry(905,980,320,20)
        Cam2Address.setStyleSheet("font: bold 15px; color:"+Cam2Check)
        Cam2Address.clicked.connect(self.PTZ2Address)

        PTZ1ID = QPushButton(' ID-'+Cam1ID, self)
        PTZ1ID.setGeometry(1225,960,40,20)
        PTZ1ID.setStyleSheet("font: bold 15px; color:"+Cam1Check)
        PTZ1ID.clicked.connect(self.PTZ1IDchange)

        PTZ2ID = QPushButton(' ID-'+Cam2ID, self)
        PTZ2ID.setGeometry(1225,980,40,20)
        PTZ2ID.setStyleSheet("font: bold 15px; color:"+Cam2Check)
        PTZ2ID.clicked.connect(self.PTZ2IDchange)

        Version = QPushButton('ISL Cam Controls Seat V2 - 1280x1024', self)
        Version.setGeometry(905,1000,360,20)
        Version.setStyleSheet("background-color: lightgrey; font: 15px; color: black; border: none")
        Version.clicked.connect(self.Quit)

        Help = QPushButton('?', self)
        Help.setGeometry(1225,1000,40,20)
        Help.setStyleSheet("background-color: lightgrey; font: 15px; color: black; border: none")
        Help.clicked.connect(self.HelpMsg)

#Preset Call Buttons
       
        Preset1 = QPushButton('Chairman', self)
        Preset1.resize(85,60)
        Preset1.move(400,80)
        Preset1.setStyleSheet("background-color: rgba(50,255,0,200); border: 0px solid black; border-radius: 5px; font: 14px; font-weight: bold; color: black")
        Preset1.clicked.connect(self.Go1)      
    
        Preset2 = GoButton('Left', self)
        Preset2.resize(85,60)
        Preset2.move(250,60)
        Preset2.setStyleSheet("background-color: rgba(50,255,0,200); border: 0px solid black; border-radius: 5px; font: 14px; font-weight: bold; color: black")
        Preset2.clicked.connect(self.Go2)

        Preset3 = GoButton('Right', self)
        Preset3.resize(85,60)
        Preset3.move(550,60)
        Preset3.setStyleSheet("background-color: rgba(50,255,0,200); border: 0px solid black; border-radius: 5px; font: 14px; font-weight: bold; color: black")
        Preset3.clicked.connect(self.Go3)
        
        Preset4 = GoButton('4', self)
        Preset4.move(20,240)
        Preset4.clicked.connect(self.Go4)
 
        Preset5 = GoButton('5', self)
        Preset5.move(60,250)
        Preset5.clicked.connect(self.Go5)
 
        Preset6 = GoButton('6', self)
        Preset6.move(95,260)
        Preset6.clicked.connect(self.Go6)
 
        Preset7 = GoButton('7', self)
        Preset7.move(132,270)
        Preset7.clicked.connect(self.Go7)
 
        Preset8 = GoButton('8', self)
        Preset8.move(307,275)
        Preset8.clicked.connect(self.Go8)
 
        Preset9 = GoButton('9', self)
        Preset9.move(345,275)
        Preset9.clicked.connect(self.Go9)
 
        Preset10 = GoButton('10', self)
        Preset10.move(383,275)
        Preset10.clicked.connect(self.Go10)
 
        Preset11 = GoButton('11', self)
        Preset11.move(421,275)
        Preset11.clicked.connect(self.Go11)
 
        Preset12 = GoButton('12', self)
        Preset12.move(459,275)
        Preset12.clicked.connect(self.Go12)
 
        Preset13 = GoButton('13', self)
        Preset13.move(497,275)
        Preset13.clicked.connect(self.Go13)
 
        Preset14 = GoButton('14', self)
        Preset14.move(535,275)
        Preset14.clicked.connect(self.Go14)
 
        Preset15 = GoButton('15', self)
        Preset15.move(700,270)
        Preset15.clicked.connect(self.Go15)
 
        Preset16 = GoButton('16', self)
        Preset16.move(738,260)
        Preset16.clicked.connect(self.Go16)
 
        Preset17 = GoButton('17', self)
        Preset17.move(775,250)
        Preset17.clicked.connect(self.Go17)
 
        Preset18 = GoButton('18', self)
        Preset18.move(810,240)
        Preset18.clicked.connect(self.Go18)
 
        Preset19 = GoButton('19', self)
        Preset19.move(20,315)
        Preset19.clicked.connect(self.Go19)
 
        Preset20 = GoButton('20', self)
        Preset20.move(60,325)
        Preset20.clicked.connect(self.Go20)
 
        Preset21 = GoButton('21', self)
        Preset21.move(95,335)
        Preset21.clicked.connect(self.Go21)
 
        Preset22 = GoButton('22', self)
        Preset22.move(132,345)
        Preset22.clicked.connect(self.Go22)
 
        Preset23 = GoButton('23', self)
        Preset23.move(307,347)
        Preset23.clicked.connect(self.Go23)
 
        Preset24 = GoButton('24', self)
        Preset24.move(345,347)
        Preset24.clicked.connect(self.Go24)
 
        Preset25 = GoButton('25', self)
        Preset25.move(383,347)
        Preset25.clicked.connect(self.Go25)
 
        Preset26 = GoButton('26', self)
        Preset26.move(421,347)
        Preset26.clicked.connect(self.Go26)
 
        Preset27 = GoButton('27', self)
        Preset27.move(459,347)
        Preset27.clicked.connect(self.Go27)
 
        Preset28 = GoButton('28', self)
        Preset28.move(497,347)
        Preset28.clicked.connect(self.Go28)
 
        Preset29 = GoButton('29', self)
        Preset29.move(535,347)
        Preset29.clicked.connect(self.Go29)
 
        Preset30 = GoButton('30', self)
        Preset30.move(700,345)
        Preset30.clicked.connect(self.Go30)
 
        Preset31 = GoButton('31', self)
        Preset31.move(738,335)
        Preset31.clicked.connect(self.Go31)
 
        Preset32 = GoButton('32', self)
        Preset32.move(775,325)
        Preset32.clicked.connect(self.Go32)
 
        Preset33 = GoButton('33', self)
        Preset33.move(810,315)
        Preset33.clicked.connect(self.Go33)
 
        Preset34 = GoButton('34', self)
        Preset34.move(20,390)
        Preset34.clicked.connect(self.Go34)
 
        Preset35 = GoButton('35', self)
        Preset35.move(60,400)
        Preset35.clicked.connect(self.Go35)
 
        Preset36 = GoButton('36', self)
        Preset36.move(95,410)
        Preset36.clicked.connect(self.Go36)
 
        Preset37 = GoButton('37', self)
        Preset37.move(132,420)
        Preset37.clicked.connect(self.Go37)
 
        Preset38 = GoButton('38', self)
        Preset38.move(307,416)
        Preset38.clicked.connect(self.Go38)
 
        Preset39 = GoButton('39', self)
        Preset39.move(345,416)
        Preset39.clicked.connect(self.Go39)
 
        Preset40 = GoButton('40', self)
        Preset40.move(383,416)
        Preset40.clicked.connect(self.Go40)
 
        Preset41 = GoButton('41', self)
        Preset41.move(421,416)
        Preset41.clicked.connect(self.Go41)
 
        Preset42 = GoButton('42', self)
        Preset42.move(459,416)
        Preset42.clicked.connect(self.Go42)
 
        Preset43 = GoButton('43', self)
        Preset43.move(497,416)
        Preset43.clicked.connect(self.Go43)
 
        Preset44 = GoButton('44', self)
        Preset44.move(535,416)
        Preset44.clicked.connect(self.Go44)
 
        Preset45 = GoButton('45', self)
        Preset45.move(700,420)
        Preset45.clicked.connect(self.Go45)

        Preset46 = GoButton('46', self)
        Preset46.move(738,410)
        Preset46.clicked.connect(self.Go46)
 
        Preset47 = GoButton('47', self)
        Preset47.move(775,400)
        Preset47.clicked.connect(self.Go47)
 
        Preset48 = GoButton('48', self)
        Preset48.move(810,390)
        Preset48.clicked.connect(self.Go48)
 
        Preset49 = GoButton('49', self)
        Preset49.move(20,465)
        Preset49.clicked.connect(self.Go49)
 
        Preset50 = GoButton('50', self)
        Preset50.move(60,475)
        Preset50.clicked.connect(self.Go50)
 
        Preset51 = GoButton('51', self)
        Preset51.move(95,485)
        Preset51.clicked.connect(self.Go51)
 
        Preset52 = GoButton('52', self)
        Preset52.move(132,495)
        Preset52.clicked.connect(self.Go52)
 
        Preset53 = GoButton('53', self)
        Preset53.move(307,485)
        Preset53.clicked.connect(self.Go53)
 
        Preset54 = GoButton('54', self)
        Preset54.move(345,485)
        Preset54.clicked.connect(self.Go54)
 
        Preset55 = GoButton('55', self)
        Preset55.move(383,485)
        Preset55.clicked.connect(self.Go55)
 
        Preset56 = GoButton('56', self)
        Preset56.move(421,485)
        Preset56.clicked.connect(self.Go56)
 
        Preset57 = GoButton('57', self)
        Preset57.move(459,485)
        Preset57.clicked.connect(self.Go57)
 
        Preset58 = GoButton('58', self)
        Preset58.move(497,485)
        Preset58.clicked.connect(self.Go58)
 
        Preset59 = GoButton('59', self)
        Preset59.move(535,485)
        Preset59.clicked.connect(self.Go59)

        Preset60 = GoButton('60', self)
        Preset60.move(700,495)
        Preset60.clicked.connect(self.Go60)
 
        Preset61 = GoButton('61', self)
        Preset61.move(738,485)
        Preset61.clicked.connect(self.Go61)
 
        Preset62 = GoButton('62', self)
        Preset62.move(775,475)
        Preset62.clicked.connect(self.Go62)
 
        Preset63 = GoButton('63', self)
        Preset63.move(810,465)
        Preset63.clicked.connect(self.Go63)
 
        Preset64 = GoButton('64', self)
        Preset64.move(20,540)
        Preset64.clicked.connect(self.Go64)
 
        Preset65 = GoButton('65', self)
        Preset65.move(60,550)
        Preset65.clicked.connect(self.Go65)
 
        Preset66 = GoButton('66', self)
        Preset66.move(95,560)
        Preset66.clicked.connect(self.Go66)
 
        Preset67 = GoButton('67', self)
        Preset67.move(132,570)
        Preset67.clicked.connect(self.Go67)
 
        Preset68 = GoButton('68', self)
        Preset68.move(307,550)
        Preset68.clicked.connect(self.Go68)
 
        Preset69 = GoButton('69', self)
        Preset69.move(345,550)
        Preset69.clicked.connect(self.Go69)
 
        Preset70 = GoButton('70', self)
        Preset70.move(383,550)
        Preset70.clicked.connect(self.Go70)
 
        Preset71 = GoButton('71', self)
        Preset71.move(421,550)
        Preset71.clicked.connect(self.Go71)
 
        Preset72 = GoButton('72', self)
        Preset72.move(459,550)
        Preset72.clicked.connect(self.Go72)
 
        Preset73 = GoButton('73', self)
        Preset73.move(497,550)
        Preset73.clicked.connect(self.Go73)

        Preset74 = GoButton('74', self)
        Preset74.move(535,550)
        Preset74.clicked.connect(self.Go74)
 
        Preset75 = GoButton('75', self)
        Preset75.move(700,570)
        Preset75.clicked.connect(self.Go75)
 
        Preset76 = GoButton('76', self)
        Preset76.move(738,560)
        Preset76.clicked.connect(self.Go76)
 
        Preset77 = GoButton('77', self)
        Preset77.move(775,550)
        Preset77.clicked.connect(self.Go77)
 
        Preset78 = GoButton('78', self)
        Preset78.move(810,540)
        Preset78.clicked.connect(self.Go78)
 
        Preset79 = GoButton('79', self)
        Preset79.move(20,615)
        Preset79.clicked.connect(self.Go79)
 
        Preset80 = GoButton('80', self)
        Preset80.move(60,625)
        Preset80.clicked.connect(self.Go80)
 
        Preset81 = GoButton('81', self)
        Preset81.move(95,635)
        Preset81.clicked.connect(self.Go81)
 
        Preset82 = GoButton('82', self)
        Preset82.move(132,645)
        Preset82.clicked.connect(self.Go82)
 
        Preset83 = GoButton('83', self)
        Preset83.move(307,618)
        Preset83.clicked.connect(self.Go83)
 
        Preset84 = GoButton('84', self)
        Preset84.move(345,618)
        Preset84.clicked.connect(self.Go84)
 
        Preset85 = GoButton('85', self)
        Preset85.move(383,618)
        Preset85.clicked.connect(self.Go85)
 
        Preset86 = GoButton('86', self)
        Preset86.move(421,618)
        Preset86.clicked.connect(self.Go86)
 
        Preset87 = GoButton('87', self)
        Preset87.move(459,618)
        Preset87.clicked.connect(self.Go87)

        Preset88 = GoButton('88', self)
        Preset88.move(497,618)
        Preset88.clicked.connect(self.Go88)
 
        Preset89 = GoButton('89', self)
        Preset89.move(535,618)
        Preset89.clicked.connect(self.Go89)
 
        Preset90 = GoButton('90', self)
        Preset90.move(700,645)
        Preset90.clicked.connect(self.Go90)
 
        Preset91 = GoButton('91', self)
        Preset91.move(738,635)
        Preset91.clicked.connect(self.Go91)
 
        Preset92 = GoButton('92', self)
        Preset92.move(775,625)
        Preset92.clicked.connect(self.Go92)
 
        Preset93 = GoButton('93', self)
        Preset93.move(810,615)
        Preset93.clicked.connect(self.Go93)

        Preset94 = GoButton('94', self)
        Preset94.move(20,690)
        Preset94.clicked.connect(self.Go94)
 
        Preset95 = GoButton('95', self)
        Preset95.move(60,700)
        Preset95.clicked.connect(self.Go95)
 
        Preset96 = GoButton('96', self)
        Preset96.move(95,710)
        Preset96.clicked.connect(self.Go96)
 
        Preset97 = GoButton('97', self)
        Preset97.move(132,720)
        Preset97.clicked.connect(self.Go97)
 
        Preset98 = GoButton('98', self)
        Preset98.move(309,686)
        Preset98.clicked.connect(self.Go98)
 
        Preset99 = GoButton('99', self)
        Preset99.move(347,686)
        Preset99.clicked.connect(self.Go99)

        Preset100 = GoButton('100', self)
        Preset100.move(383,686)
        Preset100.clicked.connect(self.Go100)
 
        Preset101 = GoButton('101', self)
        Preset101.move(421,686)
        Preset101.clicked.connect(self.Go101)
 
        Preset102 = GoButton('102', self)
        Preset102.move(459,686)
        Preset102.clicked.connect(self.Go102)
 
        Preset103 = GoButton('103', self)
        Preset103.move(497,686)
        Preset103.clicked.connect(self.Go103)
 
        Preset104 = GoButton('104', self)
        Preset104.move(535,686)
        Preset104.clicked.connect(self.Go104)

        Preset105 = GoButton('105', self)
        Preset105.move(705,722)
        Preset105.clicked.connect(self.Go105)

        Preset106 = GoButton('106', self)
        Preset106.move(743,712)
        Preset106.clicked.connect(self.Go106)

        Preset107 = GoButton('107', self)
        Preset107.move(780,702)
        Preset107.clicked.connect(self.Go107)
 
        Preset108 = GoButton('108', self)
        Preset108.move(815,692)
        Preset108.clicked.connect(self.Go108)
 
        Preset109 = GoButton('109', self)
        Preset109.move(20,765)
        Preset109.clicked.connect(self.Go109)

        Preset110 = GoButton('110', self)
        Preset110.move(60,775)
        Preset110.clicked.connect(self.Go110)

        Preset111 = GoButton('111', self)
        Preset111.move(95,785)
        Preset111.clicked.connect(self.Go111)

        Preset112 = GoButton('112', self)
        Preset112.move(132,795)
        Preset112.clicked.connect(self.Go112)
 
        Preset113 = GoButton('113', self)
        Preset113.move(309,757)
        Preset113.clicked.connect(self.Go113)
 
        Preset114 = GoButton('114', self)
        Preset114.move(347,757)
        Preset114.clicked.connect(self.Go114)

        Preset115 = GoButton('115', self)
        Preset115.move(385,757)
        Preset115.clicked.connect(self.Go115)

        Preset116 = GoButton('116', self)
        Preset116.move(423,757)
        Preset116.clicked.connect(self.Go116)

        Preset117 = GoButton('117', self)
        Preset117.move(461,757)
        Preset117.clicked.connect(self.Go117)
 
        Preset118 = GoButton('118', self)
        Preset118.move(499,757)
        Preset118.clicked.connect(self.Go118)
 
        Preset119 = GoButton('119', self)
        Preset119.move(537,757)
        Preset119.clicked.connect(self.Go119)

        Preset120 = GoButton('120', self)
        Preset120.move(707,797)
        Preset120.clicked.connect(self.Go120)

        Preset121 = GoButton('121', self)
        Preset121.move(745,787)
        Preset121.clicked.connect(self.Go121)

        Preset122 = GoButton('122', self)
        Preset122.move(782,777)
        Preset122.clicked.connect(self.Go122)

        Preset123 = GoButton('123', self)
        Preset123.move(817,767)
        Preset123.clicked.connect(self.Go123)

        Preset124 = GoButton('124', self)
        Preset124.move(12,981)
        Preset124.clicked.connect(self.Go124)
 
        Preset125 = GoButton('125', self)
        Preset125.move(73,981)
        Preset125.clicked.connect(self.Go125)
 
        Preset126 = GoButton('126', self)
        Preset126.move(126,981)
        Preset126.clicked.connect(self.Go126)

        Preset127 = GoButton('127', self)
        Preset127.move(283,981)
        Preset127.clicked.connect(self.Go127)

        Preset128 = GoButton('128', self)
        Preset128.move(322,981)
        Preset128.clicked.connect(self.Go128)
        
        #Preset129 = GoButton('129', self)
        #Preset129.move(708,970)
        #Preset129.clicked.connect(self.Go129)
        #Preset130 = GoButton('130', self)
        #Preset130.move(768,970)
        #Preset130.clicked.connect(self.Go130)
        #Preset131 = GoButton('131', self)
        #Preset131.move(824,970)
        #Preset131.clicked.connect(self.Go131)
        
#Camera Selection
        self.Cam1 = QPushButton('Platform', self)
        self.Cam1.setGeometry(905,60,180,80)
        self.Cam1.setCheckable(True)
        self.Cam1.setAutoExclusive(True)        
        self.Cam1.setChecked(True)
        self.Cam1.setToolTip('Select Platform Camera')
        self.Cam1.setStyleSheet("QPushButton{background-color: green; border: 3px solid black; font: bold 20px; color: white}QPushButton:Checked{background-color: red; font: bold 20px; color: white}")
        
        self.Cam2 = QPushButton('Comments', self)
        self.Cam2.setGeometry(1085,60,180,80)
        self.Cam2.setCheckable(True)
        self.Cam2.setAutoExclusive(True)
        self.Cam2.setToolTip('Select Comments Camera')
        self.Cam2.setStyleSheet("QPushButton{background-color: green; border: 3px solid black; font: bold 20px; color: white}QPushButton:Checked{background-color: red; font: bold 20px; color: white}")
        
        Camgroup = QButtonGroup(self)
        Camgroup.addButton(self.Cam1)
        Camgroup.addButton(self.Cam2)

#Preset/Set Selection
        self.Set1 = QPushButton('Call', self)
        self.Set1.setGeometry(40,5,100,30)
        self.Set1.setCheckable(True)
        self.Set1.setAutoExclusive(True)        
        self.Set1.setChecked(True)
        self.Set1.setToolTip('Select Preset')
        self.Set1.setStyleSheet("QPushButton{background-color: green; border: 3px solid black; font: bold 20px; color: white}QPushButton:Checked{background-color: red; font: bold 20px; color: white}")
        
        self.Set2 = QPushButton('Set', self)
        self.Set2.setGeometry(725,5,100,30)
        self.Set2.setCheckable(True)
        self.Set2.setAutoExclusive(True)
        self.Set2.setToolTip('Select Comments Camera')
        self.Set2.setStyleSheet("QPushButton{background-color: green; border: 3px solid black; font: bold 20px; color: white}QPushButton:Checked{background-color: red; font: bold 20px; color: white}")
                
        Setgroup = QButtonGroup(self)
        Setgroup.addButton(self.Set1)
        Setgroup.addButton(self.Set2)

#Speed Selection
        self.SpeedSlow = QPushButton('SLOW', self)
        self.SpeedSlow.setGeometry(905,190,180,80)
        self.SpeedSlow.setCheckable(True)
        self.SpeedSlow.setAutoExclusive(True)
        self.SpeedSlow.setChecked(True)
        self.SpeedSlow.setToolTip('Set Camera PTZ Speed to SLOW')
        self.SpeedSlow.setStyleSheet("QPushButton{background-color: green; border: 3px solid black; font: 20px; color: white}QPushButton:Checked{background-color: red; font: bold 20px; color: white}")
        
        self.SpeedFast = QPushButton('FAST', self)
        self.SpeedFast.setGeometry(1085,190,180,80)
        self.SpeedFast.setCheckable(True)
        self.SpeedFast.setAutoExclusive(True)
        self.SpeedFast.setToolTip('Set Camera PTZ Speed to FAST')
        self.SpeedFast.setStyleSheet("QPushButton{background-color: green; border: 3px solid black; font: 20px; color: white}QPushButton:Checked{background-color: red; font: bold 20px; color: white}")
        
        Speedgroup = QButtonGroup(self)
        Speedgroup.addButton(self.SpeedSlow)
        Speedgroup.addButton(self.SpeedFast)

#Labels     
        Presets = QLabel('Camera Presets', self)
        Presets.setGeometry(140,5,585,30)
        Presets.setAlignment(QtCore.Qt.AlignCenter)
        Presets.setStyleSheet("background-color: blue; border: 2px solid black; font: bold 20px; color: white")
        
        CamControls = QLabel('Camera Controls', self)
        CamControls.setGeometry(905,280,360,30)
        CamControls.setAlignment(QtCore.Qt.AlignCenter)
        CamControls.setStyleSheet("background-color: blue; border: 2px solid black; font: bold 20px; color: white")
        
        CamSelect = QLabel('Camera Selection', self)
        CamSelect.setGeometry(905,20,360,30)
        CamSelect.setAlignment(QtCore.Qt.AlignCenter)
        CamSelect.setStyleSheet("background-color: blue; border: 2px solid black; font: bold 20px; color: white")

        SpeedSelect = QLabel('PTZ Speed', self)
        SpeedSelect.setGeometry(905,150,360,30)
        SpeedSelect.setAlignment(QtCore.Qt.AlignCenter)
        SpeedSelect.setStyleSheet("background-color: blue; border: 2px solid black; font: bold 20px; color: white")
     
            
    @pyqtSlot()
        
#Error Checks and default socket details
    def ErrorCapture(self):
        print()
        
    def ErrorCapture1(self):
        QMessageBox.warning(self, 'Platform PTZ Control', 'Check That Platform Camera IP Address is set to  '+IPAddress+'  and ID 1')
                               
    def ErrorCapture2(self):
        QMessageBox.warning(self, 'Comments PTZ Control', 'Check That Comments Camera IP Address is set to  '+IPAddress2+'  and ID 2')
        
    def Cam1Call(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((IPAddress, 5678))
            s.send(Cam1DataString)
            reply = s.recv(131072)
        except (socket.timeout, OSError):
            self.ErrorCapture1()

    def Cam1aCall(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((IPAddress, 5678))
            s.send(Cam1aDataString)
            reply = s.recv(131072)
        except (socket.timeout, OSError):
            self.ErrorCapture1()

    def Cam2Call(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((IPAddress2, 5678))
            s.send(Cam2DataString)
            reply = s.recv(131072)
        except (socket.timeout, OSError):
            self.ErrorCapture2() 

    def Cam2aCall(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((IPAddress2, 5678))
            s.send(Cam2aDataString)
            reply = s.recv(131072)
        except (socket.timeout, OSError):
            self.ErrorCapture2()
            
    def Cam1Stop(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((IPAddress, 5678))
            s.send(Cam1DataString)
            reply = s.recv(131072)
        except (socket.timeout, OSError):
            print()
    
    def Cam2Stop(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((IPAddress2, 5678))
            s.send(Cam2DataString)
            reply = s.recv(131072)
        except (socket.timeout, OSError):
            print()

#Camera Controls        
    def HomeButton(self):
        if self.Cam1.isChecked():
            global Cam1DataString
            Cam1DataString= binascii.unhexlify(Cam1ID+"010604FF")
            self.Cam1Call()
        elif self.Cam2.isChecked():              
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"010604FF")
            self.Cam2Call()
            
    def UpLeft(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01060104040101ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01060110100101ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01060104040101ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01060110100101ff")
                self.Cam2aCall()     
                
    def Up(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01060100040301FF")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01060100100301FF")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01060100040301FF")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01060100100301FF")
                self.Cam2aCall() 
                
    def UpRight(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01060104040201ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01060110100201ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01060104040201ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01060110100201ff")
                self.Cam2aCall()
                    
                
    def Left(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01060104000103ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01060110000103ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01060104000103ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01060110000103ff")
                self.Cam2aCall()
                    
                
    def Right(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01060104000203ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01060110000203ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01060104000203ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01060110000203ff")
                self.Cam2aCall()
                    
            
    def DownLeft(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01060104040102ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01060110100102ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01060104040102ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01060110100102ff")
                self.Cam2aCall()
                
                
    def Down(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01060100040302ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01060100100302ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01060100040302ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01060100100302ff")
                self.Cam2aCall()
                
                
    def DownRight(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01060104040202ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01060110100202ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01060104040202ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01060110100202ff")
                self.Cam2aCall()
                
                
    def Stop(self):
        if self.Cam1.isChecked():
            global Cam1DataString
            Cam1DataString= binascii.unhexlify(Cam1ID+"01060100000303FF")
            self.Cam1Stop()
        elif self.Cam2.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01060100000303FF")
            self.Cam2Stop()
                                    
    def ZoomIn(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01040722ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01040726ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01040722ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01040726ff")
                self.Cam2aCall()
                                
    def ZoomOut(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam1DataString
                Cam1DataString= binascii.unhexlify(Cam1ID+"01040732ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked(): 
                global Cam1aDataString
                Cam1aDataString= binascii.unhexlify(Cam1ID+"01040736ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():  
                global Cam2DataString
                Cam2DataString= binascii.unhexlify(Cam2ID+"01040732ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked(): 
                global Cam2aDataString
                Cam2aDataString= binascii.unhexlify(Cam2ID+"01040736ff")
                self.Cam2aCall()
                                
    def ZoomStop(self):
        if self.Cam1.isChecked():
            global Cam1DataString
            Cam1DataString= binascii.unhexlify(Cam1ID+"01040700ff")
            self.Cam1Stop()
        elif self.Cam2.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01040700ff")
            self.Cam2Stop()
                        
#Call Presets       
    def Go1(self):
        if self.Set1.isChecked():
           global Cam1DataString
           Cam1DataString= binascii.unhexlify(Cam1ID+"01043f0201ff")
           self.Cam1Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record Chairman Position', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam1DataString= binascii.unhexlify(Cam1ID+"01043f0101ff")
                self.Cam1Call()
      
    def Go2(self):
        if self.Set1.isChecked():
            global Cam1DataString
            Cam1DataString= binascii.unhexlify(Cam1ID+"01043f0202ff")
            self.Cam1Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record Platform Left', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam1DataString= binascii.unhexlify(Cam1ID+"01043f0102ff")
                self.Cam1Call()
        
    def Go3(self):
        if self.Set1.isChecked():
            global Cam1DataString
            Cam1DataString= binascii.unhexlify(Cam1ID+"01043f0203ff")
            self.Cam1Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record Platform Right', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam1DataString= binascii.unhexlify(Cam1ID+"01043f0103ff")
                self.Cam1Call()
        
    def Go4(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0204ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P4', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0104ff")
                self.Cam2Call()
        
    def Go5(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0205ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P5', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0105ff")
                self.Cam2Call()
    
    def Go6(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0206ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P6', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0106ff")
                self.Cam2Call()
        
    def Go7(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0207ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P7', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0107ff")
                self.Cam2Call()
        
    def Go8(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0208ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P8', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0108ff")
                self.Cam2Call()
        
    def Go9(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0209ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P9', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0109ff")
                self.Cam2Call()
        
    def Go10(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f020Aff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P10', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f010Aff")
                self.Cam2Call()

    def Go11(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f020Bff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P11', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f010Bff")
                self.Cam2Call()

    def Go12(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f020Cff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P12', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f010Cff")
                self.Cam2Call()

    def Go13(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f020Dff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P13', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f010Dff")
                self.Cam2Call()

    def Go14(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f020Eff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P14', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f010Eff")
                self.Cam2Call()

    def Go15(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f020Fff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P15', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f010Fff")
                self.Cam2Call()

    def Go16(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0210ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P16', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0110ff")
                self.Cam2Call()

    def Go17(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0211ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P17', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0111ff")
                self.Cam2Call()

    def Go18(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0212ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P18', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0112ff")
                self.Cam2Call()

    def Go19(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0213ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P19', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0113ff")
                self.Cam2Call()

    def Go20(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0214ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P20', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0114ff")
                self.Cam2Call()

    def Go21(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0215ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P21', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0115ff")
                self.Cam2Call()

    def Go22(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0216ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P22', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0116ff")
                self.Cam2Call()

    def Go23(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0217ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P23', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0117ff")
                self.Cam2Call()

    def Go24(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0218ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P24', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0118ff")
                self.Cam2Call()

    def Go25(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0219ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P25', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0119ff")
                self.Cam2Call()

    def Go26(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f021Aff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P26', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f011Aff")
                self.Cam2Call()

    def Go27(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f021Bff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P27', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f011Bff")
                self.Cam2Call()

    def Go28(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f021Cff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P28', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f011Cff")
                self.Cam2Call()

    def Go29(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f021Dff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P29', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f011Dff")
                self.Cam2Call()

    def Go30(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f021Eff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P30', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f011Eff")
                self.Cam2Call()

    def Go31(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f021Fff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P31', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f011Fff")
                self.Cam2Call()

    def Go32(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0220ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P32', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0120ff")
                self.Cam2Call()

    def Go33(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0221ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P33', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0121ff")
                self.Cam2Call()

    def Go34(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0222ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P34', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0122ff")
                self.Cam2Call()

    def Go35(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0223ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P35', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0123ff")
                self.Cam2Call()

    def Go36(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0224ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P36', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0124ff")
                self.Cam2Call()
            
    def Go37(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0225ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P37', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0125ff")
                self.Cam2Call()

    def Go38(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0226ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P38', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0126ff")
                self.Cam2Call()
                
    def Go39(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0227ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P39', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0127ff")
                self.Cam2Call()

    def Go40(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0228ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P40', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0128ff")
                self.Cam2Call()

    def Go41(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0229ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P41', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0129ff")
                self.Cam2Call()
    def Go42(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f022Aff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P42', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f012Aff")
                self.Cam2Call()

    def Go43(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f022Bff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P43', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f012Bff")
                self.Cam2Call()
    def Go44(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f022Cff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P44', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f012Cff")
                self.Cam2Call()

    def Go45(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f022Dff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P45', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f012Dff")
                self.Cam2Call()

    def Go46(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f022Eff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P46', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f012Eff")
                self.Cam2Call()

    def Go47(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f022Fff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P47', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f012Fff")
                self.Cam2Call()

    def Go48(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0230ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P48', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0130ff")
                self.Cam2Call()

    def Go49(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0231ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P49', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0131ff")
                self.Cam2Call()

    def Go50(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0232ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P50', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0132ff")
                self.Cam2Call()

    def Go51(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0233ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P51', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0133ff")
                self.Cam2Call()

    def Go52(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0234ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P52', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0134ff")
                self.Cam2Call()

    def Go53(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0235ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P53', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0135ff")
                self.Cam2Call()

    def Go54(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0236ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P54', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0136ff")
                self.Cam2Call()

    def Go55(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0237ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P55', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0137ff")
                self.Cam2Call()

    def Go56(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0238ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P56', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0138ff")
                self.Cam2Call()

    def Go57(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0239ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P57', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0139ff")
                self.Cam2Call()

    def Go58(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f023Aff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P58', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f013Aff")
                self.Cam2Call()

    def Go59(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f023Bff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P59', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f013Bff")
                self.Cam2Call()

    def Go60(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f023Cff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P60', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f013Cff")
                self.Cam2Call()

    def Go61(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f023Dff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P61', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f013Dff")
                self.Cam2Call()

    def Go62(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f023Eff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P62', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f013Eff")
                self.Cam2Call()
                
    def Go63(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f023Fff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P63', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f013Fff")
                self.Cam2Call()

    def Go64(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0240ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P64', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0140ff")
                self.Cam2Call()

    def Go65(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0241ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P65', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0141ff")
                self.Cam2Call()

    def Go66(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0242ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P66', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0142ff")
                self.Cam2Call()

    def Go67(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0243ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P67', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0143ff")
                self.Cam2Call()

    def Go68(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0244ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P68', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0144ff")
                self.Cam2Call()

    def Go69(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0245ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P69', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0145ff")
                self.Cam2Call()

    def Go70(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0246ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P70', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0146ff")
                self.Cam2Call()

    def Go71(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0247ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P71', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0147ff")
                self.Cam2Call()

    def Go72(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0248ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P72', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0148ff")
                self.Cam2Call()

    def Go73(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0249ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P73', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0149ff")
                self.Cam2Call()

    def Go74(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f024Aff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P74', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f014Aff")
                self.Cam2Call()

    def Go75(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f024Bff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P75', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f014Bff")
                self.Cam2Call()

    def Go76(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f024Cff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P76', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f014Cff")
                self.Cam2Call()

    def Go77(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f024Dff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P77', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f014Dff")
                self.Cam2Call()

    def Go78(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f024Eff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P78', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f014Eff")
                self.Cam2Call()

    def Go79(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f024Fff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P79', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f014Fff")
                self.Cam2Call()

    def Go80(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0250ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P80', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0150ff")
                self.Cam2Call()

    def Go81(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0251ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P81', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0151ff")
                self.Cam2Call()

    def Go82(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0252ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P82', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0152ff")
                self.Cam2Call()

    def Go83(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0253ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P83', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0153ff")
                self.Cam2Call()

    def Go84(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0254ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P84', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0154ff")
                self.Cam2Call()

    def Go85(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0255ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P85', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0155ff")
                self.Cam2Call()

    def Go86(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0256ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P86', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0156ff")
                self.Cam2Call()

    def Go87(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0257ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P87', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0157ff")
                self.Cam2Call()

    def Go88(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0258ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P88', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0158ff")
                self.Cam2Call()

    def Go89(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0259ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P89', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0159ff")
                self.Cam2Call()

    def Go90(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f028Cff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P90', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f018Cff")
                self.Cam2Call()

    def Go91(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0258Dff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P91', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f018Dff")
                self.Cam2Call()

    def Go92(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f028Eff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P92', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f018Eff")
                self.Cam2Call()

    def Go93(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f028Fff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P93', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f018Fff")
                self.Cam2Call()

    def Go94(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0290ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P94', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0190ff")
                self.Cam2Call()

    def Go95(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0291ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P95', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0191ff")
                self.Cam2Call()

    def Go96(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0292ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P96', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0192ff")
                self.Cam2Call()
                
    def Go97(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0293ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P97', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0193ff")
                self.Cam2Call()

    def Go98(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0294ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P98', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0194ff")
                self.Cam2Call()

    def Go99(self):
        #Using Preset 140-149 range due to possible conflict in Visca
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0295ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P99', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0195ff")
                self.Cam2Call()

    def Go100(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0264ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P100', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0164ff")
                self.Cam2Call()

    def Go101(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0265ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P101', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0165ff")
                self.Cam2Call()

    def Go102(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0266ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P102', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0166ff")
                self.Cam2Call()

    def Go103(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0267ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P103', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0167ff")
                self.Cam2Call()

    def Go104(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0268ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P104', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0168ff")
                self.Cam2Call()

    def Go105(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0269ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P105', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0169ff")
                self.Cam2Call()

    def Go106(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f026Aff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P106', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f016Aff")
                self.Cam2Call()

                
    def Go107(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f026Bff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P107', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f016Bff")
                self.Cam2Call()

                
    def Go108(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f026Cff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P108', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f016Cff")
                self.Cam2Call()

                
    def Go109(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f026Dff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P109', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f016Dff")
                self.Cam2Call()
                
                
    def Go110(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f026Eff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P110', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f016Eff")
                self.Cam2Call()
                
                
    def Go111(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f026Fff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P111', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f016Fff")
                self.Cam2Call()
                
                
    def Go112(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0270ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P112', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0170ff")
                self.Cam2Call()
                
                
    def Go113(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0271ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P113', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0171ff")
                self.Cam2Call()
                
                
    def Go114(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0272ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P114', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0172ff")
                self.Cam2Call()
                
                
    def Go115(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0273ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P115', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0173ff")
                self.Cam2Call()
                
                
    def Go116(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0274ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P116', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0174ff")
                self.Cam2Call()
                
                
    def Go117(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0275ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P117', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0175ff")
                self.Cam2Call()
                
                
    def Go118(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0276ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P118', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0176ff")
                self.Cam2Call()
                
                
    def Go119(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0277ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P119', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0177ff")
                self.Cam2Call()
                
                
    def Go120(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0278ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P120', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0178ff")
                self.Cam2Call()
                
                
    def Go121(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0279ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P121', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0179ff")
                self.Cam2Call()
                
                
    def Go122(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f027Aff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P122', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f017Aff")
                self.Cam2Call()
                
                
    def Go123(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f027Bff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P123', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f017Bff")
                self.Cam2Call()
                
                
    def Go124(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f027Cff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P124', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f017Cff")
                self.Cam2Call()
                
                
    def Go125(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f027Dff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P125', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f017Dff")
                self.Cam2Call()
                
                
    def Go126(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f027Eff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P126', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f017Eff")
                self.Cam2Call()
                
                
    def Go127(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f027Fff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P127', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f017Fff")
                self.Cam2Call()
                
                
    def Go128(self):
        if self.Set1.isChecked():
            global Cam2DataString
            Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0280ff")
            self.Cam2Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record P128', "Are You Sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam2DataString= binascii.unhexlify(Cam2ID+"01043f0180ff")
                self.Cam2Call()

    def Quit(self):
        sys.exit()
        
    def PTZ1Address(self):
        IPChange= QMessageBox()
        result=IPChange.warning(self, 'Platform PTZ Control', 'Do you want to change which IP address will be used to control camera?', QMessageBox.Ok, QMessageBox.Cancel)
        if result == 1024:
            IP1update= QInputDialog()
            text, updateresult=IP1update.getText(self, 'Platform PTZ Control', 'Change IP Address to control Platform Camera - Current Address is: ', text=IPAddress)
            PTZ1IP=open("PTZ1IP.txt", "w+")
            PTZ1IP.write(text)
            PTZ1IP.close()
            os.execv(sys.executable, ['python3']+sys.argv)
        print(result)

    def PTZ2Address(self):
        IPChange= QMessageBox()
        result=IPChange.warning(self, 'Comments PTZ Control', 'Do you want to change which IP address will be used to control camera?', QMessageBox.Ok, QMessageBox.Cancel)
        if result == 1024:
            IP2update= QInputDialog()
            text, updateresult=IP2update.getText(self, 'Comments PTZ Control', 'Change IP Address to control Comments Camera - Current Address is: ', text=IPAddress2)
            PTZ2IP=open("PTZ2IP.txt", "w+")
            PTZ2IP.write(text)
            PTZ2IP.close()
            os.execv(sys.executable, ['python3']+sys.argv)
        print(result)

    def PTZ1IDchange(self):
        IDChange= QMessageBox()
        result=IDChange.warning(self, 'Platform PTZ Control', 'Do you want to change which ID will be used to control camera?', QMessageBox.Ok, QMessageBox.Cancel)
        if result == 1024:
            ID1update= QInputDialog()
            text, updateresult=ID1update.getText(self, 'Platform PTZ Control', 'Change ID to control Platform Camera - Current Address is: ', text=Cam1ID)
            PTZCam1ID=open("Cam1ID.txt", "w+")
            PTZCam1ID.write(text)
            PTZCam1ID.close()
            os.execv(sys.executable, ['python3']+sys.argv)
        print(result)

    def PTZ2IDchange(self):
        IDChange= QMessageBox()
        result=IDChange.warning(self, 'Platform PTZ Control', 'Do you want to change which ID will be used to control camera?', QMessageBox.Ok, QMessageBox.Cancel)
        if result == 1024:
            ID1update= QInputDialog()
            text, updateresult=ID1update.getText(self, 'Platform PTZ Control', 'Change ID to control Platform Camera - Current Address is: ', text=Cam2ID)
            PTZCam2ID=open("Cam2ID.txt", "w+")
            PTZCam2ID.write(text)
            PTZCam2ID.close()
            os.execv(sys.executable, ['python3']+sys.argv)
        print(result)

    def HelpMsg(self):
        HelpM= QMessageBox()
        result=HelpM.warning(self, 'For Technical Assistance', Contact, QMessageBox.Ok)
        if result == 1024:
            print(result) 
        
#Record Presets         
    

class GoButton(QPushButton):

    def __init__(self, Text, parent = MainWindow):
        super(GoButton, self).__init__(parent)
        self.setupbtn(Text)

    def setupbtn(self, Text):
        self.setText(Text)
        self.resize(35,35)
        #self.setStyleSheet("background-color: rgba(50,255,0,200); border: 0px solid black; border-radius: 5px; font: 14px; font-weight: bold; color: black")
        self.setStyleSheet("background-color: rgba(0,0,0,10); border: 0px solid black; border-radius: 5px; font: 14px; font-weight: bold; color:"+ButtonColor)

class RecButton(QPushButton):
    def __init__(self, Text, parent = MainWindow):
        super(RecButton, self).__init__(parent)
        self.setupbtn(Text)

    def setupbtn(self, Text):
        self.setText(Text)
        self.resize(85,20)
        self.setStyleSheet("border: 0px solid black; border-radius: 5px; font: 11px; font-weight: bold")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    #ex.show()
    ex.showFullScreen()
    sys.exit(app.exec_())
