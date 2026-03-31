#!/usr/bin/env python3
#--------------------------------------------------------
#
#Name: LBD-Sign Language Camera Controls - IP RPI Version
#
#Author: Isaac Urwin - IP & ISL revision by Simon Laban
#
#Date: November 2025 / Updated March 2026
#
#Changes v3:
#  - Added Session Management: Start Session / End Session buttons (top-left)
#    Start: Power ON both cameras, wait 8s, move both to Home
#    End:   Power OFF (standby) both cameras
#  - Added Focus & Exposure controls (right panel, below Camera Controls):
#    Auto Focus / One Push AF / Manual Focus
#    Brightness Up / Brightness Down / Backlight toggle (ON/OFF)
#
#Camera facing platform prefered address 1 - Default IP 172.16.1.11 stored in PTZ1IP.txt [ID 1 (81)]
#Camera facing audience prefered address 2 - Default IP 172.16.1.12 stored in PTZ2IP.txt [ID 2 (82)]
#
#--------------------------------------------------------
import os
import sys
import socket
import binascii
import PyQt5

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow, QPushButton,
                              QLabel, QMessageBox, QHBoxLayout, QButtonGroup, QInputDialog)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSlot, Qt

#os.chdir ("/home/pi/BSL_Controls")

with open('PTZ1IP.txt', 'r') as f:
    IPAddress = f.read().strip()
with open('PTZ2IP.txt', 'r') as f:
    IPAddress2 = f.read().strip()
with open('Cam1ID.txt', 'r') as f:
    Cam1ID = f.read().strip()
with open('Cam2ID.txt', 'r') as f:
    Cam2ID = f.read().strip()
with open('Contact.txt', 'r') as f:
    Contact = f.read().strip()
ButtonColor = "black"

# Initialise global DataStrings to avoid NameError before first use
Cam1DataString  = binascii.unhexlify(Cam1ID  + "01060100000303FF")  # Stop command
Cam1aDataString = binascii.unhexlify(Cam1ID  + "01060100000303FF")
Cam2DataString  = binascii.unhexlify(Cam2ID  + "01060100000303FF")
Cam2aDataString = binascii.unhexlify(Cam2ID  + "01060100000303FF")

#PTZ Address Check
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    s.connect((IPAddress, 5678))
    Cam1DataString = binascii.unhexlify(Cam1ID + "090400FF")
    s.send(Cam1DataString)
    reply = s.recv(131072)
    Cam1Check = "Green"
except (socket.timeout, socket.error, OSError):
    Cam1Check = "Red"

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    s.connect((IPAddress2, 5678))
    Cam2DataString = binascii.unhexlify(Cam2ID + "090400FF")
    s.send(Cam2DataString)
    reply = s.recv(131072)
    Cam2Check = "Green"
except (socket.timeout, socket.error, OSError):
    Cam2Check = "Red"

# VISCA preset number mapping
# Presets 4-89:  direct hex conversion
# Presets 90-99: mapped to 0x8C-0x95 (140-149) to avoid VISCA conflict
# Presets 100-128: direct hex conversion
PRESET_MAP = {}
for _i in range(4, 90):
    PRESET_MAP[_i] = f"{_i:02X}"
for _i in range(90, 100):
    PRESET_MAP[_i] = f"{0x8C + (_i - 90):02X}"
for _i in range(100, 129):
    PRESET_MAP[_i] = f"{_i:02X}"


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.WindowtTitle = 'Eccles Camera Controls'
        self.left   = 0
        self.top    = 0
        self.width  = 1920
        self.height = 1080
        self.setWindowTitle(self.WindowtTitle)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Track backlight state per camera
        self.backlight_on = {1: False, 2: False}

        screen = QApplication.primaryScreen().geometry()

        pixmap = QPixmap("Background_ISL_v2.jpg")
        scaled_pixmap = pixmap.scaled(
            self.width, self.height,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        background = QLabel(self)
        background.setPixmap(scaled_pixmap)
        background.setGeometry(0, -30, self.width, self.height)
        background.lower()

        # ── Seat positions ────────────────────────────────────────────────────
        seat_positions = {
            # Fila 1
            4: (70,210),   5: (131,210),  6: (192,210),  7: (253,210),
            8: (479,210),  9: (540,210), 10: (601,210), 11: (662,210),
           12: (722,210), 13: (783,210), 14: (844,210),
           15:(1070,210), 16:(1130,210), 17:(1191,210), 18:(1252,210),
            # Fila 2
           19: (70,295), 20: (131,295), 21: (192,295), 22: (253,295),
           23:(479,295), 24: (540,295), 25: (601,295), 26: (662,295),
           27:(722,295), 28: (783,295), 29: (844,295),
           30:(1070,295), 31:(1130,295), 32:(1191,295), 33:(1252,295),
            # Fila 3
           34: (70,382), 35: (131,382), 36: (192,382), 37: (253,382),
           38:(479,382), 39: (540,382), 40: (601,382), 41: (662,382),
           42:(723,382), 43: (783,382), 44: (844,382),
           45:(1070,382), 46:(1130,382), 47:(1191,382), 48:(1252,382),
            # Fila 4
           49: (70,465), 50: (131,465), 51: (192,465), 52: (253,465),
           53:(479,465), 54: (540,465), 55: (601,465), 56: (662,465),
           57:(722,465), 58: (783,465), 59: (844,465),
           60:(1070,465), 61:(1130,465), 62:(1191,465), 63:(1252,465),
            # Fila 5
           64: (70,550), 65: (131,550), 66: (192,550), 67: (253,550),
           68:(479,550), 69: (540,550), 70: (601,550), 71: (662,550),
           72:(722,550), 73: (783,550), 74: (844,550),
           75:(1070,550), 76:(1130,550), 77:(1191,550), 78:(1252,550),
            # Fila 6
           79: (70,635), 80: (131,635), 81: (192,635), 82: (253,635),
           83:(479,635), 84: (540,635), 85: (601,635), 86: (662,635),
           87:(722,635), 88: (783,635), 89: (844,635),
           90:(1070,635), 91:(1130,635), 92:(1191,635), 93:(1252,635),
            # Fila 7
           94: (70,720), 95: (131,720), 96: (192,720), 97: (253,720),
           98:(479,720), 99: (540,720),100: (601,720),101: (662,720),
          102:(722,720),103: (783,720),104: (844,720),
          105:(1070,720),106:(1130,720),107:(1191,720),108:(1252,720),
            # Fila 8
          109: (70,805),110: (131,805),111: (192,805),112: (253,805),
          113:(479,805),114: (540,805),115: (601,805),116: (662,805),
          117:(722,805),118: (783,805),119: (844,805),
          120:(1070,805),121:(1130,805),122:(1191,805),123:(1252,805),
            # Fila 9
          124:(108,975),125:(201,975),126:(481,975),127:(578,975),
            # Wheelchair
          128:(150,110),
        }

        # ── Platform preset buttons ───────────────────────────────────────────
        Preset1 = QPushButton('Chairman', self)
        Preset1.resize(110, 110)
        Preset1.move(623, 35)
        Preset1.setStyleSheet("background-color: rgba(0,0,0,0); font: 14px; font-weight: bold; color: black; padding-top: 70px")
        Preset1.clicked.connect(self.Go1)

        Preset2 = GoButton('Left', self)
        Preset2.resize(110, 110)
        Preset2.move(460, 35)
        Preset2.setStyleSheet("background-color: rgba(0,0,0,0); font: 14px; font-weight: bold; color: black; padding-top: 70px")
        Preset2.clicked.connect(self.Go2)

        Preset3 = GoButton('Right', self)
        Preset3.resize(110, 110)
        Preset3.move(803, 35)
        Preset3.setStyleSheet("background-color: rgba(0,0,0,0); font: 14px; font-weight: bold; color: black; padding-top: 70px")
        Preset3.clicked.connect(self.Go3)

        # ── Seat buttons ─────────────────────────────────────────────────────
        for seat_number in range(4, 129):
            if seat_number not in seat_positions:
                continue
            x, y = seat_positions[seat_number]
            button = GoButton(str(seat_number), self)
            button.move(x, y)
            button.clicked.connect(lambda checked=False, n=seat_number: self.go_to_preset(n))
            setattr(self, f"Seat{seat_number}", button)

        # ── SESSION MANAGEMENT — top-left corner (single toggle button) ─────
        # session_active: False = cameras OFF/standby, True = cameras ON
        self.session_active = False

        self.BtnSession = QPushButton('⏻', self)
        self.BtnSession.setGeometry(10, 10, 50, 50)
        self.BtnSession.setToolTip('Start Session: Power ON both cameras and go Home')
        self.BtnSession.setStyleSheet(
            "QPushButton{background-color: #8b1a1a; border: 2px solid #5a0d0d; "
            "font: bold 26px; color: white; border-radius: 25px}"
            "QPushButton:pressed{background-color: #5a0d0d}")
        self.BtnSession.clicked.connect(self.ToggleSession)

        # Small status label sits to the right of the button
        self.SessionStatus = QLabel('OFF', self)
        self.SessionStatus.setGeometry(68, 22, 60, 20)
        self.SessionStatus.setStyleSheet("font: bold 12px; color: #8b1a1a")

        # ── RIGHT PANEL — Camera Selection ───────────────────────────────────
        self.Cam1 = QPushButton('Platform', self)
        self.Cam1.setGeometry(1500, 60, 180, 70)
        self.Cam1.setCheckable(True)
        self.Cam1.setAutoExclusive(True)
        self.Cam1.setChecked(True)
        self.Cam1.setToolTip('Select Platform Camera')
        self.Cam1.setStyleSheet(
            "QPushButton{background-color: white; border: 3px solid green; font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}")

        self.Cam2 = QPushButton('Comments', self)
        self.Cam2.setGeometry(1680, 60, 180, 70)
        self.Cam2.setCheckable(True)
        self.Cam2.setAutoExclusive(True)
        self.Cam2.setToolTip('Select Comments Camera')
        self.Cam2.setStyleSheet(
            "QPushButton{background-color: white; border: 3px solid green; font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}")

        Camgroup = QButtonGroup(self)
        Camgroup.addButton(self.Cam1)
        Camgroup.addButton(self.Cam2)

        # ── RIGHT PANEL — Speed ───────────────────────────────────────────────
        self.SpeedSlow = QPushButton('SLOW', self)
        self.SpeedSlow.setGeometry(1500, 175, 180, 70)
        self.SpeedSlow.setCheckable(True)
        self.SpeedSlow.setAutoExclusive(True)
        self.SpeedSlow.setChecked(True)
        self.SpeedSlow.setToolTip('Set Camera PTZ Speed to SLOW')
        self.SpeedSlow.setStyleSheet(
            "QPushButton{background-color: white; border: 3px solid green; font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}")

        self.SpeedFast = QPushButton('FAST', self)
        self.SpeedFast.setGeometry(1680, 175, 180, 70)
        self.SpeedFast.setCheckable(True)
        self.SpeedFast.setAutoExclusive(True)
        self.SpeedFast.setToolTip('Set Camera PTZ Speed to FAST')
        self.SpeedFast.setStyleSheet(
            "QPushButton{background-color: white; border: 3px solid green; font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}")

        Speedgroup = QButtonGroup(self)
        Speedgroup.addButton(self.SpeedSlow)
        Speedgroup.addButton(self.SpeedFast)

        # ── RIGHT PANEL — Preset / Set ────────────────────────────────────────
        self.Set1 = QPushButton('Call', self)
        self.Set1.setGeometry(1500, 290, 180, 70)
        self.Set1.setCheckable(True)
        self.Set1.setAutoExclusive(True)
        self.Set1.setChecked(True)
        self.Set1.setToolTip('Select Preset')
        self.Set1.setStyleSheet(
            "QPushButton{background-color: white; border: 3px solid green; font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}")

        self.Set2 = QPushButton('Set', self)
        self.Set2.setGeometry(1680, 290, 180, 70)
        self.Set2.setCheckable(True)
        self.Set2.setAutoExclusive(True)
        self.Set2.setToolTip('Record Preset')
        self.Set2.setStyleSheet(
            "QPushButton{background-color: white; border: 3px solid green; font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}")

        Setgroup = QButtonGroup(self)
        Setgroup.addButton(self.Set1)
        Setgroup.addButton(self.Set2)

        # ── RIGHT PANEL — Labels ──────────────────────────────────────────────
        CamSelect = QLabel('Camera Selection', self)
        CamSelect.setGeometry(1500, 20, 360, 30)
        CamSelect.setAlignment(QtCore.Qt.AlignCenter)
        CamSelect.setStyleSheet("font: bold 20px; color:black")

        SpeedSelect = QLabel('PTZ Speed', self)
        SpeedSelect.setGeometry(1500, 138, 360, 30)
        SpeedSelect.setAlignment(QtCore.Qt.AlignCenter)
        SpeedSelect.setStyleSheet("font: bold 20px; color:black")

        Presets = QLabel('Camera Presets', self)
        Presets.setGeometry(1500, 253, 360, 30)
        Presets.setAlignment(QtCore.Qt.AlignCenter)
        Presets.setStyleSheet("font: bold 20px; color:black")

        CamControls = QLabel('Camera Controls', self)
        CamControls.setGeometry(1500, 367, 360, 30)
        CamControls.setAlignment(QtCore.Qt.AlignCenter)
        CamControls.setStyleSheet("font: bold 20px; color:black")

        # ── RIGHT PANEL — Zoom buttons ────────────────────────────────────────
        ZoomIn = QPushButton(self)
        ZoomIn.setGeometry(1680, 403, 100, 100)
        ZoomIn.pressed.connect(self.ZoomIn)
        ZoomIn.released.connect(self.ZoomStop)
        ZoomIn.setStyleSheet("background-image: url(ZoomIn_120.png); border: none")

        ZoomOut = QPushButton(self)
        ZoomOut.setGeometry(1510, 403, 100, 100)
        ZoomOut.pressed.connect(self.ZoomOut)
        ZoomOut.released.connect(self.ZoomStop)
        ZoomOut.setStyleSheet("background-image: url(ZoomOut_120.png); border: none")

        # ── RIGHT PANEL — Arrow buttons ───────────────────────────────────────
        UpLeft    = self._arrow_btn(1500, 510, 135); UpLeft.pressed.connect(self.UpLeft);       UpLeft.released.connect(self.Stop)
        Up        = self._arrow_btn(1605, 510, 180); Up.pressed.connect(self.Up);               Up.released.connect(self.Stop)
        UpRight   = self._arrow_btn(1710, 510, 225); UpRight.pressed.connect(self.UpRight);     UpRight.released.connect(self.Stop)
        Left      = self._arrow_btn(1500, 617,  90); Left.pressed.connect(self.Left);           Left.released.connect(self.Stop)
        Right     = self._arrow_btn(1710, 617, 270); Right.pressed.connect(self.Right);         Right.released.connect(self.Stop)
        DownLeft  = self._arrow_btn(1500, 724,  45); DownLeft.pressed.connect(self.DownLeft);   DownLeft.released.connect(self.Stop)
        Down      = self._arrow_btn(1605, 724,   0); Down.pressed.connect(self.Down);           Down.released.connect(self.Stop)
        DownRight = self._arrow_btn(1710, 724, 315); DownRight.pressed.connect(self.DownRight); DownRight.released.connect(self.Stop)

        Home = QPushButton('', self)
        Home.setGeometry(1605, 617, 100, 100)
        Home.clicked.connect(self.HomeButton)
        Home.setStyleSheet("background-image: url(home.png); border: none")

        # ── RIGHT PANEL — Focus & Exposure (NEW) ──────────────────────────────
        FocusExposureLabel = QLabel('Focus & Exposure', self)
        FocusExposureLabel.setGeometry(1500, 835, 360, 25)
        FocusExposureLabel.setAlignment(QtCore.Qt.AlignCenter)
        FocusExposureLabel.setStyleSheet("font: bold 16px; color: black")

        # Focus row: Auto | One Push | Manual
        _focus_style = (
            "QPushButton{background-color: white; border: 2px solid #555; "
            "font: bold 13px; color: black; border-radius: 4px}"
            "QPushButton:pressed{background-color: #ccc}"
        )

        BtnAutoFocus = QPushButton('Auto\nFocus', self)
        BtnAutoFocus.setGeometry(1500, 863, 110, 50)
        BtnAutoFocus.setToolTip('Auto Focus ON')
        BtnAutoFocus.setStyleSheet(_focus_style)
        BtnAutoFocus.clicked.connect(self.AutoFocus)

        BtnOnePush = QPushButton('One Push\nAF', self)
        BtnOnePush.setGeometry(1625, 863, 110, 50)
        BtnOnePush.setToolTip('One-shot autofocus then return to manual')
        BtnOnePush.setStyleSheet(_focus_style)
        BtnOnePush.clicked.connect(self.OnePushAF)

        BtnManualFocus = QPushButton('Manual\nFocus', self)
        BtnManualFocus.setGeometry(1750, 863, 110, 50)
        BtnManualFocus.setToolTip('Manual Focus mode')
        BtnManualFocus.setStyleSheet(_focus_style)
        BtnManualFocus.clicked.connect(self.ManualFocus)

        # Exposure row: Darker | Backlight | Brighter
        _exp_style = (
            "QPushButton{background-color: white; border: 2px solid #555; "
            "font: bold 13px; color: black; border-radius: 4px}"
            "QPushButton:pressed{background-color: #ccc}"
        )

        BtnDarker = QPushButton('▼ Darker', self)
        BtnDarker.setGeometry(1500, 920, 110, 45)
        BtnDarker.setToolTip('Decrease brightness')
        BtnDarker.setStyleSheet(_exp_style)
        BtnDarker.clicked.connect(self.BrightnessDown)

        # Backlight is a toggle — stored as instance variable for colour update
        self.BtnBacklight = QPushButton('Backlight\nOFF', self)
        self.BtnBacklight.setGeometry(1625, 920, 110, 45)
        self.BtnBacklight.setToolTip('Toggle backlight compensation (contraluz)')
        self._backlight_style_off = (
            "QPushButton{background-color: white; border: 2px solid #555; "
            "font: bold 13px; color: black; border-radius: 4px}"
        )
        self._backlight_style_on = (
            "QPushButton{background-color: #e6a800; border: 2px solid #b37f00; "
            "font: bold 13px; color: white; border-radius: 4px}"
        )
        self.BtnBacklight.setStyleSheet(self._backlight_style_off)
        self.BtnBacklight.clicked.connect(self.BacklightToggle)

        BtnBrighter = QPushButton('▲ Brighter', self)
        BtnBrighter.setGeometry(1750, 920, 110, 45)
        BtnBrighter.setToolTip('Increase brightness')
        BtnBrighter.setStyleSheet(_exp_style)
        BtnBrighter.clicked.connect(self.BrightnessUp)

        # ── Config / bottom buttons ───────────────────────────────────────────
        Cam1Address = QPushButton('Platform [Platform]  -  ' + IPAddress, self)
        Cam1Address.setGeometry(1500, 975, 310, 22)
        Cam1Address.setStyleSheet("font: bold 15px; color:" + Cam1Check)
        Cam1Address.clicked.connect(self.PTZ1Address)

        Cam2Address = QPushButton('Comments [Audience]  -  ' + IPAddress2, self)
        Cam2Address.setGeometry(1500, 995, 310, 22)
        Cam2Address.setStyleSheet("font: bold 15px; color:" + Cam2Check)
        Cam2Address.clicked.connect(self.PTZ2Address)

        PTZ1ID = QPushButton(' ID-' + Cam1ID, self)
        PTZ1ID.setGeometry(1815, 975, 45, 22)
        PTZ1ID.setStyleSheet("font: bold 15px; color:" + Cam1Check)
        PTZ1ID.clicked.connect(self.PTZ1IDchange)

        PTZ2ID = QPushButton(' ID-' + Cam2ID, self)
        PTZ2ID.setGeometry(1815, 995, 45, 22)
        PTZ2ID.setStyleSheet("font: bold 15px; color:" + Cam2Check)
        PTZ2ID.clicked.connect(self.PTZ2IDchange)

        Version = QPushButton('Close window', self)
        Version.setGeometry(1500, 1050, 310, 22)
        Version.setStyleSheet("background-color: lightgrey; font: 15px; color: black; border: none")
        Version.clicked.connect(self.Quit)

        Help = QPushButton('?', self)
        Help.setGeometry(1815, 1050, 45, 22)
        Help.setStyleSheet("background-color: lightgrey; font: 15px; color: black; border: none")
        Help.clicked.connect(self.HelpMsg)

    # ── Helper ────────────────────────────────────────────────────────────────
    def _arrow_btn(self, x, y, degrees):
        btn = QPushButton(self)
        btn.setGeometry(x, y, 100, 100)
        btn.setStyleSheet("border: none; background: transparent")
        pix = QPixmap("angle.png").transformed(
            QtGui.QTransform().rotate(degrees), Qt.SmoothTransformation
        )
        btn.setIcon(QtGui.QIcon(pix))
        btn.setIconSize(QtCore.QSize(90, 90))
        return btn

    def _send_cmd(self, ip, cam_id_hex, cmd_suffix):
        """Send a raw VISCA hex command to a camera. Returns True on success."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((ip, 5678))
            cmd = binascii.unhexlify(cam_id_hex + cmd_suffix)
            s.send(cmd)
            s.recv(131072)
            s.close()
            return True
        except (socket.timeout, socket.error, OSError):
            return False

    @pyqtSlot()

    # ── Error handlers ────────────────────────────────────────────────────────
    def ErrorCapture(self):
        print()

    def ErrorCapture1(self):
        QMessageBox.warning(self, 'Platform PTZ Control',
                            'Check That Platform Camera IP Address is set to  ' + IPAddress + '  and ID 1')

    def ErrorCapture2(self):
        QMessageBox.warning(self, 'Comments PTZ Control',
                            'Check That Comments Camera IP Address is set to  ' + IPAddress2 + '  and ID 2')

    # ── Socket send helpers ───────────────────────────────────────────────────
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
            s.send(binascii.unhexlify(Cam1ID + "01060100000303FF"))
            s.recv(131072)
        except (socket.timeout, OSError):
            print()

    def Cam2Stop(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((IPAddress2, 5678))
            s.send(binascii.unhexlify(Cam2ID + "01060100000303FF"))
            s.recv(131072)
        except (socket.timeout, OSError):
            print()

    # ══════════════════════════════════════════════════════════════════════════
    #  SESSION MANAGEMENT  (NEW)
    # ══════════════════════════════════════════════════════════════════════════
    def ToggleSession(self):
        """Single toggle: OFF→ON starts session, ON→OFF ends session."""
        if not self.session_active:
            # ── START ─────────────────────────────────────────────────────────
            self.session_active = True
            self.BtnSession.setEnabled(False)
            self.BtnSession.setStyleSheet(
                "QPushButton{background-color: #555; border: 2px solid #333; "
                "font: bold 26px; color: #aaa; border-radius: 25px}")
            self.SessionStatus.setText('Starting…')
            self.SessionStatus.setStyleSheet("font: bold 12px; color: #888")

            self._send_cmd(IPAddress,  Cam1ID, "01040002FF")
            self._send_cmd(IPAddress2, Cam2ID, "01040002FF")
            QtCore.QTimer.singleShot(8000, self._session_home)
        else:
            # ── END ───────────────────────────────────────────────────────────
            reply = QMessageBox.question(
                self, 'End Session',
                'Power off both cameras and end the session?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._send_cmd(IPAddress,  Cam1ID, "01040003FF")
                self._send_cmd(IPAddress2, Cam2ID, "01040003FF")
                self.session_active = False
                # Button back to red (OFF state)
                self.BtnSession.setStyleSheet(
                    "QPushButton{background-color: #8b1a1a; border: 2px solid #5a0d0d; "
                    "font: bold 26px; color: white; border-radius: 25px}"
                    "QPushButton:pressed{background-color: #5a0d0d}")
                self.BtnSession.setToolTip('Start Session: Power ON both cameras and go Home')
                self.SessionStatus.setText('OFF')
                self.SessionStatus.setStyleSheet("font: bold 12px; color: #8b1a1a")

    def _session_home(self):
        """Called 8 s after session start — moves both cameras to Home."""
        self._send_cmd(IPAddress,  Cam1ID, "010604FF")
        self._send_cmd(IPAddress2, Cam2ID, "010604FF")
        # Button turns green (ON state)
        self.BtnSession.setStyleSheet(
            "QPushButton{background-color: #1a7a1a; border: 2px solid #0d4d0d; "
            "font: bold 26px; color: white; border-radius: 25px}"
            "QPushButton:pressed{background-color: #0d4d0d}")
        self.BtnSession.setToolTip('End Session: Power OFF (standby) both cameras')
        self.BtnSession.setEnabled(True)
        self.SessionStatus.setText('ON')
        self.SessionStatus.setStyleSheet("font: bold 12px; color: #1a7a1a")

    # ══════════════════════════════════════════════════════════════════════════
    #  FOCUS CONTROLS  (NEW)
    # ══════════════════════════════════════════════════════════════════════════
    def _active_cam(self):
        """Returns (ip, cam_id) for the currently selected camera."""
        if self.Cam1.isChecked():
            return IPAddress, Cam1ID
        return IPAddress2, Cam2ID

    def AutoFocus(self):
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01043802FF")

    def ManualFocus(self):
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01043803FF")

    def OnePushAF(self):
        """Trigger a single autofocus shot then stay in manual mode."""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01041801FF")

    # ══════════════════════════════════════════════════════════════════════════
    #  EXPOSURE CONTROLS  (NEW)
    # ══════════════════════════════════════════════════════════════════════════
    def BrightnessUp(self):
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01040D02FF")

    def BrightnessDown(self):
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01040D03FF")

    def BacklightToggle(self):
        """Toggle backlight compensation ON/OFF for the active camera."""
        ip, cam_id = self._active_cam()
        cam_key = 1 if self.Cam1.isChecked() else 2
        current = self.backlight_on[cam_key]

        if current:
            # Turn OFF
            self._send_cmd(ip, cam_id, "01043303FF")
            self.backlight_on[cam_key] = False
            self.BtnBacklight.setText('Backlight\nOFF')
            self.BtnBacklight.setStyleSheet(self._backlight_style_off)
        else:
            # Turn ON
            self._send_cmd(ip, cam_id, "01043302FF")
            self.backlight_on[cam_key] = True
            self.BtnBacklight.setText('Backlight\nON')
            self.BtnBacklight.setStyleSheet(self._backlight_style_on)

    # ══════════════════════════════════════════════════════════════════════════
    #  CAMERA MOVEMENT (unchanged)
    # ══════════════════════════════════════════════════════════════════════════
    def HomeButton(self):
        if self.Cam1.isChecked():
            global Cam1DataString
            Cam1DataString = binascii.unhexlify(Cam1ID + "010604FF")
            self.Cam1Call()
        elif self.Cam2.isChecked():
            global Cam2DataString
            Cam2DataString = binascii.unhexlify(Cam2ID + "010604FF")
            self.Cam2Call()

    def UpLeft(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01060104040101ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01060110100101ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01060104040101ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01060110100101ff")
                self.Cam2aCall()

    def Up(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01060100040301FF")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01060100100301FF")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01060100040301FF")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01060100100301FF")
                self.Cam2aCall()

    def UpRight(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01060104040201ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01060110100201ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01060104040201ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01060110100201ff")
                self.Cam2aCall()

    def Left(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01060104000103ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01060110000103ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01060104000103ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01060110000103ff")
                self.Cam2aCall()

    def Right(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01060104000203ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01060110000203ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01060104000203ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01060110000203ff")
                self.Cam2aCall()

    def DownLeft(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01060104040102ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01060110100102ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01060104040102ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01060110100102ff")
                self.Cam2aCall()

    def Down(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01060100040302ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01060100100302ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01060100040302ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01060100100302ff")
                self.Cam2aCall()

    def DownRight(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01060104040202ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01060110100202ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01060104040202ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01060110100202ff")
                self.Cam2aCall()

    def Stop(self):
        if self.Cam1.isChecked():
            global Cam1DataString
            Cam1DataString = binascii.unhexlify(Cam1ID + "01060100000303FF")
            self.Cam1Stop()
        elif self.Cam2.isChecked():
            global Cam2DataString
            Cam2DataString = binascii.unhexlify(Cam2ID + "01060100000303FF")
            self.Cam2Stop()

    def ZoomIn(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01040722ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01040726ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01040722ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01040726ff")
                self.Cam2aCall()

    def ZoomOut(self):
        if self.Cam1.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam1DataString
                Cam1DataString = binascii.unhexlify(Cam1ID + "01040732ff")
                self.Cam1Call()
            elif self.SpeedFast.isChecked():
                global Cam1aDataString
                Cam1aDataString = binascii.unhexlify(Cam1ID + "01040736ff")
                self.Cam1aCall()
        elif self.Cam2.isChecked():
            if self.SpeedSlow.isChecked():
                global Cam2DataString
                Cam2DataString = binascii.unhexlify(Cam2ID + "01040732ff")
                self.Cam2Call()
            elif self.SpeedFast.isChecked():
                global Cam2aDataString
                Cam2aDataString = binascii.unhexlify(Cam2ID + "01040736ff")
                self.Cam2aCall()

    def ZoomStop(self):
        if self.Cam1.isChecked():
            global Cam1DataString
            Cam1DataString = binascii.unhexlify(Cam1ID + "01040700ff")
            self.Cam1Stop()
        elif self.Cam2.isChecked():
            global Cam2DataString
            Cam2DataString = binascii.unhexlify(Cam2ID + "01040700ff")
            self.Cam2Stop()

    # ── Call / Set Presets 1-3 (unchanged) ───────────────────────────────────
    def Go1(self):
        if self.Set1.isChecked():
            global Cam1DataString
            Cam1DataString = binascii.unhexlify(Cam1ID + "01043f0201ff")
            self.Cam1Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record Chairman Position', "Are You Sure?",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam1DataString = binascii.unhexlify(Cam1ID + "01043f0101ff")
                self.Cam1Call()

    def Go2(self):
        if self.Set1.isChecked():
            global Cam1DataString
            Cam1DataString = binascii.unhexlify(Cam1ID + "01043f0202ff")
            self.Cam1Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record Platform Left', "Are You Sure?",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam1DataString = binascii.unhexlify(Cam1ID + "01043f0102ff")
                self.Cam1Call()

    def Go3(self):
        if self.Set1.isChecked():
            global Cam1DataString
            Cam1DataString = binascii.unhexlify(Cam1ID + "01043f0203ff")
            self.Cam1Stop()
        elif self.Set2.isChecked():
            btnReply = QMessageBox.question(self, 'Record Platform Right', "Are You Sure?",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if btnReply == QMessageBox.Yes:
                Cam1DataString = binascii.unhexlify(Cam1ID + "01043f0103ff")
                self.Cam1Call()

    # ── Generic preset handler 4-128 (unchanged) ─────────────────────────────
    def go_to_preset(self, preset_number):
        global Cam1DataString, Cam2DataString
        preset_hex = PRESET_MAP.get(preset_number)
        if not preset_hex:
            return
        cam_id   = Cam1ID if self.Cam1.isChecked() else Cam2ID
        cam_call = self.Cam1Call if self.Cam1.isChecked() else self.Cam2Call
        if self.Set1.isChecked():
            cmd = binascii.unhexlify(cam_id + "01043f02" + preset_hex + "ff")
            if self.Cam1.isChecked():
                Cam1DataString = cmd
            else:
                Cam2DataString = cmd
            cam_call()
        elif self.Set2.isChecked():
            cam_name = "Platform" if self.Cam1.isChecked() else "Comments"
            reply = QMessageBox.question(
                self, f'Record Preset {preset_number} ({cam_name})',
                "Are you sure you want to record this preset?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                cmd = binascii.unhexlify(cam_id + "01043f01" + preset_hex + "ff")
                if self.Cam1.isChecked():
                    Cam1DataString = cmd
                else:
                    Cam2DataString = cmd
                cam_call()

    # ── Config / Quit / Help (unchanged) ─────────────────────────────────────
    def Quit(self):
        sys.exit()

    def PTZ1Address(self):
        result = QMessageBox().warning(self, 'Platform PTZ Control',
                                       'Do you want to change which IP address will be used to control camera?',
                                       QMessageBox.Ok, QMessageBox.Cancel)
        if result == 1024:
            text, _ = QInputDialog().getText(self, 'Platform PTZ Control',
                                             'Change IP Address to control Platform Camera - Current Address is: ',
                                             text=IPAddress)
            open("PTZ1IP.txt", "w+").write(text)
            os.execv(sys.executable, ['python3'] + sys.argv)

    def PTZ2Address(self):
        result = QMessageBox().warning(self, 'Comments PTZ Control',
                                       'Do you want to change which IP address will be used to control camera?',
                                       QMessageBox.Ok, QMessageBox.Cancel)
        if result == 1024:
            text, _ = QInputDialog().getText(self, 'Comments PTZ Control',
                                             'Change IP Address to control Comments Camera - Current Address is: ',
                                             text=IPAddress2)
            open("PTZ2IP.txt", "w+").write(text)
            os.execv(sys.executable, ['python3'] + sys.argv)

    def PTZ1IDchange(self):
        result = QMessageBox().warning(self, 'Platform PTZ Control',
                                       'Do you want to change which ID will be used to control camera?',
                                       QMessageBox.Ok, QMessageBox.Cancel)
        if result == 1024:
            text, _ = QInputDialog().getText(self, 'Platform PTZ Control',
                                             'Change ID to control Platform Camera - Current ID is: ',
                                             text=Cam1ID)
            open("Cam1ID.txt", "w+").write(text)
            os.execv(sys.executable, ['python3'] + sys.argv)

    def PTZ2IDchange(self):
        result = QMessageBox().warning(self, 'Platform PTZ Control',
                                       'Do you want to change which ID will be used to control camera?',
                                       QMessageBox.Ok, QMessageBox.Cancel)
        if result == 1024:
            text, _ = QInputDialog().getText(self, 'Platform PTZ Control',
                                             'Change ID to control Comments Camera - Current ID is: ',
                                             text=Cam2ID)
            open("Cam2ID.txt", "w+").write(text)
            os.execv(sys.executable, ['python3'] + sys.argv)

    def HelpMsg(self):
        result = QMessageBox().warning(self, 'For Technical Assistance', Contact, QMessageBox.Ok)
        if result == 1024:
            print(result)


# ── GoButton (unchanged) ──────────────────────────────────────────────────────
class GoButton(QPushButton):

    def __init__(self, Text, parent=MainWindow):
        super(GoButton, self).__init__(parent)
        self.setupbtn(Text)

    def setupbtn(self, Text):
        self.setText(Text)
        self.resize(35, 35)
        self.setStyleSheet(
            "background-color: rgba(0,0,0,10); border: 0px solid black; "
            "border-radius: 5px; font: 14px; font-weight: bold; color:" + ButtonColor
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    # ex.showFullScreen()
    sys.exit(app.exec_())