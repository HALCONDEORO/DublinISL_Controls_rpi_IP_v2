#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#
#  Name:    LBD - Sign Language Camera Controls - IP RPI Version
#  Author:  Isaac Urwin  -  IP & ISL revision by Simon Laban
#  Date:    November 2025 / Updated March 2026
#
#  Purpose:
#    PyQt5 GUI that controls two PTZ cameras over VISCA-over-IP (TCP port 5678).
#    Camera 1 faces the platform (speaker); Camera 2 faces the audience.
#    Operators click seat buttons (numbered 4-128) to call presets, or use
#    the arrow/zoom controls for manual framing.
#
#    - Session Management: single ⏻ button toggles ON/OFF
#        ON:  Power both cameras, wait 8 s, go Home
#        OFF: Power both cameras to standby
#    - Focus & Exposure panel: Auto Focus / One Push AF / Manual Focus,
#        Brightness Up/Down, Backlight toggle per camera
#
#  Config files (must exist in the working directory):
#    PTZ1IP.txt   IP address of the Platform camera  (default 172.16.1.11)
#    PTZ2IP.txt   IP address of the Comments camera  (default 172.16.1.12)
#    Cam1ID.txt   VISCA hex device ID for Camera 1   (e.g. "81")
#    Cam2ID.txt   VISCA hex device ID for Camera 2   (e.g. "82")
#    Contact.txt  Support contact shown in Help dialog
#
#
# ─────────────────────────────────────────────────────────────────────────────

import os
import re
import sys
import socket
import binascii

import PyQt5
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton,
    QLabel, QMessageBox, QHBoxLayout, QButtonGroup, QInputDialog
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSlot, Qt



def _read_config(filename, default):
    """
    Read a single-line text config file and return its stripped contents.
    If the file is missing or unreadable, log a warning and return `default`.
    """
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except (FileNotFoundError, IOError) as exc:
        print(f"[WARNING] Could not read '{filename}': {exc}  → using default '{default}'")
        return default


# Load all five config files; the app stays functional even if any are absent.
IPAddress  = _read_config('PTZ1IP.txt',  '172.16.1.11')   # Platform camera IP
IPAddress2 = _read_config('PTZ2IP.txt',  '172.16.1.12')   # Comments camera IP
Cam1ID     = _read_config('Cam1ID.txt',  '81')             # VISCA device ID (hex string)
Cam2ID     = _read_config('Cam2ID.txt',  '82')
Contact    = _read_config('Contact.txt', 'No contact information available.')

# UI colour used for seat-button text
ButtonColor = "black"

# ─────────────────────────────────────────────────────────────────────────────
#  Shared network constant
#  One place to change the TCP connect/send timeout for all socket calls.
# ─────────────────────────────────────────────────────────────────────────────
SOCKET_TIMEOUT = 1  # seconds

# ─────────────────────────────────────────────────────────────────────────────
# VISCA commands inline or via _send_cmd(), so no shared mutable
#  state is needed.  The startup connectivity check below only writes to local
#  variables (Cam1Check / Cam2Check) that control the UI indicator colour.
# ─────────────────────────────────────────────────────────────────────────────

def _check_camera(ip, cam_id):
    """
    Perform a one-shot TCP connection to verify a camera is reachable.
    Sends a VISCA power-status inquiry and discards the reply.
    Returns "Green" if the camera responded, "Red" otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(SOCKET_TIMEOUT)
            s.connect((ip, 5678))
            # VISCA power inquiry: <id>090400FF
            s.send(binascii.unhexlify(cam_id + "090400FF"))
            s.recv(131072)
        return "Green"
    except (socket.timeout, socket.error, OSError):
        return "Red"


# Run connectivity checks at startup; results colour the address labels
Cam1Check = _check_camera(IPAddress,  Cam1ID)
Cam2Check = _check_camera(IPAddress2, Cam2ID)

# ─────────────────────────────────────────────────────────────────────────────
#  VISCA preset number → hex byte mapping
#
#  VISCA uses certain byte values internally (e.g. 0x5A-0x8B are reserved).
#  Presets 90-99 would land in that range, so we remap them to 0x8C-0x95.
# ─────────────────────────────────────────────────────────────────────────────
PRESET_MAP = {}
for _i in range(4, 90):       # Direct hex for 4-89
    PRESET_MAP[_i] = f"{_i:02X}"
for _i in range(90, 100):     # Remap 90-99 → 0x8C-0x95
    PRESET_MAP[_i] = f"{0x8C + (_i - 90):02X}"
for _i in range(100, 129):    # Direct hex for 100-128
    PRESET_MAP[_i] = f"{_i:02X}"


# ─────────────────────────────────────────────────────────────────────────────
#  Validation helpers (used by FIX 3 & 4)
# ─────────────────────────────────────────────────────────────────────────────

def _is_valid_ip(text):
    """
    Return True if `text` is a plausible IPv4 address (four octets 0-255).
    Does not perform DNS resolution.
    """
    pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    match = re.match(pattern, text.strip())
    if not match:
        return False
    return all(0 <= int(g) <= 255 for g in match.groups())


def _is_valid_cam_id(text):
    """
    Return True if `text` is a non-empty hexadecimal string (e.g. "81", "82").
    VISCA IDs are typically one byte written as two hex digits.
    """
    text = text.strip()
    if not text:
        return False
    try:
        binascii.unhexlify(text)   # Will raise if not valid hex
        return True
    except (binascii.Error, ValueError):
        return False


# ═════════════════════════════════════════════════════════════════════════════
#  MainWindow
# ═════════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """
    Main application window.

    Layout (1920×1080):
      Left area  (x 0-1460)  : Seat-position preset buttons on a background image
      Right panel (x 1500+)  : Camera selection, speed, preset mode, PTZ arrows,
                                zoom, focus/exposure controls, config/quit buttons
    """

    def __init__(self):
        super().__init__()

        # ── Window geometry ───────────────────────────────────────────────────
        self.setWindowTitle('Camera Controls')
        self.setGeometry(0, 0, 1920, 1080)

        # Per-camera backlight state: True = backlight compensation ON
        # Stored here so the UI label stays correct when switching cameras.
        self.backlight_on = {1: False, 2: False}

        # ── Background image ──────────────────────────────────────────────────
        # Scales the seating-plan JPEG to fill the window behind all widgets.
        pixmap = QPixmap("Background_ISL_v2.jpg")
        scaled_pixmap = pixmap.scaled(
            1920, 1080,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        background = QLabel(self)
        background.setPixmap(scaled_pixmap)
        background.setGeometry(0, -30, 1920, 1080)
        background.lower()   # Push behind every other widget

        # ── Seat pixel positions ──────────────────────────────────────────────
        # Maps preset number → (x, y) top-left corner of the button on screen.
        # Numbers match the physical seat numbers printed on the background image.
        seat_positions = {
            # Row 1
            4:(70,210),   5:(131,210),  6:(192,210),  7:(253,210),
            8:(479,210),  9:(540,210), 10:(601,210), 11:(662,210),
           12:(722,210), 13:(783,210), 14:(844,210),
           15:(1070,210),16:(1130,210),17:(1191,210),18:(1252,210),
            # Row 2
           19:(70,295),  20:(131,295), 21:(192,295), 22:(253,295),
           23:(479,295), 24:(540,295), 25:(601,295), 26:(662,295),
           27:(722,295), 28:(783,295), 29:(844,295),
           30:(1070,295),31:(1130,295),32:(1191,295),33:(1252,295),
            # Row 3
           34:(70,382),  35:(131,382), 36:(192,382), 37:(253,382),
           38:(479,382), 39:(540,382), 40:(601,382), 41:(662,382),
           42:(723,382), 43:(783,382), 44:(844,382),
           45:(1070,382),46:(1130,382),47:(1191,382),48:(1252,382),
            # Row 4
           49:(70,465),  50:(131,465), 51:(192,465), 52:(253,465),
           53:(479,465), 54:(540,465), 55:(601,465), 56:(662,465),
           57:(722,465), 58:(783,465), 59:(844,465),
           60:(1070,465),61:(1130,465),62:(1191,465),63:(1252,465),
            # Row 5
           64:(70,550),  65:(131,550), 66:(192,550), 67:(253,550),
           68:(479,550), 69:(540,550), 70:(601,550), 71:(662,550),
           72:(722,550), 73:(783,550), 74:(844,550),
           75:(1070,550),76:(1130,550),77:(1191,550),78:(1252,550),
            # Row 6
           79:(70,635),  80:(131,635), 81:(192,635), 82:(253,635),
           83:(479,635), 84:(540,635), 85:(601,635), 86:(662,635),
           87:(722,635), 88:(783,635), 89:(844,635),
           90:(1070,635),91:(1130,635),92:(1191,635),93:(1252,635),
            # Row 7
           94:(70,720),  95:(131,720), 96:(192,720), 97:(253,720),
           98:(479,720), 99:(540,720),100:(601,720),101:(662,720),
          102:(722,720),103:(783,720),104:(844,720),
          105:(1070,720),106:(1130,720),107:(1191,720),108:(1252,720),
            # Row 8
          109:(70,805), 110:(131,805),111:(192,805),112:(253,805),
          113:(479,805),114:(540,805),115:(601,805),116:(662,805),
          117:(722,805),118:(783,805),119:(844,805),
          120:(1070,805),121:(1130,805),122:(1191,805),123:(1252,805),
            # Row 9
          124:(108,975),125:(201,975),126:(481,975),127:(578,975),
            # Wheelchair space
          128:(150,110),
        }

        # ── Platform preset buttons (fixed positions above seating plan) ───────
        # These three call hardcoded presets on Camera 1 (platform camera only).
        Preset1 = QPushButton('Chairman', self)
        Preset1.resize(110, 110)
        Preset1.move(623, 35)
        Preset1.setStyleSheet(
            "background-color: rgba(0,0,0,0); font: 14px; font-weight: bold; "
            "color: black; padding-top: 70px"
        )
        Preset1.clicked.connect(self.Go1)

        Preset2 = GoButton('Left', self)
        Preset2.resize(110, 110)
        Preset2.move(460, 35)
        Preset2.setStyleSheet(
            "background-color: rgba(0,0,0,0); font: 14px; font-weight: bold; "
            "color: black; padding-top: 70px"
        )
        Preset2.clicked.connect(self.Go2)

        Preset3 = GoButton('Right', self)
        Preset3.resize(110, 110)
        Preset3.move(803, 35)
        Preset3.setStyleSheet(
            "background-color: rgba(0,0,0,0); font: 14px; font-weight: bold; "
            "color: black; padding-top: 70px"
        )
        Preset3.clicked.connect(self.Go3)

        # ── Seat buttons (dynamic, one per entry in seat_positions) ───────────
        # Each button calls go_to_preset(n) with the seat's preset number.
        # We use a default-argument trick (n=seat_number) to capture the loop
        # variable correctly inside the lambda.
        for seat_number in range(4, 129):
            if seat_number not in seat_positions:
                continue
            x, y = seat_positions[seat_number]
            button = GoButton(str(seat_number), self)
            button.move(x, y)
            button.clicked.connect(
                lambda checked=False, n=seat_number: self.go_to_preset(n)
            )
            # Store a reference so the button isn't garbage-collected
            setattr(self, f"Seat{seat_number}", button)

        # ── SESSION MANAGEMENT — top-left corner ──────────────────────────────
        # A single ⏻ button toggles between OFF (red) → Starting → ON (green).
        # ON:  Powers both cameras, waits 8 s, sends both to Home position.
        # OFF: Powers both cameras to standby after user confirmation.
        self.session_active = False

        self.BtnSession = QPushButton('⏻', self)
        self.BtnSession.setGeometry(10, 10, 50, 50)
        self.BtnSession.setToolTip('Start Session: Power ON both cameras and go Home')
        self.BtnSession.setStyleSheet(
            "QPushButton{background-color: #8b1a1a; border: 2px solid #5a0d0d; "
            "font: bold 26px; color: white; border-radius: 25px}"
            "QPushButton:pressed{background-color: #5a0d0d}"
        )
        self.BtnSession.clicked.connect(self.ToggleSession)

        # Small text label next to the session button showing OFF / Starting… / ON
        self.SessionStatus = QLabel('OFF', self)
        self.SessionStatus.setGeometry(68, 22, 60, 20)
        self.SessionStatus.setStyleSheet("font: bold 12px; color: #8b1a1a")

        # ── RIGHT PANEL — Camera Selection ────────────────────────────────────
        # Exclusive checkable buttons; only one can be active at a time.
        # Platform = Camera 1; Comments = Camera 2.
        _cam_style = (
            "QPushButton{background-color: white; border: 3px solid green; "
            "font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}"
        )

        self.Cam1 = QPushButton('Platform', self)
        self.Cam1.setGeometry(1500, 60, 180, 70)
        self.Cam1.setCheckable(True)
        self.Cam1.setAutoExclusive(True)
        self.Cam1.setChecked(True)    # Platform camera selected by default
        self.Cam1.setToolTip('Select Platform Camera')
        self.Cam1.setStyleSheet(_cam_style)

        self.Cam2 = QPushButton('Comments', self)
        self.Cam2.setGeometry(1680, 60, 180, 70)
        self.Cam2.setCheckable(True)
        self.Cam2.setAutoExclusive(True)
        self.Cam2.setToolTip('Select Comments Camera')
        self.Cam2.setStyleSheet(_cam_style)

        # Group ensures mutual exclusivity at the Qt level as well
        Camgroup = QButtonGroup(self)
        Camgroup.addButton(self.Cam1)
        Camgroup.addButton(self.Cam2)

        # When switching cameras, refresh the Backlight button label/colour
        # so it reflects that camera's individual backlight state.
        self.Cam1.clicked.connect(self._update_backlight_ui)
        self.Cam2.clicked.connect(self._update_backlight_ui)

        # ── RIGHT PANEL — PTZ Speed ───────────────────────────────────────────
        # SLOW and FAST produce different VISCA speed bytes in movement commands.
        _speed_style = (
            "QPushButton{background-color: white; border: 3px solid green; "
            "font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}"
        )

        self.SpeedSlow = QPushButton('SLOW', self)
        self.SpeedSlow.setGeometry(1500, 175, 180, 70)
        self.SpeedSlow.setCheckable(True)
        self.SpeedSlow.setAutoExclusive(True)
        self.SpeedSlow.setChecked(True)
        self.SpeedSlow.setToolTip('Set Camera PTZ Speed to SLOW')
        self.SpeedSlow.setStyleSheet(_speed_style)

        self.SpeedFast = QPushButton('FAST', self)
        self.SpeedFast.setGeometry(1680, 175, 180, 70)
        self.SpeedFast.setCheckable(True)
        self.SpeedFast.setAutoExclusive(True)
        self.SpeedFast.setToolTip('Set Camera PTZ Speed to FAST')
        self.SpeedFast.setStyleSheet(_speed_style)

        Speedgroup = QButtonGroup(self)
        Speedgroup.addButton(self.SpeedSlow)
        Speedgroup.addButton(self.SpeedFast)


        # ── RIGHT PANEL — Section labels ──────────────────────────────────────
        for text, geom in [
            ('Camera Selection',  (1500,  20, 360, 30)),
            ('PTZ Speed',         (1500, 138, 360, 30)),
            ('Camera Presets',    (1500, 253, 360, 30)),
            ('Camera Controls',   (1500, 367, 360, 30)),
        ]:
            lbl = QLabel(text, self)
            lbl.setGeometry(*geom)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet("font: bold 20px; color:black")
            
        # ── RIGHT PANEL — Preset mode (Call / Set) ───────────────────────────
        # "Call" = recall a stored preset position.
        # "Set"  = overwrite a preset with the camera's current position.
        _preset_style = (
            "QPushButton{background-color: white; border: 3px solid green; "
            "font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}"
        )

        self.Set1 = QPushButton('Call', self)
        self.Set1.setGeometry(1500, 290, 180, 70)
        self.Set1.setCheckable(True)
        self.Set1.setAutoExclusive(True)
        self.Set1.setChecked(True)
        self.Set1.setToolTip('Select Preset')
        self.Set1.setStyleSheet(_preset_style)

        self.Set2 = QPushButton('Set', self)
        self.Set2.setGeometry(1680, 290, 180, 70)
        self.Set2.setCheckable(True)
        self.Set2.setAutoExclusive(True)
        self.Set2.setToolTip('Record Preset')
        self.Set2.setStyleSheet(_preset_style)

        Setgroup = QButtonGroup(self)
        Setgroup.addButton(self.Set1)
        Setgroup.addButton(self.Set2)

        # ── RIGHT PANEL — Zoom buttons ────────────────────────────────────────
        # pressed → start zoom;  released → stop zoom (separate VISCA command)
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

        # ── RIGHT PANEL — Arrow / direction buttons ───────────────────────────
        # _arrow_btn() creates a transparent button with a rotated arrow icon.
        # pressed → start movement;  released → stop (Stop command).
        UpLeft    = self._arrow_btn(1500, 510, 135); UpLeft.pressed.connect(self.UpLeft);       UpLeft.released.connect(self.Stop)
        Up        = self._arrow_btn(1605, 510, 180); Up.pressed.connect(self.Up);               Up.released.connect(self.Stop)
        UpRight   = self._arrow_btn(1710, 510, 225); UpRight.pressed.connect(self.UpRight);     UpRight.released.connect(self.Stop)
        Left      = self._arrow_btn(1500, 617,  90); Left.pressed.connect(self.Left);           Left.released.connect(self.Stop)
        Right     = self._arrow_btn(1710, 617, 270); Right.pressed.connect(self.Right);         Right.released.connect(self.Stop)
        DownLeft  = self._arrow_btn(1500, 724,  45); DownLeft.pressed.connect(self.DownLeft);   DownLeft.released.connect(self.Stop)
        Down      = self._arrow_btn(1605, 724,   0); Down.pressed.connect(self.Down);           Down.released.connect(self.Stop)
        DownRight = self._arrow_btn(1710, 724, 315); DownRight.pressed.connect(self.DownRight); DownRight.released.connect(self.Stop)

        # Home button: sends camera to its factory Home position
        Home = QPushButton('', self)
        Home.setGeometry(1605, 617, 100, 100)
        Home.clicked.connect(self.HomeButton)
        Home.setStyleSheet("background-image: url(home.png); border: none")

        # ── RIGHT PANEL — Focus & Exposure ────────────────────────────────────
        FocusExposureLabel = QLabel('Focus & Exposure', self)
        FocusExposureLabel.setGeometry(1500, 835, 360, 25)
        FocusExposureLabel.setAlignment(QtCore.Qt.AlignCenter)
        FocusExposureLabel.setStyleSheet("font: bold 16px; color: black")

        _focus_style = (
            "QPushButton{background-color: white; border: 2px solid #555; "
            "font: bold 13px; color: black; border-radius: 4px}"
            "QPushButton:pressed{background-color: #ccc}"
        )

        # Auto Focus: camera continuously adjusts focus automatically
        BtnAutoFocus = QPushButton('Auto\nFocus', self)
        BtnAutoFocus.setGeometry(1500, 863, 110, 50)
        BtnAutoFocus.setToolTip('Auto Focus ON')
        BtnAutoFocus.setStyleSheet(_focus_style)
        BtnAutoFocus.clicked.connect(self.AutoFocus)

        # One Push AF: camera focuses once then returns to manual mode
        BtnOnePush = QPushButton('One Push\nAF', self)
        BtnOnePush.setGeometry(1625, 863, 110, 50)
        BtnOnePush.setToolTip('One-shot autofocus then return to manual')
        BtnOnePush.setStyleSheet(_focus_style)
        BtnOnePush.clicked.connect(self.OnePushAF)

        # Manual Focus: locks focus, operator adjusts via camera menu
        BtnManualFocus = QPushButton('Manual\nFocus', self)
        BtnManualFocus.setGeometry(1750, 863, 110, 50)
        BtnManualFocus.setToolTip('Manual Focus mode')
        BtnManualFocus.setStyleSheet(_focus_style)
        BtnManualFocus.clicked.connect(self.ManualFocus)

        _exp_style = (
            "QPushButton{background-color: white; border: 2px solid #555; "
            "font: bold 13px; color: black; border-radius: 4px}"
            "QPushButton:pressed{background-color: #ccc}"
        )

        # Brightness Down: decreases exposure compensation by one step
        BtnDarker = QPushButton('▼ Darker', self)
        BtnDarker.setGeometry(1500, 920, 110, 45)
        BtnDarker.setToolTip('Decrease brightness')
        BtnDarker.setStyleSheet(_exp_style)
        BtnDarker.clicked.connect(self.BrightnessDown)

        # Backlight toggle: compensates for subjects lit from behind (contraluz).
        # Button colour reflects the current camera's backlight state.
        self.BtnBacklight = QPushButton('Backlight\nOFF', self)
        self.BtnBacklight.setGeometry(1625, 920, 110, 45)
        self.BtnBacklight.setToolTip('Toggle backlight compensation (contraluz)')
        # Two style sheets stored as attributes so _update_backlight_ui() can swap them
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

        # Brightness Up: increases exposure compensation by one step
        BtnBrighter = QPushButton('▲ Brighter', self)
        BtnBrighter.setGeometry(1750, 920, 110, 45)
        BtnBrighter.setToolTip('Increase brightness')
        BtnBrighter.setStyleSheet(_exp_style)
        BtnBrighter.clicked.connect(self.BrightnessUp)

        # ── Config / status buttons (bottom of right panel) ───────────────────
        # Clicking these labels opens a dialog to change the IP or camera ID.
        # Colour reflects whether the camera was reachable at startup.
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

        # Close application
        Version = QPushButton('Close window', self)
        Version.setGeometry(1500, 1050, 310, 22)
        Version.setStyleSheet(
            "background-color: lightgrey; font: 15px; color: black; border: none"
        )
        Version.clicked.connect(self.Quit)

        # Help button: shows the Contact.txt contents
        Help = QPushButton('?', self)
        Help.setGeometry(1815, 1050, 45, 22)
        Help.setStyleSheet(
            "background-color: lightgrey; font: 15px; color: black; border: none"
        )
        Help.clicked.connect(self.HelpMsg)

    # ─────────────────────────────────────────────────────────────────────────
    #  UI Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _arrow_btn(self, x, y, degrees):
        """
        Create a transparent push-button with a rotated arrow icon.
        `degrees` rotates the base arrow image (angle.png) clockwise.
        """
        btn = QPushButton(self)
        btn.setGeometry(x, y, 100, 100)
        btn.setStyleSheet("border: none; background: transparent")
        pix = QPixmap("angle.png").transformed(
            QtGui.QTransform().rotate(degrees), Qt.SmoothTransformation
        )
        btn.setIcon(QtGui.QIcon(pix))
        btn.setIconSize(QtCore.QSize(90, 90))
        return btn

    def _update_backlight_ui(self):
        """
        Refresh the Backlight button's label and colour to match the
        backlight state of whichever camera is currently selected.
        Called whenever the camera-selection buttons are clicked.
        """
        cam_key = 1 if self.Cam1.isChecked() else 2
        if self.backlight_on[cam_key]:
            self.BtnBacklight.setText('Backlight\nON')
            self.BtnBacklight.setStyleSheet(self._backlight_style_on)
        else:
            self.BtnBacklight.setText('Backlight\nOFF')
            self.BtnBacklight.setStyleSheet(self._backlight_style_off)

    # ─────────────────────────────────────────────────────────────────────────
    #  Core VISCA send helper
    # ─────────────────────────────────────────────────────────────────────────

    def _send_cmd(self, ip, cam_id_hex, cmd_suffix):
        """
        Open a TCP connection to the camera, send one VISCA command, read
        the acknowledgement, and close the socket.

        Args:
            ip          : Camera IP address string (e.g. "172.16.1.11")
            cam_id_hex  : Camera VISCA device ID as a hex string (e.g. "81")
            cmd_suffix  : Hex string for the command body after the device ID
                          (e.g. "01040722ff" for Zoom Tele slow)

        Returns:
            True  on success
            False on any network or OS error (caller may choose to alert user)
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(SOCKET_TIMEOUT)
                s.connect((ip, 5678))
                cmd = binascii.unhexlify(cam_id_hex + cmd_suffix)
                s.send(cmd)
                s.recv(131072)   # Read and discard the VISCA ACK/completion
            return True
        except (socket.timeout, socket.error, OSError):
            return False

    def _active_cam(self):
        """
        Return (ip, cam_id) for whichever camera is currently selected
        in the Camera Selection panel.
        """
        if self.Cam1.isChecked():
            return IPAddress, Cam1ID
        return IPAddress2, Cam2ID

    def _is_slow(self):
        """Return True if the SLOW speed button is checked."""
        return self.SpeedSlow.isChecked()

    # ─────────────────────────────────────────────────────────────────────────
    #   ErrorCapture() shows a generic
    #  warning so the operator knows something went wrong; ErrorCapture1/2
    #  continue to show camera-specific messages with the expected IP address.
    # ─────────────────────────────────────────────────────────────────────────

    def ErrorCapture(self):
        QMessageBox.warning(self, 'Camera Control Error',
                            'A network error occurred. Check camera connections.')

    def ErrorCapture1(self):
        QMessageBox.warning(self, 'Platform PTZ Control',
                            f'Check that the Platform Camera IP Address is set to '
                            f'"{IPAddress}" and ID 1.')

    def ErrorCapture2(self):
        QMessageBox.warning(self, 'Comments PTZ Control',
                            f'Check that the Comments Camera IP Address is set to '
                            f'"{IPAddress2}" and ID 2.')

    # Individual camera send helpers — used by legacy call paths that need
    # camera-specific error dialogs rather than the generic one.
    def Cam1Call(self):
        if not self._send_cmd(IPAddress, Cam1ID, "01060100000303FF"):
            self.ErrorCapture1()

    def Cam1aCall(self):
        if not self._send_cmd(IPAddress, Cam1ID, "01060100000303FF"):
            self.ErrorCapture1()

    def Cam2Call(self):
        if not self._send_cmd(IPAddress2, Cam2ID, "01060100000303FF"):
            self.ErrorCapture2()

    def Cam2aCall(self):
        if not self._send_cmd(IPAddress2, Cam2ID, "01060100000303FF"):
            self.ErrorCapture2()

    def Cam1Stop(self):
        # VISCA stop: <id>01060100000303FF
        self._send_cmd(IPAddress, Cam1ID, "01060100000303FF")

    def Cam2Stop(self):
        self._send_cmd(IPAddress2, Cam2ID, "01060100000303FF")

    # ─────────────────────────────────────────────────────────────────────────
    #  SESSION MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────

    def ToggleSession(self):
        """Start or end a broadcast session.

        Starting: powers both cameras ON, disables the button while cameras warm
        up (8 s), then moves both to Home and re-enables the button in green.

        Ending: asks for confirmation, sends standby to both cameras, resets UI."""
        if not self.session_active:
            # ── START session ────────────────────────────────────────────────
            self.session_active = True

            # Disable the button while cameras power up to prevent double-clicks
            self.BtnSession.setEnabled(False)
            self.BtnSession.setStyleSheet(
                "QPushButton{background-color: #555; border: 2px solid #333; "
                "font: bold 26px; color: #aaa; border-radius: 25px}"
            )
            self.SessionStatus.setText('Starting…')
            self.SessionStatus.setStyleSheet("font: bold 12px; color: #888")

            # VISCA power ON: <id>01040002FF
            self._send_cmd(IPAddress,  Cam1ID, "01040002FF")
            self._send_cmd(IPAddress2, Cam2ID, "01040002FF")

            # After 8 seconds both cameras should be ready to accept commands
            QtCore.QTimer.singleShot(8000, self._session_home)

        else:
            # ── END session ──────────────────────────────────────────────────
            reply = QMessageBox.question(
                self, 'End Session',
                'Power off both cameras and end the session?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # VISCA standby: <id>01040003FF
                self._send_cmd(IPAddress,  Cam1ID, "01040003FF")
                self._send_cmd(IPAddress2, Cam2ID, "01040003FF")
                self.session_active = False
                # Reset button to red / OFF state
                self.BtnSession.setStyleSheet(
                    "QPushButton{background-color: #8b1a1a; border: 2px solid #5a0d0d; "
                    "font: bold 26px; color: white; border-radius: 25px}"
                    "QPushButton:pressed{background-color: #5a0d0d}"
                )
                self.BtnSession.setToolTip('Start Session: Power ON both cameras and go Home')
                self.SessionStatus.setText('OFF')
                self.SessionStatus.setStyleSheet("font: bold 12px; color: #8b1a1a")
            # If the operator chose "No", nothing changes — button stays green/enabled.

    def _session_home(self):
        """
        Called 8 seconds after session start (via QTimer).
        Sends both cameras to their Home position and marks the session as fully ON.
        VISCA Home: <id>010604FF
        """
        self._send_cmd(IPAddress,  Cam1ID, "010604FF")
        self._send_cmd(IPAddress2, Cam2ID, "010604FF")
        # Update button to green / ON state
        self.BtnSession.setStyleSheet(
            "QPushButton{background-color: #1a7a1a; border: 2px solid #0d4d0d; "
            "font: bold 26px; color: white; border-radius: 25px}"
            "QPushButton:pressed{background-color: #0d4d0d}"
        )
        self.BtnSession.setToolTip('End Session: Power OFF (standby) both cameras')
        self.BtnSession.setEnabled(True)
        self.SessionStatus.setText('ON')
        self.SessionStatus.setStyleSheet("font: bold 12px; color: #1a7a1a")

    # ─────────────────────────────────────────────────────────────────────────
    #  FOCUS CONTROLS
    #  VISCA focus mode commands sent to whichever camera is active.
    # ─────────────────────────────────────────────────────────────────────────

    def AutoFocus(self):
        """Enable continuous autofocus"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01043802FF")

    def ManualFocus(self):
        """Switch to manual focus mode"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01043803FF")

    def OnePushAF(self):
        """Trigger one autofocus cycle, then return to manual"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01041801FF")

    # ─────────────────────────────────────────────────────────────────────────
    #  EXPOSURE CONTROLS
    # ─────────────────────────────────────────────────────────────────────────

    def BrightnessUp(self):
        """Increase exposure compensation by one step. VISCA: <id>01040D02FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01040D02FF")

    def BrightnessDown(self):
        """Decrease exposure compensation by one step. VISCA: <id>01040D03FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01040D03FF")

    def BacklightToggle(self):
        """
        Toggle backlight compensation (contraluz) for the active camera.
        Backlight ON  → VISCA: <id>01043302FF
        Backlight OFF → VISCA: <id>01043303FF
        State is tracked per camera so switching cameras shows the correct status.
        """
        ip, cam_id = self._active_cam()
        cam_key = 1 if self.Cam1.isChecked() else 2
        if self.backlight_on[cam_key]:
            self._send_cmd(ip, cam_id, "01043303FF")   # Turn backlight OFF
            self.backlight_on[cam_key] = False
        else:
            self._send_cmd(ip, cam_id, "01043302FF")   # Turn backlight ON
            self.backlight_on[cam_key] = True
        self._update_backlight_ui()

    # ─────────────────────────────────────────────────────────────────────────
    #  CAMERA MOVEMENT
    #  All movement methods:
    #    pressed  → send a continuous-move VISCA command
    #    released → send Stop (via Stop / ZoomStop)
    #  Speed byte differs between SLOW (0x04 pan / 0x04 tilt) and
    #  FAST (0x10 pan / 0x10 tilt).
    # ─────────────────────────────────────────────────────────────────────────

    def HomeButton(self):
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "010604FF")

    def UpLeft(self):
        ip, cam_id = self._active_cam()
        suffix = "01060104040101ff" if self._is_slow() else "01060110100101ff"
        self._send_cmd(ip, cam_id, suffix)

    def Up(self):
        ip, cam_id = self._active_cam()
        suffix = "01060100040301FF" if self._is_slow() else "01060100100301FF"
        self._send_cmd(ip, cam_id, suffix)

    def UpRight(self):
        ip, cam_id = self._active_cam()
        suffix = "01060104040201ff" if self._is_slow() else "01060110100201ff"
        self._send_cmd(ip, cam_id, suffix)

    def Left(self):
        ip, cam_id = self._active_cam()
        suffix = "01060104000103ff" if self._is_slow() else "01060110000103ff"
        self._send_cmd(ip, cam_id, suffix)

    def Right(self):
        ip, cam_id = self._active_cam()
        suffix = "01060104000203ff" if self._is_slow() else "01060110000203ff"
        self._send_cmd(ip, cam_id, suffix)

    def DownLeft(self):
        ip, cam_id = self._active_cam()
        suffix = "01060104040102ff" if self._is_slow() else "01060110100102ff"
        self._send_cmd(ip, cam_id, suffix)

    def Down(self):
        ip, cam_id = self._active_cam()
        suffix = "01060100040302ff" if self._is_slow() else "01060100100302ff"
        self._send_cmd(ip, cam_id, suffix)

    def DownRight(self):
        ip, cam_id = self._active_cam()
        suffix = "01060104040202ff" if self._is_slow() else "01060110100202ff"
        self._send_cmd(ip, cam_id, suffix)

    def Stop(self):
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01060100000303FF")

    def ZoomIn(self):
        ip, cam_id = self._active_cam()
        suffix = "01040722ff" if self._is_slow() else "01040726ff"
        self._send_cmd(ip, cam_id, suffix)

    def ZoomOut(self):
        ip, cam_id = self._active_cam()
        suffix = "01040732ff" if self._is_slow() else "01040736ff"
        self._send_cmd(ip, cam_id, suffix)

    def ZoomStop(self):
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01040700ff")

    # ─────────────────────────────────────────────────────────────────────────
    #  PRESET HANDLERS — Platform positions (Camera 1 only, presets 1-3)
    #
    #  NOTE: Go1/Go2/Go3 always target Camera 1 regardless of the Camera
    #  Selection panel.  These are physical platform positions (Chairman,
    #  Left, Right) that are only meaningful for the platform-facing camera.
    # ─────────────────────────────────────────────────────────────────────────

    def Go1(self):
        """Chairman preset (Camera 1 preset #1). Call or Set depending on mode."""
        if self.Set1.isChecked():
            # Call preset 1 → VISCA: 81 01 04 3F 02 01 FF
            self._send_cmd(IPAddress, Cam1ID, "01043f0201ff")
        elif self.Set2.isChecked():
            reply = QMessageBox.question(self, 'Record Chairman Position', "Are You Sure?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Set preset 1 → VISCA: 81 01 04 3F 01 01 FF
                self._send_cmd(IPAddress, Cam1ID, "01043f0101ff")

    def Go2(self):
        """Platform Left preset (Camera 1 preset #2). Call or Set depending on mode."""
        if self.Set1.isChecked():
            self._send_cmd(IPAddress, Cam1ID, "01043f0202ff")
        elif self.Set2.isChecked():
            reply = QMessageBox.question(self, 'Record Platform Left', "Are You Sure?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._send_cmd(IPAddress, Cam1ID, "01043f0102ff")

    def Go3(self):
        """Platform Right preset (Camera 1 preset #3). Call or Set depending on mode."""
        if self.Set1.isChecked():
            self._send_cmd(IPAddress, Cam1ID, "01043f0203ff")
        elif self.Set2.isChecked():
            reply = QMessageBox.question(self, 'Record Platform Right', "Are You Sure?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self._send_cmd(IPAddress, Cam1ID, "01043f0103ff")

    # ─────────────────────────────────────────────────────────────────────────
    #  PRESET HANDLER — Seat buttons (presets 4-128, respects camera selection)
    # ─────────────────────────────────────────────────────────────────────────

    def go_to_preset(self, preset_number):
        """
        Call or set a seat preset on the currently active camera.

        Call mode: moves camera to the stored position for `preset_number`.
        Set mode:  overwrites that preset with the camera's current position
                   (asks for confirmation first).

        VISCA Call: <id> 01 04 3F 02 <preset_hex> FF
        VISCA Set:  <id> 01 04 3F 01 <preset_hex> FF
        """
        preset_hex = PRESET_MAP.get(preset_number)
        if not preset_hex:
            return   # Preset number not in map — should not happen

        ip, cam_id = self._active_cam()

        if self.Set1.isChecked():
            # Call (recall) the preset
            self._send_cmd(ip, cam_id, "01043f02" + preset_hex + "ff")

        elif self.Set2.isChecked():
            # Set (record) the preset — confirm to avoid accidental overwrites
            cam_name = "Platform" if self.Cam1.isChecked() else "Comments"
            reply = QMessageBox.question(
                self, f'Record Preset {preset_number} ({cam_name})',
                "Are you sure you want to record this preset?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._send_cmd(ip, cam_id, "01043f01" + preset_hex + "ff")

    # ─────────────────────────────────────────────────────────────────────────
    #  CONFIG DIALOGS — change IP address or VISCA ID at runtime
    # ─────────────────────────────────────────────────────────────────────────

    def PTZ1Address(self):
        """ Let the operator change Camera 1's IP address."""
        result = QMessageBox.warning(
            self, 'Platform PTZ Control',
            'Do you want to change the IP address used to control the Platform camera?',
            QMessageBox.Ok, QMessageBox.Cancel
        )
        if result == QMessageBox.Ok:
            text, ok = QInputDialog.getText(
                self, 'Platform PTZ Control',
                f'New IP address for Platform Camera  (current: {IPAddress}):',
                text=IPAddress
            )
            if ok and text:
                if not _is_valid_ip(text):
                    QMessageBox.warning(self, 'Invalid IP Address',
                                        f'"{text}" is not a valid IPv4 address.\n'
                                        'Please enter four numbers separated by dots '
                                        '(e.g. 172.16.1.11).')
                    return
                with open("PTZ1IP.txt", "w") as f:
                    f.write(text.strip())
                # Restart the app to reload all config and re-check connectivity
                os.execv(sys.executable, ['python3'] + sys.argv)

    def PTZ2Address(self):
        """Let the operator change Camera 2's IP address."""
        result = QMessageBox.warning(
            self, 'Comments PTZ Control',
            'Do you want to change the IP address used to control the Comments camera?',
            QMessageBox.Ok, QMessageBox.Cancel
        )
        if result == QMessageBox.Ok:
            text, ok = QInputDialog.getText(
                self, 'Comments PTZ Control',
                f'New IP address for Comments Camera  (current: {IPAddress2}):',
                text=IPAddress2
            )
            if ok and text:
                if not _is_valid_ip(text):
                    QMessageBox.warning(self, 'Invalid IP Address',
                                        f'"{text}" is not a valid IPv4 address.\n'
                                        'Please enter four numbers separated by dots '
                                        '(e.g. 172.16.1.12).')
                    return
                with open("PTZ2IP.txt", "w") as f:
                    f.write(text.strip())
                os.execv(sys.executable, ['python3'] + sys.argv)

    def PTZ1IDchange(self):
        """ Let the operator change Camera 1's VISCA device ID.
        FIX 4 — Previously any text was saved without checking whether it was
        valid hex.  An invalid ID causes binascii.Error at next startup when
        VISCA commands are assembled.  We now validate with _is_valid_cam_id()."""
        result = QMessageBox.warning(
            self, 'Platform PTZ Control',
            'Do you want to change the VISCA ID used to control the Platform camera?',
            QMessageBox.Ok, QMessageBox.Cancel
        )
        if result == QMessageBox.Ok:
            text, ok = QInputDialog.getText(
                self, 'Platform PTZ Control',
                f'New VISCA ID for Platform Camera  (current: {Cam1ID}):',
                text=Cam1ID
            )
            if ok and text:
                if not _is_valid_cam_id(text):
                    QMessageBox.warning(self, 'Invalid Camera ID',
                                        f'"{text}" is not a valid hexadecimal ID.\n'
                                        'Please enter a hex value such as "81" or "82".')
                    return
                with open("Cam1ID.txt", "w") as f:
                    f.write(text.strip())
                os.execv(sys.executable, ['python3'] + sys.argv)

    def PTZ2IDchange(self):
    
        """Let the operator change Camera 2's VISCA device ID."""

        result = QMessageBox.warning(
            self, 'Comments PTZ Control',
            'Do you want to change the VISCA ID used to control the Comments camera?',
            QMessageBox.Ok, QMessageBox.Cancel
        )
        if result == QMessageBox.Ok:
            text, ok = QInputDialog.getText(
                self, 'Comments PTZ Control',
                f'New VISCA ID for Comments Camera  (current: {Cam2ID}):',
                text=Cam2ID
            )
            if ok and text:
                if not _is_valid_cam_id(text):
                    QMessageBox.warning(self, 'Invalid Camera ID',
                                        f'"{text}" is not a valid hexadecimal ID.\n'
                                        'Please enter a hex value such as "81" or "82".')
                    return
                with open("Cam2ID.txt", "w") as f:
                    f.write(text.strip())
                os.execv(sys.executable, ['python3'] + sys.argv)

    def Quit(self):
        """Close the application cleanly."""
        sys.exit()

    def HelpMsg(self):
        """Display the technical support contact from Contact.txt."""
        QMessageBox.information(self, 'For Technical Assistance', Contact, QMessageBox.Ok)


# ═════════════════════════════════════════════════════════════════════════════
#  GoButton — small numbered seat button used across the seating plan
# ═════════════════════════════════════════════════════════════════════════════

class GoButton(QPushButton):
    """
    A small (35×35 px) transparent push-button used for seat preset numbers
    and the platform Left/Right labels.
    """

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._setup(text)

    def _setup(self, text):
        self.setText(text)
        self.resize(35, 35)
        self.setStyleSheet(
            "background-color: rgba(0,0,0,10); border: 0px solid black; "
            "border-radius: 5px; font: 14px; font-weight: bold; color:" + ButtonColor
        )


# ═════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # Uncomment the line below (and comment out show()) to run full-screen
    # on the production Raspberry Pi touchscreen:
    # window.showFullScreen()
    sys.exit(app.exec_())