# custom_widgets.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

from constants import COLOR_PANEL, COLOR_BORDER, COLOR_ACCENT, COLOR_TEXT_DIM

# --- CLASSES PERSONNALISÉES POUR L'INTERFACE ---
def apply_shadow(widget, blur=15, alpha=50):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, alpha))
    shadow.setOffset(0, 4)
    widget.setGraphicsEffect(shadow)

class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 0px;
            }}
        """)
        apply_shadow(self)

class MetricWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            MetricWidget {{
                background-color: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
                padding: 0px;
            }}
        """)
        apply_shadow(self)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # En-tête
        self.header_layout = QHBoxLayout()
        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 10px; border:none;")
        self.lbl_title = QLabel("TITRE")
        self.lbl_title.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1px; border:none;")
        self.header_layout.addWidget(self.dot)
        self.header_layout.addWidget(self.lbl_title)
        self.header_layout.addStretch()
        self.layout.addLayout(self.header_layout)
        
        # Valeur
        self.val_layout = QHBoxLayout()
        self.lbl_val = QLabel("-")
        self.lbl_val.setStyleSheet("color: white; font-size: 28px; font-weight: 600; border:none;")
        self.lbl_unit = QLabel("")
        self.lbl_unit.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 14px; margin-bottom: 4px; border:none;")
        self.val_layout.addWidget(self.lbl_val)
        self.val_layout.addWidget(self.lbl_unit, 0, Qt.AlignBottom)
        self.val_layout.addStretch()
        self.layout.addLayout(self.val_layout)

    def set_data(self, title, value, unit="", color=COLOR_ACCENT):
        self.lbl_title.setText(title.upper())
        self.lbl_val.setText(str(value))
        self.lbl_unit.setText(unit)
        self.dot.setStyleSheet(f"color: {color}; font-size: 10px; border:none;")