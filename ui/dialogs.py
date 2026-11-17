"""Диалоги: создание/редактирование привычки и окно статистики."""

from datetime import date

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QRadioButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)

from database import get_all_habits, get_archived_habits, get_completions
from stats import current_streak, month_percent, record_streak

COLORS = ["#10b981", "#3b82f6", "#ef4444", "#f59e0b",
          "#8b5cf6", "#06b6d4", "#f97316", "#8d6e63"]


class HabitDialog(QDialog):
    def __init__(self, parent=None, habit=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование привычки" if habit else "Новая привычка")
        self.setMinimumWidth(360)
        self.habit = habit

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Название:"))
        self.name_edit = QLineEdit()
        if habit:
            self.name_edit.setText(habit["name"])
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Описание:"))
        self.desc_edit = QLineEdit()
        if habit:
            self.desc_edit.setText(habit["description"] or "")
        layout.addWidget(self.desc_edit)

        layout.addWidget(QLabel("Цвет:"))
        self.color_combo = QComboBox()
        for c in COLORS:
            pixmap = QPixmap(14, 14)
            pixmap.fill(QColor(c))
            self.color_combo.addItem(QIcon(pixmap), c, c)
        if habit:
            index = COLORS.index(habit["color"]) if habit["color"] in COLORS else 0
            self.color_combo.setCurrentIndex(index)
        layout.addWidget(self.color_combo)

        self.daily_radio = QRadioButton("Ежедневно")
        self.weekly_radio = QRadioButton("N раз в неделю:")
        if habit and habit["freq_type"] == "weekly":
            self.weekly_radio.setChecked(True)
        else:
            self.daily_radio.setChecked(True)
        layout.addWidget(self.daily_radio)
        row = QHBoxLayout()
        row.addWidget(self.weekly_radio)
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 7)
        if habit and habit["freq_type"] == "weekly":
            self.target_spin.setValue(habit["freq_target"] or 1)
        row.addWidget(self.target_spin)
        layout.addLayout(row)

        buttons = QHBoxLayout()
        ok = QPushButton("Сохранить")
        cancel = QPushButton("Отмена")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

    def accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название привычки")
            return
        super().accept()

    def get_data(self):
        if self.daily_radio.isChecked():
            freq_type, freq_target = "daily", None
        else:
            freq_type, freq_target = "weekly", self.target_spin.value()
        return {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "color": self.color_combo.currentData(),
            "freq_type": freq_type,
            "freq_target": freq_target,
        }


class StatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Статистика")
        self.resize(580, 480)
        layout = QVBoxLayout(self)

        habits = get_all_habits() + get_archived_habits()

        table = QTableWidget(len(habits), 4)
        table.setHorizontalHeaderLabels(["Привычка", "% за месяц", "Серия", "Рекорд"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(table)

        counts = {}
        for i, habit in enumerate(habits):
            dates = get_completions(habit["id"])
            for s in dates:
                counts[s] = counts.get(s, 0) + 1
            table.setItem(i, 0, QTableWidgetItem(habit["name"]))
            table.setItem(i, 1, QTableWidgetItem(str(month_percent(habit, dates))))
            table.setItem(i, 2, QTableWidgetItem(str(current_streak(dates))))
            table.setItem(i, 3, QTableWidgetItem(str(record_streak(dates))))

        figure = Figure(figsize=(5, 2.5))
        canvas = FigureCanvasQTAgg(figure)
        layout.addWidget(canvas)

        today = date.today()
        days = [date(today.year, today.month, d) for d in range(1, today.day + 1)]
        values = [counts.get(str(d), 0) for d in days]
        ax = figure.add_subplot(111)
        ax.bar(range(1, today.day + 1), values, color="#10b981")
        ax.set_title("Отметки по дням (текущий месяц)")
        ax.set_xlabel("День месяца")
        ax.set_ylabel("Отметок")
