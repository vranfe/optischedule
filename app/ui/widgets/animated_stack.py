from PySide6.QtWidgets import QStackedWidget, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve

class AnimatedStackedWidget(QStackedWidget):
    """
    QStackedWidget with smooth React-like opacity fade transitions between pages.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fade_duration = 200  # milliseconds
        self.anim = None

    def setCurrentIndex(self, index: int):
        if index == self.currentIndex():
            return

        next_widget = self.widget(index)
        if not next_widget:
            super().setCurrentIndex(index)
            return

        effect = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        super().setCurrentIndex(index)

        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(self.fade_duration)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.finished.connect(lambda: next_widget.setGraphicsEffect(None))
        self.anim.start()
