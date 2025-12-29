import sys, os, random
from functools import partial
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect, \
    QLineEdit, QLabel
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QUrl
from PyQt5.QtGui import QPainter, QBrush, QFont, QPixmap


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


Background_PATH = resource_path("images/background.jpg")
BUBBLE_TEXTURE_PATH = resource_path("images/chiikawa.png")


class BackgroundWidget(QWidget):
    """带背景图的容器"""

    def __init__(self):
        super().__init__()
        self.bg = QPixmap(Background_PATH) if os.path.exists(Background_PATH) else None

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.bg:
            painter.drawPixmap(self.rect(), self.bg)
        else:
            painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)


class BubbleButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(70, 70)
        self.texture = QPixmap(BUBBLE_TEXTURE_PATH) if os.path.exists(BUBBLE_TEXTURE_PATH) else None
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(1.0)
        self.visible_flag = True

    def update_style(self):
        size = self.width()
        self.setStyleSheet(
            f"""
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: {size // 2}px;
            color: #123;
            font-weight: bold;
            font-size: {max(8, int(16 * size / 70))}px;
            background-color: transparent;
            """
        )

    def paintEvent(self, event):
        if not self.visible_flag:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        if self.texture:
            brush = QBrush(self.texture.scaled(rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect)
        painter.setPen(Qt.black)
        font = QFont()
        font.setBold(True)
        font.setPointSize(int(self.width() * 0.22))
        painter.setFont(font)
        # 下移 10% 高度
        adjusted_rect = rect.adjusted(0, int(rect.height() * 0.3), 0, 0)
        painter.drawText(adjusted_rect, Qt.AlignHCenter | Qt.AlignVCenter, self.text())

    def pop(self):
        if not self.visible_flag:
            return
        self.setEnabled(False)
        anim = QPropertyAnimation(self.effect, b"opacity")
        anim.setDuration(350)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InQuad)

        def hide_and_flag():
            self.hide()
            self.visible_flag = False

        anim.finished.connect(hide_and_flag)
        anim.start()
        self._anim = anim


class BubbleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("作业到手不拖拉 泡泡一消乐哈哈")
        self.init_width = 1100
        self.init_height = 650
        self.resize(self.init_width, self.init_height)
        self.undo_stack = []
        self.muted = False
        self.sounds = []

        sound_files = [
            "sounds/funny_sound1.wav",
            "sounds/funny_sound2.wav",
            "sounds/funny_sound3.wav",
            "sounds/funny_sound4.wav"
        ]
        for sf in sound_files:
            path = resource_path(sf)
            if os.path.exists(path):
                sound = QSoundEffect()
                sound.setSource(QUrl.fromLocalFile(path))
                sound.setVolume(0.8)
                self.sounds.append(sound)

        self.setup_ui()

    def setup_ui(self):
        self.bg = BackgroundWidget()
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.bg)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 底部控制按钮
        btn_layout = QHBoxLayout()
        self.undo_btn = QPushButton("撤销")
        self.undo_btn.clicked.connect(self.undo_pop)
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_bubbles)
        self.mute_btn = QPushButton("静音")
        self.mute_btn.clicked.connect(self.toggle_mute)
        self.input_line = QLineEdit()
        self.input_line.setFixedWidth(150)
        self.input_line.setPlaceholderText("输入班级学生数量")
        self.generate_btn = QPushButton("确定")
        self.generate_btn.clicked.connect(self.generate_bubbles)

        btn_layout.addWidget(self.mute_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.input_line)
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.undo_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.bubble_init_size = 70
        self.buttons = []
        self.positions = []

    def toggle_mute(self):
        self.muted = not self.muted
        self.mute_btn.setText("取消静音" if self.muted else "静音")

    def generate_bubbles(self):
        try:
            num_new = int(self.input_line.text())
            if num_new <= 0:
                return
        except ValueError:
            return

        # 清空旧按钮
        for btn in self.buttons:
            btn.setParent(None)
        self.buttons.clear()
        self.positions.clear()
        self.undo_stack.clear()

        cols = min(12, num_new)
        rows = (num_new + cols - 1) // cols

        # 生成新按钮
        for i in range(num_new):
            btn = BubbleButton(str(i + 1), self.bg)
            btn.clicked.connect(partial(self.pop_bubble, btn))
            self.buttons.append(btn)
            r = i // cols
            c = i % cols
            x_ratio = 0.1 + 0.8 * c / max(1, cols - 1)
            y_ratio = 0.2 + 0.6 * r / max(1, rows - 1)
            self.positions.append((x_ratio, y_ratio))
            btn.show()

        self.update_bubble_positions()
        self.input_line.clear()

    def pop_bubble(self, btn):
        btn.pop()
        if not self.muted and self.sounds:
            sound = random.choice(self.sounds)
            sound.play()
        self.undo_stack.append(btn)

    def undo_pop(self):
        if self.undo_stack:
            btn = self.undo_stack.pop()
            btn.visible_flag = True
            btn.setEnabled(True)
            btn.effect.setOpacity(1.0)
            btn.show()

    def reset_bubbles(self):
        for btn in self.buttons:
            btn.visible_flag = True
            btn.setEnabled(True)
            btn.effect.setOpacity(1.0)
            btn.show()
        self.undo_stack.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_bubble_positions()

    def update_bubble_positions(self):
        if not self.buttons:
            return
        w_ratio = self.bg.width() / self.init_width
        h_ratio = self.bg.height() / self.init_height
        scale = min(w_ratio, h_ratio)
        for btn, (x_ratio, y_ratio) in zip(self.buttons, self.positions):
            size = int(self.bubble_init_size * scale)
            btn.setFixedSize(size, size)
            btn.update_style()
            x = int(x_ratio * self.bg.width() - size / 2)
            y = int(y_ratio * self.bg.height() - size / 2)
            btn.move(x, y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BubbleWindow()
    w.show()
    sys.exit(app.exec_())
