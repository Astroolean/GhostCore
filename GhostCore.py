import sys
import json
import requests
import phonenumbers # type: ignore
from phonenumbers import carrier, geocoder, timezone # type: ignore
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QStackedWidget,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QMessageBox, QSizePolicy, QSpacerItem, QFrame, QProgressBar, QTextEdit,
    QCheckBox, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject
from PyQt6.QtGui import QFont, QColor
import random
import subprocess
import concurrent.futures

COLOR_PRIMARY = "#0A192F"
COLOR_SECONDARY = "#1F6FEB"
COLOR_BACKGROUND = "#000000"
COLOR_TEXT_DARK = "#E0E0E0"
COLOR_TEXT_LIGHT = "#FFFFFF"
COLOR_ACCENT = "#00FFFF"
COLOR_ERROR = "#DC143C"
COLOR_GREY_LIGHT = "#333333"
COLOR_GREY_MEDIUM = "#222222"
COLOR_GREEN = "#28a745"
COLOR_RED = "#dc3545"

class WorkerThread(QThread):
    finished = pyqtSignal(str, object)
    error = pyqtSignal(str, str)
    progress_updated = pyqtSignal(str, int, int)

    def __init__(self, task_name, func, *args, **kwargs):
        super().__init__()
        self.task_name = task_name
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            if self.task_name == "Username Tracking":
                result = self.func(*self.args, progress_callback=self._emit_progress, **self.kwargs)
            else:
                result = self.func(*self.args, **self.kwargs)
            self.finished.emit(self.task_name, result)
        except Exception as e:
            self.error.emit(self.task_name, str(e))

    def _emit_progress(self, current, total):
        self.progress_updated.emit(self.task_name, current, total)

class GhostCore(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("👻 Ghost Core V1.0 - Created by Astroolean")
        self.setGeometry(100, 100, 900, 700) 

        self._apply_stylesheet()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self._init_content_area()
        self._init_nav_panel()

        self.ip_retrieved = False
        QTimer.singleShot(0, self.nav_list.setFocus)

    class WifiWorker(QObject):
        finished = pyqtSignal()
        result_ready = pyqtSignal(list)
        error_occurred = pyqtSignal(str)

        def run(self):
            try:
                if sys.platform != "win32":
                    error_msg = "This application's Wi-Fi Grabber feature only works on Windows operating systems."
                    self.error_occurred.emit(error_msg)
                    self.finished.emit()
                    return

                data = subprocess.check_output(
                    ['netsh', 'wlan', 'show', 'profiles'],
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).decode('utf-8', errors='ignore').split('\n')

                profiles = [i.split(":")[1][1:-1].strip() for i in data if "All User Profile" in i]

                all_results = []
                for i in profiles:
                    try:
                        results = subprocess.check_output(
                            ['netsh', 'wlan', 'show', 'profile', i, 'key=clear'],
                            creationflags=subprocess.CREATE_NO_WINDOW
                        ).decode('utf-8', errors='ignore').split('\n')
                        
                        key_content = [b.split(":")[1][1:-1].strip() for b in results if "Key Content" in b]
                        password = key_content[0] if key_content else ""
                        all_results.append([i, password])
                    except subprocess.CalledProcessError:
                        all_results.append([i, "Error retrieving password (Admin privileges needed or no key)"])
                    except Exception as e:
                        # Corrected syntax here: closing f-string and list properly
                        all_results.append([i, f"Error: {e}"]) 
                
                self.result_ready.emit(all_results)
            except subprocess.CalledProcessError as e:
                error_msg = f"Error executing netsh command: {e}\nPlease ensure you run this application as Administrator for full functionality."
                self.error_occurred.emit(error_msg)
            except Exception as e:
                error_msg = f"An unexpected error occurred in WifiWorker: {e}"
                self.error_occurred.emit(error_msg)
            finally:
                self.finished.emit()

    def _init_nav_panel(self):
        self.nav_frame = QFrame()
        self.nav_frame.setObjectName("navFrame")
        self.nav_layout = QVBoxLayout(self.nav_frame)
        self.nav_layout.setContentsMargins(10, 20, 10, 10)
        self.nav_layout.setSpacing(10)

        self.logo_label = QLabel("👻 Ghost Core V1.0")
        self.logo_label.setObjectName("logoLabel")
        self.nav_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.nav_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        item_height = 50
        num_items = 6
        self.nav_list.setMinimumHeight(item_height * num_items + (num_items - 1) * self.nav_layout.spacing())
        self.nav_list.setMaximumHeight(item_height * num_items + (num_items - 1) * self.nav_layout.spacing())

        self.nav_list.addItem(QListWidgetItem("Show Your IP"))
        self.nav_list.addItem(QListWidgetItem("IP Tracker"))
        self.nav_list.addItem(QListWidgetItem("Phone Number Tracker"))
        self.nav_list.addItem(QListWidgetItem("Username Tracker"))
        self.nav_list.addItem(QListWidgetItem("WiFi Grabber")) 
        self.nav_list.addItem(QListWidgetItem("Exit"))
        
        self.nav_list.itemClicked.connect(self._on_nav_item_clicked) 
        self.nav_list.setCurrentRow(0)

        self.nav_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.nav_list.keyPressEvent = self._nav_list_key_press_event

        self.nav_layout.addWidget(self.nav_list)
        self.nav_layout.addStretch(1)

        self.main_layout.addWidget(self.nav_frame, 1)

    def _on_nav_item_clicked(self, item):
        index = self.nav_list.row(item)
        self._change_page(index)

    def _nav_list_key_press_event(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            current_row = self.nav_list.currentRow()
            self._change_page(current_row)
        elif event.key() == Qt.Key.Key_Right:
            current_index = self.stacked_widget.currentIndex()
            if current_index == 0:
                self.get_my_ip_button.setFocus()
            elif current_index == 1:
                self.ip_input_field.setFocus()
            elif current_index == 2:
                self.phone_input_field.setFocus()
            elif current_index == 3:
                self.username_input_field.setFocus()
            elif current_index == 4:
                self.wifi_terms_checkbox.setFocus()
        else:
            super(QListWidget, self.nav_list).keyPressEvent(event)

    def _init_content_area(self):
        self.content_frame = QFrame()
        self.content_frame.setObjectName("contentFrame")
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        self.stacked_widget = QStackedWidget()

        self.show_ip_widget = QWidget()
        self.show_ip_layout = QVBoxLayout(self.show_ip_widget)
        self.show_ip_layout.setContentsMargins(0, 0, 0, 0)
        self.show_ip_layout.setSpacing(15)
        
        your_ip_ascii_art = QLabel("""
<pre>
███████╗██╗  ██╗ ██████╗ ██╗    ██╗    ██╗   ██╗ ██████╗ ██╗   ██╗██████╗     ██╗██████╗ 
██╔════╝██║  ██║██╔═══██╗██║    ██║    ╚██╗ ██╔╝██╔═══██╗██║   ██║██╔══██╗    ██║██╔══██╗
███████╗███████║██║   ██║██║ █╗ ██║     ╚████╔╝ ██║   ██║██║   ██║██████╔╝    ██║██████╔╝
╚════██║██╔══██║██║   ██║██║███╗██║      ╚██╔╝  ██║   ██║██║   ██║██╔══██╗    ██║██╔═══╝ 
███████║██║  ██║╚██████╔╝╚███╔███╔╝       ██║   ╚██████╔╝╚██████╔╝██║  ██║    ██║██║     
╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝        ╚═╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝    ╚═╝╚═╝     
</pre>
        """)
        your_ip_ascii_art.setObjectName("widgetTitle")
        your_ip_ascii_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.show_ip_layout.addWidget(your_ip_ascii_art)

        self.ip_display_label = QLabel("Click 'Get My IP' to see your public IP address.", objectName="ipDisplayLabel", alignment=Qt.AlignmentFlag.AlignCenter)
        self.show_ip_layout.addWidget(self.ip_display_label)
        self.get_my_ip_button = QPushButton("Get My IP", objectName="actionButton")
        self.get_my_ip_button.clicked.connect(self._on_get_copy_ip_clicked)
        self.show_ip_layout.addWidget(self.get_my_ip_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.show_ip_status_label = QLabel("Ready.", objectName="statusLabel")
        self.show_ip_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        self.show_ip_layout.addWidget(self.show_ip_status_label)
        self.show_ip_layout.addStretch(1)
        self.stacked_widget.addWidget(self.show_ip_widget)

        self.ip_tracker_widget = QWidget()
        self.ip_tracker_layout = QVBoxLayout(self.ip_tracker_widget)
        self.ip_tracker_layout.setContentsMargins(0, 0, 0, 0)
        self.ip_tracker_layout.setSpacing(15)
        
        ip_tracker_ascii_art = QLabel("""
<pre>
██╗██████╗     ████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ 
██║██╔══██╗    ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║██████╔╝       ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝
██║██╔═══╝        ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
██║██║            ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
╚═╝╚═╝            ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
</pre>
        """)
        ip_tracker_ascii_art.setObjectName("widgetTitle")
        ip_tracker_ascii_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ip_tracker_layout.addWidget(ip_tracker_ascii_art)

        self.ip_input_field = QLineEdit(placeholderText="Enter IP address (e.g., 8.8.8.8)", objectName="inputField")
        self.ip_track_button = QPushButton("Track IP", objectName="actionButton")
        self.ip_track_button.clicked.connect(self._track_ip)

        self.ip_input_field.returnPressed.connect(self._track_ip)

        ip_input_layout = QHBoxLayout()
        ip_input_layout.addWidget(self.ip_input_field)
        ip_input_layout.addWidget(self.ip_track_button)
        self.ip_tracker_layout.addLayout(ip_input_layout)
        self.ip_result_table = QTableWidget(columnCount=2, objectName="resultTable")
        self.ip_result_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.ip_result_table.horizontalHeader().setStretchLastSection(True)
        self.ip_result_table.verticalHeader().setVisible(False)
        self.ip_result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ip_tracker_layout.addWidget(self.ip_result_table)
        self.ip_status_label = QLabel("Ready.", objectName="statusLabel")
        self.ip_tracker_layout.addWidget(self.ip_status_label)
        self.stacked_widget.addWidget(self.ip_tracker_widget)

        self.phone_tracker_widget = QWidget()
        self.phone_tracker_layout = QVBoxLayout(self.phone_tracker_widget)
        self.phone_tracker_layout.setContentsMargins(0, 0, 0, 0)
        self.phone_tracker_layout.setSpacing(15)
        
        phone_tracker_ascii_art = QLabel("""
<pre>
██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗    ████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ 
██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝    ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██████╔╝███████║██║   ██║██╔██╗ ██║█████╗         ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝
██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝         ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗       ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
</pre>
        """)
        phone_tracker_ascii_art.setObjectName("widgetTitle")
        phone_tracker_ascii_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phone_tracker_layout.addWidget(phone_tracker_ascii_art)

        self.phone_input_field = QLineEdit(placeholderText="Enter phone number (e.g., +6281xxxxxxxxx)", objectName="inputField")
        self.phone_track_button = QPushButton("Track Phone Number", objectName="actionButton")
        self.phone_track_button.clicked.connect(self._track_phone)

        self.phone_input_field.returnPressed.connect(self._track_phone)

        phone_input_layout = QHBoxLayout()
        phone_input_layout.addWidget(self.phone_input_field)
        phone_input_layout.addWidget(self.phone_track_button)
        self.phone_tracker_layout.addLayout(phone_input_layout)
        self.phone_result_table = QTableWidget(columnCount=2, objectName="resultTable")
        self.phone_result_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.phone_result_table.horizontalHeader().setStretchLastSection(True)
        self.phone_result_table.verticalHeader().setVisible(False)
        self.phone_result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.phone_tracker_layout.addWidget(self.phone_result_table)
        self.phone_status_label = QLabel("Ready.", objectName="statusLabel")
        self.phone_tracker_layout.addWidget(self.phone_status_label)
        self.stacked_widget.addWidget(self.phone_tracker_widget)

        self.username_tracker_widget = QWidget()
        self.username_tracker_layout = QVBoxLayout(self.username_tracker_widget)
        self.username_tracker_layout.setContentsMargins(0, 0, 0, 0)
        self.username_tracker_layout.setSpacing(15)
        
        username_tracker_ascii_art = QLabel("""
<pre>
██╗   ██╗███████╗███████╗██████╗ ███╗   ██╗ █████╗ ███╗   ███╗███████╗    ████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ 
██║   ██║██╔════╝██╔════╝██╔══██╗████╗  ██║██╔══██╗████╗ ████║██╔════╝    ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║   ██║███████╗█████╗  ██████╔╝██╔██╗ ██║███████║██╔████╔██║█████╗         ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝
██║   ██║╚════██║██╔══╝  ██╔══██╗██║╚██╗██║██╔══██║██║╚██╔╝██║██╔══╝         ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
╚██████╔╝███████║███████╗██║  ██║██║ ╚████║██║  ██║██║ ╚═╝ ██║███████╗       ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
 ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
</pre>
        """)
        username_tracker_ascii_art.setObjectName("widgetTitle")
        username_tracker_ascii_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_tracker_layout.addWidget(username_tracker_ascii_art)

        self.username_input_field = QLineEdit(placeholderText="Enter username", objectName="inputField")
        self.username_track_button = QPushButton("Track Username", objectName="actionButton")
        self.username_track_button.clicked.connect(self._track_username)

        self.username_input_field.returnPressed.connect(self._track_username)

        username_input_layout = QHBoxLayout()
        username_input_layout.addWidget(self.username_input_field)
        username_input_layout.addWidget(self.username_track_button)
        self.username_tracker_layout.addLayout(username_input_layout)
        
        self.username_progress_bar = QProgressBar()
        self.username_progress_bar.setObjectName("progressBar")
        self.username_progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_progress_bar.setTextVisible(False)
        self.username_progress_bar.hide()
        self.username_tracker_layout.addWidget(self.username_progress_bar)

        self.username_result_table = QTableWidget(columnCount=2, objectName="resultTable")
        self.username_result_table.setHorizontalHeaderLabels(["Site", "Status/URL"]) 
        self.username_result_table.horizontalHeader().setStretchLastSection(True)
        self.username_result_table.verticalHeader().setVisible(False)
        self.username_result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.username_tracker_layout.addWidget(self.username_result_table)
        self.username_status_label = QLabel("Ready.", objectName="statusLabel")
        self.username_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        self.username_tracker_layout.addWidget(self.username_status_label)
        self.stacked_widget.addWidget(self.username_tracker_widget)

        self.wifi_grabber_widget = QWidget()
        self.wifi_grabber_layout = QVBoxLayout(self.wifi_grabber_widget)
        self.wifi_grabber_layout.setContentsMargins(0, 0, 0, 0)
        self.wifi_grabber_layout.setSpacing(15)

        wifi_grabber_ascii_art = QLabel("""
<pre>
██╗    ██╗██╗███████╗██╗     ██████╗ ██████╗  █████╗ ██████╗ ██████╗ ███████╗██████╗ 
██║    ██║██║██╔════╝██║    ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║ █╗ ██║██║█████╗  ██║    ██║  ███╗██████╔╝███████║██████╔╝██████╔╝█████╗  ██████╔╝
██║███╗██║██║██╔══╝  ██║    ██║   ██║██╔══██╗██╔══██║██╔══██╗██╔══██╗██╔══╝  ██╔══██╗
╚███╔███╔╝██║██║     ██║    ╚██████╔╝██║  ██║██║  ██║██████╔╝██████╔╝███████╗██║  ██║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
</pre>
        """)
        wifi_grabber_ascii_art.setObjectName("widgetTitle")
        wifi_grabber_ascii_art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wifi_grabber_layout.addWidget(wifi_grabber_ascii_art)

        terms_layout = QHBoxLayout()
        terms_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wifi_terms_checkbox = QCheckBox("I agree to not be fucking stupid...")
        self.wifi_terms_checkbox.setFont(self.font())
        self.wifi_terms_checkbox.stateChanged.connect(self._toggle_wifi_scan_button_state)
        terms_layout.addWidget(self.wifi_terms_checkbox)
        self.wifi_grabber_layout.addLayout(terms_layout)

        self.wifi_scan_button = QPushButton("Scan Wi-Fi Passwords", objectName="actionButton")
        self.wifi_scan_button.setFont(self.font())
        self.wifi_scan_button.setFixedSize(250, 50)
        self.wifi_scan_button.clicked.connect(self._start_wifi_scan)
        self.wifi_scan_button.setEnabled(False)
        self.wifi_grabber_layout.addWidget(self.wifi_scan_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.wifi_result_table = QTableWidget(columnCount=2, objectName="resultTable")
        self.wifi_result_table.setHorizontalHeaderLabels(["Name", "Password"])
        self.wifi_result_table.horizontalHeader().setStretchLastSection(True)
        self.wifi_result_table.verticalHeader().setVisible(False)
        self.wifi_result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Set size policy to expand vertically
        self.wifi_result_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.wifi_grabber_layout.addWidget(self.wifi_result_table, 1) # Add stretch factor to the table

        self.wifi_status_label = QLabel("Ready to scan. Please agree to terms.", objectName="statusLabel")
        self.wifi_status_label.setFont(self.font())
        self.wifi_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wifi_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        self.wifi_grabber_layout.addWidget(self.wifi_status_label)
        # Removed self.wifi_grabber_layout.addStretch(1) to allow the table to expand

        self.stacked_widget.addWidget(self.wifi_grabber_widget)

        self.content_layout.addWidget(self.stacked_widget)
        self.main_layout.addWidget(self.content_frame, 4)

    def _toggle_wifi_scan_button_state(self, state):
        self.wifi_scan_button.setEnabled(state == Qt.CheckState.Checked.value)
        if state == Qt.CheckState.Checked.value:
            self.wifi_status_label.setText("Click 'Scan Wi-Fi Passwords' to begin.")
            self.wifi_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        else:
            self.wifi_status_label.setText("Please agree to not be fucking stupid to enable scanning.")
            self.wifi_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")

    def _start_wifi_scan(self):
        self.wifi_status_label.setText("Scanning Wi-Fi networks... This may take a moment.")
        self.wifi_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        self.wifi_scan_button.setEnabled(False)
        self.wifi_terms_checkbox.setEnabled(False)
        self.wifi_result_table.setRowCount(0)

        self._current_wifi_thread = QThread()
        self._current_wifi_worker = self.WifiWorker()
        self._current_wifi_worker.moveToThread(self._current_wifi_thread)

        self._current_wifi_thread.started.connect(self._current_wifi_worker.run)
        self._current_wifi_worker.finished.connect(self._current_wifi_thread.quit)
        self._current_wifi_worker.finished.connect(self._current_wifi_worker.deleteLater)
        self._current_wifi_thread.finished.connect(self._current_wifi_thread.deleteLater)
        self._current_wifi_thread.finished.connect(self._clear_wifi_thread_references)

        self._current_wifi_worker.result_ready.connect(self._display_wifi_results)
        self._current_wifi_worker.error_occurred.connect(self._show_wifi_error_message)

        self._current_wifi_thread.start()

    def _clear_wifi_thread_references(self):
        self._current_wifi_thread = None
        self._current_wifi_worker = None

    def _display_wifi_results(self, results):
        self.wifi_result_table.setRowCount(0)
        current_row = 0

        if not results:
            self.wifi_status_label.setText("No Wi-Fi profiles found or an error occurred during scan.")
            self.wifi_status_label.setStyleSheet(f"color: {COLOR_ERROR};")
            return

        self.wifi_result_table.insertRow(current_row)
        header_item = QTableWidgetItem(f"--- WI-FI PROFILES FOUND ({len(results)}) ---")
        header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        header_item.setBackground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.Highlight))
        header_item.setForeground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.HighlightedText))
        self.wifi_result_table.setSpan(current_row, 0, 1, 2)
        self.wifi_result_table.setItem(current_row, 0, header_item)
        current_row += 1

        for row_data in results:
            self.wifi_result_table.insertRow(current_row)
            for col_idx, item in enumerate(row_data):
                table_item = QTableWidgetItem(str(item))
                # Set text color to white for better visibility
                table_item.setForeground(QColor(COLOR_TEXT_LIGHT))
                self.wifi_result_table.setItem(current_row, col_idx, table_item)
            current_row += 1
        
        self.wifi_status_label.setText(f"Scan complete. Found {len(results)} Wi-Fi profiles.")
        self.wifi_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        self.wifi_scan_button.setEnabled(True)
        self.wifi_terms_checkbox.setEnabled(True)
        # Ensure columns stretch to fill space
        self.wifi_result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.wifi_result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # Adjust row height to fit content, if necessary
        self.wifi_result_table.resizeRowsToContents()


    def _show_wifi_error_message(self, message):
        QMessageBox.critical(self, "Wi-Fi Scan Error", message)
        self.wifi_status_label.setText("Scan failed. Please check error message.")
        self.wifi_status_label.setStyleSheet(f"color: {COLOR_ERROR};")
        self.wifi_scan_button.setEnabled(True)
        self.wifi_terms_checkbox.setEnabled(True)

    def _on_worker_finished(self, task_name, result, input_widget, button_widget, table_widget, status_label):
        status_label.setText(f"{task_name} completed.")
        status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        
        button_widget.setEnabled(True)
        if input_widget:
            input_widget.setEnabled(True)

        if task_name == "Username Tracking":
            self.username_progress_bar.hide()

        if task_name == "IP Tracking":
            self._display_ip_results(result, table_widget, status_label)
        elif task_name == "Phone Number Tracking":
            self._display_phone_results(result, table_widget, status_label)
        elif task_name == "Username Tracking":
            self._display_username_results(result, table_widget, status_label)
        elif task_name == "Your IP":
            self._display_your_ip_results(result, status_label)

    def _on_worker_error(self, task_name, error_message, input_widget, button_widget, status_label):
        status_label.setText(f"Error during {task_name}: {error_message}")
        status_label.setStyleSheet(f"color: {COLOR_ERROR};")
        button_widget.setEnabled(True)
        if input_widget:
            input_widget.setEnabled(True)
        QMessageBox.critical(self, f"Error {task_name}", f"An error occurred: {error_message}")
        
        if task_name == "Your IP":
            self.ip_retrieved = False
            self.get_my_ip_button.setText("Get My IP")
            self.ip_display_label.setText("Click 'Get My IP' to see your public IP address.")
            self.ip_display_label.setStyleSheet(f"font-size: 20px; color: {COLOR_TEXT_DARK};")
        
        if task_name == "Username Tracking":
            self.username_progress_bar.hide()

    def _get_ip_info(self, ip):
        all_data = {}
        errors = []

        try:
            req_api_whois = requests.get(f"http://ipwho.is/{ip}", timeout=5)
            req_api_whois.raise_for_status()
            whois_data = json.loads(req_api_whois.text)
            if whois_data.get("success"):
                all_data['ipwhois'] = {
                    "IP target": whois_data.get("ip", "N/A"),
                    "Type IP": whois_data.get("type", "N/A"),
                    "Country": whois_data.get("country", "N/A"),
                    "Country Code": whois_data.get("country_code", "N/A"),
                    "City": whois_data.get("city", "N/A"),
                    "Continent": whois_data.get("continent", "N/A"),
                    "Continent Code": whois_data.get("continent_code", "N/A"),
                    "Region": whois_data.get("region", "N/A"),
                    "Region Code": whois_data.get("region_code", "N/A"),
                    "Latitude": whois_data.get("latitude", "N/A"),
                    "Longitude": whois_data.get("longitude", "N/A"),
                    "EU": whois_data.get("is_eu", "N/A"),
                    "Postal": whois_data.get("postal", "N/A"),
                    "Calling Code": whois_data.get("calling_code", "N/A"),
                    "Capital": whois_data.get("capital", "N/A"),
                    "Borders": whois_data.get("borders", "N/A"),
                    "Country Flag": whois_data.get("flag", {}).get("emoji", "N/A"),
                    "ASN": whois_data.get("connection", {}).get("asn", "N/A"),
                    "ORG": whois_data.get("connection", {}).get("org", "N/A"),
                    "ISP": whois_data.get("connection", {}).get("isp", "N/A"),
                    "Domain": whois_data.get("connection", {}).get("domain", "N/A"),
                    "Timezone ID": whois_data.get("timezone", {}).get("id", "N/A"),
                    "Timezone ABBR": whois_data.get("timezone", {}).get("abbr", "N/A"),
                    "Timezone DST": whois_data.get("timezone", {}).get("is_dst", "N/A"),
                    "Timezone Offset": whois_data.get("timezone", {}).get("offset", "N/A"),
                    "Current Time": whois_data.get("timezone", {}).get("current_time", "N/A")
                }
                lat = whois_data.get('latitude')
                lon = whois_data.get('longitude')
                if lat is not None and lon is not None:
                    try:
                        lat_val = float(lat)
                        lon_val = float(lon)
                        all_data['ipwhois']["Maps"] = f"https://www.google.com/maps/@{lat_val},{lon_val},8z"
                    except ValueError:
                        all_data['ipwhois']["Maps"] = "N/A (Invalid coordinates)"
            else:
                errors.append(f"ipwho.is error: {whois_data.get('message', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            errors.append(f"ipwho.is connection error: {e}")

        try:
            req_api_ipapi = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            req_api_ipapi.raise_for_status()
            ipapi_data = json.loads(req_api_ipapi.text)
            if ipapi_data.get("status") == "success":
                all_data['ip-api'] = {
                    "Status": ipapi_data.get("status", "N/A"),
                    "Country": ipapi_data.get("country", "N/A"),
                    "Country Code": ipapi_data.get("countryCode", "N/A"),
                    "Region": ipapi_data.get("region", "N/A"),
                    "Region Name": ipapi_data.get("regionName", "N/A"),
                    "City": ipapi_data.get("city", "N/A"),
                    "ZIP": ipapi_data.get("zip", "N/A"),
                    "Latitude": ipapi_data.get("lat", "N/A"),
                    "Longitude": ipapi_data.get("lon", "N/A"),
                    "Timezone": ipapi_data.get("timezone", "N/A"),
                    "ISP": ipapi_data.get("isp", "N/A"),
                    "Organization": ipapi_data.get("org", "N/A"),
                    "AS": ipapi_data.get("as", "N/A"),
                    "Query IP": ipapi_data.get("query", "N/A")
                }
                lat = ipapi_data.get('lat')
                lon = ipapi_data.get('lon')
                if lat is not None and lon is not None:
                    try:
                        lat_val = float(lat)
                        lon_val = float(lon)
                        all_data['ip-api']["Maps"] = f"https://www.google.com/maps/@{lat_val},{lon_val},8z"
                    except ValueError:
                        all_data['ip-api']["Maps"] = "N/A (Invalid coordinates)"
            else:
                errors.append(f"ip-api.com error: {ipapi_data.get('message', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            errors.append(f"ip-api.com connection error: {e}")

        try:
            req_api_ipapico = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
            req_api_ipapico.raise_for_status()
            ipapico_data = json.loads(req_api_ipapico.text)
            if ipapico_data.get("error") is None:
                all_data['ipapi.co'] = {
                    "IP": ipapico_data.get("ip", "N/A"),
                    "City": ipapico_data.get("city", "N/A"),
                    "Region": ipapico_data.get("region", "N/A"),
                    "Region Code": ipapico_data.get("region_code", "N/A"),
                    "Country": ipapico_data.get("country_name", "N/A"),
                    "Country Code": ipapico_data.get("country_code", "N/A"),
                    "Continent Code": ipapico_data.get("continent_code", "N/A"),
                    "Postal": ipapico_data.get("postal", "N/A"),
                    "Latitude": ipapico_data.get("latitude", "N/A"),
                    "Longitude": ipapico_data.get("longitude", "N/A"),
                    "Timezone": ipapico_data.get("timezone", "N/A"),
                    "UTC Offset": ipapico_data.get("utc_offset", "N/A"),
                    "Country Calling Code": ipapico_data.get("country_calling_code", "N/A"),
                    "Currency": ipapico_data.get("currency", "N/A"),
                    "Org": ipapico_data.get("org", "N/A"),
                    "ASN": ipapico_data.get("asn", "N/A"),
                }
                lat = ipapico_data.get('latitude')
                lon = ipapico_data.get('longitude') 
                if lat is not None and lon is not None:
                    try:
                        lat_val = float(lat)
                        lon_val = float(lon)
                        all_data['ipapi.co']["Maps"] = f"https://www.google.com/maps/@{lat_val},{lon_val},8z"
                    except ValueError:
                        all_data['ipapi.co']["Maps"] = "N/A (Invalid coordinates)"
            else:
                errors.append(f"ipapi.co error: {ipapico_data.get('reason', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            errors.append(f"ipapi.co connection error: {e}")

        try:
            req_api_freegeoip = requests.get(f"https://freegeoip.app/json/{ip}", timeout=5)
            req_api_freegeoip.raise_for_status()
            freegeoip_data = json.loads(req_api_freegeoip.text)
            if freegeoip_data.get("ip"):
                all_data['freegeoip.app'] = {
                    "IP": freegeoip_data.get("ip", "N/A"),
                    "Country Name": freegeoip_data.get("country_name", "N/A"),
                    "Country Code": freegeoip_data.get("country_code", "N/A"),
                    "Region Name": freegeoip_data.get("region_name", "N/A"),
                    "Region Code": freegeoip_data.get("region_code", "N/A"),
                    "City": freegeoip_data.get("city", "N/A"),
                    "ZIP Code": freegeoip_data.get("zip_code", "N/A"),
                    "Time Zone": freegeoip_data.get("time_zone", "N/A"),
                    "Latitude": freegeoip_data.get("latitude", "N/A"),
                    "Longitude": freegeoip_data.get("longitude", "N/A"),
                    "Metro Code": freegeoip_data.get("metro_code", "N/A"),
                }
                lat = freegeoip_data.get('latitude')
                lon = freegeoip_data.get('longitude') 
                if lat is not None and lon is not None:
                    try:
                        lat_val = float(lat)
                        lon_val = float(lon)
                        all_data['freegeoip.app']["Maps"] = f"https://www.google.com/maps/@{lat_val},{lon_val},8z"
                    except ValueError:
                        all_data['freegeoip.app']["Maps"] = "N/A (Invalid coordinates)"
            else:
                errors.append(f"freegeoip.app error: No IP data returned.")
        except requests.exceptions.RequestException as e:
            errors.append(f"freegeoip.app connection error: {e}")

        if not all_data and errors:
            raise Exception(f"Failed to retrieve IP info from all sources: {'; '.join(errors)}")
        elif not all_data:
            raise Exception("No data retrieved from any IP APIs.")

        best_judgment = self._determine_best_judgment(all_data)
        all_data['Best Judgment'] = best_judgment

        return all_data

    def _determine_best_judgment(self, all_source_data):
        best_data = {}
        priority_fields = [
            "City", "Region Name", "Region", "Country", "Country Name", "Country Code",
            "Latitude", "Longitude", "Timezone", "ISP", "Organization", "ASN", "Postal", "ZIP"
        ]
        
        source_preference = ['ip-api', 'ipwhois', 'ipapi.co', 'freegeoip.app']

        for field in priority_fields:
            values = []
            for source_name in source_preference:
                if source_name in all_source_data:
                    val = all_source_data[source_name].get(field)
                    if val is None:
                        if field == "Region Name" and "Region" in all_source_data[source_name]:
                            val = all_source_data[source_name]["Region"]
                        elif field == "Region" and "Region Name" in all_source_data[source_name]:
                            val = all_source_data[source_name]["Region Name"]
                        elif field == "Country Name" and "Country" in all_source_data[source_name]:
                            val = all_source_data[source_name]["Country"]
                        elif field == "Country" and "Country Name" in all_source_data[source_name]:
                            val = all_source_data[source_name]["Country Name"]
                        elif field == "ZIP" and "Postal" in all_source_data[source_name]:
                            val = all_source_data[source_name]["Postal"]
                        elif field == "Postal" and "ZIP Code" in all_source_data[source_name]:
                            val = all_source_data[source_name]["ZIP Code"]
                        elif field == "ISP" and "ORG" in all_source_data[source_name]:
                            val = all_source_data[source_name]["ORG"]
                        elif field == "ORG" and "ISP" in all_source_data[source_name]:
                            val = all_source_data[source_name]["ISP"]

                    if val not in ["N/A", None, ""]:
                        values.append((val, source_name))

            if not values:
                best_data[field] = "N/A"
                continue

            value_counts = {}
            for val, _ in values:
                value_counts[val] = value_counts.get(val, 0) + 1

            majority_value = None
            max_count = 0
            for val, count in value_counts.items():
                if count > max_count:
                    max_count = count
                    majority_value = val
            
            if majority_value is not None and max_count >= (len(values) / 2):
                best_data[field] = majority_value
            else:
                found = False
                for pref_source in source_preference:
                    for val, src in values:
                        if src == pref_source:
                            best_data[field] = val
                            found = True
                            break
                    if found:
                        break
                if not found:
                    best_data[field] = values[0][0]

        lat = best_data.get('Latitude')
        lon = best_data.get('Longitude')
        if lat not in ["N/A", None] and lon not in ["N/A", None]:
            try:
                lat_val = float(lat)
                lon_val = float(lon)
                best_data["Maps"] = f"https://www.google.com/maps/@{lat_val},{lon_val},8z"
            except ValueError:
                        best_data["Maps"] = "N/A (Invalid coordinates)"
        else:
            best_data["Maps"] = "N/A"

        return best_data

    def _track_ip(self):
        ip = self.ip_input_field.text().strip()
        if not ip:
            self.ip_status_label.setText("Please enter an IP address.")
            self.ip_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
            return
        self._start_worker("IP Tracking", self._get_ip_info, self.ip_input_field, self.ip_track_button, self.ip_result_table, self.ip_status_label, ip)

    def _display_ip_results(self, ip_data, table_widget, status_label):
        table_widget.setRowCount(0)
        current_row = 0

        if not ip_data:
            status_label.setText(f"Error: No IP data retrieved.")
            status_label.setStyleSheet(f"color: {COLOR_ERROR};")
            return

        for source_name, data in ip_data.items():
            table_widget.insertRow(current_row)
            header_item = QTableWidgetItem(f"--- {source_name.replace('-', ' ').upper()} ---")
            header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            header_item.setBackground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.Highlight))
            header_item.setForeground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.HighlightedText))
            table_widget.setSpan(current_row, 0, 1, 2)
            table_widget.setItem(current_row, 0, header_item)
            current_row += 1

            sorted_keys = sorted(data.keys())
            for key in sorted_keys:
                value = data[key]
                table_widget.insertRow(current_row)
                item_key = QTableWidgetItem(str(key))
                item_value = QTableWidgetItem(str(value))
                item_key.setForeground(QColor(COLOR_TEXT_LIGHT))
                item_value.setForeground(QColor(COLOR_TEXT_LIGHT))
                table_widget.setItem(current_row, 0, item_key)
                table_widget.setItem(current_row, 1, item_value)
                current_row += 1
            
            table_widget.insertRow(current_row)
            table_widget.setSpan(current_row, 0, 1, 2)
            table_widget.setItem(current_row, 0, QTableWidgetItem(""))
            current_row += 1

        table_widget.resizeColumnsToContents()
        table_widget.horizontalHeader().setStretchLastSection(True)

    def _get_phone_info(self, phone_number):
        default_region = "US"
        all_data = {}
        
        try:
            parsed_number = phonenumbers.parse(phone_number, default_region)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number. Please ensure it includes the country code (e.g., +1234567890).")

            all_data['Basic Information'] = {
                "Location": geocoder.description_for_number(parsed_number, "en") or "N/A",
                "Region Code": phonenumbers.region_code_for_number(parsed_number) or "N/A",
                "Timezone": ', '.join(timezone.time_zones_for_number(parsed_number)) or "N/A",
                "Operator/Carrier": carrier.name_for_number(parsed_number, "en") or "N/A",
            }

            all_data['Validity & Core Details'] = {
                "Valid Number": phonenumbers.is_valid_number(parsed_number),
                "Possible Number": phonenumbers.is_possible_number(parsed_number),
                "Country Code": parsed_number.country_code,
                "National Number": parsed_number.national_number,
                "Number of leading zeros": phonenumbers.get_number_of_leading_zeros(parsed_number) if hasattr(phonenumbers, 'get_number_of_leading_zeros') else "N/A",
                "Has Italian leading zero": phonenumbers.italian_leading_zero(parsed_number) if hasattr(phonenumbers, 'italian_leading_zero') else "N/A",
            }

            number_type_enum = phonenumbers.number_type(parsed_number)
            number_type_str = "Unknown Type"
            if number_type_enum == phonenumbers.PhoneNumberType.MOBILE:
                number_type_str = "Mobile Number"
            elif number_type_enum == phonenumbers.PhoneNumberType.FIXED_LINE:
                number_type_str = "Fixed-line Number"
            elif number_type_enum == phonenumbers.PhoneNumberType.TOLL_FREE:
                number_type_str = "Toll-Free Number"
            elif number_type_enum == phonenumbers.PhoneNumberType.PREMIUM_RATE:
                number_type_str = "Premium Rate Number"
            elif number_type_enum == phonenumbers.PhoneNumberType.SHARED_COST:
                number_type_str = "Shared Cost Number"
            elif number_type_enum == phonenumbers.PhoneNumberType.VOIP:
                number_type_str = "VoIP Number"
            elif number_type_enum == phonenumbers.PhoneNumberType.PAGER:
                number_type_str = "Pager Number"
            elif number_type_enum == phonenumbers.PhoneNumberType.UAN:
                number_type_str = "Universal Access Number"
            elif number_type_enum == phonenumbers.PhoneNumberType.VOICEMAIL:
                number_type_str = "Voicemail Number"
            elif number_type_enum == phonenumbers.PhoneNumberType.PERSONAL_NUMBER:
                number_type_str = "Personal Number"
            
            all_data['Number Type'] = {
                "Type": number_type_str,
                "Is Fixed Line": phonenumbers.is_fixed_line(parsed_number) if hasattr(phonenumbers, 'is_fixed_line') else None,
                "Is Mobile": phonenumbers.is_mobile_number(parsed_number) if hasattr(phonenumbers, 'is_mobile_number') else None,
                "Is Toll Free": phonenumbers.is_toll_free_number(parsed_number) if hasattr(phonenumbers, 'is_toll_free_number') else None,
                "Is Premium Rate": phonenumbers.is_premium_rate(parsed_number) if hasattr(phonenumbers, 'is_premium_rate') else None,
                "Is Shared Cost": phonenumbers.is_shared_cost_number(parsed_number) if hasattr(phonenumbers, 'is_shared_cost_number') else None,
                "Is VoIP": phonenumbers.is_voip_number(parsed_number) if hasattr(phonenumbers, 'is_voip_number') else None,
                "Is Pager": phonenumbers.is_pager_number(parsed_number) if hasattr(phonenumbers, 'is_pager_number') else None,
                "Is UAN": phonenumbers.is_uan_number(parsed_number) if hasattr(phonenumbers, 'is_uan_number') else None,
                "Is Voicemail": phonenumbers.is_voicemail_number(parsed_number) if hasattr(phonenumbers, 'is_voicemail_number') else None,
            }

            all_data['Number Formats'] = {
                "International Format": phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                "E.164 Format": phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164),
                "National Format": phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL),
                "Mobile Dialing Format": phonenumbers.format_number_for_mobile_dialing(parsed_number, phonenumbers.region_code_for_number(parsed_number), with_formatting=True),
                "RFC3966 Format": phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.RFC3966),
            }

            best_judgment = self._determine_phone_best_judgment(all_data, parsed_number)
            all_data['Best Judgment'] = best_judgment

        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise ValueError(f"Error parsing phone number: {e}. Please check the format (e.g., +1234567890).")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {e}")
        
        return all_data

    def _determine_phone_best_judgment(self, all_source_data, parsed_number):
        best_data = {}

        best_data["Phone Number (International)"] = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        best_data["Phone Number (E.164)"] = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        best_data["Phone Number (National)"] = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)

        location = all_source_data['Basic Information'].get("Location")
        best_data["Location"] = location if location not in [None, "N/A", ""] else "N/A"

        region_code = all_source_data['Basic Information'].get("Region Code")
        best_data["Region Code"] = region_code if region_code not in [None, "N/A", ""] else "N/A"

        timezone_info = all_source_data['Basic Information'].get("Timezone")
        best_data["Timezone"] = timezone_info if timezone_info not in [None, "N/A", ""] else "N/A"

        operator_carrier = all_source_data['Basic Information'].get("Operator/Carrier")
        best_data["Operator/Carrier"] = operator_carrier if operator_carrier not in [None, "N/A", ""] else "N/A"

        if best_data["Operator/Carrier"] == "N/A" and best_data["Region Code"] == "US":
            us_prefix = str(parsed_number.national_number)[:3]
            if us_prefix in ["401", "415", "212", "310"]:
                best_data["Operator/Carrier"] = "Common US Carrier (e.g., Verizon/AT&T/T-Mobile)"
            else:
                best_data["Operator/Carrier"] = "US Carrier (details not available)"

        number_type_str = all_source_data['Number Type'].get("Type")
        best_data["Type"] = number_type_str if number_type_str not in [None, "N/A", "Unknown Type"] else "N/A"
        
        best_data["Valid Number"] = "Yes" if all_source_data['Validity & Core Details'].get("Valid Number") is True else ("No" if all_source_data['Validity & Core Details'].get("Valid Number") is False else "N/A")
        best_data["Possible Number"] = "Yes" if all_source_data['Validity & Core Details'].get("Possible Number") is True else ("No" if all_source_data['Validity & Core Details'].get("Possible Number") is False else "N/A")

        if all_source_data['Number Type'].get("Is Mobile") is True:
            best_data["Is Mobile"] = "Yes"
        if all_source_data['Number Type'].get("Is Fixed Line") is True:
            best_data["Is Fixed Line"] = "Yes"
        if all_source_data['Number Type'].get("Is VoIP") is True:
            best_data["Is VoIP"] = "Yes"
        if all_source_data['Number Type'].get("Is Toll Free") is True:
            best_data["Is Toll Free"] = "Yes"

        return best_data

    def _track_phone(self):
        phone_num = self.phone_input_field.text().strip()
        if not phone_num:
            self.phone_status_label.setText("Please enter a phone number.")
            self.phone_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
            return
        self._start_worker("Phone Number Tracking", self._get_phone_info, self.phone_input_field, self.phone_track_button, self.phone_result_table, self.phone_status_label, phone_num)

    def _display_phone_results(self, phone_data, table_widget, status_label):
        table_widget.setRowCount(0)
        current_row = 0

        if not phone_data:
            status_label.setText(f"Error: No phone data retrieved.")
            status_label.setStyleSheet(f"color: {COLOR_ERROR};")
            return

        category_order = [
            'Basic Information',
            'Validity & Core Details',
            'Number Type',
            'Number Formats',
            'Best Judgment'
        ]

        for category_name in category_order:
            if category_name in phone_data:
                data = phone_data[category_name]
                display_data = {k: v for k, v in data.items() if v is not None and v != "N/A" and v != ""}

                if category_name == 'Number Type':
                    has_meaningful_type_data = False
                    if display_data.get("Type") != "Unknown Type":
                        has_meaningful_type_data = True
                    else:
                        for key, value in display_data.items():
                            if key.startswith("Is ") and value == "Yes":
                                has_meaningful_type_data = True
                                break
                    if not has_meaningful_type_data:
                        continue

                if not display_data and category_name != 'Best Judgment':
                    continue

                table_widget.insertRow(current_row)
                header_item = QTableWidgetItem(f"--- {category_name.upper()} ---")
                header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                header_item.setBackground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.Highlight))
                header_item.setForeground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.HighlightedText))
                table_widget.setSpan(current_row, 0, 1, 2)
                table_widget.setItem(current_row, 0, header_item)
                current_row += 1

                sorted_keys = sorted(display_data.keys())
                for key in sorted_keys:
                    value = display_data[key]
                    table_widget.insertRow(current_row)
                    item_key = QTableWidgetItem(str(key))
                    item_value = QTableWidgetItem(str(value))
                    item_key.setForeground(QColor(COLOR_TEXT_LIGHT))
                    item_value.setForeground(QColor(COLOR_TEXT_LIGHT))
                    table_widget.setItem(current_row, 0, item_key)
                    table_widget.setItem(current_row, 1, item_value)
                    current_row += 1
                
                if category_name != category_order[-1]:
                    table_widget.insertRow(current_row)
                    table_widget.setSpan(current_row, 0, 1, 2)
                    table_widget.setItem(current_row, 0, QTableWidgetItem(""))
                    current_row += 1

        table_widget.resizeColumnsToContents()
        table_widget.horizontalHeader().setStretchLastSection(True)

    def _check_username(self, username, progress_callback=None):
        results = {}
        social_media = [
            {"url": "https://www.youtube.com/@{}", "name": "YouTube"},
            {"url": "https://www.twitch.tv/{}", "name": "Twitch"},
            {"url": "https://m.twitch.tv/{}", "name": "Twitch Mobile"},
            {"url": "https://x.com/{}", "name": "X"},
            {"url": "https://www.facebook.com/{}", "name": "Facebook"},
            {"url": "https://www.instagram.com/{}", "name": "Instagram"},
            {"url": "https://www.linkedin.com/in/{}", "name": "LinkedIn"},
            {"url": "https://github.com/{}", "name": "GitHub"},
            {"url": "https://www.pinterest.com/{}", "name": "Pinterest"},
            {"url": "https://soundcloud.com/{}", "name": "SoundCloud"},
            {"url": "https://www.snapchat.com/add/{}", "name": "Snapchat"},
            {"url": "https://www.tiktok.com/@{}", "name": "TikTok"},
            {"url": "https://www.threads.net/@{}", "name": "Threads"},
            {"url": "https://discord.com/users/{}", "name": "Discord"},
            {"url": "https://www.reddit.com/user/{}", "name": "Reddit"},
            {"url": "https://www.kick.com/{}", "name": "Kick"},
            {"url": "https://onlyfans.com/{}", "name": "OnlyFans"}, 
            {"url": "https://itch.io/profile/{}", "name": "Itch.io"}, 
            {"url": "https://gamejolt.com/@{}", "name": "GameJolt"}, 
            {"url": "https://steamcommunity.com/id/{}", "name": "Steam"},
            {"url": "https://www.epicgames.com/id/{}", "name": "Epic Games"}, 
            {"url": "https://open.spotify.com/user/{}", "name": "Spotify"},
            {"url": "https://www.mixcloud.com/{}", "name": "Mixcloud"},
            {"url": "https://www.roblox.com/users/{}/profile", "name": "Roblox"},
            {"url": "https://linktr.ee/{}", "name": "Linktree"},
            {"url": "https://www.patreon.com/{}", "name": "Patreon"},
            {"url": "https://venmo.com/{}", "name": "Venmo"},
            {"url": "https://cash.app/{}", "name": "Cash App"},
            {"url": "https://paypal.me/{}", "name": "PayPal"},
            {"url": "https://www.notion.so/{}", "name": "Notion"},
            {"url": "https://www.behance.net/{}", "name": "Behance"},
            {"url": "https://dribbble.com/{}", "name": "Dribbble"},
            {"url": "https://ko-fi.com/{}", "name": "Ko-fi"},
            {"url": "https://mastodon.social/@{}", "name": "Mastodon"},
            {"url": "https://blueskyweb.xyz/profile/{}", "name": "Bluesky"},
            {"url": "https://substack.com/@{}", "name": "Substack"},
            {"url": "https://www.deviantart.com/{}", "name": "DeviantArt"},
            {"url": "https://www.artstation.com/{}", "name": "ArtStation"},
            {"url": "https://www.furaffinity.net/user/{}", "name": "FurAffinity"},
            {"url": "https://letterboxd.com/{}", "name": "Letterboxd"},
            {"url": "https://www.goodreads.com/user/show/{}", "name": "Goodreads"},
            {"url": "https://bandcamp.com/{}", "name": "Bandcamp"},
            {"url": "https://bsky.app/profile/{}", "name": "BlueSky (Alt URL)"},
            {"url": "https://www.carrd.co/{}", "name": "Carrd"},
            {"url": "https://www.buymeacoffee.com/{}", "name": "Buy Me a Coffee"},
            {"url": "https://www.wattpad.com/user/{}", "name": "Wattpad"},
            {"url": "https://vsco.co/{}", "name": "VSCO"},
            {"url": "https://rumble.com/c/{}", "name": "Rumble"},
            {"url": "https://bento.me/{}", "name": "Bento"},
            {"url": "https://socialclub.rockstargames.com/member/{}", "name": "Rockstar Social Club"},
            {"url": "https://www.anilist.co/user/{}", "name": "AniList"},
            {"url": "https://8tracks.com/{}", "name": "8tracks"},
            {"url": "https://www.stackoverflow.com/users/{}", "name": "Stack Overflow"},
            {"url": "https://forum.3dnews.ru/member.php?username={}", "name": "3dnews Forum"},
            {"url": "https://www.7cups.com/@{}", "name": "7 Cups"},
            {"url": "https://www.9gag.com/u/{}", "name": "9GAG"},
            {"url": "https://about.me/{}", "name": "About.me"},
            {"url": "https://independent.academia.edu/{}", "name": "Academia.edu"},
            {"url": "https://airlinepilot.life/u/{}", "name": "Airline Pilot Life"},
            {"url": "https://airbit.com/{}", "name": "Airbit"},
            {"url": "https://www.alik.cz/u/{}", "name": "Alik.cz"},
            {"url": "https://allmylinks.com/{}", "name": "AllMyLinks"},
            {"url": "https://aminoapps.com/u/{}", "name": "Amino Apps"},
            {"url": "https://developer.apple.com/forums/profile/{}", "name": "Apple Developer Forums"},
            {"url": "https://discussions.apple.com/profile/{}", "name": "Apple Discussions"},
            {"url": "https://archiveofourown.org/users/{}", "name": "Archive of Our Own"},
            {"url": "https://archive.org/details/@{}", "name": "Internet Archive"},
            {"url": "https://asciinema.org/~{}", "name": "Asciinema"},
            {"url": "https://ask.fedoraproject.org/u/{}", "name": "Fedora Project Ask"},
            {"url": "https://audiojungle.net/user/{}", "name": "AudioJungle"},
            {"url": "https://www.autofrage.net/nutzer/{}", "name": "Autofrage"},
            {"url": "https://www.avizo.cz/{}", "name": "Avizo.cz"},
            {"url": "https://blip.fm/{}", "name": "Blip.fm"},
            {"url": "https://bezuzyteczna.pl/uzytkownicy/{}", "name": "Bezuzyteczna.pl"},
            {"url": "https://www.biggerpockets.com/users/{}", "name": "BiggerPockets"},
            {"url": "https://forum.dangerousthings.com/u/{}", "name": "Dangerous Things Forum"},
            {"url": "https://bitcoinforum.com/profile/{}", "name": "Bitcoin Forum"},
            {"url": "https://bodyspace.bodybuilding.com/{}", "name": "BodySpace"},
            {"url": "https://buymeacoff.ee/{}", "name": "Buy Me a Coffee Alt"},
            {"url": "https://buzzfeed.com/{}", "name": "BuzzFeed"},
            {"url": "https://www.cgtrader.com/{}", "name": "CGTrader"},
            {"url": "https://ctan.org/author/{}", "name": "CTAN"},
            {"url": "https://career.habr.com/{}", "name": "Habr Career"},
            {"url": "https://www.championat.com/user/{}", "name": "Championat.com"},
            {"url": "https://chaos.social/@{}", "name": "Chaos Social"},
            {"url": "https://www.chess.com/member/{}", "name": "Chess.com"},
            {"url": "https://clapperapp.com/{}", "name": "Clapper"},
            {"url": "https://community.cloudflare.com/u/{}", "name": "Cloudflare Community"},
            {"url": "https://www.clozemaster.com/players/{}", "name": "Clozemaster"},
            {"url": "https://www.clubhouse.com/@{}", "name": "Clubhouse"},
            {"url": "https://codesnippets.fandom.com/wiki/User:{}", "name": "Code Snippets Fandom"},
            {"url": "https://www.codecademy.com/profiles/{}", "name": "Codecademy"},
            {"url": "https://www.codechef.com/users/{}", "name": "CodeChef"},
            {"url": "https://codepen.io/{}", "name": "CodePen"},
            {"url": "https://coderwall.com/{}", "name": "Coderwall"},
            {"url": "https://www.codewars.com/users/{}", "name": "Codewars"},
            {"url": "https://coinvote.cc/profile/{}", "name": "CoinVote"},
            {"url": "https://www.colourlovers.com/lover/{}", "name": "COLOURlovers"},
            {"url": "https://www.coroflot.com/{}", "name": "Coroflot"},
            {"url": "https://crowdin.com/profile/{}", "name": "Crowdin"},
            {"url": "https://community.cryptomator.org/u/{}", "name": "Cryptomator Community"},
            {"url": "https://dev.to/{}", "name": "DEV Community"},
            {"url": "https://dmoj.ca/user/{}", "name": "DMOJ"},
            {"url": "https://www.dailymotion.com/{}", "name": "Dailymotion"},
            {"url": "https://www.discogs.com/user/{}", "name": "Discogs"},
            {"url": "https://discuss.elastic.co/u/{}", "name": "Elastic Discuss"},
            {"url": "https://disqus.com/by/{}", "name": "Disqus"},
            {"url": "https://dribbble.com/{}", "name": "Dribbble"},
            {"url": "https://www.duolingo.com/profile/{}", "name": "Duolingo"},
            {"url": "https://community.eintracht.de/fans/{}", "name": "Eintracht Community"},
            {"url": "https://forums.envato.com/u/{}", "name": "Envato Forums"},
            {"url": "https://www.etsy.com/shop/{}", "name": "Etsy"},
            {"url": "https://euw.op.gg/summoner/userName={}", "name": "OP.GG EUW"},
            {"url": "https://www.eyeem.com/u/{}", "name": "EyeEm"},
            {"url": "https://fameswap.com/user/{}", "name": "FameSwap"},
            {"url": "https://www.fandom.com/u/{}", "name": "Fandom"},
            {"url": "https://www.finanzfrage.net/nutzer/{}", "name": "Finanzfrage"},
            {"url": "https://www.fiverr.com/{}", "name": "Fiverr"},
            {"url": "https://www.flickr.com/people/{}", "name": "Flickr"},
            {"url": "https://my.flightradar24.com/{}", "name": "Flightradar24"},
            {"url": "https://flipboard.com/@{}", "name": "Flipboard"},
            {"url": "https://fortnitetracker.com/profile/all/{}", "name": "Fortnite Tracker"},
            {"url": "https://freelance.habr.com/freelancers/{}", "name": "Habr Freelance"},
            {"url": "https://www.freelancer.com/u/{}", "name": "Freelancer"},
            {"url": "https://www.g2g.com/{}", "name": "G2G"},
            {"url": "https://gitlab.gnome.org/{}", "name": "GNOME GitLab"},
            {"url": "https://www.gaiaonline.com/profiles/{}", "name": "Gaia Online"},
            {"url": "https://geeksforgeeks.org/user/{}", "name": "GeeksforGeeks"},
            {"url": "https://genius.com/artists/{}", "name": "Genius"},
            {"url": "https://www.gesundheitsfrage.net/nutzer/{}", "name": "Gesundheitsfrage"},
            {"url": "https://giphy.com/channel/{}", "name": "Giphy"},
            {"url": "https://gitee.com/{}", "name": "Gitee"},
            {"url": "https://play.google.com/store/apps/developer?id={}", "name": "Google Play Developer"},
            {"url": "https://plugins.gradle.org/u/{}", "name": "Gradle Plugins"},
            {"url": "https://www.grailed.com/users/{}", "name": "Grailed"},
            {"url": "http://en.gravatar.com/{}", "name": "Gravatar"},
            {"url": "https://www.gumroad.com/{}", "name": "Gumroad"},
            {"url": "https://forums.gunsandammo.com/profile/{}", "name": "Guns and Ammo Forums"},
            {"url": "https://www.gutefrage.net/nutzer/{}", "name": "Gutefrage"},
            {"url": "https://www.hexrpg.com/userinfo/{}", "name": "Hexrpg"},
            {"url": "https://forum.hackthebox.eu/profile/{}", "name": "Hack The Box Forum"},
            {"url": "https://hackaday.io/project/{}", "name": "Hackaday.io"},
            {"url": "https://hackerearth.com/@{}", "name": "HackerEarth"},
            {"url": "https://news.ycombinator.com/user?id={}", "name": "Hacker News"},
            {"url": "https://hackerone.com/{}", "name": "HackerOne"},
            {"url": "https://hackerrank.com/profile/{}", "name": "HackerRank"},
            {"url": "https://holopin.io/@{}", "name": "Holopin"},
            {"url": "https://houzz.com/user/{}", "name": "Houzz"},
            {"url": "https://hubpages.com/@{}", "name": "HubPages"},
            {"url": "https://hubski.com/user/{}", "name": "Hubski"},
            {"url": "https://www.ifttt.com/p/{}", "name": "IFTTT"},
            {"url": "https://www.irl.com/{}", "name": "IRL"},
            {"url": "https://imgup.cz/user/{}", "name": "ImgUp.cz"},
            {"url": "https://imgur.com/user/{}", "name": "Imgur"},
            {"url": "https://www.instructables.com/member/{}", "name": "Instructables"},
            {"url": "https://app.intigriti.com/profile/{}", "name": "Intigriti"},
            {"url": "https://forum.ionicframework.com/u/{}", "name": "Ionic Framework Forum"},
            {"url": "https://issuu.com/{}", "name": "Issuu"},
            {"url": "https://www.itemfix.com/c/{}", "name": "ItemFix"},
            {"url": "https://discourse.joplinapp.org/u/{}", "name": "Joplin Forum"},
            {"url": "https://www.keakr.com/en/profile/{}", "name": "Keakr"},
            {"url": "https://www.kaggle.com/{}", "name": "Kaggle"},
            {"url": "https://keybase.io/{}", "name": "Keybase"},
            {"url": "https://kik.me/{}", "name": "Kik"},
            {"url": "https://www.kongregate.com/accounts/{}", "name": "Kongregate"},
            {"url": "https://launchpad.net/~{}", "name": "Launchpad"},
            {"url": "https://leetcode.com/problemset/all/?username={}", "name": "LeetCode"},
            {"url": "https://www.lesswrong.com/users/@{}", "name": "LessWrong"},
            {"url": "https://lichess.org/@/{}", "name": "Lichess"},
            {"url": "https://listed.to/@{}", "name": "Listed.to"},
            {"url": "https://lobste.rs/u/{}", "name": "Lobste.rs"},
            {"url": "https://lolchess.gg/profile/na/{}", "name": "LoLChess.gg"},
            {"url": "https://lottiefiles.com/{}", "name": "LottieFiles"},
            {"url": "https://forums.mmorpg.com/profile/{}", "name": "MMORPG.com Forums"},
            {"url": "https://mapify.travel/{}", "name": "Mapify"},
            {"url": "https://medium.com/@{}", "name": "Medium"},
            {"url": "https://api.mojang.com/users/profiles/minecraft/{}", "name": "Mojang API (Minecraft)"},
            {"url": "https://monkeytype.com/profile/{}", "name": "Monkeytype"},
            {"url": "https://www.motorradfrage.net/nutzer/{}", "name": "Motorradfrage"},
            {"url": "https://www.munzee.com/m/{}", "name": "Munzee"},
            {"url": "https://myanimelist.net/profile/{}", "name": "MyAnimeList"},
            {"url": "https://www.myminifactory.com/users/{}", "name": "MyMiniFactory"},
            {"url": "https://www.mydramalist.com/profile/{}", "name": "MyDramaList"},
            {"url": "https://myspace.com/{}", "name": "MySpace"},
            {"url": "https://community.native-instruments.com/profile/{}", "name": "Native Instruments Community"},
            {"url": "https://nationstates.net/nation={}", "name": "NationStates Nation"},
            {"url": "https://nationstates.net/region={}", "name": "NationStates Region"},
            {"url": "https://blog.naver.com/{}", "name": "Naver Blog"},
            {"url": "https://ninjakiwi.com/profile/{}", "name": "Ninja Kiwi"},
            {"url": "https://www.nintendolife.com/users/{}", "name": "Nintendo Life"},
            {"url": "https://www.nitrotype.com/racer/{}", "name": "Nitro Type"},
            {"url": "https://notabug.org/{}", "name": "Notabug"},
            {"url": "https://nyaa.si/user/{}", "name": "Nyaa.si"},
            {"url": "https://ogu.gg/user/{}", "name": "OGU.gg"},
            {"url": "https://www.openstreetmap.org/user/{}", "name": "OpenStreetMap"},
            {"url": "https://opensource.com/users/{}", "name": "Opensource.com"},
            {"url": "https://community.oracle.com/people/{}", "name": "Oracle Community"},
            {"url": "https://ourdjtalk.com/members?username={}", "name": "OurDJTalk"},
            {"url": "https://forums.pcgamer.com/members/?username={}", "name": "PC Gamer Forums"},
            {"url": "https://psnprofiles.com/{}", "name": "PSN Profiles"},
            {"url": "https://pastebin.com/u/{}", "name": "Pastebin"},
            {"url": "https://play.google.com/store/apps/developer?id={}", "name": "Google Play Developer (Alt)"},
            {"url": "https://pokemonshowdown.com/users/{}", "name": "Pokemon Showdown"},
            {"url": "https://polarsteps.com/{}", "name": "Polarsteps"},
            {"url": "https://www.polygon.com/users/{}", "name": "Polygon"},
            {"url": "https://polymart.org/user/{}", "name": "Polymart"},
            {"url": "https://www.producthunt.com/@{}", "name": "Product Hunt"},
            {"url": "http://promodj.com/{}", "name": "PromoDJ"},
            {"url": "https://pypi.org/user/{}", "name": "PyPI"},
            {"url": "https://quizlet.com/{}", "name": "Quizlet"},
            {"url": "https://rateyourmusic.com/~{}", "name": "RateYourMusic"},
            {"url": "https://forum.rclone.org/u/{}", "name": "Rclone Forum"},
            {"url": "https://www.redbubble.com/people/{}", "name": "Redbubble"},
            {"url": "https://www.reisefrage.net/nutzer/{}", "name": "Reisefrage"},
            {"url": "https://replit.com/@{}", "name": "Replit"},
            {"url": "https://www.researchgate.net/profile/{}", "name": "ResearchGate"},
            {"url": "https://www.reverbnation.com/{}", "name": "ReverbNation"},
            {"url": "https://www.roblox.com/user.aspx?username={}", "name": "Roblox (Alt)"},
            {"url": "https://rubygems.org/profiles/{}", "name": "RubyGems"},
            {"url": "https://rumble.com/user/{}", "name": "Rumble (Alt)"},
            {"url": "https://apps.runescape.com/runemetrics/app/overview/player/{}", "name": "RuneScape RuneMetrics"},
            {"url": "https://apps.runescape.com/runemetrics/profile/profile?user={}", "name": "RuneScape RuneMetrics Profile"},
            {"url": "https://swapd.co/u/{}", "name": "Swapd"},
            {"url": "https://www.sbazar.cz/{}", "name": "Sbazar.cz"},
            {"url": "https://scratch.mit.edu/users/{}", "name": "Scratch"},
            {"url": "https://www.scribd.com/user/{}", "name": "Scribd"},
            {"url": "https://www.shitpostbot.com/user/{}", "name": "Shitpostbot"},
            {"url": "https://www.shpock.com/shop/{}", "name": "Shpock"},
            {"url": "https://community.signalusers.org/u/{}", "name": "Signal Community"},
            {"url": "https://sketchfab.com/{}", "name": "Sketchfab"},
            {"url": "https://www.slant.co/users/{}", "name": "Slant"},
            {"url": "https://slashdot.org/~{}", "name": "Slashdot"},
            {"url": "https://slideshare.net/{}", "name": "SlideShare"},
            {"url": "https://slides.com/{}", "name": "Slides"},
            {"url": "https://www.smule.com/{}", "name": "Smule"},
            {"url": "https://soundcloud.com/{}", "name": "SoundCloud"},
            {"url": "https://sourceforge.net/u/{}", "name": "SourceForge"},
            {"url": "https://soylentnews.org/~{}", "name": "Soylent News"},
            {"url": "https://speedrun.com/user/{}", "name": "Speedrun.com"},
            {"url": "https://splice.com/{}", "name": "Splice"},
            {"url": "https://splits.io/users/{}", "name": "Splits.io"},
            {"url": "https://www.sportlerfrage.net/nutzer/{}", "name": "Sportlerfrage"},
            {"url": "https://www.sports.ru/profile/{}", "name": "Sports.ru"},
            {"url": "https://robertsspaceindustries.com/citizens/{}", "name": "Roberts Space Industries"},
            {"url": "https://steamcommunity.com/groups/{}", "name": "Steam Groups"},
            {"url": "https://www.strava.com/athletes/{}", "name": "Strava"},
            {"url": "https://forum.sublimetext.com/u/{}", "name": "Sublime Text Forum"},
            {"url": "https://ch.tetr.io/u/{}", "name": "Tetr.io"},
            {"url": "https://tldrlegal.com/users/{}", "name": "TLDRLegal"},
            {"url": "https://traktrain.com/{}", "name": "Traktrain"},
            {"url": "https://t.me/{}", "name": "Telegram"},
            {"url": "https://tellonym.me/{}", "name": "Tellonym"},
            {"url": "https://tenor.com/users/{}", "name": "Tenor"},
            {"url": "https://themeforest.net/user/{}", "name": "ThemeForest"},
            {"url": "https://www.tradingview.com/u/{}", "name": "TradingView"},
            {"url": "https://www.trakt.tv/users/{}", "name": "Trakt.tv"},
            {"url": "https://trashbox.ru/users/{}", "name": "Trashbox.ru"},
            {"url": "https://traewelling.de/@{}", "name": "Traewelling"},
            {"url": "https://trello.com/{}", "name": "Trello"},
            {"url": "https://trello.com/1/Members/{}", "name": "Trello Members API"},
            {"url": "https://tryhackme.com/p/{}", "name": "TryHackMe Profile"},
            {"url": "https://tryhackme.com/api/user/exist/{}", "name": "TryHackMe API"},
            {"url": "https://tuna.voicemod.net/user/{}", "name": "Voicemod Tuna"},
            {"url": "https://tweakers.net/gallery/{}", "name": "Tweakers.net"},
            {"url": "https://nitter.net/{}", "name": "Nitter"},
            {"url": "https://data.typeracer.com/pit/profile?user={}", "name": "TypeRacer"},
            {"url": "https://ultimate-guitar.com/u/{}", "name": "Ultimate Guitar"},
            {"url": "https://unsplash.com/@{}", "name": "Unsplash"},
            {"url": "https://vk.com/{}", "name": "VK"},
            {"url": "https://www.quora.com/profile/{}", "name": "Quora"},
            {"url": "https://truthsocial.com/@{}", "name": "Truth Social"},
            {"url": "https://apclips.com/user/{}", "name": "APClips"},
            {"url": "https://admireme.vip/{}", "name": "AdmireMe.VIP"},
            {"url": "https://www.allthingsworn.com/profile/{}", "name": "All Things Worn"},
            {"url": "https://pt.bongacams.com/profile/{}", "name": "BongaCams"},
            {"url": "https://chaturbate.com/{}", "name": "Chaturbate"},
            {"url": "https://www.erome.com/a/{}", "name": "Erome"},
            {"url": "https://www.forumophilia.com/profile.php?mode=viewprofile&u={}", "name": "Forumophilia"},
            {"url": "https://www.heavy-r.com/user/{}", "name": "Heavy-R"},
            {"url": "https://www.imagefap.com/profile/{}", "name": "ImageFap"},
            {"url": "https://pussy.com/u/{}", "name": "Pussy.com"},
            {"url": "https://pocketstars.com/{}", "name": "PocketStars"},
            {"url": "https://pornhub.com/users/{}", "name": "Pornhub"},
            {"url": "https://www.redtube.com/users/{}", "name": "Redtube"},
            {"url": "https://www.rockettube.com/{}", "name": "RocketTube"},
            {"url": "https://royalcams.com/profile/{}", "name": "RoyalCams"},
            {"url": "https://www.tnaflix.com/profile/{}", "name": "TNAFlix"},
            # Added 13 more websites to reach 300
            {"url": "https://www.fandom.com/f/{}", "name": "Fandom Community"},
            {"url": "https://www.gamespot.com/profile/{}", "name": "GameSpot"},
            {"url": "https://www.ign.com/boards/members/{}", "name": "IGN Boards"},
            {"url": "https://www.nexusmods.com/users/{}", "name": "Nexus Mods"},
            {"url": "https://www.moddb.com/members/{}", "name": "ModDB"},
            {"url": "https://www.indiedb.com/members/{}", "name": "IndieDB"},
            {"url": "https://www.gog.com/u/{}", "name": "GOG.com"},
            {"url": "https://www.origin.com/usa/en-us/profile/user/{}", "name": "Origin"},
            {"url": "https://www.ubisoft.com/en-us/profile/{}", "name": "Ubisoft"},
            {"url": "https://www.battlenet.com/profile/{}", "name": "Battle.net"},
            {"url": "https://www.epicgames.com/account/profile/user/{}", "name": "Epic Games (Alt)"},
            {"url": "https://www.xbox.com/en-us/profile/{}", "name": "Xbox"},
            {"url": "https://www.playstation.com/en-us/my-playstation/profile/{}", "name": "PlayStation Network"},
        ][:300] # Limit to 300 websites

        # Dictionary mapping site names to their specific "not found" keywords.
        # If a site is not listed here, the "default" keywords will be used.
        not_found_keywords = {
            "default": ["not found", "page not found", "error 404", "unavailable", "this content isn't available", "no such user", "doesn't exist", "could not be found", "not here", "nothing to see here", "whoops", "oops", "error", "no account", "invalid link", "private", "not found error", "unregistered", "site not found"],
            "YouTube": ["this page isn't available. sorry about that."],
            "Twitch": ["unless you’ve got a time machine, that content is unavailable."],
            "Twitch Mobile": ["sorry, that page is in another castle!"],
            "X": ["this account doesn’t exist"],
            "8tracks": ["this page has vanished, or perhaps it never even existed..."],
            "Stack Overflow": ["this content isn't available right now"],
            "3dnews Forum": ["your connection isn't private"],
            "7 Cups": ["not found"],
            "9GAG": ["there's nothing here."],
            "APClips": ["none"],
            "About.me": ["please check the name and try again."],
            "Academia.edu": ["oops! it looks like you're in the wrong aisle"],
            "AdmireMe.VIP": ["we’ve made a boob! we can’t seem to find the page you’re looking for."],
            "Airline Pilot Life": ["oops! that page doesn’t exist or is private."],
            "Airbit": ["user not found"],
            "Alik.cz": ["none"],
            "All Things Worn": ["this member has either changed their username or deleted their account."],
            "AllMyLinks": ["page not found"],
            "Amino Apps": ["ooops, this content does not exist."],
            "Apple Developer Forums": ["the page you’re looking for can’t be found"],
            "Apple Discussions": ["the page you tried was not found."],
            "Archive of Our Own": ["the page you tried was not found."],
            "Internet Archive": ["cannot find account"],
            "ArtStation": ["page not found"],
            "Asciinema": ["this page doesn't exist. sorry!"],
            "Fedora Project Ask": ["oops! that page doesn’t exist or is private."],
            "AudioJungle": ["404 - nothing to see here"],
            "Autofrage": ["hoppla!"],
            "Avizo.cz": ["none"],
            "Blip.fm": ["sorry, but the page you are trying to view does not exist."],
            "Bandcamp": ["sorry, that something isn’t here."],
            "Behance": ["oops! we can’t find that page."],
            "Bezuzyteczna.pl": ["none"],
            "BiggerPockets": ["it looks like the page you were looking for doesn't actually exist"],
            "Dangerous Things Forum": ["oops! that page doesn’t exist or is private."],
            "Bitcoin Forum": ["the user whose profile you are trying to view does not exist."],
            "BodySpace": ["none"],
            "BongaCams": ["none"],
            "Buy Me a Coffee": ["the page you’re looking for doesn’t exist."],
            "Buy Me a Coffee Alt": ["the page you’re looking for doesn’t exist."],
            "BuzzFeed": ["the page you’re looking for doesn’t exist."],
            "CGTrader": ["the page you’re looking for doesn’t exist."],
            "CTAN": ["not found"],
            "Habr Career": ["none"],
            "Championat.com": ["none"],
            "Chaos Social": ["the page you are looking for isn't here."],
            "Chaturbate": ["http 404 - page not found"],
            "Chess.com": ["oops! something is clearly wrong here..."],
            "Clapper": ["couldn't find this account"],
            "Cloudflare Community": ["oops! that page doesn’t exist or is private."],
            "Clozemaster": ["oh no! that page wasn't"],
            "Clubhouse": ["sorry! we couldn’t find what you were looking for"],
            "Code Snippets Fandom": ["there is currently no text in this page."],
            "Codecademy": ["this profile could not be found"],
            "CodeChef": ["error occured! page could not be found"],
            "CodePen": ["i'm afraid you've found a page that doesn't exist on codepen."],
            "Coderwall": ["404! our feels when that url is used"],
            "Codewars": ["whoops! the page you were looking for doesn't seem to exist."],
            "CoinVote": ["error 503 backend fetch failed"],
            "COLOURlovers": ["no one's home"],
            "Coroflot": ["sorry, the page you requested is no longer here, or you typed the wrong url."],
            "Crowdin": ["none"],
            "Cryptomator Community": ["oops! that page doesn’t exist or is private."],
            "DEV Community": ["this page does not exist"],
            "DMOJ": ["no user handle"],
            "Dailymotion": ["page not found"],
            "Discogs": ["we couldn't find that page."],
            "Elastic Discuss": ["oops! that page doesn’t exist or is private."],
            "Disqus": ["oops! this page could not be found!"],
            "Dribbble": ["whoops, that page is gone."],
            "Duolingo": ["sorry, the page you were looking for doesn’t exist."],
            "Eintracht Community": ["seite nicht gefunden"],
            "Envato Forums": ["oops! that page doesn’t exist or is private."],
            "Erome": ["page not found"],
            "Etsy": ["sorry, the page you were looking for was not found."],
            "OP.GG EUW": ["please try again."],
            "EyeEm": ["whoops! we can't find the user you're looking for"],
            "FameSwap": ["none"],
            "Fandom": ["this is not the page you are looking for."],
            "Finanzfrage": ["hoppla!"],
            "Fiverr": ["well, this isn't what you were looking for"],
            "Flickr": ["this is not the page you’re looking for."],
            "Flightradar24": ["sorry, this page could not be found"],
            "Flipboard": ["this page does not exist"],
            "Fortnite Tracker": ["404 not found. we are unable to find your profile"],
            "Forumophilia": ["sorry, but that user does not exist."],
            "Habr Freelance": ["none"],
            "Freelancer": ["404 - page not found"],
            "G2G": ["none"],
            "GNOME GitLab": ["none"],
            "Gaia Online": ["no user id specified or user does not exist!"],
            "GeeksforGeeks": ["no user id specified or user does not exist!"],
            "Genius": ["oops! page not found"],
            "Gesundheitsfrage": ["hoppla!"],
            "Giphy": ["oops! there’s nothing here."],
            "GitHub": ["find code, projects, and people on github"],
            "Gitee": ["none"],
            "Goodreads": ["page-is-gone"],
            "Google Play Developer": ["we're sorry, the requested url was not found on this server."],
            "Google Play Developer (Alt)": ["this page couldn’t be found"],
            "Gradle Plugins": ["user not found"],
            "Grailed": ["404 - page not found"],
            "Gravatar": ["uh oh. page not found"],
            "Gumroad": ["uh oh. page not found"],
            "Guns and Ammo Forums": ["oops... it looks like there was an error with that link."],
            "Gutefrage": ["hoppla!"],
            "Hexrpg": ["error"],
            "Hack The Box Forum": ["oops! that page doesn’t exist or is private."],
            "Hackaday.io": ["page not found"],
            "HackerEarth": ["404. url not found."],
            "Hacker News": ["no such user."],
            "HackerOne": ["not found"],
            "HackerRank": ["we could not find the page you were looking for, so we found something to make you laugh to make up for it."],
            "Heavy-R": ["none"],
            "Holopin": ["not found"],
            "Houzz": ["not found"],
            "HubPages": ["404. page does not exist"],
            "Hubski": ["no such user."],
            "IFTTT": ["the requested page or file does not exist"],
            "IRL": ["irl has shut down"],
            "ImageFap": ["none"],
            "ImgUp.cz": ["oops! that page can’t be found."],
            "Imgur": ["we searched high and low, but we couldn’t find the page"],
            "Instructables": ["404: we're sorry, things break sometimes"],
            "Intigriti": ["we didn't find what you're looking for"],
            "Ionic Framework Forum": ["oops! that page doesn’t exist or is private."],
            "Issuu": ["oops — we can’t seem to find the page you’re looking for"],
            "ItemFix": ["none"],
            "Joplin Forum": ["oops! that page doesn’t exist or is private."],
            "Keakr": ["sorry, this page doesn't exist"],
            "Kaggle": ["we can't find that page."],
            "Keybase": ["sorry, what you are looking for...it does not exist."],
            "Kik": ["none"],
            "Kongregate": ["sorry, no account with that name was found."],
            "Launchpad": ["lost something?"],
            "LeetCode": ["page not found"],
            "LessWrong": ["404 not found"],
            "Letterboxd": ["sorry, we can’t find the page you’ve requested."],
            "Lichess": ["page not found!"],
            "Pussy.com": ["none"],
            "Linktree": ["the page you’re looking for doesn’t exist."],
            "Listed.to": ["the page you were looking for doesn't exist."],
            "Lobste.rs": ["the resource you requested was not found, or the story has been deleted."],
            "LoLChess.gg": ["please try again."],
            "LottieFiles": ["we couldn’t find the page you’re looking for."],
            "Lush Stories": ["page not found"],
            "MMORPG.com Forums": ["404 not found"],
            "Mapify": ["page not found"],
            "Medium": ["out of nothing, something."],
            "Mojang API (Minecraft)": ["not found"],
            "Monkeytype": ["not found"],
            "Motherless.com": ["none"],
            "Motorradfrage": ["hoppla!"],
            "Munzee": ["oops, looks like the page is not found"],
            "MyAnimeList": ["this page doesn't exist."],
            "MyMiniFactory": ["something has gone wrong or you have entered an incorrect link"],
            "MyDramaList": ["don't have an account?"],
            "MySpace": ["page not found"],
            "Native Instruments Community": ["none"],
            "NationStates Nation": ["nation not found"],
            "NationStates Region": ["region not found"],
            "Naver Blog": ["none"],
            "Ninja Kiwi": ["this page isn’t working right now"],
            "Nintendo Life": ["not found"],
            "Nitro Type": ["oops! are you lost, racer?"],
            "Notabug": ["if you think this is an error, please open an issue on"],
            "Nyaa.si": ["404 not found"],
            "OGU.gg": ["none"],
            "OpenStreetMap": ["does not exist"],
            "Opensource.com": ["page not found"],
            "Oracle Community": ["user not found"],
            "OurDJTalk": ["the specified member cannot be found. please enter a member's entire name."],
            "PC Gamer Forums": ["the specified member cannot be found. please enter a member's entire name."],
            "PSN Profiles": ["none"],
            "Pastebin": ["not found (#404)"],
            "Patreon": ["this page couldn’t be found"],
            "PocketStars": ["none"],
            "Pokemon Showdown": ["(unregistered)"],
            "Polarsteps": ["it seems like this user is not here (anymore)."],
            "Polygon": ["404 not found"],
            "Polymart": ["looks like we couldn't find this user. sorry!"],
            "Pornhub": ["none"],
            "Product Hunt": ["we seem to have lost this page"],
            "PromoDJ": ["page not found"],
            "PyPI": ["we looked everywhere but couldn't find this page"],
            "Quizlet": ["hmm, looks like you're studying old notes"],
            "RateYourMusic": ["error 404: not found"],
            "Rclone Forum": ["oops! that page doesn’t exist or is private."],
            "Redtube": ["none"],
            "Redbubble": ["404. houston, we have a problem"],
            "Reddit": ["sorry, nobody on reddit goes by that name"],
            "Reisefrage": ["hoppla!"],
            "Replit": ["not found error: this is not the page you’re looking for."],
            "ResearchGate": ["page not found"],
            "ReverbNation": ["sorry, we couldn't find that page"],
            "Roblox": ["page cannot be found or no longer exists"],
            "Roblox (Alt)": ["page cannot be found or no longer exists"],
            "RocketTube": ["none"],
            "RoyalCams": ["none"],
            "RubyGems": ["page not found"],
            "Rumble": ["channel not found", "user not found", "page not found", "error 404", "could not find what you were looking for"],
            "Rumble (Alt)": ["404 - not found"],
            "RuneScape RuneMetrics": ["sorry, that player could not be found."],
            "RuneScape RuneMetrics Profile": ["no_profile"],
            "Swapd": ["oops! that page doesn’t exist :("],
            "Sbazar.cz": ["stránka nenalezena"],
            "Scratch": ["whoops! our server is scratch'ing its head"],
            "Scribd": ["page not found"],
            "Shitpostbot": ["returning 404 page"],
            "Shpock": ["if you see this, something went wrong."],
            "Signal Community": ["oops! that page doesn’t exist or is private."],
            "Sketchfab": ["error 404"],
            "Slant": ["404 page not found"],
            "Slashdot": ["the user you requested does not exist, no matter how much you wish this might be the case."],
            "SlideShare": ["this username"],
            "Slides": ["we couldn't find what you're looking for"],
            "Smule": ["right tune, wrong note!"],
            "SoundCloud": ["we can’t find that user."],
            "SourceForge": ["whoops, we can't find that page."],
            "Soylent News": ["the user you requested does not exist, no matter how much you wish this might be the case."],
            "Speedrun.com": ["not found"],
            "Splice": ["the page you were looking for could not be found."],
            "Splits.io": ["this page doesn't exist."],
            "Sportlerfrage": ["hoppla!"],
            "Sports.ru": ["none"],
            "Roberts Space Industries": ["navigating uncharted territory"],
            "Steam Groups": ["sorry!"],
            "Strava": ["none"],
            "Sublime Text Forum": ["oops! that page doesn’t exist or is private."],
            "Tetr.io": ["no such user!"],
            "TLDRLegal": ["oops... something went wrong."],
            "Traktrain": ["mistyped url"],
            "Telegram": ["none"],
            "Tellonym": ["none"],
            "Tenor": ["we could not find the page you were looking for."],
            "ThemeForest": ["404 - nothing to see here"],
            "TradingView": ["page not found"],
            "Trakt.tv": ["come, my lord, you are a long way from home and winter is coming."],
            "Trashbox.ru": ["404 — not found"],
            "Traewelling": ["not found"],
            "Trello": ["page not found."],
            "Trello Members API": ["oh no! 404!"],
            "TryHackMe Profile": ["nothing to see here"],
            "TryHackMe API": ["false"],
            "Voicemod Tuna": ["the page you are looking for could not be found."],
            "Tweakers.net": ["404 not found"],
            "Nitter": ["page not found"],
            "TypeRacer": ["profile not found"],
            "Ultimate Guitar": ["oops! we couldn't find that page."],
            "Unsplash": ["page not found"],
            "VK": ["page not found"],
            "Quora": ["page not found"],
            "Truth Social": ["none"],
            "APClips": ["none"],
            "AdmireMe.VIP": ["we’ve made a boob! we can’t seem to find the page you’re looking for."],
            "All Things Worn": ["this member has either changed their username or deleted their account."],
            "BongaCams": ["none"],
            "Chaturbate": ["http 404 - page not found"],
            "Erome": ["page not found"],
            "Forumophilia": ["sorry, but that user does not exist."],
            "Heavy-R": ["none"],
            "ImageFap": ["none"],
            "Pussy.com": ["none"],
            "PocketStars": ["none"],
            "Pornhub": ["none"],
            "Redtube": ["none"],
            "RocketTube": ["none"],
            "RoyalCams": ["none"],
            "TNAFlix": ["welcome to our most secret page"],
            "Fandom Community": ["this is not the page you are looking for."],
            "GameSpot": ["page not found"],
            "IGN Boards": ["the page you tried was not found."],
            "Nexus Mods": ["404 not found"],
            "ModDB": ["error 404"],
            "IndieDB": ["error 404"],
            "GOG.com": ["page not found"],
            "Origin": ["page not found"],
            "Ubisoft": ["page not found"],
            "Battle.net": ["page not found"],
            "Epic Games (Alt)": ["page not found"],
            "Xbox": ["page not found"],
            "PlayStation Network": ["page not found"],
        }

        total_sites = len(social_media)
        completed_tasks = 0
        
        def check_single_site(site_info):
            site_url_template = site_info['url']
            site_name = site_info['name']
            url = site_url_template.format(username)
            
            response = None  # Initialize response to None
            try:
                response = requests.get(url, timeout=7)
                response.raise_for_status()
                response_text_lower = response.text.lower()
                
                site_not_found_keywords = not_found_keywords.get(site_name, not_found_keywords["default"])
                
                found_specific_not_found = False
                for keyword in site_not_found_keywords:
                    if keyword in response_text_lower:
                        found_specific_not_found = True
                        break

                if found_specific_not_found:
                    return site_name, "Username not found."
                else:
                    return site_name, url
            except requests.exceptions.Timeout:
                return site_name, "Username not found."
            except requests.exceptions.RequestException as e:
                # For any request exception, including 404, just return "Username not found."
                return site_name, "Username not found."
            except Exception as e:
                return site_name, "Username not found."

        # Use ThreadPoolExecutor for concurrent requests to speed up checks
        # Increased max_workers to 40 for even faster checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
            future_to_site = {executor.submit(check_single_site, site): site for site in social_media}
            
            for future in concurrent.futures.as_completed(future_to_site):
                site_name, status_or_url = future.result()
                results[site_name] = status_or_url
                completed_tasks += 1
                if progress_callback:
                    progress_callback(completed_tasks, total_sites)

        return results

    def _track_username(self):
        username = self.username_input_field.text().strip()
        if not username:
            self.username_status_label.setText("Please enter a username.")
            self.username_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
            return
        
        # This list is used only for setting the progress bar range.
        # It must be identical to the social_media list in _check_username.
        temp_social_media_list_for_progress = [
            {"url": "https://www.youtube.com/@{}", "name": "YouTube"},
            {"url": "https://www.twitch.tv/{}", "name": "Twitch"},
            {"url": "https://m.twitch.tv/{}", "name": "Twitch Mobile"},
            {"url": "https://x.com/{}", "name": "X"},
            {"url": "https://www.facebook.com/{}", "name": "Facebook"},
            {"url": "https://www.instagram.com/{}", "name": "Instagram"},
            {"url": "https://www.linkedin.com/in/{}", "name": "LinkedIn"},
            {"url": "https://github.com/{}", "name": "GitHub"},
            {"url": "https://www.pinterest.com/{}", "name": "Pinterest"},
            {"url": "https://soundcloud.com/{}", "name": "SoundCloud"},
            {"url": "https://www.snapchat.com/add/{}", "name": "Snapchat"},
            {"url": "https://www.tiktok.com/@{}", "name": "TikTok"},
            {"url": "https://www.threads.net/@{}", "name": "Threads"},
            {"url": "https://discord.com/users/{}", "name": "Discord"},
            {"url": "https://www.reddit.com/user/{}", "name": "Reddit"},
            {"url": "https://www.kick.com/{}", "name": "Kick"},
            {"url": "https://onlyfans.com/{}", "name": "OnlyFans"}, 
            {"url": "https://itch.io/profile/{}", "name": "Itch.io"}, 
            {"url": "https://gamejolt.com/@{}", "name": "GameJolt"}, 
            {"url": "https://steamcommunity.com/id/{}", "name": "Steam"},
            {"url": "https://www.epicgames.com/id/{}", "name": "Epic Games"}, 
            {"url": "https://open.spotify.com/user/{}", "name": "Spotify"},
            {"url": "https://www.mixcloud.com/{}", "name": "Mixcloud"},
            {"url": "https://www.roblox.com/users/{}/profile", "name": "Roblox"},
            {"url": "https://linktr.ee/{}", "name": "Linktree"},
            {"url": "https://www.patreon.com/{}", "name": "Patreon"},
            {"url": "https://venmo.com/{}", "name": "Venmo"},
            {"url": "https://cash.app/{}", "name": "Cash App"},
            {"url": "https://paypal.me/{}", "name": "PayPal"},
            {"url": "https://www.notion.so/{}", "name": "Notion"},
            {"url": "https://www.behance.net/{}", "name": "Behance"},
            {"url": "https://dribbble.com/{}", "name": "Dribbble"},
            {"url": "https://ko-fi.com/{}", "name": "Ko-fi"},
            {"url": "https://mastodon.social/@{}", "name": "Mastodon"},
            {"url": "https://blueskyweb.xyz/profile/{}", "name": "Bluesky"},
            {"url": "https://substack.com/@{}", "name": "Substack"},
            {"url": "https://www.deviantart.com/{}", "name": "DeviantArt"},
            {"url": "https://www.artstation.com/{}", "name": "ArtStation"},
            {"url": "https://www.furaffinity.net/user/{}", "name": "FurAffinity"},
            {"url": "https://letterboxd.com/{}", "name": "Letterboxd"},
            {"url": "https://www.goodreads.com/user/show/{}", "name": "Goodreads"},
            {"url": "https://bandcamp.com/{}", "name": "Bandcamp"},
            {"url": "https://bsky.app/profile/{}", "name": "BlueSky (Alt URL)"},
            {"url": "https://www.carrd.co/{}", "name": "Carrd"},
            {"url": "https://www.buymeacoffee.com/{}", "name": "Buy Me a Coffee"},
            {"url": "https://www.wattpad.com/user/{}", "name": "Wattpad"},
            {"url": "https://vsco.co/{}", "name": "VSCO"},
            {"url": "https://rumble.com/c/{}", "name": "Rumble"},
            {"url": "https://bento.me/{}", "name": "Bento"},
            {"url": "https://socialclub.rockstargames.com/member/{}", "name": "Rockstar Social Club"},
            {"url": "https://www.anilist.co/user/{}", "name": "AniList"},
            {"url": "https://8tracks.com/{}", "name": "8tracks"},
            {"url": "https://www.stackoverflow.com/users/{}", "name": "Stack Overflow"},
            {"url": "https://forum.3dnews.ru/member.php?username={}", "name": "3dnews Forum"},
            {"url": "https://www.7cups.com/@{}", "name": "7 Cups"},
            {"url": "https://www.9gag.com/u/{}", "name": "9GAG"},
            {"url": "https://about.me/{}", "name": "About.me"},
            {"url": "https://independent.academia.edu/{}", "name": "Academia.edu"},
            {"url": "https://airlinepilot.life/u/{}", "name": "Airline Pilot Life"},
            {"url": "https://airbit.com/{}", "name": "Airbit"},
            {"url": "https://www.alik.cz/u/{}", "name": "Alik.cz"},
            {"url": "https://allmylinks.com/{}", "name": "AllMyLinks"},
            {"url": "https://aminoapps.com/u/{}", "name": "Amino Apps"},
            {"url": "https://developer.apple.com/forums/profile/{}", "name": "Apple Developer Forums"},
            {"url": "https://discussions.apple.com/profile/{}", "name": "Apple Discussions"},
            {"url": "https://archiveofourown.org/users/{}", "name": "Archive of Our Own"},
            {"url": "https://archive.org/details/@{}", "name": "Internet Archive"},
            {"url": "https://asciinema.org/~{}", "name": "Asciinema"},
            {"url": "https://ask.fedoraproject.org/u/{}", "name": "Fedora Project Ask"},
            {"url": "https://audiojungle.net/user/{}", "name": "AudioJungle"},
            {"url": "https://www.autofrage.net/nutzer/{}", "name": "Autofrage"},
            {"url": "https://www.avizo.cz/{}", "name": "Avizo.cz"},
            {"url": "https://blip.fm/{}", "name": "Blip.fm"},
            {"url": "https://bezuzyteczna.pl/uzytkownicy/{}", "name": "Bezuzyteczna.pl"},
            {"url": "https://www.biggerpockets.com/users/{}", "name": "BiggerPockets"},
            {"url": "https://forum.dangerousthings.com/u/{}", "name": "Dangerous Things Forum"},
            {"url": "https://bitcoinforum.com/profile/{}", "name": "Bitcoin Forum"},
            {"url": "https://bodyspace.bodybuilding.com/{}", "name": "BodySpace"},
            {"url": "https://buymeacoff.ee/{}", "name": "Buy Me a Coffee Alt"},
            {"url": "https://buzzfeed.com/{}", "name": "BuzzFeed"},
            {"url": "https://www.cgtrader.com/{}", "name": "CGTrader"},
            {"url": "https://ctan.org/author/{}", "name": "CTAN"},
            {"url": "https://career.habr.com/{}", "name": "Habr Career"},
            {"url": "https://www.championat.com/user/{}", "name": "Championat.com"},
            {"url": "https://chaos.social/@{}", "name": "Chaos Social"},
            {"url": "https://www.chess.com/member/{}", "name": "Chess.com"},
            {"url": "https://clapperapp.com/{}", "name": "Clapper"},
            {"url": "https://community.cloudflare.com/u/{}", "name": "Cloudflare Community"},
            {"url": "https://www.clozemaster.com/players/{}", "name": "Clozemaster"},
            {"url": "https://www.clubhouse.com/@{}", "name": "Clubhouse"},
            {"url": "https://codesnippets.fandom.com/wiki/User:{}", "name": "Code Snippets Fandom"},
            {"url": "https://www.codecademy.com/profiles/{}", "name": "Codecademy"},
            {"url": "https://www.codechef.com/users/{}", "name": "CodeChef"},
            {"url": "https://codepen.io/{}", "name": "CodePen"},
            {"url": "https://coderwall.com/{}", "name": "Coderwall"},
            {"url": "https://www.codewars.com/users/{}", "name": "Codewars"},
            {"url": "https://coinvote.cc/profile/{}", "name": "CoinVote"},
            {"url": "https://www.colourlovers.com/lover/{}", "name": "COLOURlovers"},
            {"url": "https://www.coroflot.com/{}", "name": "Coroflot"},
            {"url": "https://crowdin.com/profile/{}", "name": "Crowdin"},
            {"url": "https://community.cryptomator.org/u/{}", "name": "Cryptomator Community"},
            {"url": "https://dev.to/{}", "name": "DEV Community"},
            {"url": "https://dmoj.ca/user/{}", "name": "DMOJ"},
            {"url": "https://www.dailymotion.com/{}", "name": "Dailymotion"},
            {"url": "https://www.discogs.com/user/{}", "name": "Discogs"},
            {"url": "https://discuss.elastic.co/u/{}", "name": "Elastic Discuss"},
            {"url": "https://disqus.com/by/{}", "name": "Disqus"},
            {"url": "https://dribbble.com/{}", "name": "Dribbble"},
            {"url": "https://www.duolingo.com/profile/{}", "name": "Duolingo"},
            {"url": "https://community.eintracht.de/fans/{}", "name": "Eintracht Community"},
            {"url": "https://forums.envato.com/u/{}", "name": "Envato Forums"},
            {"url": "https://www.etsy.com/shop/{}", "name": "Etsy"},
            {"url": "https://euw.op.gg/summoner/userName={}", "name": "OP.GG EUW"},
            {"url": "https://www.eyeem.com/u/{}", "name": "EyeEm"},
            {"url": "https://fameswap.com/user/{}", "name": "FameSwap"},
            {"url": "https://www.fandom.com/u/{}", "name": "Fandom"},
            {"url": "https://www.finanzfrage.net/nutzer/{}", "name": "Finanzfrage"},
            {"url": "https://www.fiverr.com/{}", "name": "Fiverr"},
            {"url": "https://www.flickr.com/people/{}", "name": "Flickr"},
            {"url": "https://my.flightradar24.com/{}", "name": "Flightradar24"},
            {"url": "https://flipboard.com/@{}", "name": "Flipboard"},
            {"url": "https://fortnitetracker.com/profile/all/{}", "name": "Fortnite Tracker"},
            {"url": "https://freelance.habr.com/freelancers/{}", "name": "Habr Freelance"},
            {"url": "https://www.freelancer.com/u/{}", "name": "Freelancer"},
            {"url": "https://www.g2g.com/{}", "name": "G2G"},
            {"url": "https://gitlab.gnome.org/{}", "name": "GNOME GitLab"},
            {"url": "https://www.gaiaonline.com/profiles/{}", "name": "Gaia Online"},
            {"url": "https://geeksforgeeks.org/user/{}", "name": "GeeksforGeeks"},
            {"url": "https://genius.com/artists/{}", "name": "Genius"},
            {"url": "https://www.gesundheitsfrage.net/nutzer/{}", "name": "Gesundheitsfrage"},
            {"url": "https://giphy.com/channel/{}", "name": "Giphy"},
            {"url": "https://gitee.com/{}", "name": "Gitee"},
            {"url": "https://play.google.com/store/apps/developer?id={}", "name": "Google Play Developer"},
            {"url": "https://plugins.gradle.org/u/{}", "name": "Gradle Plugins"},
            {"url": "https://www.grailed.com/users/{}", "name": "Grailed"},
            {"url": "http://en.gravatar.com/{}", "name": "Gravatar"},
            {"url": "https://www.gumroad.com/{}", "name": "Gumroad"},
            {"url": "https://forums.gunsandammo.com/profile/{}", "name": "Guns and Ammo Forums"},
            {"url": "https://www.gutefrage.net/nutzer/{}", "name": "Gutefrage"},
            {"url": "https://www.hexrpg.com/userinfo/{}", "name": "Hexrpg"},
            {"url": "https://forum.hackthebox.eu/profile/{}", "name": "Hack The Box Forum"},
            {"url": "https://hackaday.io/project/{}", "name": "Hackaday.io"},
            {"url": "https://hackerearth.com/@{}", "name": "HackerEarth"},
            {"url": "https://news.ycombinator.com/user?id={}", "name": "Hacker News"},
            {"url": "https://hackerone.com/{}", "name": "HackerOne"},
            {"url": "https://hackerrank.com/profile/{}", "name": "HackerRank"},
            {"url": "https://holopin.io/@{}", "name": "Holopin"},
            {"url": "https://houzz.com/user/{}", "name": "Houzz"},
            {"url": "https://hubpages.com/@{}", "name": "HubPages"},
            {"url": "https://hubski.com/user/{}", "name": "Hubski"},
            {"url": "https://www.ifttt.com/p/{}", "name": "IFTTT"},
            {"url": "https://www.irl.com/{}", "name": "IRL"},
            {"url": "https://imgup.cz/user/{}", "name": "ImgUp.cz"},
            {"url": "https://imgur.com/user/{}", "name": "Imgur"},
            {"url": "https://www.instructables.com/member/{}", "name": "Instructables"},
            {"url": "https://app.intigriti.com/profile/{}", "name": "Intigriti"},
            {"url": "https://forum.ionicframework.com/u/{}", "name": "Ionic Framework Forum"},
            {"url": "https://issuu.com/{}", "name": "Issuu"},
            {"url": "https://www.itemfix.com/c/{}", "name": "ItemFix"},
            {"url": "https://discourse.joplinapp.org/u/{}", "name": "Joplin Forum"},
            {"url": "https://www.keakr.com/en/profile/{}", "name": "Keakr"},
            {"url": "https://www.kaggle.com/{}", "name": "Kaggle"},
            {"url": "https://keybase.io/{}", "name": "Keybase"},
            {"url": "https://kik.me/{}", "name": "Kik"},
            {"url": "https://www.kongregate.com/accounts/{}", "name": "Kongregate"},
            {"url": "https://launchpad.net/~{}", "name": "Launchpad"},
            {"url": "https://leetcode.com/problemset/all/?username={}", "name": "LeetCode"},
            {"url": "https://www.lesswrong.com/users/@{}", "name": "LessWrong"},
            {"url": "https://lichess.org/@/{}", "name": "Lichess"},
            {"url": "https://listed.to/@{}", "name": "Listed.to"},
            {"url": "https://lobste.rs/u/{}", "name": "Lobste.rs"},
            {"url": "https://lolchess.gg/profile/na/{}", "name": "LoLChess.gg"},
            {"url": "https://lottiefiles.com/{}", "name": "LottieFiles"},
            {"url": "https://forums.mmorpg.com/profile/{}", "name": "MMORPG.com Forums"},
            {"url": "https://mapify.travel/{}", "name": "Mapify"},
            {"url": "https://medium.com/@{}", "name": "Medium"},
            {"url": "https://api.mojang.com/users/profiles/minecraft/{}", "name": "Mojang API (Minecraft)"},
            {"url": "https://monkeytype.com/profile/{}", "name": "Monkeytype"},
            {"url": "https://www.motorradfrage.net/nutzer/{}", "name": "Motorradfrage"},
            {"url": "https://www.munzee.com/m/{}", "name": "Munzee"},
            {"url": "https://myanimelist.net/profile/{}", "name": "MyAnimeList"},
            {"url": "https://www.myminifactory.com/users/{}", "name": "MyMiniFactory"},
            {"url": "https://www.mydramalist.com/profile/{}", "name": "MyDramaList"},
            {"url": "https://myspace.com/{}", "name": "MySpace"},
            {"url": "https://community.native-instruments.com/profile/{}", "name": "Native Instruments Community"},
            {"url": "https://nationstates.net/nation={}", "name": "NationStates Nation"},
            {"url": "https://nationstates.net/region={}", "name": "NationStates Region"},
            {"url": "https://blog.naver.com/{}", "name": "Naver Blog"},
            {"url": "https://ninjakiwi.com/profile/{}", "name": "Ninja Kiwi"},
            {"url": "https://www.nintendolife.com/users/{}", "name": "Nintendo Life"},
            {"url": "https://www.nitrotype.com/racer/{}", "name": "Nitro Type"},
            {"url": "https://notabug.org/{}", "name": "Notabug"},
            {"url": "https://nyaa.si/user/{}", "name": "Nyaa.si"},
            {"url": "https://ogu.gg/user/{}", "name": "OGU.gg"},
            {"url": "https://www.openstreetmap.org/user/{}", "name": "OpenStreetMap"},
            {"url": "https://opensource.com/users/{}", "name": "Opensource.com"},
            {"url": "https://community.oracle.com/people/{}", "name": "Oracle Community"},
            {"url": "https://ourdjtalk.com/members?username={}", "name": "OurDJTalk"},
            {"url": "https://forums.pcgamer.com/members/?username={}", "name": "PC Gamer Forums"},
            {"url": "https://psnprofiles.com/{}", "name": "PSN Profiles"},
            {"url": "https://pastebin.com/u/{}", "name": "Pastebin"},
            {"url": "https://play.google.com/store/apps/developer?id={}", "name": "Google Play Developer (Alt)"},
            {"url": "https://pokemonshowdown.com/users/{}", "name": "Pokemon Showdown"},
            {"url": "https://polarsteps.com/{}", "name": "Polarsteps"},
            {"url": "https://www.polygon.com/users/{}", "name": "Polygon"},
            {"url": "https://polymart.org/user/{}", "name": "Polymart"},
            {"url": "https://www.producthunt.com/@{}", "name": "Product Hunt"},
            {"url": "http://promodj.com/{}", "name": "PromoDJ"},
            {"url": "https://pypi.org/user/{}", "name": "PyPI"},
            {"url": "https://quizlet.com/{}", "name": "Quizlet"},
            {"url": "https://rateyourmusic.com/~{}", "name": "RateYourMusic"},
            {"url": "https://forum.rclone.org/u/{}", "name": "Rclone Forum"},
            {"url": "https://www.redbubble.com/people/{}", "name": "Redbubble"},
            {"url": "https://www.reisefrage.net/nutzer/{}", "name": "Reisefrage"},
            {"url": "https://replit.com/@{}", "name": "Replit"},
            {"url": "https://www.researchgate.net/profile/{}", "name": "ResearchGate"},
            {"url": "https://www.reverbnation.com/{}", "name": "ReverbNation"},
            {"url": "https://www.roblox.com/user.aspx?username={}", "name": "Roblox (Alt)"},
            {"url": "https://rubygems.org/profiles/{}", "name": "RubyGems"},
            {"url": "https://rumble.com/user/{}", "name": "Rumble (Alt)"},
            {"url": "https://apps.runescape.com/runemetrics/app/overview/player/{}", "name": "RuneScape RuneMetrics"},
            {"url": "https://apps.runescape.com/runemetrics/profile/profile?user={}", "name": "RuneScape RuneMetrics Profile"},
            {"url": "https://swapd.co/u/{}", "name": "Swapd"},
            {"url": "https://www.sbazar.cz/{}", "name": "Sbazar.cz"},
            {"url": "https://scratch.mit.edu/users/{}", "name": "Scratch"},
            {"url": "https://www.scribd.com/user/{}", "name": "Scribd"},
            {"url": "https://www.shitpostbot.com/user/{}", "name": "Shitpostbot"},
            {"url": "https://www.shpock.com/shop/{}", "name": "Shpock"},
            {"url": "https://community.signalusers.org/u/{}", "name": "Signal Community"},
            {"url": "https://sketchfab.com/{}", "name": "Sketchfab"},
            {"url": "https://www.slant.co/users/{}", "name": "Slant"},
            {"url": "https://slashdot.org/~{}", "name": "Slashdot"},
            {"url": "https://slideshare.net/{}", "name": "SlideShare"},
            {"url": "https://slides.com/{}", "name": "Slides"},
            {"url": "https://www.smule.com/{}", "name": "Smule"},
            {"url": "https://soundcloud.com/{}", "name": "SoundCloud"},
            {"url": "https://sourceforge.net/u/{}", "name": "SourceForge"},
            {"url": "https://soylentnews.org/~{}", "name": "Soylent News"},
            {"url": "https://speedrun.com/user/{}", "name": "Speedrun.com"},
            {"url": "https://splice.com/{}", "name": "Splice"},
            {"url": "https://splits.io/users/{}", "name": "Splits.io"},
            {"url": "https://www.sportlerfrage.net/nutzer/{}", "name": "Sportlerfrage"},
            {"url": "https://www.sports.ru/profile/{}", "name": "Sports.ru"},
            {"url": "https://robertsspaceindustries.com/citizens/{}", "name": "Roberts Space Industries"},
            {"url": "https://steamcommunity.com/groups/{}", "name": "Steam Groups"},
            {"url": "https://www.strava.com/athletes/{}", "name": "Strava"},
            {"url": "https://forum.sublimetext.com/u/{}", "name": "Sublime Text Forum"},
            {"url": "https://ch.tetr.io/u/{}", "name": "Tetr.io"},
            {"url": "https://tldrlegal.com/users/{}", "name": "TLDRLegal"},
            {"url": "https://traktrain.com/{}", "name": "Traktrain"},
            {"url": "https://t.me/{}", "name": "Telegram"},
            {"url": "https://tellonym.me/{}", "name": "Tellonym"},
            {"url": "https://tenor.com/users/{}", "name": "Tenor"},
            {"url": "https://themeforest.net/user/{}", "name": "ThemeForest"},
            {"url": "https://www.tradingview.com/u/{}", "name": "TradingView"},
            {"url": "https://www.trakt.tv/users/{}", "name": "Trakt.tv"},
            {"url": "https://trashbox.ru/users/{}", "name": "Trashbox.ru"},
            {"url": "https://traewelling.de/@{}", "name": "Traewelling"},
            {"url": "https://trello.com/{}", "name": "Trello"},
            {"url": "https://trello.com/1/Members/{}", "name": "Trello Members API"},
            {"url": "https://tryhackme.com/p/{}", "name": "TryHackMe Profile"},
            {"url": "https://tryhackme.com/api/user/exist/{}", "name": "TryHackMe API"},
            {"url": "https://tuna.voicemod.net/user/{}", "name": "Voicemod Tuna"},
            {"url": "https://tweakers.net/gallery/{}", "name": "Tweakers.net"},
            {"url": "https://nitter.net/{}", "name": "Nitter"},
            {"url": "https://data.typeracer.com/pit/profile?user={}", "name": "TypeRacer"},
            {"url": "https://ultimate-guitar.com/u/{}", "name": "Ultimate Guitar"},
            {"url": "https://unsplash.com/@{}", "name": "Unsplash"},
            {"url": "https://vk.com/{}", "name": "VK"},
            {"url": "https://www.quora.com/profile/{}", "name": "Quora"},
            {"url": "https://truthsocial.com/@{}", "name": "Truth Social"},
            {"url": "https://apclips.com/user/{}", "name": "APClips"},
            {"url": "https://admireme.vip/{}", "name": "AdmireMe.VIP"},
            {"url": "https://www.allthingsworn.com/profile/{}", "name": "All Things Worn"},
            {"url": "https://pt.bongacams.com/profile/{}", "name": "BongaCams"},
            {"url": "https://chaturbate.com/{}", "name": "Chaturbate"},
            {"url": "https://www.erome.com/a/{}", "name": "Erome"},
            {"url": "https://www.forumophilia.com/profile.php?mode=viewprofile&u={}", "name": "Forumophilia"},
            {"url": "https://www.heavy-r.com/user/{}", "name": "Heavy-R"},
            {"url": "https://www.imagefap.com/profile/{}", "name": "ImageFap"},
            {"url": "https://pussy.com/u/{}", "name": "Pussy.com"},
            {"url": "https://pocketstars.com/{}", "name": "PocketStars"},
            {"url": "https://pornhub.com/users/{}", "name": "Pornhub"},
            {"url": "https://www.redtube.com/users/{}", "name": "Redtube"},
            {"url": "https://www.rockettube.com/{}", "name": "RocketTube"},
            {"url": "https://royalcams.com/profile/{}", "name": "RoyalCams"},
            {"url": "https://www.tnaflix.com/profile/{}", "name": "TNAFlix"},
            # Added 13 more websites to reach 300
            {"url": "https://www.fandom.com/f/{}", "name": "Fandom Community"},
            {"url": "https://www.gamespot.com/profile/{}", "name": "GameSpot"},
            {"url": "https://www.ign.com/boards/members/{}", "name": "IGN Boards"},
            {"url": "https://www.nexusmods.com/users/{}", "name": "Nexus Mods"},
            {"url": "https://www.moddb.com/members/{}", "name": "ModDB"},
            {"url": "https://www.indiedb.com/members/{}", "name": "IndieDB"},
            {"url": "https://www.gog.com/u/{}", "name": "GOG.com"},
            {"url": "https://www.origin.com/usa/en-us/profile/user/{}", "name": "Origin"},
            {"url": "https://www.ubisoft.com/en-us/profile/{}", "name": "Ubisoft"},
            {"url": "https://www.battlenet.com/profile/{}", "name": "Battle.net"},
            {"url": "https://www.epicgames.com/account/profile/user/{}", "name": "Epic Games (Alt)"},
            {"url": "https://www.xbox.com/en-us/profile/{}", "name": "Xbox"},
            {"url": "https://www.playstation.com/en-us/my-playstation/profile/{}", "name": "PlayStation Network"},
        ][:300] # Limit to 300 websites

        self.username_progress_bar.setRange(0, len(temp_social_media_list_for_progress))
        self._start_worker("Username Tracking", self._check_username, self.username_input_field, self.username_track_button, self.username_result_table, self.username_status_label, username)

    def _update_username_progress(self, task_name, current_progress, total_progress):
        if task_name == "Username Tracking":
            self.username_progress_bar.setValue(current_progress)
            self.username_status_label.setText(f"Checking {current_progress}/{total_progress} sites...")
            self.username_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")

    def _display_username_results(self, username_data, table_widget, status_label):
        table_widget.setRowCount(0)
        if isinstance(username_data, dict):
            found_users = {k: v for k, v in username_data.items() if "not found" not in str(v).lower()}
            not_found_users = {k: v for k, v in username_data.items() if "not found" in str(v).lower()}

            sorted_found_keys = sorted(found_users.keys())
            sorted_not_found_keys = sorted(not_found_users.keys())

            table_widget.setRowCount(len(sorted_found_keys) + len(sorted_not_found_keys) + (2 if found_users else 0) + (2 if not_found_users else 0))
            row = 0

            if found_users:
                table_widget.insertRow(row)
                header_item = QTableWidgetItem(f"--- USERNAME FOUND ---")
                header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                header_item.setBackground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.Highlight))
                header_item.setForeground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.HighlightedText))
                table_widget.setSpan(row, 0, 1, 2)
                table_widget.setItem(row, 0, header_item)
                row += 1

                for key in sorted_found_keys:
                    value = found_users[key]
                    table_widget.setItem(row, 0, QTableWidgetItem(str(key)))
                    table_widget.setItem(row, 1, QTableWidgetItem(str(value)))
                    table_item_key = table_widget.item(row, 0)
                    table_item_value = table_widget.item(row, 1)
                    if table_item_key: table_item_key.setForeground(QColor(COLOR_TEXT_LIGHT))
                    if table_item_value: table_item_value.setForeground(QColor(COLOR_TEXT_LIGHT))
                    row += 1
                
                table_widget.insertRow(row)
                table_widget.setSpan(row, 0, 1, 2)
                table_widget.setItem(row, 0, QTableWidgetItem(""))
                row += 1

            if not_found_users:
                table_widget.insertRow(row)
                header_item = QTableWidgetItem(f"--- USERNAME NOT FOUND ---")
                header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                header_item.setBackground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.Highlight))
                header_item.setForeground(QApplication.palette().brush(QApplication.palette().ColorGroup.Active, QApplication.palette().ColorRole.HighlightedText))
                table_widget.setSpan(row, 0, 1, 2)
                table_widget.setItem(row, 0, header_item)
                row += 1

                for key in sorted_not_found_keys:
                    value = not_found_users[key]
                    table_widget.setItem(row, 0, QTableWidgetItem(str(key)))
                    table_widget.setItem(row, 1, QTableWidgetItem(str(value)))
                    table_item_key = table_widget.item(row, 0)
                    table_item_value = table_widget.item(row, 1)
                    if table_item_key: table_item_key.setForeground(QColor(COLOR_TEXT_LIGHT))
                    if table_item_value: table_item_value.setForeground(QColor(COLOR_TEXT_LIGHT))
                    row += 1
        else:
            table_widget.setRowCount(1)
            table_widget.setItem(0, 0, QTableWidgetItem("Error"))
            table_widget.setItem(0, 1, QTableWidgetItem(str(username_data)))
            status_label.setText("Error displaying username results.")
            status_label.setStyleSheet(f"color: {COLOR_ERROR};")
        table_widget.resizeColumnsToContents()

    def _on_get_copy_ip_clicked(self):
        if not self.ip_retrieved:
            self.show_ip_status_label.setText("Fetching IP...")
            self.show_ip_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
            self.ip_display_label.setText("Fetching IP...")
            self.ip_display_label.setStyleSheet(f"font-size: 20px; color: {COLOR_TEXT_DARK};")
            self.get_my_ip_button.setEnabled(False)
            self._start_worker("Your IP", self._get_your_ip_data_direct, None, self.get_my_ip_button, None, self.show_ip_status_label)
        else:
            self._copy_ip_to_clipboard()

    def _copy_ip_to_clipboard(self):
        ip_text = self.ip_display_label.text()
        try:
            start_index = ip_text.find(";'>") + 3
            end_index = ip_text.find("</span>")
            ip_address = ip_text[start_index:end_index]
            QApplication.clipboard().setText(ip_address)
            self.get_my_ip_button.setText("Success!")
            self.get_my_ip_button.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; background-color: {COLOR_SECONDARY};")
            self.get_my_ip_button.setEnabled(False)
            QTimer.singleShot(1500, self._reset_ip_button)
        except Exception as e:
            self.show_ip_status_label.setText(f"Error copying IP: {e}")
            self.show_ip_status_label.setStyleSheet(f"color: {COLOR_ERROR};")
            self.get_my_ip_button.setEnabled(True)
            self.ip_retrieved = False
            self.get_my_ip_button.setText("Get My IP")
            self.get_my_ip_button.setStyleSheet(f"background-color: {COLOR_SECONDARY}; color: {COLOR_TEXT_LIGHT};")

    def _reset_ip_button(self):
        self.ip_retrieved = False
        self.get_my_ip_button.setText("Get My IP")
        self.get_my_ip_button.setEnabled(True)
        self.get_my_ip_button.setStyleSheet(f"background-color: {COLOR_SECONDARY}; color: {COLOR_TEXT_LIGHT};")
        self.ip_display_label.setText("Click 'Get My IP' to see your public IP address.")
        self.ip_display_label.setStyleSheet(f"font-size: 20px; color: {COLOR_TEXT_DARK};")
        self.show_ip_status_label.setText("Ready.")
        self.show_ip_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")

    def _get_your_ip_data_direct(self):
        try:
            response = requests.get('https://api.ipify.org/', timeout=5)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get direct IP: {e}")

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #1a1a2e;
                color: #e0e0e0;
                font-family: "Inter", sans-serif;
            }}
            QWidget {{
                background-color: #1a1a2e;
                color: #e0e0e0;
            }}
            QLabel {{
                color: #e0e0e0;
            }}
            QLabel#ascii_art_label {{
                color: {COLOR_ACCENT};
            }}

            #navFrame {{
                background-color: {COLOR_PRIMARY};
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
            }}

            #logoLabel {{
                color: {COLOR_TEXT_LIGHT};
                font-size: 28px;
                font-weight: bold;
                padding-bottom: 15px;
                border-bottom: 1px solid {COLOR_GREY_MEDIUM};
                background-color: transparent;
            }}

            #navList {{
                background-color: {COLOR_PRIMARY};
                border: none;
                outline: none;
                padding: 0;
            }}

            #navList::item {{
                padding: 15px 10px;
                color: {COLOR_TEXT_DARK};
                font-size: 16px;
                border-radius: 5px;
                margin-bottom: 5px;
                background-color: {COLOR_PRIMARY};
            }}

            #navList::item:hover {{
                background-color: {COLOR_PRIMARY};
                color: {COLOR_TEXT_DARK};
            }}

            #navList::item:selected {{
                background-color: {COLOR_SECONDARY};
                font-weight: bold;
                color: {COLOR_TEXT_LIGHT};
                border-left: 5px solid {COLOR_ACCENT};
                padding-left: 5px;
            }}

            #contentFrame {{
                background-color: #1a1a2e;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }}

            #widgetTitle {{
                font-size: 8px;
                font-weight: bold;
                color: {COLOR_ACCENT};
                margin-bottom: 20px;
            }}

            #inputField {{
                padding: 12px;
                border: 1px solid #4a4a5e;
                border-radius: 8px;
                font-size: 16px;
                background-color: #2a2a3e;
                color: #e0e0e0;
            }}

            #inputField:focus {{
                border: 2px solid {COLOR_ACCENT};
            }}

            QPushButton {{
                background-color: {COLOR_SECONDARY};
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #175bb8;
            }}
            QPushButton:pressed {{
                background-color: #114185;
            }}
            QPushButton:disabled {{
                background-color: #3b3b4a;
                color: #888888;
            }}

            #resultTable {{
                border: 1px solid #4a4a5e;
                border-radius: 10px;
                background-color: #2a2a3e;
                selection-background-color: {COLOR_SECONDARY};
                gridline-color: #4a4a5e;
                color: {COLOR_TEXT_LIGHT}; /* Changed default text color to white */
            }}

            #resultTable::item {{
                padding: 8px;
                color: {COLOR_TEXT_LIGHT}; /* Explicitly set item text color to white */
            }}

            #resultTable::item:selected {{
                color: #ffffff;
            }}

            #resultTable QHeaderView::section {{
                background-color: #3a3a4e;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #4a4a5e;
                font-weight: bold;
            }}

            #statusLabel {{
                font-size: 14px;
                color: {COLOR_ACCENT};
                margin-top: 10px;
            }}

            #ipDisplayLabel {{
                font-size: 20px;
                font-weight: bold;
                color: {COLOR_TEXT_LIGHT};
                padding: 20px;
                background-color: {COLOR_GREY_MEDIUM};
                border-radius: 8px;
                margin-top: 20px;
                margin-bottom: 20px;
            }}

            #progressBar {{
                height: 20px;
                text-align: center;
                border: 1px solid {COLOR_SECONDARY};
                border-radius: 10px;
                background-color: {COLOR_GREY_MEDIUM};
            }}

            #progressBar::chunk {{
                background-color: {COLOR_ACCENT};
                border-radius: 8px;
            }}

            QCheckBox {{
                color: #e0e0e0;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid {COLOR_SECONDARY};
                background-color: #2a2a3e;
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLOR_SECONDARY};
                border: 2px solid {COLOR_SECONDARY};
            }}
            QTableWidget QScrollBar:vertical {{
                border: none;
                background: #2a2a3e;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QTableWidget QScrollBar::handle:vertical {{
                background: #5a5a6e;
                border-radius: 5px;
                min-height: 20px;
            }}
            QTableWidget QScrollBar::add-line:vertical, QTableWidget QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QTableWidget QScrollBar::add-page:vertical, QTableWidget QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

    def _change_page(self, index):
        if index == 5:
            self.close()
        else:
            self.stacked_widget.setCurrentIndex(index)
            if index == 0:
                self._reset_ip_button()
            elif index == 1:
                self.ip_status_label.setText("Ready.")
                self.ip_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
                self.ip_input_field.clear()
                self.ip_result_table.setRowCount(0)
            elif index == 2:
                self.phone_status_label.setText("Ready.")
                self.phone_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
                self.phone_input_field.clear()
                self.phone_result_table.setRowCount(0)
            elif index == 3:
                self.username_status_label.setText("Ready.")
                self.username_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
                self.username_input_field.clear()
                self.username_result_table.setRowCount(0)
                self.username_progress_bar.hide()
            elif index == 4:
                self.wifi_status_label.setText("Ready to scan. Please agree to terms.")
                self.wifi_status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
                self.wifi_terms_checkbox.setChecked(False)
                self.wifi_scan_button.setEnabled(False)
                self.wifi_terms_checkbox.setEnabled(True)
                self.wifi_result_table.setRowCount(0)

    def _start_worker(self, task_name, func, input_widget, button_widget, table_widget, status_label, *args, **kwargs):
        # Create a new thread and worker for each task to prevent RuntimeError
        self._current_worker_thread = WorkerThread(task_name, func, *args, **kwargs)
        
        status_label.setText(f"Starting {task_name}...")
        status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        button_widget.setEnabled(False)
        if input_widget:
            input_widget.setEnabled(True)
        if table_widget:
            table_widget.setRowCount(0)

        if task_name == "Username Tracking":
            self.username_progress_bar.show()
            self.username_progress_bar.setValue(0)
            self._current_worker_thread.progress_updated.connect(self._update_username_progress)

        self._current_worker_thread.finished.connect(
            lambda tn, res: self._on_worker_finished(tn, res, input_widget, button_widget, table_widget, status_label)
        )
        self._current_worker_thread.error.connect(
            lambda tn, err: self._on_worker_error(tn, err, input_widget, button_widget, status_label)
        )
        
        # Connect finished signal to clean up thread references
        self._current_worker_thread.finished.connect(self._current_worker_thread.quit)
        self._current_worker_thread.finished.connect(self._current_worker_thread.deleteLater)
        self._current_worker_thread.finished.connect(self._clear_worker_thread_references)

        self._current_worker_thread.start()

    def _clear_worker_thread_references(self):
        self._current_worker_thread = None

    def _display_your_ip_results(self, ip_address, status_label):
        if ip_address:
            self.ip_display_label.setText(f"<span style='color: {COLOR_ACCENT};'>{ip_address}</span>")
            self.ip_display_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLOR_TEXT_LIGHT}; padding: 20px; background-color: {COLOR_GREY_MEDIUM}; border-radius: 8px; margin-top: 20px; margin-bottom: 20px;")
            self.get_my_ip_button.setText("Copy IP")
            self.get_my_ip_button.setEnabled(True)
            self.ip_retrieved = True
            status_label.setText("Your IP address retrieved. Click 'Copy IP' to copy it.")
            status_label.setStyleSheet(f"color: {COLOR_ACCENT};")
        else:
            self.ip_display_label.setText("Could not retrieve your public IP address.")
            self.ip_display_label.setStyleSheet(f"font-size: 20px; color: {COLOR_ERROR};")
            self.get_my_ip_button.setText("Get My IP")
            self.get_my_ip_button.setEnabled(True)
            self.ip_retrieved = False
            status_label.setText("Failed to retrieve IP.")
            status_label.setStyleSheet(f"color: {COLOR_ERROR};")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Inter", 12))
    window = GhostCore()
    window.show()
    sys.exit(app.exec())
