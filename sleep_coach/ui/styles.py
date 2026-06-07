def build_app_style(scale: float = 1.0) -> str:
    def px(value: int) -> int:
        return max(1, round(value * scale))

    return f"""
QWidget {{
    color: #F5E9D0;
    font-family: "Bahnschrift", "Microsoft YaHei UI", "Segoe UI";
}}

QMainWindow, QWidget#mainSurface {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #141A2A,
        stop:0.48 #0E1320,
        stop:1 #070A12);
}}

QDialog {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #11182A,
        stop:1 #0A0F1B);
    border: 1px solid rgba(242, 185, 110, 0.22);
    border-radius: {px(26)}px;
}}

QFrame[card="true"] {{
    background: rgba(15, 20, 34, 232);
    border: 1px solid rgba(242, 185, 110, 24);
    border-radius: {px(28)}px;
}}

QFrame[subtlePanel="true"] {{
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: {px(22)}px;
}}

QFrame[metricChip="true"] {{
    background: rgba(255, 203, 116, 0.08);
    border: 1px solid rgba(255, 203, 116, 0.15);
}}

QLabel#eyebrow {{
    color: #F2B96E;
    font-size: {px(20)}px;
    font-weight: 900;
    letter-spacing: 2px;
    text-transform: uppercase;
}}

QLabel#titleHero {{
    font-size: {px(54)}px;
    font-weight: 900;
    color: #FFF3DE;
}}

QLabel#bodyCopy {{
    color: rgba(245, 233, 208, 0.84);
    font-size: {px(21)}px;
}}

QLabel#cardTitle {{
    font-size: {px(38)}px;
    font-weight: 900;
    color: #FFF3DE;
}}

QLabel#cardTitleInline {{
    font-size: {px(32)}px;
    font-weight: 900;
    color: #FFF3DE;
}}

QLabel#quoteHero {{
    font-size: {px(34)}px;
    font-weight: 900;
    color: #FFF3DE;
}}

QLabel#gateTitle {{
    font-size: {px(36)}px;
    font-weight: 900;
    color: #FFF3DE;
}}

QLabel#gateTimer {{
    font-size: {px(86)}px;
    font-weight: 900;
    color: #FFCB74;
}}

QLabel#gateQuote {{
    font-size: {px(24)}px;
    font-weight: 800;
    color: #FFF3DE;
}}

QLabel#panelTitle {{
    font-size: {px(26)}px;
    font-weight: 800;
    color: #FFCB74;
}}

QLabel#helperText {{
    color: rgba(245, 233, 208, 0.68);
    font-size: {px(19)}px;
}}

QLabel#helperTextStrong {{
    color: rgba(255, 203, 116, 0.96);
    font-size: {px(20)}px;
    font-weight: 700;
}}

QLabel#fieldLabel {{
    font-size: {px(19)}px;
    font-weight: 700;
    color: rgba(245, 233, 208, 0.94);
}}

QLabel#metricFieldLabel {{
    font-size: {px(19)}px;
    font-weight: 700;
    color: rgba(245, 233, 208, 0.92);
}}

QLabel#chipLabel {{
    color: rgba(245, 233, 208, 0.62);
    font-size: {px(16)}px;
    font-weight: 700;
}}

QLabel#chipValue {{
    color: #FFCB74;
    font-size: {px(30)}px;
    font-weight: 900;
}}

QLabel#statValue {{
    font-size: {px(48)}px;
    font-weight: 900;
    color: #FFCB74;
}}

QLabel#statLabel {{
    color: rgba(245, 233, 208, 0.68);
    font-size: {px(18)}px;
    font-weight: 600;
}}

QLabel#recordHeader {{
    color: rgba(245, 233, 208, 0.64);
    font-size: {px(16)}px;
    font-weight: 700;
}}

QLabel#recordPeriod {{
    color: #FFCB74;
    font-size: {px(20)}px;
    font-weight: 800;
}}

QLabel#recordMetricLabel {{
    color: rgba(245, 233, 208, 0.72);
    font-size: {px(15)}px;
    font-weight: 700;
}}

QLabel#recordValue {{
    color: #FFF3DE;
    font-size: {px(22)}px;
    font-weight: 800;
}}

QLabel#recordRatio {{
    color: #FFCB74;
    font-size: {px(18)}px;
    font-weight: 800;
}}

QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #F39C4D,
        stop:1 #E55A55);
    border: none;
    border-radius: {px(16)}px;
    padding: {px(12)}px {px(22)}px;
    min-height: {px(32)}px;
    font-size: {px(19)}px;
    font-weight: 800;
    color: #FFF7ED;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #F7AC66,
        stop:1 #F1726B);
}}

QPushButton:focus {{
    outline: none;
    border: 1px solid rgba(255, 203, 116, 0.55);
}}

QPushButton:disabled {{
    background: rgba(255, 255, 255, 0.10);
    color: rgba(255, 243, 222, 0.58);
}}

QPushButton[size="compact"] {{
    padding: {px(6)}px {px(18)}px;
    min-height: {px(18)}px;
    font-size: {px(17)}px;
    border-radius: {px(14)}px;
}}

QPushButton[variant="ghost"] {{
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 203, 116, 0.18);
    color: #FFD9A2;
}}

QPushButton[variant="ghost"]:hover {{
    background: rgba(255, 203, 116, 0.14);
}}

QLineEdit, QTimeEdit, QSpinBox {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: {px(16)}px;
    padding: {px(8)}px {px(12)}px;
    font-size: {px(22)}px;
    font-weight: 700;
    color: #FFF3DE;
    selection-background-color: rgba(242, 185, 110, 0.38);
}}

QTimeEdit:disabled, QSpinBox:disabled {{
    color: rgba(255, 243, 222, 0.52);
    background: rgba(255, 255, 255, 0.03);
}}

QTimeEdit:focus, QSpinBox:focus {{
    border: 1px solid rgba(255, 203, 116, 0.55);
}}

QTimeEdit::up-button, QTimeEdit::down-button,
QSpinBox::up-button, QSpinBox::down-button {{
    width: {px(26)}px;
    border: none;
    background: rgba(255, 255, 255, 0.04);
}}

QCheckBox {{
    spacing: {px(12)}px;
    font-size: {px(20)}px;
    font-weight: 700;
    color: rgba(245, 233, 208, 0.94);
}}

QCheckBox::indicator {{
    width: {px(20)}px;
    height: {px(20)}px;
}}

QCheckBox::indicator:unchecked {{
    border-radius: {px(6)}px;
    border: 1px solid rgba(255, 203, 116, 0.48);
    background: rgba(255, 255, 255, 0.08);
}}

QCheckBox::indicator:checked {{
    border-radius: {px(6)}px;
    border: 1px solid rgba(255, 203, 116, 0.9);
    background: #F39C4D;
}}

QMenu {{
    background: rgba(12, 18, 31, 0.98);
    color: #FFF3DE;
    border: 1px solid rgba(255, 203, 116, 0.28);
    padding: {px(8)}px;
    font-size: {px(18)}px;
}}

QMenu::item {{
    padding: {px(10)}px {px(18)}px;
    border-radius: {px(10)}px;
    background: transparent;
}}

QMenu::item:selected {{
    background: rgba(255, 203, 116, 0.16);
    color: #FFCB74;
}}

QMenu::separator {{
    height: 1px;
    margin: {px(6)}px {px(8)}px;
    background: rgba(255, 255, 255, 0.08);
}}

QWidget#topBarRoot {{
    background: rgba(15, 18, 30, 220);
    border: 1px solid rgba(255, 203, 116, 0.22);
    border-radius: {px(24)}px;
}}

QLabel#topBarTime {{
    font-size: {px(32)}px;
    font-weight: 900;
    color: #FFCB74;
}}

QLabel#topBarClock {{
    font-size: {px(32)}px;
    font-weight: 800;
    color: #FFCB74;
}}

QLabel#topBarQuote {{
    font-size: {px(28)}px;
    font-weight: 700;
    color: #FFCB74;
}}

QLabel#inlineHelperText {{
    color: rgba(245, 233, 208, 0.74);
    font-size: {px(18)}px;
    font-weight: 700;
}}

QWidget#overlayRoot {{
    background: rgba(6, 8, 14, 245);
}}

QLabel#overlayTimer {{
    font-size: {px(96)}px;
    font-weight: 900;
    color: #FFCB74;
}}

QLabel#overlayQuote {{
    font-size: {px(32)}px;
    font-weight: 800;
    color: #FFF3DE;
}}
"""
