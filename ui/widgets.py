"""Сетка активности за 8 недель в стиле GitHub: закрашенный день — выполнено."""

from datetime import date, timedelta

from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

EMPTY_COLOR = "#ebedf0"


class HeatmapGrid(QWidget):
    """Сетка 8 недель: клик по дню ставит или снимает отметку."""

    day_clicked = pyqtSignal(object)  # передаёт дату (datetime.date)

    def __init__(self, weeks=8, parent=None):
        super().__init__(parent)
        self.weeks = weeks
        self.days = 7
        self.done = set()          # строки дат формата YYYY-MM-DD
        self.color = "#10b981"
        self.setMinimumSize(420, 150)

    def refresh(self, dates, color):
        self.done = set(dates)
        self.color = color or "#10b981"
        self.update()

    # ----- геометрия сетки -----

    def _geometry(self):
        w, h = self.width(), self.height()
        cell = min((w - 34) / self.weeks, (h - 10) / self.days, 18)
        gap = cell * 0.2
        x0 = 34
        y0 = (h - self.days * (cell + gap)) / 2
        return cell, gap, x0, y0

    def _first_monday(self):
        today = date.today()
        return today - timedelta(days=today.weekday()) - timedelta(weeks=self.weeks - 1)

    # ----- отрисовка -----

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cell, gap, x0, y0 = self._geometry()
        painter.setPen(Qt.PenStyle.NoPen)

        for row, name in enumerate(["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]):
            painter.setPen(QColor("#6b7280"))
            painter.drawText(0, int(y0 + row * (cell + gap)),
                             30, int(cell + gap),
                             Qt.AlignmentFlag.AlignVCenter, name)
            painter.setPen(Qt.PenStyle.NoPen)

        monday = self._first_monday()
        today = date.today()
        for col in range(self.weeks):
            for row in range(self.days):
                day = monday + timedelta(weeks=col, days=row)
                if day > today:
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                else:
                    filled = str(day) in self.done
                    painter.setBrush(QColor(self.color if filled else EMPTY_COLOR))
                rect = QRectF(x0 + col * (cell + gap),
                              y0 + row * (cell + gap), cell, cell)
                painter.drawRoundedRect(rect, 2, 2)

    # ----- клик по дню -----

    def mousePressEvent(self, event):
        cell, gap, x0, y0 = self._geometry()
        col = int((event.position().x() - x0) / (cell + gap))
        row = int((event.position().y() - y0) / (cell + gap))
        if 0 <= col < self.weeks and 0 <= row < self.days:
            day = self._first_monday() + timedelta(weeks=col, days=row)
            if day <= date.today():
                self.day_clicked.emit(day)
        super().mousePressEvent(event)
