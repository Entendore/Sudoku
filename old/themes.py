"""
Theme definitions — Color schemes and stylesheets for dark/light modes
"""

DARK_COLORS = dict(
    bg="#181825", ce="#1E1E2E", co="#232336",
    gf="#CDD6F4", uf="#89B4FA", ef="#F38BA8", eb="#3B1A2A",
    nf="#7F849C", sb="#45475A", sn="#1E3A5F", sp="#1C2333",
    lt="#313244", lk="#585B70", bd="#6C7086", sv=(0, 180, 100, 35),
)

LIGHT_COLORS = dict(
    bg="#DFE6ED", ce="#FFFFFF", co="#F0F4F8",
    gf="#1A237E", uf="#1565C0", ef="#C62828", eb="#FFCDD2",
    nf="#78909C", sb="#90CAF9", sn="#BBDEFB", sp="#E3F2FD",
    lt="#B0BEC5", lk="#37474F", bd="#263238", sv=(0, 200, 80, 30),
)

DARK_BASE_STYLESHEET = """
    QMainWindow, QWidget { background:#181825; }
    QLabel { color:#CDD6F4; }
    QLabel#hintLabel { color:#A6ADC8; font-size:11pt;
        background:#1E1E2E; padding:10px; border-radius:8px; }
    QLabel#keyHint { color:#585B70; font-size:9pt; }
    QCheckBox { color:#CDD6F4; spacing:6px; }
    QCheckBox::indicator { width:16px; height:16px; }
    QComboBox { background:#313244; color:#CDD6F4; border:1px solid #45475A;
        border-radius:4px; padding:4px 8px; }
    QComboBox QAbstractItemView { background:#313244; color:#CDD6F4;
        selection-background-color:#45475A; }
    QComboBox::drop-down { border:none; }
    QFrame[frameShape="4"] { color:#313244; }
"""

DARK_BUTTON_STYLESHEET = """
    QPushButton#actionBtn { background:#313244; color:#CDD6F4;
        border:1px solid #45475A; border-radius:6px; font-weight:bold; }
    QPushButton#actionBtn:hover { background:#45475A; }
    QPushButton#actionBtn:pressed { background:#585B70; }
    QPushButton#actionBtn:disabled { background:#1E1E2E; color:#45475A; }
    QPushButton#toggleBtn { background:#313244; color:#CDD6F4;
        border:1px solid #45475A; border-radius:6px; padding:6px 12px; font-weight:bold; }
    QPushButton#toggleBtn:hover { background:#45475A; }
    QPushButton#toggleBtn:checked { background:#89B4FA; color:#1E1E2E; }
    QPushButton#themeBtn { background:#313244; color:#CDD6F4;
        border:1px solid #45475A; border-radius:8px; font-size:18px; }
    QPushButton#themeBtn:hover { background:#45475A; }
    NumButton { background:#313244; border:1px solid #45475A;
        border-radius:8px; }
    NumButton:hover { background:#45475A; }
    NumButton:disabled { background:#1E1E2E; color:#45475A; }
    QLabel { color:#CDD6F4; }
"""

LIGHT_BASE_STYLESHEET = """
    QMainWindow, QWidget { background:#F0F2F5; }
    QLabel { color:#212121; }
    QLabel#hintLabel { color:#424242; font-size:11pt;
        background:#FFFFFF; padding:10px; border-radius:8px;
        border:1px solid #E0E0E0; }
    QLabel#keyHint { color:#9E9E9E; font-size:9pt; }
    QCheckBox { color:#212121; spacing:6px; }
    QComboBox { background:#FFFFFF; color:#212121; border:1px solid #BDBDBD;
        border-radius:4px; padding:4px 8px; }
    QComboBox QAbstractItemView { background:#FFFFFF; color:#212121;
        selection-background-color:#E3F2FD; }
    QComboBox::drop-down { border:none; }
    QFrame[frameShape="4"] { color:#E0E0E0; }
"""

LIGHT_BUTTON_STYLESHEET = """
    QPushButton#actionBtn { background:#FFFFFF; color:#212121;
        border:1px solid #E0E0E0; border-radius:6px; font-weight:bold; }
    QPushButton#actionBtn:hover { background:#E3F2FD; border-color:#90CAF9; }
    QPushButton#actionBtn:pressed { background:#BBDEFB; }
    QPushButton#actionBtn:disabled { background:#F5F5F5; color:#BDBDBD; }
    QPushButton#toggleBtn { background:#FFFFFF; color:#212121;
        border:1px solid #E0E0E0; border-radius:6px; padding:6px 12px; font-weight:bold; }
    QPushButton#toggleBtn:hover { background:#E3F2FD; }
    QPushButton#toggleBtn:checked { background:#1976D2; color:#FFFFFF; }
    QPushButton#themeBtn { background:#FFFFFF; color:#212121;
        border:1px solid #E0E0E0; border-radius:8px; font-size:18px; }
    QPushButton#themeBtn:hover { background:#E3F2FD; }
    NumButton { background:#FFFFFF; border:1px solid #E0E0E0;
        border-radius:8px; }
    NumButton:hover { background:#E3F2FD; }
    NumButton:disabled { background:#F5F5F5; color:#BDBDBD; }
    QLabel { color:#212121; }
"""


def get_colors(dark_mode: bool) -> dict:
    """Return color dictionary for current theme."""
    return dict(DARK_COLORS if dark_mode else LIGHT_COLORS)


def get_base_stylesheet(dark_mode: bool) -> str:
    """Return base stylesheet for main window."""
    return DARK_BASE_STYLESHEET if dark_mode else LIGHT_BASE_STYLESHEET


def get_button_stylesheet(dark_mode: bool) -> str:
    """Return stylesheet for buttons and num buttons."""
    return DARK_BUTTON_STYLESHEET if dark_mode else LIGHT_BUTTON_STYLESHEET


def get_hint_highlight_color(dark_mode: bool) -> str:
    """Return highlight color for hint cells."""
    return "#4A3F00" if dark_mode else "#FFF9C4"


def get_solve_place_colors(dark_mode: bool) -> tuple:
    """Return (flash_color, fade_color) for solver placement animation."""
    if dark_mode:
        return "#2E7D32", "#1B5E20"
    return "#66BB6A", "#C8E6C9"


def get_solve_remove_colors(dark_mode: bool) -> tuple:
    """Return (flash_color, fade_color) for solver removal animation."""
    if dark_mode:
        return "#7F1D1D", "#4A1A1A"
    return "#EF9A9A", "#FFEBEE"