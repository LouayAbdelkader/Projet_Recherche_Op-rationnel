# constants.py

# --- DESIGN SYSTEM ---
# Couleurs identiques au premier code
COLOR_BG = "#0a0e1a"
COLOR_PANEL = "#121218"
COLOR_ACCENT = "#4d9fff"
COLOR_TEXT_MAIN = "#e0e6ed"
COLOR_TEXT_DIM = "#7c8594"
COLOR_BORDER = "#1a2332"

STYLESHEET = f"""
QMainWindow {{ background-color: {COLOR_BG}; }}
QWidget {{ font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 13px; color: {COLOR_TEXT_MAIN}; }}

/* --- TABS --- */
QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar::tab {{
    background: transparent;
    color: {COLOR_TEXT_DIM};
    padding: 12px 24px;
    font-weight: 600;
    font-size: 14px;
    border-bottom: 3px solid transparent;
}}
QTabBar::tab:selected {{ color: {COLOR_ACCENT}; border-bottom: 3px solid {COLOR_ACCENT}; }}
QTabBar::tab:hover:!selected {{ color: #ffffff; }}

/* --- INPUTS --- */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: #23232a;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    color: white;
    padding: 8px;
    font-weight: bold;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {COLOR_ACCENT};
    background-color: #2a2a32;
}}

/* --- BUTTONS --- */
QPushButton {{
    background-color: #2a2a35;
    color: white;
    border: 1px solid {COLOR_BORDER};
    padding: 10px 15px;
    border-radius: 6px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: #32323e; border-color: {COLOR_TEXT_DIM}; }}

QPushButton#RunButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4c6ef5, stop:1 #748ffc);
    color: white;
    border: none;
    font-size: 15px;
    padding: 15px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    border-radius: 8px;
}}
QPushButton#RunButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5c7cfa, stop:1 #91a7ff);
}}

/* --- TABLES --- */
QTableWidget {{
    background-color: {COLOR_PANEL};
    gridline-color: {COLOR_BORDER};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    outline: none;
}}
QHeaderView::section {{
    background-color: #23232a;
    color: {COLOR_TEXT_DIM};
    padding: 8px;
    border: none;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 11px;
}}
QTableWidget::item {{ padding: 5px; }}
QTableWidget::item:selected {{ background-color: rgba(92, 124, 250, 0.2); }}

/* --- TEXT EDIT --- */
QTextEdit {{
    background-color: #0f0f13;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    color: #ced4da;
    font-family: 'Consolas', monospace;
    font-size: 12px;
}}

/* --- PLAIN TEXT EDIT --- */
QPlainTextEdit {{
    background-color: #0f0f13;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    color: #ced4da;
    font-family: 'Consolas', monospace;
    font-size: 12px;
    padding: 10px;
}}

/* --- SCROLLBAR --- */
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #3f3f4b; min-height: 20px; border-radius: 4px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

/* --- GROUP BOX --- */
QGroupBox {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    margin-top: 1.5em;
    padding-top: 10px;
    font-weight: bold;
    color: {COLOR_ACCENT};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}

/* --- SCROLL AREA --- */
QScrollArea {{ border: none; background-color: transparent; }}

/* --- CHECKBOX --- */
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLOR_ACCENT};
    border-radius: 4px;
}}
QCheckBox::indicator:checked {{ background-color: {COLOR_ACCENT}; }}

/* --- SPINBOX ARROWS --- */
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid {COLOR_BORDER};
    border-radius: 0px 4px 0px 0px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid {COLOR_BORDER};
    border-radius: 0px 0px 4px 0px;
}}
"""