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
#    - Session Management: single button toggles ON/OFF
#        ON:  Power both cameras, wait 8 s, go Home
#        OFF: Power both cameras to standby
#    - Focus & Exposure panel: Auto Focus / One Push AF / Manual Focus,
#        Brightness Up/Down, Backlight toggle per camera
#    - Speed control: continuous QSlider (SLOW to FAST) replaces the old
#        two-button pair.  Pan/tilt speed 1-18 and zoom speed 1-7 are both
#        derived from the same slider value so all axes scale proportionally.
#
#  Config files (must exist in the working directory):
#    PTZ1IP.txt   IP address of the Platform camera  (default 172.16.1.11)
#    PTZ2IP.txt   IP address of the Comments camera  (default 172.16.1.12)
#    Cam1ID.txt   VISCA hex device ID for Camera 1   (e.g. "81")
#    Cam2ID.txt   VISCA hex device ID for Camera 2   (e.g. "82")
#    Contact.txt  Support contact shown in Help dialog
#
# ─────────────────────────────────────────────────────────────────────────────

import os
import re
import sys
import socket
import binascii
import threading

import PyQt5
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton,
    QLabel, QMessageBox, QButtonGroup, QInputDialog, QSlider
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


# ─────────────────────────────────────────────────────────────────────────────
#  Speed slider constants
#
#  SPEED_MIN / SPEED_MAX define the range of the pan/tilt speed byte in VISCA
#  Pan-Tilt Drive commands.  The VISCA spec allows 0x01-0x18 (1-24) for pan
#  and 0x01-0x14 (1-20) for tilt; we cap at 18 so the value is safe for both.
#
#  SPEED_DEFAULT is the position the slider starts at on launch.
#  Value 8 sits comfortably in the mid-range; the old "SLOW" was 4, "FAST" 16.
#
#  Zoom speed occupies the low nibble of the zoom byte (valid range 0-7).
#  It is derived from the pan/tilt slider via linear interpolation so both
#  axes always feel proportional to each other.
# ─────────────────────────────────────────────────────────────────────────────
SPEED_MIN     = 1   # Slowest pan/tilt speed (VISCA minimum is 1)
SPEED_MAX     = 18  # Fastest safe pan/tilt speed (ceiling for both axes)
SPEED_DEFAULT = 8   # Slider starts here; roughly medium pace


# ─────────────────────────────────────────────────────────────────────────────
#  Shared network constant
# ─────────────────────────────────────────────────────────────────────────────
SOCKET_TIMEOUT = 1  # Seconds used for every TCP connect / send / recv call


# ─────────────────────────────────────────────────────────────────────────────
#  Config helpers
# ─────────────────────────────────────────────────────────────────────────────

def _read_config(filename, default):
    """
    Read a single-line text config file; return its stripped contents.
    If the file is missing or unreadable, log a warning and return `default`.
    The application remains functional even when config files are absent.
    """
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except (FileNotFoundError, IOError) as exc:
        print(f"[WARNING] Could not read '{filename}': {exc}  -> using default '{default}'")
        return default


IPAddress  = _read_config('PTZ1IP.txt',  '172.16.1.11')   # Platform camera IP
IPAddress2 = _read_config('PTZ2IP.txt',  '172.16.1.12')   # Comments camera IP
Cam1ID     = _read_config('Cam1ID.txt',  '81')             # VISCA device ID hex string
Cam2ID     = _read_config('Cam2ID.txt',  '82')
Contact    = _read_config('Contact.txt', 'No contact information available.')

ButtonColor = "black"   # Seat-button text colour


# ─────────────────────────────────────────────────────────────────────────────
#  Startup camera connectivity check
# ─────────────────────────────────────────────────────────────────────────────

def _check_camera(ip, cam_id):
    """
    Try a one-shot TCP connection to verify a camera is reachable at startup.
    Sends a VISCA power-status inquiry and discards the reply.
    Returns "Green" if the camera responded within SOCKET_TIMEOUT, else "Red".
    The returned string is used directly as a Qt CSS colour for the address label.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(SOCKET_TIMEOUT)
            s.connect((ip, 5678))
            s.send(binascii.unhexlify(cam_id + "090400FF"))   # VISCA power inquiry
            s.recv(131072)
        return "Green"
    except (socket.timeout, socket.error, OSError):
        return "Red"


Cam1Check = _check_camera(IPAddress,  Cam1ID)
Cam2Check = _check_camera(IPAddress2, Cam2ID)


# ─────────────────────────────────────────────────────────────────────────────
#  VISCA preset number -> hex byte mapping
#
#  Presets 90-99 would land in the VISCA-reserved range 0x5A-0x8B, so they
#  are remapped to 0x8C-0x95.  All others use direct two-digit hex conversion.
# ─────────────────────────────────────────────────────────────────────────────
PRESET_MAP = {}
for _i in range(1, 4):       # Platform presets: Chairman(1), Left(2), Right(3)
    PRESET_MAP[_i] = f"{_i:02X}"
for _i in range(4, 90):
    PRESET_MAP[_i] = f"{_i:02X}"
for _i in range(90, 100):
    PRESET_MAP[_i] = f"{0x8C + (_i - 90):02X}"
for _i in range(100, 130):
    PRESET_MAP[_i] = f"{_i:02X}"


# ─────────────────────────────────────────────────────────────────────────────
#  Validation helpers (used in the config dialogs)
# ─────────────────────────────────────────────────────────────────────────────

def _is_valid_ip(text):
    """
    Return True if text looks like a valid IPv4 address (four octets, each 0-255).
    Does not perform DNS resolution or reachability testing.
    """
    match = re.match(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$', text.strip())
    if not match:
        return False
    return all(0 <= int(g) <= 255 for g in match.groups())


def _is_valid_cam_id(text):
    """
    Return True if text is a non-empty hexadecimal string (e.g. "81", "82").
    VISCA device IDs are typically one byte written as two hex digits.
    An invalid ID would cause binascii.Error when VISCA commands are assembled.
    """
    text = text.strip()
    if not text:
        return False
    try:
        binascii.unhexlify(text)
        return True
    except (binascii.Error, ValueError):
        return False


# =============================================================================
#  MainWindow
# =============================================================================

class MainWindow(QMainWindow):
    """
    Main application window (1920x1080).

    Layout:
      Left area  (x 0-1460)  : Seat-position preset buttons on a background image.
      Right panel (x 1500+)  : Camera selection, speed slider, preset mode,
                               PTZ arrows, zoom, focus/exposure, config buttons.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Camera Controls')
        self.setGeometry(0, 0, 1920, 1080)

        # Per-camera backlight compensation state (True = ON).
        # Stored here so the Backlight button label stays correct when the
        # operator switches between Camera 1 and Camera 2.
        self.backlight_on = {1: False, 2: False}

        # ── Background image ──────────────────────────────────────────────────
        # Scales the seating-plan JPEG to fill the window behind all widgets.
        pixmap = QPixmap("Background_ISL_v2.jpg")
        scaled_pixmap = pixmap.scaled(1920, 1080, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        background = QLabel(self)
        background.setPixmap(scaled_pixmap)
        background.setGeometry(0, -30, 1920, 1080)
        background.lower()   # Push behind every other widget

        # ── Seat pixel positions ──────────────────────────────────────────────
        # Maps preset number -> (x, y) top-left corner of its button on screen.
        seat_positions = {
            # Row 1
             4:(70,210),  5:(131,210),  6:(192,210),  7:(253,210),
             8:(479,210), 9:(540,210), 10:(601,210), 11:(662,210),
            12:(722,210),13:(783,210), 14:(844,210),
            15:(1070,210),16:(1130,210),17:(1191,210),18:(1252,210),
            # Row 2
            19:(70,295), 20:(131,295), 21:(192,295), 22:(253,295),
            23:(479,295),24:(540,295), 25:(601,295), 26:(662,295),
            27:(722,295),28:(783,295), 29:(844,295),
            30:(1070,295),31:(1130,295),32:(1191,295),33:(1252,295),
            # Row 3
            34:(70,382), 35:(131,382), 36:(192,382), 37:(253,382),
            38:(479,382),39:(540,382), 40:(601,382), 41:(662,382),
            42:(723,382),43:(783,382), 44:(844,382),
            45:(1070,382),46:(1130,382),47:(1191,382),48:(1252,382),
            # Row 4
            49:(70,465), 50:(131,465), 51:(192,465), 52:(253,465),
            53:(479,465),54:(540,465), 55:(601,465), 56:(662,465),
            57:(722,465),58:(783,465), 59:(844,465),
            60:(1070,465),61:(1130,465),62:(1191,465),63:(1252,465),
            # Row 5
            64:(70,550), 65:(131,550), 66:(192,550), 67:(253,550),
            68:(479,550),69:(540,550), 70:(601,550), 71:(662,550),
            72:(722,550),73:(783,550), 74:(844,550),
            75:(1070,550),76:(1130,550),77:(1191,550),78:(1252,550),
            # Row 6
            79:(70,635), 80:(131,635), 81:(192,635), 82:(253,635),
            83:(479,635),84:(540,635), 85:(601,635), 86:(662,635),
            87:(722,635),88:(783,635), 89:(844,635),
            90:(1070,635),91:(1130,635),92:(1191,635),93:(1252,635),
            # Row 7
            94:(70,720), 95:(131,720), 96:(192,720), 97:(253,720),
            98:(479,720),99:(540,720),100:(601,720),101:(662,720),
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
           # Second Room
           129:(445,975),
        }

        # ── Platform preset buttons (Chairman, Left, Right) ─────────────────────
        # These use the original working style and connect to go_to_preset.
        Preset1 = QPushButton('Chairman', self)
        Preset1.resize(110, 110)
        Preset1.move(623, 35)
        Preset1.setStyleSheet(
            "background-color: rgba(0,0,0,0); font: 14px; font-weight: bold; "
            "color: black; padding-top: 70px"
        )
        Preset1.clicked.connect(lambda: self.go_to_preset(1))

        Preset2 = QPushButton('Left', self)
        Preset2.resize(110, 110)
        Preset2.move(460, 35)
        Preset2.setStyleSheet(
            "background-color: rgba(0,0,0,0); font: 14px; font-weight: bold; "
            "color: black; padding-top: 70px"
        )
        Preset2.clicked.connect(lambda: self.go_to_preset(2))

        Preset3 = QPushButton('Right', self)
        Preset3.resize(110, 110)
        Preset3.move(803, 35)
        Preset3.setStyleSheet(
            "background-color: rgba(0,0,0,0); font: 14px; font-weight: bold; "
            "color: black; padding-top: 70px"
        )
        Preset3.clicked.connect(lambda: self.go_to_preset(3))

        # ── Seat buttons (one per entry in seat_positions) ────────────────────
        # Presets 1-3 (Chairman, Left, Right) are included here;
        # go_to_preset() always routes them to Camera 1.
        for seat_number in range(4, 130):
            if seat_number not in seat_positions:
                continue
            x, y = seat_positions[seat_number]
            button = GoButton(str(seat_number), self)
            button.move(x, y)

            # Seat 129 (Second Room): QToolButton so icon sits above text natively
            if seat_number == 129:
                from PyQt5.QtWidgets import QToolButton
                button.hide()          # hide the GoButton placeholder
                button = QToolButton(self)
                button.move(x, y)
                button.resize(55, 65)
                button.setText('Second Room')
                button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
                button.setStyleSheet(
                    "QToolButton { background-color: rgba(0,0,0,10); border: 0px solid black; "
                    "border-radius: 5px; font: 8px; font-weight: bold; color: " + ButtonColor + "; }"
                )
                pix = QPixmap("second_room.png").scaled(
                    40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                button.setIcon(QtGui.QIcon(pix))
                button.setIconSize(QtCore.QSize(40, 40))

            # Default-argument trick captures the loop variable correctly
            button.clicked.connect(
                lambda checked=False, n=seat_number: self.go_to_preset(n)
            )
            setattr(self, f"Seat{seat_number}", button)   # Prevent GC

        # ── SESSION MANAGEMENT — top-left corner ──────────────────────────────
        self.session_active = False

        self.BtnSession = QPushButton('\u23fb', self)   # Unicode power symbol
        self.BtnSession.setGeometry(10, 10, 50, 50)
        self.BtnSession.setToolTip('Start Session: Power ON both cameras and go Home')
        self.BtnSession.setStyleSheet(
            "QPushButton{background-color: #8b1a1a; border: 2px solid #5a0d0d; "
            "font: bold 26px; color: white; border-radius: 25px}"
            "QPushButton:pressed{background-color: #5a0d0d}"
        )
        self.BtnSession.clicked.connect(self.ToggleSession)

        self.SessionStatus = QLabel('OFF', self)
        self.SessionStatus.setGeometry(68, 22, 60, 20)
        self.SessionStatus.setStyleSheet("font: bold 12px; color: #8b1a1a")

        # ── RIGHT PANEL — Section labels ──────────────────────────────────────
        for text, geom in [
            ('Camera Selection', (1500,  20, 360, 30)),
            ('PTZ Speed',        (1500, 138, 360, 30)),
            ('Camera Presets',   (1500, 253, 360, 30)),
            ('Camera Controls',  (1500, 367, 360, 30)),
        ]:
            lbl = QLabel(text, self)
            lbl.setGeometry(*geom)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet("font: bold 20px; color: black")

        # ── RIGHT PANEL — Camera Selection ────────────────────────────────────
        _cam_style = (
            "QPushButton{background-color: white; border: 3px solid green; "
            "font: bold 20px; color: black}"
            "QPushButton:Checked{background-color: green; font: bold 20px; color: white}"
        )

        self.Cam1 = QPushButton('Platform', self)
        self.Cam1.setGeometry(1500, 60, 180, 70)
        self.Cam1.setCheckable(True)
        self.Cam1.setAutoExclusive(True)
        self.Cam1.setChecked(True)
        self.Cam1.setToolTip('Select Platform Camera')
        self.Cam1.setStyleSheet(_cam_style)

        self.Cam2 = QPushButton('Comments', self)
        self.Cam2.setGeometry(1680, 60, 180, 70)
        self.Cam2.setCheckable(True)
        self.Cam2.setAutoExclusive(True)
        self.Cam2.setToolTip('Select Comments Camera')
        self.Cam2.setStyleSheet(_cam_style)

        Camgroup = QButtonGroup(self)
        Camgroup.addButton(self.Cam1)
        Camgroup.addButton(self.Cam2)

        # Refresh the Backlight button label whenever the active camera changes
        self.Cam1.clicked.connect(self._update_backlight_ui)
        self.Cam2.clicked.connect(self._update_backlight_ui)

        # ── RIGHT PANEL — PTZ Speed Slider ────────────────────────────────────
        #
        #
        #  The slider exposes a continuous integer range [SPEED_MIN, SPEED_MAX]
        #  (default 1-18).  Moving the handle to the left slows all camera
        #  movements; moving it to the right speeds them up.
        #
        #  The pan/tilt speed byte in VISCA Pan-Tilt Drive commands is set
        #  directly to this value.  The zoom speed nibble (0-7) is derived via
        #  linear interpolation so both axes always feel proportional.
        #
        #  Visual layout inside the 360 px-wide right panel (x 1500-1860):
        #
        #   x=1500        x=1560                  x=1790  x=1860
        #     SLOW  |====== green slider track ======|  FAST
        #                  Speed: 8  (medium)
        #
        # ── Left end-label: "SLOW" ────────────────────────────────────────────
        SlowLabel = QLabel('SLOW', self)
        SlowLabel.setGeometry(1500, 190, 55, 20)
        SlowLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        SlowLabel.setStyleSheet("font: bold 13px; color: #444")

        # ── QSlider (horizontal, green handle) ───────────────────────────────
        self.SpeedSlider = QSlider(Qt.Horizontal, self)
        self.SpeedSlider.setGeometry(1560, 172, 230, 48)
        self.SpeedSlider.setMinimum(SPEED_MIN)
        self.SpeedSlider.setMaximum(SPEED_MAX)
        self.SpeedSlider.setValue(SPEED_DEFAULT)
        # Tick marks appear below the groove; one tick every 3 steps
        self.SpeedSlider.setTickPosition(QSlider.TicksBelow)
        self.SpeedSlider.setTickInterval(3)
        self.SpeedSlider.setToolTip(
            f'Drag to set PTZ speed  (min {SPEED_MIN} = slowest  /  max {SPEED_MAX} = fastest)'
        )
        # Green palette to match the rest of the right-panel controls
        self.SpeedSlider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #cccccc;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #1a7a1a;
                border: 2px solid #0d4d0d;
                width: 24px;
                height: 24px;
                margin: -9px 0;
                border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #4caf50;
                border-radius: 4px;
            }
        """)

        # ── Right end-label: "FAST" ───────────────────────────────────────────
        FastLabel = QLabel('FAST', self)
        FastLabel.setGeometry(1797, 190, 55, 20)
        FastLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        FastLabel.setStyleSheet("font: bold 13px; color: #444")

        # ── Numeric readout ───────────────────────────────────────────────────
        # Shows the exact speed value and a plain-English description so
        # operators always know where they are on the scale at a glance.
        # Updated in real time via the slider's valueChanged signal.
        self.SpeedValueLabel = QLabel(self._speed_label_text(SPEED_DEFAULT), self)
        self.SpeedValueLabel.setGeometry(1500, 224, 360, 20)
        self.SpeedValueLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.SpeedValueLabel.setStyleSheet("font: 12px; color: #555")

        # Wire the slider so the readout updates immediately as the handle moves
        self.SpeedSlider.valueChanged.connect(self._on_speed_changed)

        # ── RIGHT PANEL — Preset mode (Call / Set) ────────────────────────────
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
        # pressed -> start zoom command;  released -> ZoomStop
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
        # pressed -> send continuous-move command;  released -> Stop
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

        BtnAutoFocus = QPushButton('Auto\nFocus', self)
        BtnAutoFocus.setGeometry(1500, 863, 110, 50)
        BtnAutoFocus.setToolTip('Enable continuous autofocus')
        BtnAutoFocus.setStyleSheet(_focus_style)
        BtnAutoFocus.clicked.connect(self.AutoFocus)

        BtnOnePush = QPushButton('One Push\nAF', self)
        BtnOnePush.setGeometry(1625, 863, 110, 50)
        BtnOnePush.setToolTip('One-shot autofocus then return to manual')
        BtnOnePush.setStyleSheet(_focus_style)
        BtnOnePush.clicked.connect(self.OnePushAF)

        BtnManualFocus = QPushButton('Manual\nFocus', self)
        BtnManualFocus.setGeometry(1750, 863, 110, 50)
        BtnManualFocus.setToolTip('Lock to manual focus mode')
        BtnManualFocus.setStyleSheet(_focus_style)
        BtnManualFocus.clicked.connect(self.ManualFocus)

        _exp_style = (
            "QPushButton{background-color: white; border: 2px solid #555; "
            "font: bold 13px; color: black; border-radius: 4px}"
            "QPushButton:pressed{background-color: #ccc}"
        )

        BtnDarker = QPushButton('\u25bc Darker', self)
        BtnDarker.setGeometry(1500, 920, 110, 45)
        BtnDarker.setToolTip('Decrease exposure compensation one step')
        BtnDarker.setStyleSheet(_exp_style)
        BtnDarker.clicked.connect(self.BrightnessDown)

        # Backlight toggle: colour changes to amber when ON to make the state
        # immediately obvious across the room.
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

        BtnBrighter = QPushButton('\u25b2 Brighter', self)
        BtnBrighter.setGeometry(1750, 920, 110, 45)
        BtnBrighter.setToolTip('Increase exposure compensation one step')
        BtnBrighter.setStyleSheet(_exp_style)
        BtnBrighter.clicked.connect(self.BrightnessUp)

        # ── Config / status buttons (bottom of right panel) ───────────────────
        # Green = camera was reachable at startup; Red = not reachable.
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

    # -------------------------------------------------------------------------
    #  Speed helpers
    # -------------------------------------------------------------------------

    def _speed_label_text(self, value):
        """
        Build the human-readable string shown below the speed slider.

        Shows the raw numeric value and a plain-English word so operators can
        judge at a glance whether they are near the slow or fast end of the range.

        Examples:
            value=1  -> "Speed: 1  (minimum)"
            value=8  -> "Speed: 8  (medium)"
            value=18 -> "Speed: 18  (maximum)"
        """
        mid = (SPEED_MIN + SPEED_MAX) / 2
        if value <= SPEED_MIN:
            desc = "minimum"
        elif value >= SPEED_MAX:
            desc = "maximum"
        elif value < mid - 2:
            desc = "slow"
        elif value > mid + 2:
            desc = "fast"
        else:
            desc = "medium"
        return f"Speed: {value}  ({desc})"

    def _on_speed_changed(self, value):
        """
        Slot connected to SpeedSlider.valueChanged.
        Updates the numeric readout label immediately as the slider handle moves.
        """
        self.SpeedValueLabel.setText(self._speed_label_text(value))

    def _get_speed(self):
        """
        Return the current pan/tilt speed as an integer in [SPEED_MIN, SPEED_MAX].

        This integer is inserted directly as both the pan-speed byte and the
        tilt-speed byte inside VISCA Pan-Tilt Drive commands:
            <id> 01 06 01 <pan_spd> <tilt_spd> <pan_dir> <tilt_dir> FF

        When only one axis is moving, the stopped axis always sends 0x00 for
        its speed byte; only the active axis uses this value.
        """
        return self.SpeedSlider.value()

    def _get_zoom_speed(self):
        """
        Map the pan/tilt slider (SPEED_MIN to SPEED_MAX) to a zoom speed nibble
        (1 to 7) via linear interpolation.

        VISCA zoom commands encode direction and speed in one byte:
            Zoom tele: <id> 01 04 07 2<spd> FF   (e.g. 0x22 = tele at speed 2)
            Zoom wide: <id> 01 04 07 3<spd> FF   (e.g. 0x36 = wide at speed 6)
        Speed nibble 0 means stop, so we clamp to a minimum of 1 to guarantee
        visible movement whenever the operator presses a zoom button.
        """
        raw = round(self.SpeedSlider.value() * 7 / SPEED_MAX)
        return max(1, min(7, raw))

    # -------------------------------------------------------------------------
    #  UI helpers
    # -------------------------------------------------------------------------

    def _arrow_btn(self, x, y, degrees):
        """
        Create a 100x100 transparent push-button with a rotated arrow icon.
        `degrees` rotates angle.png clockwise so all eight directions share one image.
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
        Refresh the Backlight button's label and colour to reflect the backlight
        state of whichever camera is currently selected.
        Called whenever the Platform / Comments camera buttons are clicked.
        """
        cam_key = 1 if self.Cam1.isChecked() else 2
        if self.backlight_on[cam_key]:
            self.BtnBacklight.setText('Backlight\nON')
            self.BtnBacklight.setStyleSheet(self._backlight_style_on)
        else:
            self.BtnBacklight.setText('Backlight\nOFF')
            self.BtnBacklight.setStyleSheet(self._backlight_style_off)

    # -------------------------------------------------------------------------
    #  Core VISCA send helper
    # -------------------------------------------------------------------------

    def _send_cmd(self, ip, cam_id_hex, cmd_suffix):
        """
        Fire-and-forget: launches the network call in a daemon thread so the
        UI never blocks waiting for the camera to respond.
        """
        threading.Thread(
            target=self._send_cmd_blocking,
            args=(ip, cam_id_hex, cmd_suffix),
            daemon=True
        ).start()

    def _send_cmd_blocking(self, ip, cam_id_hex, cmd_suffix):
        """
        Blocking network call — runs in a background thread.
        Opens a TCP connection, sends the VISCA command, reads the ACK,
        and closes the socket. Errors are silently ignored so a lost
        packet never crashes the UI.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(SOCKET_TIMEOUT)
                s.connect((ip, 5678))
                s.send(binascii.unhexlify(cam_id_hex + cmd_suffix))
                s.recv(131072)   # Read and discard the VISCA ACK / completion reply
        except (socket.timeout, socket.error, OSError):
            pass

    def _active_cam(self):
        """Return (ip, cam_id) for whichever camera is currently selected."""
        if self.Cam1.isChecked():
            return IPAddress, Cam1ID
        return IPAddress2, Cam2ID

    # -------------------------------------------------------------------------
    #  Error dialogs
    # -------------------------------------------------------------------------

    def ErrorCapture(self):
        QMessageBox.warning(self, 'Camera Control Error',
                            'A network error occurred. Check camera connections.')

    def ErrorCapture1(self):
        QMessageBox.warning(self, 'Platform PTZ Control',
                            f'Check that the Platform Camera IP is "{IPAddress}" and ID 1.')

    def ErrorCapture2(self):
        QMessageBox.warning(self, 'Comments PTZ Control',
                            f'Check that the Comments Camera IP is "{IPAddress2}" and ID 2.')

    # Thin stop helpers retained for any future callers; they delegate to _send_cmd.
    def Cam1Stop(self): self._send_cmd(IPAddress,  Cam1ID, "01060100000303FF")
    def Cam2Stop(self): self._send_cmd(IPAddress2, Cam2ID, "01060100000303FF")

    # -------------------------------------------------------------------------
    #  SESSION MANAGEMENT
    # -------------------------------------------------------------------------

    def ToggleSession(self):
        """
        Toggle the broadcast session ON or OFF.

        ON path:
          1. Sets the flag, disables the button to prevent double-clicks.
          2. Sends VISCA Power-ON to both cameras.
          3. After 8 seconds (QTimer) moves both cameras to Home and re-enables.

        OFF path:
          1. Asks for confirmation.
          2. Sends VISCA Standby to both cameras.
          3. Resets the button to its red / OFF appearance.
        """
        if not self.session_active:
            self.session_active = True
            self.BtnSession.setEnabled(False)
            self.BtnSession.setStyleSheet(
                "QPushButton{background-color: #555; border: 2px solid #333; "
                "font: bold 26px; color: #aaa; border-radius: 25px}"
            )
            self.SessionStatus.setText('Starting...')
            self.SessionStatus.setStyleSheet("font: bold 12px; color: #888")
            # VISCA Power ON: <id> 01 04 00 02 FF
            self._send_cmd(IPAddress,  Cam1ID, "01040002FF")
            self._send_cmd(IPAddress2, Cam2ID, "01040002FF")
            # Non-blocking 8-second wait; UI remains responsive during warm-up
            QtCore.QTimer.singleShot(8000, self._session_home)

        else:
            reply = QMessageBox.question(
                self, 'End Session',
                'Power off both cameras and end the session?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # VISCA Standby: <id> 01 04 00 03 FF
                self._send_cmd(IPAddress,  Cam1ID, "01040003FF")
                self._send_cmd(IPAddress2, Cam2ID, "01040003FF")
                self.session_active = False
                self.BtnSession.setStyleSheet(
                    "QPushButton{background-color: #8b1a1a; border: 2px solid #5a0d0d; "
                    "font: bold 26px; color: white; border-radius: 25px}"
                    "QPushButton:pressed{background-color: #5a0d0d}"
                )
                self.BtnSession.setToolTip('Start Session: Power ON both cameras and go Home')
                self.SessionStatus.setText('OFF')
                self.SessionStatus.setStyleSheet("font: bold 12px; color: #8b1a1a")

    def _session_home(self):
        """
        Called 8 seconds after session start (via QTimer.singleShot).
        Sends both cameras to their Home position and marks the session fully ON.
        VISCA Home: <id> 01 06 04 FF
        """
        self._send_cmd(IPAddress,  Cam1ID, "010604FF")
        self._send_cmd(IPAddress2, Cam2ID, "010604FF")
        self.BtnSession.setStyleSheet(
            "QPushButton{background-color: #1a7a1a; border: 2px solid #0d4d0d; "
            "font: bold 26px; color: white; border-radius: 25px}"
            "QPushButton:pressed{background-color: #0d4d0d}"
        )
        self.BtnSession.setToolTip('End Session: Power OFF (standby) both cameras')
        self.BtnSession.setEnabled(True)
        self.SessionStatus.setText('ON')
        self.SessionStatus.setStyleSheet("font: bold 12px; color: #1a7a1a")

    # -------------------------------------------------------------------------
    #  FOCUS CONTROLS
    # -------------------------------------------------------------------------

    def AutoFocus(self):
        """Enable continuous autofocus.  VISCA: <id> 01 04 38 02 FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01043802FF")

    def ManualFocus(self):
        """Lock to manual focus mode.  VISCA: <id> 01 04 38 03 FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01043803FF")

    def OnePushAF(self):
        """Trigger one AF cycle then stay in manual.  VISCA: <id> 01 04 18 01 FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01041801FF")

    # -------------------------------------------------------------------------
    #  EXPOSURE CONTROLS
    # -------------------------------------------------------------------------

    def BrightnessUp(self):
        """Increase exposure compensation one step.  VISCA: <id> 01 04 0D 02 FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01040D02FF")

    def BrightnessDown(self):
        """Decrease exposure compensation one step.  VISCA: <id> 01 04 0D 03 FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01040D03FF")

    def BacklightToggle(self):
        """
        Toggle backlight compensation for the active camera.
          Backlight ON  -> VISCA: <id> 01 04 33 02 FF
          Backlight OFF -> VISCA: <id> 01 04 33 03 FF
        State is tracked independently per camera in self.backlight_on.
        """
        ip, cam_id = self._active_cam()
        cam_key = 1 if self.Cam1.isChecked() else 2
        if self.backlight_on[cam_key]:
            self._send_cmd(ip, cam_id, "01043303FF")   # Turn OFF
            self.backlight_on[cam_key] = False
        else:
            self._send_cmd(ip, cam_id, "01043302FF")   # Turn ON
            self.backlight_on[cam_key] = True
        self._update_backlight_ui()

    # -------------------------------------------------------------------------
    #  CAMERA MOVEMENT
    #
    #  All methods build the VISCA command dynamically using the speed value
    #  read from the slider at the moment the button is pressed, so the full
    #  continuous range is available without any binary switching logic.
    #
    #  VISCA Pan-Tilt Drive format:
    #      <id> 01 06 01 <pan_spd> <tilt_spd> <pan_dir> <tilt_dir> FF
    #
    #  Direction nibbles:
    #      Pan:  01 = left   02 = right   03 = stop
    #      Tilt: 01 = up     02 = down    03 = stop
    #
    #  For single-axis moves the idle axis gets speed byte 0x00 (the camera
    #  ignores the speed for a stopped axis, but explicit zero is cleaner).
    # -------------------------------------------------------------------------

    def HomeButton(self):
        """Move camera to its factory Home position.  VISCA: <id> 01 06 04 FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "010604FF")

    def _move(self, pan_dir, tilt_dir):
        """
        Send a VISCA Pan-Tilt Drive command for any direction.

        pan_dir / tilt_dir nibbles:
            01 = left/up   02 = right/down   03 = stop

        Single-axis moves pass speed only on the active axis;
        the stopped axis always gets 0x00.
        Diagonal moves use full speed on both axes.
        """
        ip, cam_id = self._active_cam()
        spd = self._get_speed()
        pan_spd  = 0  if pan_dir  == 0x03 else spd
        tilt_spd = 0  if tilt_dir == 0x03 else spd
        self._send_cmd(ip, cam_id,
            f"010601{pan_spd:02X}{tilt_spd:02X}{pan_dir:02X}{tilt_dir:02X}FF")

    # Direction wrappers — connected to arrow button pressed/released signals
    def Up(self):        self._move(0x03, 0x01)
    def Down(self):      self._move(0x03, 0x02)
    def Left(self):      self._move(0x01, 0x03)
    def Right(self):     self._move(0x02, 0x03)
    def UpLeft(self):    self._move(0x01, 0x01)
    def UpRight(self):   self._move(0x02, 0x01)
    def DownLeft(self):  self._move(0x01, 0x02)
    def DownRight(self): self._move(0x02, 0x02)

    def Stop(self):
        """Stop all pan/tilt movement (sent on button release).
        VISCA: <id> 01 06 01 00 00 03 03 FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01060100000303FF")

    # -- Zoom -----------------------------------------------------------------
    #
    #  VISCA Zoom format:  <id> 01 04 07 <zoom_byte> FF
    #    zoom_byte = 0x2<spd>  tele (zoom in),  e.g. 0x22 = tele at speed 2
    #    zoom_byte = 0x3<spd>  wide (zoom out), e.g. 0x36 = wide at speed 6
    #    zoom_byte = 0x00      stop
    #
    #  Zoom speed nibble (1-7) is derived from the slider via _get_zoom_speed().

    def ZoomIn(self):
        """
        Start zooming in (tele) at a speed proportional to the slider.
        zoom_byte = 0x20 | zoom_speed   e.g. speed 3 -> byte 0x23
        """
        ip, cam_id = self._active_cam()
        zspd = self._get_zoom_speed()
        self._send_cmd(ip, cam_id, f"010407{0x20 | zspd:02X}FF")

    def ZoomOut(self):
        """
        Start zooming out (wide) at a speed proportional to the slider.
        zoom_byte = 0x30 | zoom_speed   e.g. speed 3 -> byte 0x33
        """
        ip, cam_id = self._active_cam()
        zspd = self._get_zoom_speed()
        self._send_cmd(ip, cam_id, f"010407{0x30 | zspd:02X}FF")

    def ZoomStop(self):
        """Stop zoom movement.  VISCA: <id> 01 04 07 00 FF"""
        ip, cam_id = self._active_cam()
        self._send_cmd(ip, cam_id, "01040700FF")

    # -------------------------------------------------------------------------
    #  PRESET HANDLER — All seat buttons (presets 1-129)
#
#  Presets 1-3 (Chairman, Left, Right) always target Camera 1.
#  Presets 4-129 target whichever camera is currently selected.
    # -------------------------------------------------------------------------

    def go_to_preset(self, preset_number):
        """
        Call or set a preset on the active camera.
        Presets 1-3 always use Camera 1 (platform positions).
        All others use the camera selected in the Camera Selection panel.

        Call mode (Set1 checked):
            VISCA Recall: <id> 01 04 3F 02 <preset_hex> FF
        Set mode (Set2 checked):
            VISCA Set:    <id> 01 04 3F 01 <preset_hex> FF
        """
        preset_hex = PRESET_MAP.get(preset_number)
        if not preset_hex:
            return

        # Platform presets always go to Camera 1
        if preset_number in (1, 2, 3):
            ip, cam_id = IPAddress, Cam1ID
            cam_name = 'Platform'
        else:
            ip, cam_id = self._active_cam()
            cam_name = 'Platform' if self.Cam1.isChecked() else 'Comments'

        if self.Set1.isChecked():
            self._send_cmd(ip, cam_id, "01043f02" + preset_hex + "ff")
        elif self.Set2.isChecked():
            reply = QMessageBox.question(
                self, f'Record Preset {preset_number} ({cam_name})',
                "Are you sure you want to record this preset?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._send_cmd(ip, cam_id, "01043f01" + preset_hex + "ff")

    # -------------------------------------------------------------------------
    #  CONFIG DIALOGS — change IP / VISCA ID at runtime without editing files
    # -------------------------------------------------------------------------

    def _change_ip(self, cam_num):
        """
        Generic dialog to change the IP address of Camera 1 or 2.
        Validates, saves to the appropriate config file, and restarts.
        """
        cam_name  = 'Platform' if cam_num == 1 else 'Comments'
        title     = f'{cam_name} PTZ Control'
        current   = IPAddress if cam_num == 1 else IPAddress2
        filename  = 'PTZ1IP.txt' if cam_num == 1 else 'PTZ2IP.txt'
        result = QMessageBox.warning(
            self, title,
            f'Do you want to change the IP address for the {cam_name} camera?',
            QMessageBox.Ok, QMessageBox.Cancel
        )
        if result == QMessageBox.Ok:
            text, ok = QInputDialog.getText(
                self, title,
                f'New IP address for {cam_name} Camera  (current: {current}):',
                text=current
            )
            if ok and text:
                if not _is_valid_ip(text):
                    QMessageBox.warning(self, 'Invalid IP Address',
                                        f'"{text}" is not a valid IPv4 address.\n'
                                        'Enter four numbers 0-255 separated by dots.')
                    return
                with open(filename, 'w') as f:
                    f.write(text.strip())
                os.execv(sys.executable, ['python3'] + sys.argv)

    def _change_cam_id(self, cam_num):
        """
        Generic dialog to change the VISCA device ID of Camera 1 or 2.
        Validates hex format, saves to config file, and restarts.
        """
        cam_name  = 'Platform' if cam_num == 1 else 'Comments'
        title     = f'{cam_name} PTZ Control'
        current   = Cam1ID if cam_num == 1 else Cam2ID
        filename  = 'Cam1ID.txt' if cam_num == 1 else 'Cam2ID.txt'
        result = QMessageBox.warning(
            self, title,
            f'Do you want to change the VISCA ID for the {cam_name} camera?',
            QMessageBox.Ok, QMessageBox.Cancel
        )
        if result == QMessageBox.Ok:
            text, ok = QInputDialog.getText(
                self, title,
                f'New VISCA ID for {cam_name} Camera  (current: {current}):',
                text=current
            )
            if ok and text:
                if not _is_valid_cam_id(text):
                    QMessageBox.warning(self, 'Invalid Camera ID',
                                        f'"{text}" is not valid hex (e.g. "81" or "82").')
                    return
                with open(filename, 'w') as f:
                    f.write(text.strip())
                os.execv(sys.executable, ['python3'] + sys.argv)

    # Thin public wrappers kept so button .clicked connections need no change
    def PTZ1Address(self):  self._change_ip(1)
    def PTZ2Address(self):  self._change_ip(2)
    def PTZ1IDchange(self): self._change_cam_id(1)
    def PTZ2IDchange(self): self._change_cam_id(2)

    def Quit(self):
        """Close the application cleanly."""
        sys.exit()

    def HelpMsg(self):
        """Display the technical support contact loaded from Contact.txt."""
        QMessageBox.information(self, 'For Technical Assistance', Contact, QMessageBox.Ok)


# =============================================================================
#  GoButton -- compact numbered seat button
# =============================================================================

class GoButton(QPushButton):
    """
    A small (35x35 px) semi-transparent push-button used for seat preset numbers
    on the seating plan and for the platform Left/Right labels.
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


# =============================================================================
#  Entry point
# =============================================================================

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # Uncomment for production Raspberry Pi touchscreen:
    # window.showFullScreen()
    sys.exit(app.exec_())