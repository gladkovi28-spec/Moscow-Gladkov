"""Главное окно приложения."""

import csv
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)

from database import (
    create_habit, delete_habit, export_all, get_all_habits,
    get_archived_habits, get_completions, set_archived, toggle_completion,
    update_habit,
)
from stats import current_streak, month_percent, record_streak
from ui.dialogs import HabitDialog, StatsDialog
from ui.widgets import HeatmapGrid

STYLE = """
    QWidget { background-color: #f3f4f6;
              font-family: 'Segoe UI', Arial, sans-serif; }
    QFrame#container { background-color: white;
                       border-radius: 12px;
                       border: 1px solid #e5e7eb; }
    QLabel#title { font-size: 18px; font-weight: 600; color: #111827; }
    QLabel#subtitle { font-size: 13px; color: #6b7280; }
    QLabel#streak_value { font-size: 20px; font-weight: 700; color: #10b981; }
    QLabel#info { font-size: 13px; color: #374151; }
    QListWidget { background-color: white; border: 1px solid #e5e7eb;
                  border-radius: 8px; padding: 4px; font-size: 13px; }
    QCheckBox { font-size: 13px; color: #374151; }
    QPushButton { border: none; border-radius: 8px;
                  padding: 10px 20px; font-weight: 600; font-size: 13px; }
    QPushButton#check_btn { background-color: #10b981; color: white; }
    QPushButton#check_btn:hover { background-color: #059669; }
    QPushButton#demo_btn { background-color: #e5e7eb; color: #374151; }
    QPushButton#demo_btn:hover { background-color: #d1d5db; }
    QPushButton#reset_btn { background-color: transparent;
                            color: #ef4444; border: 1px solid #ef4444; }
    QPushButton#reset_btn:hover { background-color: #fee2e2; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Habit Tracker")
        self.setMinimumSize(860, 560)
        self.setStyleSheet(STYLE)
        self.current_id = None
        self._habits = {}

        central = QWidget()
        self.setCentralWidget(central)
        window_layout = QVBoxLayout(central)

        container = QFrame()
        container.setObjectName("container")
        window_layout.addWidget(container)
        root = QHBoxLayout(container)
        root.setContentsMargins(24, 24, 24, 24)

        # ----- левая панель: список привычек -----
        left = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_select)
        left.addWidget(self.list_widget)

        btn_add = QPushButton("Добавить")
        btn_add.setObjectName("check_btn")
        btn_stats = QPushButton("Статистика")
        btn_stats.setObjectName("demo_btn")
        btn_export = QPushButton("Экспорт CSV")
        btn_export.setObjectName("demo_btn")
        btn_add.clicked.connect(self.add_habit)
        btn_stats.clicked.connect(self.show_stats)
        btn_export.clicked.connect(self.export_csv)
        row = QHBoxLayout()
        row.addWidget(btn_add)
        row.addWidget(btn_stats)
        row.addWidget(btn_export)
        left.addLayout(row)

        self.show_archived = QCheckBox("Показывать архив")
        self.show_archived.toggled.connect(lambda *_: self.refresh_list())
        left.addWidget(self.show_archived)
        root.addLayout(left, 1)

        # ----- правая панель: детали привычки -----
        right = QVBoxLayout()
        self.title_label = QLabel("Добро пожаловать в Habit Tracker!")
        self.title_label.setObjectName("title")
        self.subtitle_label = QLabel("Выберите привычку слева или создайте новую.")
        self.subtitle_label.setObjectName("subtitle")
        self.info_label = QLabel("")
        self.info_label.setObjectName("info")
        self.info_label.setWordWrap(True)
        self.streak_value = QLabel("")
        self.streak_value.setObjectName("streak_value")
        self.grid = HeatmapGrid(weeks=8)

        right.addWidget(self.title_label)
        right.addWidget(self.subtitle_label)
        right.addWidget(self.streak_value)
        right.addWidget(self.info_label)
        right.addWidget(self.grid, 1)

        btn_check = QPushButton("Отметиться")
        btn_check.setObjectName("check_btn")
        btn_check.clicked.connect(self.toggle_today)
        btn_edit = QPushButton("Редактировать")
        btn_edit.setObjectName("demo_btn")
        btn_edit.clicked.connect(self.edit_habit)
        btn_archive = QPushButton("Архив / Вернуть")
        btn_archive.setObjectName("demo_btn")
        btn_archive.clicked.connect(self.archive_habit)
        btn_delete = QPushButton("Удалить привычку")
        btn_delete.setObjectName("reset_btn")
        btn_delete.clicked.connect(self.delete_habit)

        buttons = QHBoxLayout()
        for b in (btn_check, btn_edit, btn_archive, btn_delete):
            buttons.addWidget(b)
        right.addLayout(buttons)
        root.addLayout(right, 2)

        self.grid.day_clicked.connect(self.on_day_clicked)
        self.refresh_list()

    # ----- список и детали -----

    def refresh_list(self, keep_id=None):
        if keep_id is None:
            keep_id = self.current_id
        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        habits = get_all_habits()
        if self.show_archived.isChecked():
            habits += get_archived_habits()
        self._habits = {h["id"]: h for h in habits}

        for h in habits:
            dates = get_completions(h["id"])
            streak = current_streak(dates)
            suffix = " (архив)" if h["archived"] else ""
            item = QListWidgetItem(f"● {h['name']} — серия: {streak}{suffix}")
            item.setData(Qt.ItemDataRole.UserRole, h["id"])
            pixmap = QPixmap(12, 12)
            pixmap.fill(QColor(h["color"]))
            item.setIcon(QIcon(pixmap))
            self.list_widget.addItem(item)

        found = False
        for row in range(self.list_widget.count()):
            if self.list_widget.item(row).data(Qt.ItemDataRole.UserRole) == keep_id:
                self.list_widget.setCurrentRow(row)
                found = True
                break
        self.list_widget.blockSignals(False)

        if found:
            self.current_id = keep_id
            self.show_details(self._habits[keep_id])
        else:
            self.current_id = None
            self.show_details(None)

    def on_select(self, row):
        item = self.list_widget.item(row)
        if item is None:
            self.current_id = None
            self.show_details(None)
            return
        habit_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_id = habit_id
        self.show_details(self._habits[habit_id])

    def show_details(self, habit):
        if habit is None:
            self.title_label.setText("Выберите привычку")
            self.subtitle_label.setText("Выберите привычку слева или создайте новую.")
            self.streak_value.setText("")
            self.info_label.setText("")
            self.grid.refresh([], "#ebedf0")
            return
        dates = get_completions(habit["id"])
        freq = (
            "ежедневно"
            if habit["freq_type"] == "daily"
            else f"{habit['freq_target']} раз(а) в неделю"
        )
        self.title_label.setText(habit["name"])
        self.subtitle_label.setText(
            f"{habit['description'] or 'Без описания'} · Частота: {freq}")
        self.streak_value.setText(
            f"Серия: {current_streak(dates)} · Рекорд: {record_streak(dates)} · "
            f"% за месяц: {month_percent(habit, dates)}")
        self.info_label.setText(
            "Сетка активности — чем ярче квадратик, тем лучше. "
            "Кликните по дню, чтобы поставить или снять отметку.")
        self.grid.refresh(dates, habit["color"])

    # ----- отметки (функции 4 и 5 из ТЗ) -----

    def toggle_today(self):
        self._toggle(date.today())

    def on_day_clicked(self, day):
        self._toggle(day)

    def _toggle(self, day):
        if self.current_id is None:
            QMessageBox.information(self, "Отметка", "Сначала выберите привычку.")
            return
        toggle_completion(self.current_id, str(day))
        self.refresh_list()

    # ----- CRUD (функции 1–3 и 12 из ТЗ) -----

    def add_habit(self):
        dialog = HabitDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                new_id = create_habit(**data)
            except Exception:
                QMessageBox.warning(
                    self, "Ошибка", "Привычка с таким названием уже есть")
                return
            self.refresh_list(keep_id=new_id)

    def edit_habit(self):
        if self.current_id is None:
            return
        habit = self._habits[self.current_id]
        dialog = HabitDialog(self, habit=habit)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                update_habit(self.current_id, **dialog.get_data())
            except Exception:
                QMessageBox.warning(
                    self, "Ошибка", "Привычка с таким названием уже есть")
                return
            self.refresh_list()

    def delete_habit(self):
        if self.current_id is None:
            return
        habit = self._habits[self.current_id]
        answer = QMessageBox.question(
            self, "Удаление",
            f"Удалить привычку «{habit['name']}» и все её отметки?")
        if answer == QMessageBox.StandardButton.Yes:
            delete_habit(self.current_id)
            self.current_id = None
            self.refresh_list()

    def archive_habit(self):
        if self.current_id is None:
            return
        habit = self._habits[self.current_id]
        set_archived(self.current_id, 0 if habit["archived"] else 1)
        self.refresh_list()

    # ----- статистика и экспорт (функции 9 и 11 из ТЗ) -----

    def show_stats(self):
        StatsDialog(self).exec()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить CSV", "habits.csv", "CSV (*.csv)")
        if not path:
            return
        rows = export_all()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Привычка", "Дата"])
            writer.writerows(rows)
        QMessageBox.information(self, "Готово", f"Экспортировано отметок: {len(rows)}")
