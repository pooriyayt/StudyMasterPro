# Author: Pouriya Parniyan
# website: pouriyaparniyan.ir
# Github: github.com/pooriyayt

import sys
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
import os

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog,
    QSpinBox, QFileDialog, QDialog, QDialogButtonBox, QFormLayout, QComboBox,
    QTextEdit, QGroupBox, QTableWidget, QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor, QPixmap
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DB_FILENAME = "study.db"


try:
    font_path = resource_path('font/Vazir.ttf')  
    if os.path.exists(font_path):
        prop = fm.FontProperties(fname=font_path)
    else:
        prop = fm.FontProperties(family="Tahoma")
except:
    
    prop = fm.FontProperties(family="Tahoma")


def persian_to_fingilish(text):
    mapping = {
        'ا': 'a', 'آ': 'a', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's',
        'ج': 'j', 'چ': 'ch', 'ح': 'h', 'خ': 'kh',
        'د': 'd', 'ذ': 'z', 'ر': 'r', 'ز': 'z', 'ژ': 'zh',
        'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z',
        'ع': '', 'غ': 'gh', 'ف': 'f', 'ق': 'gh',
        'ک': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n',
        'و': 'o',
        'ه': 'h', 'ئ': 'i', 'ء': '', ' ': ' ',
    }
    result = ''
    words = text.split(' ')
    for word in words:
        transliterated = ''
        for i, ch in enumerate(word):
            if ch == 'ی':
                if i == 0:
                    transliterated += 'y'
                else:
                    transliterated += 'i'
            elif ch == 'و':
                if i > 0 and word[i - 1] in ['ا', 'آ', 'و', 'ی']:
                    transliterated += 'v'
                else:
                    transliterated += 'o'
            else:
                transliterated += mapping.get(ch, ch)
        result += transliterated + ' '
    return result.strip()


def gregorian_to_jalali(gy, gm, gd):
    if gy > 1600:
        gy -= 1600
        jy = 979
    else:
        gy -= 621
        jy = 0
    gy2 = gm > 2 and gy + 1 or gy
    days = 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 - 80 + gd + (31 * (gm - 1) if gm <= 7 else 30 * (gm - 1) + 5)
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    jm = 1 + days // 31 if days < 186 else 7 + (days - 186) // 30
    jd = 1 + days % 31
    return jy, jm, jd

def jalali_to_gregorian(jy, jm, jd):
    
    if jm < 1 or jm > 12:
        raise ValueError(f"Invalid Jalali month: {jm}. Must be between 1 and 12.")

    jy += 1595
    days = -355668 + (365 * jy) + (jy // 33 * 8) + ((jy % 33 + 3) // 4) + jd
    if jm < 7:
        days += (jm - 1) * 31
    else:
        days += (jm - 7) * 30 + 186

    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        gy += 100 * ((days - 1) // 36524)
        days = (days - 1) % 36524
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1

    
    gm_d = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gm = 1
    for m in range(1, 13):
        if m < len(gm_d) and gd <= gm_d[m]:
            gm = m
            break

    gd -= gm_d[gm - 1] if gm > 0 else 0
    return gy, gm, gd

def is_jalali_leap(jy):
    return jy % 33 in [1, 5, 9, 13, 17, 22, 26, 30]


def create_app_icon():
    """Load custom icon or create a default one"""
    
    icon_paths = [
        resource_path('icon.png'),
        resource_path('icon.ico'),
        resource_path('assets/icon.png'),
        resource_path('images/icon.png'),
        'icon.png',  
        'icon.ico'
    ]
    
    for icon_path in icon_paths:
        try:
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    return icon
        except:
            pass
    
    
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    
    
    painter.setBrush(QBrush(QColor(13, 110, 253)))  
    painter.setPen(QPen(QColor(10, 88, 202), 2))
    painter.drawRoundedRect(10, 8, 44, 48, 3, 3)
    
    
    painter.setBrush(QBrush(QColor(255, 255, 255)))
    painter.setPen(QPen(QColor(200, 200, 200), 1))
    painter.drawRect(14, 12, 36, 40)
    
    
    painter.setPen(QPen(QColor(13, 110, 253), 1))
    for i in range(4):
        y = 20 + i * 8
        painter.drawLine(18, y, 46, y)
    
    
    painter.setBrush(QBrush(QColor(220, 53, 69)))  
    painter.setPen(Qt.NoPen)
    points = [
        (32, 8),
        (28, 8),
        (28, 20),
        (30, 18),
        (32, 20)
    ]
    from PyQt5.QtCore import QPoint
    from PyQt5.QtGui import QPolygon
    polygon = QPolygon([QPoint(x, y) for x, y in points])
    painter.drawPolygon(polygon)
    
    painter.end()
    
    return QIcon(pixmap)


class DB:
    def __init__(self, filename=DB_FILENAME):
        self.filename = filename
        self._create_tables()

    @contextmanager
    def _get_cursor(self):
        conn = sqlite3.connect(self.filename)
        try:
            yield conn.cursor()
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _create_tables(self):
        with self._get_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    target_minutes INTEGER DEFAULT 0,
                    total_done_minutes INTEGER DEFAULT 0
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY,
                    subject_id INTEGER,
                    minutes REAL,
                    ts TEXT,
                    FOREIGN KEY(subject_id) REFERENCES subjects(id)
                )
            """)

    def add_subject(self, name, target_minutes=0):
        with self._get_cursor() as cur:
            cur.execute("INSERT OR IGNORE INTO subjects (name, target_minutes) VALUES (?, ?)", (name, target_minutes))
            return cur.lastrowid

    def delete_subject(self, subj_id):
        with self._get_cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE subject_id=?", (subj_id,))
            cur.execute("DELETE FROM subjects WHERE id=?", (subj_id,))

    def list_subjects(self):
        with self._get_cursor() as cur:
            cur.execute("SELECT id, name, target_minutes, total_done_minutes FROM subjects ORDER BY id")
            return cur.fetchall()

    def update_target(self, subj_id, minutes):
        with self._get_cursor() as cur:
            cur.execute("UPDATE subjects SET target_minutes=? WHERE id=?", (minutes, subj_id))

    def add_session(self, subj_id, minutes):
        with self._get_cursor() as cur:
            ts = datetime.now().isoformat()
            cur.execute("INSERT INTO sessions (subject_id, minutes, ts) VALUES (?, ?, ?)", (subj_id, minutes, ts))
            cur.execute("UPDATE subjects SET total_done_minutes = total_done_minutes + ? WHERE id=?", (minutes, subj_id))

    def get_sessions_for_subject(self, subj_id):
        with self._get_cursor() as cur:
            cur.execute("SELECT minutes, ts FROM sessions WHERE subject_id=? ORDER BY ts", (subj_id,))
            return cur.fetchall()

    def get_sessions_for_day(self, date_str):
        start = f"{date_str}T00:00:00"
        end = f"{date_str}T23:59:59"
        with self._get_cursor() as cur:
            cur.execute("""
                SELECT subjects.name, sessions.minutes, sessions.ts
                FROM sessions
                JOIN subjects ON sessions.subject_id = subjects.id
                WHERE sessions.ts BETWEEN ? AND ?
                ORDER BY sessions.ts
            """, (start, end))
            return cur.fetchall()

    def get_sessions_for_week(self, start_date, end_date):
        start = f"{start_date}T00:00:00"
        end = f"{end_date}T23:59:59"
        with self._get_cursor() as cur:
            cur.execute("""
                SELECT subjects.name, SUM(sessions.minutes) as total_minutes
                FROM sessions
                JOIN subjects ON sessions.subject_id = subjects.id
                WHERE sessions.ts BETWEEN ? AND ?
                GROUP BY subjects.name
                ORDER BY total_minutes DESC
            """, (start, end))
            return cur.fetchall()

    def get_sessions_for_month(self, j_year, j_month):
        start_g_y, start_g_m, start_g_d = jalali_to_gregorian(j_year, j_month, 1)
        days_in_month = 31 if j_month <= 6 else 30 if j_month <= 11 else 30 if is_jalali_leap(j_year) else 29
        end_g_y, end_g_m, end_g_d = jalali_to_gregorian(j_year, j_month, days_in_month)
        start = f"{start_g_y}-{start_g_m:02d}-{start_g_d:02d}T00:00:00"
        end = f"{end_g_y}-{end_g_m:02d}-{end_g_d:02d}T23:59:59"
        with self._get_cursor() as cur:
            cur.execute("""
                SELECT subjects.name, SUM(sessions.minutes) as total_minutes
                FROM sessions
                JOIN subjects ON sessions.subject_id = subjects.id
                WHERE sessions.ts BETWEEN ? AND ?
                GROUP BY subjects.name
                ORDER BY total_minutes DESC
            """, (start, end))
            return cur.fetchall()

    def get_study_days_for_j_month(self, j_year, j_month):
        study_days = set()
        with self._get_cursor() as cur:
            cur.execute("SELECT ts FROM sessions")
            for row in cur.fetchall():
                ts = row[0]
                g_date = datetime.fromisoformat(ts).date()
                jy, jm, jd = gregorian_to_jalali(g_date.year, g_date.month, g_date.day)
                if jy == j_year and jm == j_month:
                    study_days.add(jd)
        return study_days

    def close(self):
        pass


class ProgressChart(FigureCanvas):
    def __init__(self, parent=None, theme=None):
        fig = Figure(figsize=(6, 5), tight_layout=True)
        super().__init__(fig)
        self.axes = fig.add_subplot(111)
        self.setParent(parent)
        self.theme = theme or {
            'background': '#FFFFFF',
            'text': '#000000',
            'accent': '#0D6EFD',
        }
        self.axes.set_title("Subject Progress", fontproperties=prop)
        self.update_colors()

    def update_colors(self):
        self.axes.set_facecolor(self.theme['background'])
        self.axes.title.set_color(self.theme['text'])
        self.axes.xaxis.label.set_color(self.theme['text'])
        self.axes.yaxis.label.set_color(self.theme['text'])
        self.axes.tick_params(axis='x', colors=self.theme['text'])
        self.axes.tick_params(axis='y', colors=self.theme['text'])
        self.figure.set_facecolor(self.theme['background'])

    def plot(self, subjects):
        self.axes.clear()
        self.update_colors()
        names = [s[1] for s in subjects]
        names_fingilish = [persian_to_fingilish(name) for name in names]
        dones = [s[3] for s in subjects]
        targets = [s[2] if s[2] > 0 else 1 for s in subjects]
        percents = [min(100, int(d/t*100)) for d,t in zip(dones, targets)]

        colors = []
        base_color = self.theme['accent']
        num_colors = len(percents)

        if num_colors > 0:
            for i in range(num_colors):
                opacity = 0.3 + (0.7 * i / num_colors)
                if '#' in base_color:
                    r = int(base_color[1:3], 16)
                    g = int(base_color[3:5], 16)
                    b = int(base_color[5:7], 16)
                    colors.append((r/255, g/255, b/255, opacity))
                else:
                    colors = plt.get_cmap('Pastel1')(np.linspace(0, 1, num_colors))

        self.axes.pie(
            percents,
            labels=names_fingilish,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'color': self.theme['text']}
        )
        self.axes.axis('equal')
        self.draw()


class StatisticsWindow(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Statistics")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowIcon(create_app_icon())
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Subject", "Date", "Duration (minutes)"])
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)
        self._load_data()

    def _load_data(self):
        subjects = self.db.list_subjects()
        for subject in subjects:
            sessions = self.db.get_sessions_for_subject(subject[0])
            for session in sessions:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(subject[1]))
                self.table.setItem(row, 1, QTableWidgetItem(session[1]))
                self.table.setItem(row, 2, QTableWidgetItem(str(session[0])))


class CalendarWindow(QDialog):
    def __init__(self, db, theme, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = theme
        self.setWindowTitle("Monthly Study Calendar")
        self.setGeometry(100, 100, 1000, 700)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowIcon(create_app_icon())
        self.setStyleSheet(self.global_styles())
        self._build_ui()

    def global_styles(self):
        return f"""
        QWidget {{ background-color: {self.theme['background']}; font-family: Tahoma; color: {self.theme['text']}; }}
        QLabel {{ color: {self.theme['text']}; }}
        QGroupBox {{ border: 1px solid {self.theme['accent']}; border-radius: 5px; margin-top: 10px; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; color: {self.theme['accent']}; }}
        QTextEdit {{ background: {self.theme['table_background']}; color: {self.theme['text']}; border: 1px solid {self.theme['table_header']}; }}
        QTableWidget {{ background: {self.theme['table_background']}; color: {self.theme['text']}; }}
        """

    def _build_ui(self):
        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        self.calendar = CustomJalaliCalendar(self.db, self.theme, self)
        self.calendar.clicked.connect(self.show_day_details)
        left_layout.addWidget(self.calendar)
        main_layout.addLayout(left_layout, stretch=2)

        right_layout = QVBoxLayout()

        day_group = QGroupBox("Day Details")
        day_layout = QVBoxLayout()
        self.day_details = QTextEdit()
        self.day_details.setReadOnly(True)
        day_layout.addWidget(self.day_details)
        day_group.setLayout(day_layout)
        right_layout.addWidget(day_group)

        summary_group = QGroupBox("Summaries")
        summary_layout = QVBoxLayout()
        self.week_summary = QTextEdit()
        self.week_summary.setReadOnly(True)
        summary_layout.addWidget(QLabel("Weekly Summary:"))
        summary_layout.addWidget(self.week_summary)
        self.month_summary = QTextEdit()
        self.month_summary.setReadOnly(True)
        summary_layout.addWidget(QLabel("Monthly Summary:"))
        summary_layout.addWidget(self.month_summary)
        summary_group.setLayout(summary_layout)
        right_layout.addWidget(summary_group)

        main_layout.addLayout(right_layout, stretch=1)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        right_layout.addWidget(close_btn)

        self.setLayout(main_layout)
        self.update_calendar()

    def update_calendar(self):
        self.calendar.update_calendar()
        self.show_month_summary(self.calendar.current_jy, self.calendar.current_jm)
        date = self.calendar.selected_date
        if date:
            self.show_week_summary(date)
            self.show_day_details(date)

    def show_day_details(self, date):
        jy, jm, jd = gregorian_to_jalali(date.year(), date.month(), date.day())
        j_date_str = f"{jy}/{jm:02d}/{jd:02d}"
        date_str = date.toString("yyyy-MM-dd")
        sessions = self.db.get_sessions_for_day(date_str)
        total_seconds = sum(s[1] * 60 for s in sessions)
        total_minutes = int(total_seconds // 60)
        remaining_seconds = int(total_seconds % 60)
        details = f"Date: {j_date_str} (Gregorian: {date_str})\nTotal Study Time: {total_minutes} hours {remaining_seconds} minutes\n\nSessions:\n"
        for name, minutes, ts in sessions:
            mins = int(minutes // 1)
            secs = int((minutes % 1) * 60)
            details += f"- {name}: {mins} minutes {secs} seconds at {ts[11:16]}\n"
        self.day_details.setText(details)
        self.show_week_summary(date)
        self.calendar.selected_date = date

    def show_week_summary(self, date):
        weekday = date.dayOfWeek()
        offset = (weekday - 6) % 7
        start_date = date.addDays(-offset)
        end_date = start_date.addDays(6)
        sessions = self.db.get_sessions_for_week(start_date.toString("yyyy-MM-dd"), end_date.toString("yyyy-MM-dd"))
        total_seconds = sum(s[1] * 60 for s in sessions)
        total_minutes = int(total_seconds // 60)
        remaining_seconds = int(total_seconds % 60)
        s_jy, s_jm, s_jd = gregorian_to_jalali(start_date.year(), start_date.month(), start_date.day())
        e_jy, e_jm, e_jd = gregorian_to_jalali(end_date.year(), end_date.month(), end_date.day())
        j_start = f"{s_jy}/{s_jm:02d}/{s_jd:02d}"
        j_end = f"{e_jy}/{e_jm:02d}/{e_jd:02d}"
        summary = f"Week: {j_start} to {j_end}\nTotal Study Time: {total_minutes} hours {remaining_seconds} minutes\n\nSubjects:\n"
        if sessions:
            most_studied = sessions[0][0]
            summary += f"Most Studied: {most_studied}\n"
            for name, minutes in sessions:
                mins = int(minutes // 1)
                secs = int((minutes % 1) * 60)
                summary += f"- {name}: {mins} minutes {secs} seconds\n"
        else:
            summary += "No study sessions this week."
        self.week_summary.setText(summary)

    def show_month_summary(self, j_year, j_month):
        try:
            sessions = self.db.get_sessions_for_month(j_year, j_month)
            total_seconds = sum(s[1] * 60 for s in sessions)
            total_minutes = int(total_seconds // 60)
            remaining_seconds = int(total_seconds % 60)
            summary = f"Month: {j_year}/{j_month:02d}\nTotal Study Time: {total_minutes} hours {remaining_seconds} minutes\n\nSubjects:\n"
            if sessions:
                most_studied = sessions[0][0]
                summary += f"Most Studied: {most_studied}\n"
                for name, minutes in sessions:
                    mins = int(minutes // 1)
                    secs = int((minutes % 1) * 60)
                    summary += f"- {name}: {mins} minutes {secs} seconds\n"
            else:
                summary += "No study sessions this month."
            self.month_summary.setText(summary)
        except Exception as e:
            self.month_summary.setText(f"Error loading summary: {str(e)}")

class CustomJalaliCalendar(QWidget):
    clicked = pyqtSignal(QDate)

    def __init__(self, db, theme, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme = theme
        self.study_days = set()
        now_g = datetime.now()
        self.current_jy, self.current_jm, self.current_jd = gregorian_to_jalali(now_g.year, now_g.month, now_g.day)
        self.selected_date = QDate(now_g.year, now_g.month, now_g.day)
        self._build_ui()

    def _build_ui(self):
        self.layout = QVBoxLayout()

        header = QHBoxLayout()
        self.btn_prev = QPushButton("Previous Month")
        self.btn_prev.clicked.connect(self.prev_month)
        self.lbl_month = QLabel()
        self.btn_next = QPushButton("Next Month")
        self.btn_next.clicked.connect(self.next_month)
        header.addWidget(self.btn_prev)
        header.addWidget(self.lbl_month)
        header.addWidget(self.btn_next)
        self.layout.addLayout(header)

        self.table = QTableWidget(6, 7)
        self.table.setHorizontalHeaderLabels(['Shanbe', 'Yekshanbe', 'Doshanbe', 'Seshanbe', 'Chaharshanbe', 'Panjshanbe', 'Jome'])
        self.table.itemClicked.connect(self.on_day_clicked)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.table)

        self.setLayout(self.layout)

    def update_calendar(self):
        j_month_names = ['Farvardin', 'Ordibehesht', 'Khordad', 'Tir', 'Mordad', 'Shahrivar',
                        'Mehr', 'Aban', 'Azar', 'Dey', 'Bahman', 'Esfand']
        self.lbl_month.setText(f"{j_month_names[self.current_jm - 1]} {self.current_jy}")

        days_in_month = 31 if self.current_jm <= 6 else 30 if self.current_jm <= 11 else 30 if is_jalali_leap(self.current_jy) else 29
        g_y, g_m, g_d = jalali_to_gregorian(self.current_jy, self.current_jm, 1)
        first_date = QDate(g_y, g_m, g_d)
        weekday = first_date.dayOfWeek()
        col_start = (weekday - 6) % 7

        self.table.clearContents()
        day = 1
        row = 0
        col = col_start
        self.study_days = self.db.get_study_days_for_j_month(self.current_jy, self.current_jm)

        accent_color = QColor(self.theme['accent'])
        bg_color = QColor(self.theme['background'])
        non_study_color = QColor(
            min(255, bg_color.red() + 30),
            min(255, bg_color.green() + 30),
            min(255, bg_color.blue() + 30)
        )

        while day <= days_in_month:
            item = QTableWidgetItem(str(day))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if day in self.study_days:
                item.setBackground(accent_color)
            else:
                item.setBackground(non_study_color)
            self.table.setItem(row, col, item)
            col += 1
            if col == 7:
                col = 0
                row += 1
            day += 1

    def prev_month(self):
        try:
            self.current_jm -= 1
            if self.current_jm == 0:
                self.current_jm = 12
                self.current_jy -= 1
            if self.current_jy < 1:
                self.current_jy = 1
                self.current_jm = 1
                QMessageBox.warning(self, "Navigation Error", "Cannot navigate before year 1.")
                return
            self.update_calendar()
            self.parent().update_calendar()
        except Exception as e:
            QMessageBox.warning(self, "Navigation Error", f"Cannot navigate further back: {str(e)}")

    def next_month(self):
        try:
            self.current_jm += 1
            if self.current_jm == 13:
                self.current_jm = 1
                self.current_jy += 1
            current_year = datetime.now().year
            if self.current_jy > current_year + 10:
                self.current_jy = current_year + 10
                self.current_jm = 12
                QMessageBox.warning(self, "Navigation Error", "Cannot navigate more than 10 years into the future.")
                return
            self.update_calendar()
            self.parent().update_calendar()
        except Exception as e:
            QMessageBox.warning(self, "Navigation Error", f"Cannot navigate further forward: {str(e)}")

    def on_day_clicked(self, item):
        if item:
            jd = int(item.text())
            try:
                g_y, g_m, g_d = jalali_to_gregorian(self.current_jy, self.current_jm, jd)
                date = QDate(g_y, g_m, g_d)
                self.clicked.emit(date)
                self.selected_date = date
            except Exception as e:
                QMessageBox.warning(self, "Date Error", f"Cannot select this date: {str(e)}")


class StudyMaster(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DB()
        self.setWindowTitle("StudyMaster Pro")
        self.setWindowIcon(create_app_icon())
        self.setMinimumSize(900, 700)
        self.themes = {
            'light': {
                'background': '#F8F9FA',
                'text': '#212529',
                'accent': '#0D6EFD',
                'button': '#E9ECEF',
                'button_text': '#0D6EFD',
                'table_background': '#FFFFFF',
                'table_header': '#E9ECEF',
                'completed_background': '#E9F7FE',
                'delete_button': '#FF6B6B',
                'delete_button_text': '#FFFFFF',
            },
            'dark': {
                'background': '#212529',
                'text': '#F8F9FA',
                'accent': '#6C757D',
                'button': '#343A40',
                'button_text': '#ADB5BD',
                'table_background': '#343A40',
                'table_header': '#495057',
                'completed_background': '#2D3748',
                'delete_button': '#5C0000',
                'delete_button_text': '#FFEBEE',
            },
            'dark_green': {
                'background': '#1A3E2E',
                'text': '#F8F9FA',
                'accent': '#28A745',
                'button': '#2D5A3D',
                'button_text': '#28A745',
                'table_background': '#2D5A3D',
                'table_header': '#346A40',
                'completed_background': '#1F5D3D',
                'delete_button': '#8C0000',
                'delete_button_text': '#FFEBEE',
            },
            'light_green': {
                'background': '#E8F5E9',
                'text': '#2E7D32',
                'accent': '#4CAF50',
                'button': '#C8E6C9',
                'button_text': '#2E7D32',
                'table_background': '#E8F5E9',
                'table_header': '#A5D6A7',
                'completed_background': '#C8E6C9',
                'delete_button': '#C62828',
                'delete_button_text': '#FFFFFF',
            },
            'dark_blue': {
                'background': '#1A2E4A',
                'text': '#F8F9FA',
                'accent': '#0D6EFD',
                'button': '#2A4A6A',
                'button_text': '#0D6EFD',
                'table_background': '#2A4A6A',
                'table_header': '#3A5A7A',
                'completed_background': '#1E3A5F',
                'delete_button': '#8C0000',
                'delete_button_text': '#FFEBEE',
            },
            'light_blue': {
                'background': '#E3F2FD',
                'text': '#1976D2',
                'accent': '#2196F3',
                'button': '#BBDEFB',
                'button_text': '#1976D2',
                'table_background': '#E3F2FD',
                'table_header': '#90CAF9',
                'completed_background': '#BBDEFB',
                'delete_button': '#C62828',
                'delete_button_text': '#FFFFFF',
            },
            'dark_purple': {
                'background': '#2D1B4D',
                'text': '#F8F9FA',
                'accent': '#6F42C1',
                'button': '#3D2B5D',
                'button_text': '#6F42C1',
                'table_background': '#3D2B5D',
                'table_header': '#4D3B6D',
                'completed_background': '#2D1B4D',
                'delete_button': '#5C003C',
                'delete_button_text': '#FCE4EC',
            },
            'light_purple': {
                'background': '#F3E5F5',
                'text': '#7B1FA2',
                'accent': '#9C27B0',
                'button': '#E1BEE7',
                'button_text': '#7B1FA2',
                'table_background': '#F3E5F5',
                'table_header': '#BA68C8',
                'completed_background': '#E1BEE7',
                'delete_button': '#C62828',
                'delete_button_text': '#FFFFFF',
            },
            'dark_red': {
                'background': '#5C0000',
                'text': '#FFEBEE',
                'accent': '#FF8A80',
                'button': '#8C0000',
                'button_text': '#FFEBEE',
                'table_background': '#8C0000',
                'table_header': '#FF8A80',
                'completed_background': '#7B0000',
                'delete_button': '#FFCDD2',
                'delete_button_text': '#C62828',
            },
            'light_red': {
                'background': '#FFEBEE',
                'text': '#C62828',
                'accent': '#EF9A9A',
                'button': '#FFCDD2',
                'button_text': '#C62828',
                'table_background': '#FFEBEE',
                'table_header': '#FF8A80',
                'completed_background': '#FFCDD2',
                'delete_button': '#C62828',
                'delete_button_text': '#FFFFFF',
            },
            'dark_pink': {
                'background': '#4A003C',
                'text': '#FCE4EC',
                'accent': '#F06292',
                'button': '#7B0055',
                'button_text': '#FCE4EC',
                'table_background': '#7B0055',
                'table_header': '#F06292',
                'completed_background': '#5C003C',
                'delete_button': '#7B0055',
                'delete_button_text': '#FCE4EC',
            },
            'light_pink': {
                'background': '#FCE4EC',
                'text': '#C2185B',
                'accent': '#F8BBD9',
                'button': '#F48FB1',
                'button_text': '#C2185B',
                'table_background': '#FCE4EC',
                'table_header': '#F06292',
                'completed_background': '#F48FB1',
                'delete_button': '#C62828',
                'delete_button_text': '#FFFFFF',
            },
            'dark_rose': {
                'background': '#3D004A',
                'text': '#F3E5F5',
                'accent': '#BA68C8',
                'button': '#6A007B',
                'button_text': '#F3E5F5',
                'table_background': '#6A007B',
                'table_header': '#BA68C8',
                'completed_background': '#5D006A',
                'delete_button': '#6A007B',
                'delete_button_text': '#F3E5F5',
            },
            'light_rose': {
                'background': '#F3E5F5',
                'text': '#7B1FA2',
                'accent': '#E1BEE7',
                'button': '#CE93D8',
                'button_text': '#7B1FA2',
                'table_background': '#F3E5F5',
                'table_header': '#BA68C8',
                'completed_background': '#E1BEE7',
                'delete_button': '#C62828',
                'delete_button_text': '#FFFFFF',
            }
        }
        self.current_theme = 'light'
        self.setStyleSheet(self.global_styles())
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.pomodoro_seconds = 25 * 60
        self.remaining_seconds = 0
        self.timer_running = False
        self.current_subject_id = None
        self.session_accumulated_seconds = 0
        self._build_ui()
        self._load_subjects()
        self.update_chart()

    def global_styles(self):
        theme = self.themes[self.current_theme]
        return f"""
        QWidget {{ background-color: {theme['background']}; font-family: Tahoma; color: {theme['text']}; }}
        QLabel#title {{ font-size: 20px; font-weight:700; color:{theme['text']}; }}
        QPushButton {{ background-color: {theme['button']}; border-radius:10px; padding:8px 12px; color: {theme['button_text']}; }}
        QPushButton#primary {{ background-color: {theme['accent']}; color:white; border:none; }}
        QLineEdit {{ border:1px solid #e0e0e0; border-radius:10px; padding:8px; background:{theme['table_background']}; color: {theme['text']}; }}
        QTableWidget {{ background:{theme['table_background']}; border:1px solid #e6e6e6; border-radius:8px; color: {theme['text']}; }}
        QHeaderView::section {{ background:{theme['table_header']}; padding:6px; font-weight:600; color: {theme['text']}; }}
        QTableWidget#completedTable {{ background:{theme['completed_background']}; border:1px solid #e6e6e6; border-radius:8px; color: {theme['text']}; }}
        QPushButton.deleteButton {{ background-color: {theme['delete_button']}; color: {theme['delete_button_text']}; border-radius: 8px; padding: 4px 8px; }}
        QScrollArea {{ background: transparent; border: none; }}
        """

    def _build_ui(self):
        main_layout = QHBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()

        title = QLabel("StudyMaster Pro")
        title.setObjectName("title")
        left.addWidget(title)

        theme_row = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems([
            "Light", "Dark",
            "Light Green", "Dark Green",
            "Light Blue", "Dark Blue",
            "Light Purple", "Dark Purple",
            "Light Red", "Dark Red",
            "Light Pink", "Dark Pink",
            "Light Rose", "Dark Rose"
        ])
        self.theme_selector.currentIndexChanged.connect(self.change_theme)
        theme_row.addWidget(theme_label)
        theme_row.addWidget(self.theme_selector)
        left.addLayout(theme_row)

        add_row = QHBoxLayout()
        self.input_subject = QLineEdit()
        self.input_subject.setPlaceholderText("Add new subject (e.g., Math)")
        self.input_target = QSpinBox()
        self.input_target.setRange(0, 100000)
        self.input_target.setSuffix(" minutes target")
        self.input_target.setValue(5)
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self.add_subject_clicked)
        add_row.addWidget(self.input_subject)
        add_row.addWidget(self.input_target)
        add_row.addWidget(add_btn)
        left.addLayout(add_row)

        active_label = QLabel("Active Subjects")
        active_label.setStyleSheet("font-weight:700; margin-top: 10px;")
        left.addWidget(active_label)

        self.active_table = QTableWidget(0, 5)
        self.active_table.setObjectName("activeTable")
        self.active_table.setHorizontalHeaderLabels([
            "ID",
            "Subject",
            "Target (m)",
            "Completed (m)",
            "Actions"
        ])
        self.active_table.setColumnHidden(0, True)
        self.active_table.setSelectionBehavior(self.active_table.SelectRows)
        self.active_table.cellClicked.connect(lambda r, c: self.on_subject_selected(r, c, self.active_table))

        self.active_table.setMinimumHeight(200)
        self.active_table.setColumnWidth(1, 200)
        self.active_table.setColumnWidth(2, 100)
        self.active_table.setColumnWidth(3, 120)
        self.active_table.setColumnWidth(4, 90)
        self.active_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.active_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.active_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left.addWidget(self.active_table)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"margin: 10px 0; background: {self.themes[self.current_theme]['accent']};")
        left.addWidget(separator)

        self.btn_toggle_completed = QPushButton("Show Completed Subjects")
        self.btn_toggle_completed.setCheckable(True)
        self.btn_toggle_completed.clicked.connect(self.toggle_completed_table)
        left.addWidget(self.btn_toggle_completed)

        self.completed_label = QLabel("Completed Subjects")
        self.completed_label.setStyleSheet("font-weight:700; margin-top: 10px;")
        self.completed_label.hide()
        left.addWidget(self.completed_label)

        self.completed_table = QTableWidget(0, 5)
        self.completed_table.setObjectName("completedTable")
        self.completed_table.setHorizontalHeaderLabels([
            "ID",
            "Subject",
            "Target (m)",
            "Completed (m)",
            "Actions"
        ])
        self.completed_table.setColumnHidden(0, True)
        self.completed_table.setSelectionBehavior(self.completed_table.SelectRows)
        self.completed_table.cellClicked.connect(lambda r, c: self.on_subject_selected(r, c, self.completed_table))

        self.completed_table.setMinimumHeight(200)
        self.completed_table.setColumnWidth(1, 200)
        self.completed_table.setColumnWidth(2, 100)
        self.completed_table.setColumnWidth(3, 120)
        self.completed_table.setColumnWidth(4, 80)
        self.completed_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.completed_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.completed_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.completed_table.hide()

        left.addWidget(self.completed_table)

        timer_box = QVBoxLayout()
        timer_title = QLabel("⏳ Pomodoro Timer")
        timer_title.setStyleSheet("font-weight:700;")
        timer_box.addWidget(timer_title)
        self.lbl_timer = QLabel(self._format_time(self.pomodoro_seconds))
        self.lbl_timer.setAlignment(Qt.AlignCenter)
        self.lbl_timer.setStyleSheet("font-size:28px;font-weight:700;")
        timer_box.addWidget(self.lbl_timer)
        durations = QHBoxLayout()
        for m in (15, 25, 50):
            b = QPushButton(f"{m} minutes")
            b.clicked.connect(lambda checked, mm=m: self.set_duration(mm))
            durations.addWidget(b)
        timer_box.addLayout(durations)
        tbtns = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName("primary")
        self.btn_start.setIcon(QIcon.fromTheme("media-playback-start"))
        self.btn_start.clicked.connect(self.start_pause_timer)
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.btn_reset.clicked.connect(self.reset_timer)
        tbtns.addWidget(self.btn_start)
        tbtns.addWidget(self.btn_reset)
        timer_box.addLayout(tbtns)
        self.btn_mark_complete = QPushButton("Save Session")
        self.btn_mark_complete.setIcon(QIcon.fromTheme("document-save"))
        self.btn_mark_complete.clicked.connect(self.mark_session_complete)
        timer_box.addWidget(self.btn_mark_complete)
        left.addLayout(timer_box)

        stats_btn = QPushButton("View Statistics")
        stats_btn.setIcon(QIcon.fromTheme("document-properties"))
        stats_btn.clicked.connect(self.view_statistics)
        left.addWidget(stats_btn)

        calendar_btn = QPushButton("View Calendar")
        calendar_btn.setIcon(QIcon.fromTheme("view-calendar"))
        calendar_btn.clicked.connect(self.view_calendar)
        left.addWidget(calendar_btn)

        chart_container = QWidget()
        chart_layout = QVBoxLayout()
        self.chart = ProgressChart(chart_container, self.themes[self.current_theme])
        chart_layout.addWidget(self.chart, stretch=2)

        detail_title = QLabel("Selected Subject Details")
        detail_title.setStyleSheet("font-weight:700;")
        chart_layout.addWidget(detail_title)
        self.lbl_detail = QLabel("No subject selected")
        self.lbl_detail.setWordWrap(True)
        self.lbl_detail.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        chart_layout.addWidget(self.lbl_detail)
        btn_export = QPushButton("Export Sessions to CSV")
        btn_export.setIcon(QIcon.fromTheme("document-export"))
        btn_export.clicked.connect(self.export_csv)
        chart_layout.addWidget(btn_export, alignment=Qt.AlignLeft)
        chart_container.setLayout(chart_layout)

        main_layout.addLayout(left, stretch=3)
        main_layout.addWidget(chart_container, stretch=2)

        self.setLayout(main_layout)

    def toggle_completed_table(self, checked):
        if checked:
            self.completed_label.show()
            self.completed_table.show()
            self.btn_toggle_completed.setText("Hide Completed Subjects")
        else:
            self.completed_label.hide()
            self.completed_table.hide()
            self.btn_toggle_completed.setText("Show Completed Subjects")

    def resizeEvent(self, event):
        width = self.width()
        if width > 900:
            self.active_table.setColumnWidth(1, 220)
            self.completed_table.setColumnWidth(1, 220)
        else:
            self.active_table.setColumnWidth(1, 200)
            self.completed_table.setColumnWidth(1, 200)
        super().resizeEvent(event)

    def change_theme(self, index):
        themes = [
            "light", "dark",
            "light_green", "dark_green",
            "light_blue", "dark_blue",
            "light_purple", "dark_purple",
            "light_red", "dark_red",
            "light_pink", "dark_pink",
            "light_rose", "dark_rose"
        ]
        self.current_theme = themes[index]
        self.setStyleSheet(self.global_styles())
        self.chart.theme = self.themes[self.current_theme]
        self.chart.update_colors()
        self.update_chart()

    def add_subject_clicked(self):
        name = self.input_subject.text().strip()
        target = int(self.input_target.value())
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a subject name.")
            return
        self.db.add_subject(name, target)
        self.input_subject.clear()
        self._load_subjects()
        self.update_chart()

    def _load_subjects(self):
        self.subjects = self.db.list_subjects()
        self.active_table.setRowCount(0)
        self.completed_table.setRowCount(0)

        for row_idx, s in enumerate(self.subjects):
            subj_id, name, target, done = s
            table = self.completed_table if target > 0 and done >= target else self.active_table

            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(subj_id)))

            subject_item = QTableWidgetItem(name)
            subject_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, subject_item)

            target_item = QTableWidgetItem(f"{target}")
            target_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 2, target_item)

            completed_item = QTableWidgetItem(f"{done:.2f}")
            completed_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 3, completed_item)

            delete_btn = QPushButton("🗑️Delete")
            delete_btn.setObjectName("deleteButton")
            delete_btn.setFixedSize(85, 35)
            delete_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            delete_btn.clicked.connect(lambda _, sid=subj_id: self.delete_subject(sid))
            table.setCellWidget(row, 4, delete_btn)

    def on_subject_selected(self, r, c, table):
        if c == 4:
            return

        subj_id = int(table.item(r, 0).text())
        name = table.item(r, 1).text()
        target = int(float(table.item(r, 2).text()))
        done = float(table.item(r, 3).text())

        self.current_subject_id = subj_id
        text = f"Subject: {name}\nTarget: {target} minutes\nCompleted: {done:.2f} minutes"
        sessions = self.db.get_sessions_for_subject(subj_id)
        if sessions:
            text += f"\n\nLast sessions ({len(sessions)}):"
            for m, ts in sessions[-5:]:
                mins = int(m // 1)
                secs = int((m % 1) * 60)
                text += f"\n- {mins} minutes {secs} seconds on {ts[:16]}"
        self.lbl_detail.setText(text)

    def delete_subject(self, subj_id):
        name = None
        for r in range(self.active_table.rowCount()):
            if int(self.active_table.item(r, 0).text()) == subj_id:
                name = self.active_table.item(r, 1).text()
                break
        for r in range(self.completed_table.rowCount()):
            if int(self.completed_table.item(r, 0).text()) == subj_id:
                name = self.completed_table.item(r, 1).text()
                break

        if name is None:
            QMessageBox.warning(self, "Error", "Subject not found.")
            return

        ok = QMessageBox.question(self, "Delete", f"Are you sure you want to delete the subject '{name}' and all its sessions?")
        if ok == QMessageBox.Yes:
            self.db.delete_subject(subj_id)
            self._load_subjects()
            self.update_chart()
            self.lbl_detail.setText("No subject selected")
            self.current_subject_id = None
            QMessageBox.information(self, "Deleted", f"Subject '{name}' has been deleted.")

    def set_duration(self, minutes):
        self.pomodoro_seconds = minutes * 60
        self.remaining_seconds = self.pomodoro_seconds
        self.lbl_timer.setText(self._format_time(self.remaining_seconds))

    def start_pause_timer(self):
        if not self.timer_running:
            if self.current_subject_id is None:
                QMessageBox.information(self, "Select Subject", "Please select a subject from the list first.")
                return
            if self.remaining_seconds <= 0:
                self.remaining_seconds = self.pomodoro_seconds
                self.session_accumulated_seconds = 0
            self.timer.start()
            self.timer_running = True
            self.btn_start.setText("Pause")
        else:
            self.timer.stop()
            self.timer_running = False
            self.btn_start.setText("Start")

    def reset_timer(self):
        self.timer.stop()
        self.timer_running = False
        self.remaining_seconds = self.pomodoro_seconds
        self.session_accumulated_seconds = 0
        self.lbl_timer.setText(self._format_time(self.remaining_seconds))
        self.btn_start.setText("Start")

    def _tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.session_accumulated_seconds += 1
            self.lbl_timer.setText(self._format_time(self.remaining_seconds))
        else:
            self.timer.stop()
            self.timer_running = False
            self.btn_start.setText("Start")
            minutes = self.session_accumulated_seconds / 60
            if minutes <= 0:
                minutes = 0
            self._register_session(minutes)
            QMessageBox.information(self, "Time's Up", "⏰ Session time is up. Session saved.")
            self.remaining_seconds = self.pomodoro_seconds
            self.session_accumulated_seconds = 0
            self.lbl_timer.setText(self._format_time(self.remaining_seconds))

    def mark_session_complete(self):
        if self.current_subject_id is None:
            QMessageBox.information(self, "Selection", "Please select a subject.")
            return
        minutes = self.session_accumulated_seconds / 60
        if minutes <= 0:
            QMessageBox.information(self, "No Time", "No study time has been accumulated yet.")
            return
        self._register_session(minutes)
        QMessageBox.information(self, "Saved", f"{self.session_accumulated_seconds} seconds saved for the subject.")
        self.session_accumulated_seconds = 0

    def _register_session(self, minutes):
        self.db.add_session(self.current_subject_id, minutes)
        self._load_subjects()
        self.update_chart()

        rows = self.active_table.rowCount()
        found = False
        for r in range(rows):
            if int(self.active_table.item(r, 0).text()) == self.current_subject_id:
                self.on_subject_selected(r, 0, self.active_table)
                found = True
                break

        if not found:
            rows = self.completed_table.rowCount()
            for r in range(rows):
                if int(self.completed_table.item(r, 0).text()) == self.current_subject_id:
                    self.on_subject_selected(r, 0, self.completed_table)
                    break

    def update_chart(self):
        subjects = self.db.list_subjects()
        if subjects:
            self.chart.plot(subjects)
        else:
            self.chart.axes.clear()
            self.chart.update_colors()
            self.chart.axes.text(0.5, 0.5, "No subjects added", ha="center", va="center", color=self.themes[self.current_theme]['text'])
            self.chart.draw()

    def export_csv(self):
        if self.current_subject_id is None:
            QMessageBox.information(self, "Selection", "Please select a subject.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        sessions = self.db.get_sessions_for_subject(self.current_subject_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("minutes,ts\n")
                for m, ts in sessions:
                    f.write(f"{m},{ts}\n")
            QMessageBox.information(self, "Export", "CSV file saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving: {e}")

    def view_statistics(self):
        self.stats_window = StatisticsWindow(self.db, self)
        self.stats_window.show()

    def view_calendar(self):
        self.calendar_window = CalendarWindow(self.db, self.themes[self.current_theme], self)
        self.calendar_window.show()

    def _format_time(self, seconds):
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def closeEvent(self, event):
        self.db.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    

    import ctypes
    try:

        myappid = 'mycompany.studymaster.pro.1'  
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        pass 
    

    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)

    QApplication.setWindowIcon(app_icon)
    
    window = StudyMaster()
    window.show()
    sys.exit(app.exec_())