import maya.cmds as cmds
import maya.api.OpenMaya as om
import random
import time

try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

# --- CONSTANTS ---
WINDOW_TITLE = "SPACE.SWITCH // DASHBOARD"
WINDOW_NAME = "ss_dashboard_window"
LOCATOR_SUFFIX = "_SS_loc"
OFFSET_SUFFIX = "_offset"

LOCATOR_COLORS = {
    "red": 13, "yellow": 17, "green": 14, "blue": 6,
    "purple": 9, "white": 16, "cyan": 18, "orange": 21
}

UI_COLORS = {
    "red": "#ff4444", "yellow": "#eab308", "green": "#55ff55",
    "blue": "#55aaff", "purple": "#a855f7", "white": "#f8fafc",
    "cyan": "#00f3ff", "orange": "#f6a226"
}

# --- QSS STYLESHEET ---
QSS = """
QWidget {
    background-color: #05060a; 
    color: #e0e7ff; 
    font-family: "Consolas", "Courier New", monospace; 
    font-size: 10px;
}
QMainWindow { background-color: #05060a; }

/* Scrollbars */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #05060a; width: 6px; border: none; }
QScrollBar::handle:vertical { background: rgba(0, 243, 255, 0.2); min-height: 20px; border-radius: 3px; }
QScrollBar::handle:vertical:hover { background: rgba(0, 243, 255, 0.4); }

/* Panels */
QFrame#HudPanel {
    background: rgba(10, 12, 18, 0.9);
    border: 1px solid rgba(0, 243, 255, 0.15);
    border-radius: 2px;
}

/* Headers */
QPushButton#GroupLabel {
    background: transparent;
    color: rgba(255, 255, 255, 0.2);
    text-align: left;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 10px;
    letter-spacing: 2px;
    padding: 2px 0px;
    margin-top: 2px;
}
QPushButton#GroupLabel:hover {
    color: #00f3ff;
    border-bottom: 1px solid rgba(0, 243, 255, 0.5);
}
QPushButton#GroupLabel:pressed {
    padding: 2px 0px; 
    background: transparent;
    color: #00f3ff;
}

/* General Buttons */
QPushButton {
    background-color: rgba(0, 243, 255, 0.03); 
    border: 1px solid rgba(0, 243, 255, 0.2);
    color: #00f3ff; 
    padding: 3px 6px; 
    font-family: "Consolas", monospace; 
    font-size: 9px;
    text-transform: uppercase; 
    letter-spacing: 1px;
}
QPushButton:hover { background-color: rgba(0, 243, 255, 0.15); }
QPushButton:pressed {
    padding-top: 5px; padding-bottom: 1px;
    background-color: rgba(0, 243, 255, 0.3);
}

/* Mode Buttons Specific Styling */
QPushButton#ModeBtn {
    color: rgba(0, 243, 255, 0.3);
    border-color: rgba(0, 243, 255, 0.15);
    background-color: transparent;
}
QPushButton#ModeBtn:hover {
    color: rgba(0, 243, 255, 0.7);
    border-color: rgba(0, 243, 255, 0.4);
    background-color: rgba(0, 243, 255, 0.05);
}
QPushButton#ModeBtn:checked {
    background-color: rgba(0, 243, 255, 0.25);
    border-color: #00f3ff;
    color: #ffffff;
    font-weight: bold;
    padding-top: 5px; padding-bottom: 1px; /* Impressed look */
}

/* Custom Action Buttons */
QPushButton#ActionPrimary { border-color: rgba(0, 243, 255, 0.5); font-size: 11px; padding: 6px; }
QPushButton#ActionPrimary:pressed { padding-top: 8px; padding-bottom: 4px; background-color: rgba(0, 243, 255, 0.25); }

QPushButton#ActionOrange { border-color: rgba(246, 162, 38, 0.5); color: #f6a226; font-size: 11px; padding: 6px; }
QPushButton#ActionOrange:hover { background: rgba(246, 162, 38, 0.15); }
QPushButton#ActionOrange:pressed { padding-top: 8px; padding-bottom: 4px; background-color: rgba(246, 162, 38, 0.3); }

QPushButton#Danger { border-color: rgba(255, 68, 68, 0.5); color: #ff4444; }
QPushButton#Danger:hover { background: rgba(255, 68, 68, 0.15); }
QPushButton#Danger:pressed { padding-top: 5px; padding-bottom: 1px; background-color: rgba(255, 68, 68, 0.3); }

/* --------------------------------------------------------
   HOVER ANIMATIONS (Pulse / Glitch Properties) 
   -------------------------------------------------------- */

QPushButton[flicker="g1"] { background-color: rgba(255,255,255,0.1); border: 1px dashed white; color: white; }
QPushButton[flicker="g2"] { background-color: transparent; border: 1px dotted #00f3ff; color: #00f3ff; }

QPushButton[flicker="p1"] { background-color: rgba(0, 243, 255, 0.15); border: 1px solid rgba(0, 243, 255, 0.8); }
QPushButton[flicker="p2"] { background-color: rgba(0, 243, 255, 0.05); border: 1px solid rgba(0, 243, 255, 0.3); }

QPushButton#ActionOrange[flicker="p1"] { background-color: rgba(246, 162, 38, 0.2); border-color: #f6a226; color: white; }
QPushButton#ActionOrange[flicker="p2"] { background-color: rgba(246, 162, 38, 0.05); border-color: rgba(246, 162, 38, 0.4); }

QPushButton#Danger[flicker="p1"] { background-color: rgba(255, 68, 68, 0.2); border-color: #ff4444; color: white; }
QPushButton#Danger[flicker="p2"] { background-color: rgba(255, 68, 68, 0.05); border-color: rgba(255, 68, 68, 0.4); }

/* ToggleBtn Logic */
QPushButton#ToggleBtn {
    text-align: left;
    font-weight: bold;
    border-radius: 2px;
}
QPushButton#ToggleBtn:pressed { padding-top: 5px; padding-bottom: 1px; }

QPushButton#ToggleBtn[toggle_state="on"] {
    background-color: rgba(85, 255, 85, 0.1); border: 1px solid rgba(85, 255, 85, 0.6); color: #55ff55;
}
QPushButton#ToggleBtn[toggle_state="off"] {
    background-color: rgba(255, 68, 68, 0.05); border: 1px solid rgba(255, 68, 68, 0.4); color: #ff4444;
}

QPushButton#ToggleBtn[toggle_state="on"][flicker="p1"] { background-color: rgba(85, 255, 85, 0.25); border-color: white; color: white; }
QPushButton#ToggleBtn[toggle_state="on"][flicker="p2"] { background-color: rgba(85, 255, 85, 0.15); border-color: #55ff55; }
QPushButton#ToggleBtn[toggle_state="off"][flicker="p1"] { background-color: rgba(255, 68, 68, 0.2); border-color: white; color: white; }
QPushButton#ToggleBtn[toggle_state="off"][flicker="p2"] { background-color: rgba(255, 68, 68, 0.1); border-color: #ff4444; }

/* Individual Button Flash States */
QPushButton[flash_color="red"] {
    background-color: rgba(255, 68, 68, 0.8) !important;
    color: white !important;
    border: 1px solid #ff4444 !important;
}

QPushButton[flash_color="green"] {
    background-color: rgba(85, 255, 85, 0.8) !important;
    color: black !important;
    border: 1px solid #55ff55 !important;
}

QPushButton[flash_color="white"] {
    background-color: rgba(255, 255, 255, 0.9) !important;
    color: black !important;
    border: 1px solid white !important;
}

/* Click Flash Overrides (Absolute highest priority) */
QPushButton[flashing="true"], QFrame[flashing="true"], QLineEdit[flashing="true"] {
    background-color: white !important;
    color: black !important;
    border: 1px solid white !important;
}

/* Text Input Boxes */
QLineEdit { 
    background-color: rgba(30, 35, 45, 0.9); 
    border: 1px solid rgba(0, 243, 255, 0.4); 
    color: #00f3ff; 
    padding: 4px 8px; 
    margin: 0px 2px;
    border-radius: 2px;
}
QLineEdit:focus { border-color: #00f3ff; background-color: rgba(40, 45, 55, 1.0); }

QLineEdit#SourceInput { 
    color: #f6a226; 
    border-color: rgba(246, 162, 38, 0.4); 
}
QLineEdit#SourceInput:focus { border-color: #f6a226; }

QLineEdit#TargetInput { 
    color: #ff3300; 
    border-color: rgba(255, 51, 0, 0.4); 
}
QLineEdit#TargetInput:focus { border-color: #ff3300; }

/* Spin Boxes & ComboBoxes */
QDoubleSpinBox, QSpinBox { 
    background-color: rgba(0,0,0,0.6); border: 1px solid rgba(0,243,255,0.15); color: #00f3ff; padding: 4px; 
}
QDoubleSpinBox:focus, QSpinBox:focus { border-color: rgba(0,243,255,0.4); }

QComboBox { 
    background-color: rgba(5,8,15,0.9); border: 1px solid rgba(0,243,255,0.15); color: #00f3ff; padding: 4px; 
}
QComboBox::drop-down { border: none; width: 14px; }
QComboBox QAbstractItemView { 
    background: #0a0c12; color: #00f3ff; selection-background-color: rgba(0,243,255,0.15); 
}

/* Slider */
QSlider::groove:horizontal { border: none; height: 2px; background: rgba(255, 0, 234, 0.2); }
QSlider::handle:horizontal { background: #ff00ea; width: 6px; height: 14px; margin: -6px 0; }
"""

# ==============================================================================
# SPACE SWITCHER CORE LOGIC
# ==============================================================================

class SpaceSwitcher:
    def __init__(self):
        self.created_locators = []
        self.temp_constraints = []

    def get_best_rotation_order(self, obj, start, end):
        om_map = {0: om.MTransformationMatrix.kXYZ, 1: om.MTransformationMatrix.kYZX, 
                  2: om.MTransformationMatrix.kZXY, 3: om.MTransformationMatrix.kXZY, 
                  4: om.MTransformationMatrix.kYXZ, 5: om.MTransformationMatrix.kZYX}
        scores = {i: 0 for i in range(6)}
        try:
            for f in range(int(start), int(end) + 1):
                tm = om.MTransformationMatrix(om.MMatrix(cmds.getAttr(f"{obj}.worldMatrix[0]", time=f)))
                for idx, order in om_map.items():
                    e = tm.asEulerRotation()
                    e.reorderIt(order)
                    if abs(e.y) > scores[idx]: scores[idx] = abs(e.y)
            return min(scores, key=scores.get)
        except Exception:
            return 0 

    def clean_static_keys(self, nodes, threshold=0.001):
        curves = cmds.listConnections(nodes, type="animCurve") or []
        for c in curves:
            vals = cmds.keyframe(c, q=True, vc=True)
            if vals and (max(vals) - min(vals)) < threshold: cmds.delete(c)

    def build_locator_setup(self, source, target, settings):
        name_base = source.replace(":", "_")
        master_grp = cmds.group(em=True, n=f"{name_base}_Master_Space")
        cmds.matchTransform(master_grp, source, pos=True, rot=True)
        
        parent = master_grp
        for i in range(settings["offsets"]):
            loc = cmds.spaceLocator(n=f"{name_base}{OFFSET_SUFFIX}_{i+1}")[0]
            cmds.matchTransform(loc, source, pos=True, rot=True)
            cmds.parent(loc, parent)
            shape = cmds.listRelatives(loc, shapes=True)[0]
            cmds.setAttr(f"{shape}.overrideEnabled", 1)
            cmds.setAttr(f"{shape}.overrideColor", LOCATOR_COLORS.get(settings["color"], 17))
            s = settings["scale"]
            cmds.setAttr(f"{loc}.localScale", s, s, s)
            if settings["hide_offset"]: cmds.setAttr(f"{shape}.visibility", 0)
            parent = loc
            
        main_loc = cmds.spaceLocator(n=f"{name_base}{LOCATOR_SUFFIX}")[0]
        cmds.matchTransform(main_loc, source, pos=True, rot=True)
        cmds.parent(main_loc, parent)
        main_shape = cmds.listRelatives(main_loc, shapes=True)[0]
        cmds.setAttr(f"{main_shape}.overrideEnabled", 1)
        cmds.setAttr(f"{main_shape}.overrideColor", LOCATOR_COLORS.get(settings["color"], 17))
        s = settings["scale"] * 1.2
        cmds.setAttr(f"{main_loc}.localScale", s, s, s)
        
        if settings["add_layer"]:
            layer_name = "SpaceSwitch_Layer"
            if not cmds.objExists(layer_name): cmds.createDisplayLayer(name=layer_name, empty=True)
            cmds.editDisplayLayerMembers(layer_name, master_grp)
        
        self.created_locators.extend([master_grp, main_loc])
        return master_grp, main_loc

    def cleanup(self):
        nodes = cmds.ls(f"*{LOCATOR_SUFFIX}", f"*{OFFSET_SUFFIX}*", "*_Master_Space", "SS_Preview_Loc")
        if nodes: cmds.delete(nodes)
        self.created_locators = []
        cmds.inViewMessage(amg="Space Switch Data Cleaned Up.", pos='midCenter', fade=True)


# ==============================================================================
# CUSTOM UI WIDGETS
# ==============================================================================

class CyberButton(QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        
        self._base_text = self.text()
        
        # Hover / Pulse Animation Setup
        self._hover_timer = QtCore.QTimer(self)
        self._hover_timer.timeout.connect(self._do_flicker)
        self._hover_timer.setInterval(80)
        self._hover_ticks = 0

        # Click / Bracket Animation Setup
        self._click_timer = QtCore.QTimer(self)
        self._click_timer.timeout.connect(self._animate_click)
        self._click_step = 0

    def sizeHint(self):
        hint = super().sizeHint()
        if not hasattr(self, '_base_text') or not self._base_text:
            return hint
            
        fm = self.fontMetrics()
        width_func = fm.horizontalAdvance if hasattr(fm, "horizontalAdvance") else fm.width
        
        clean_text = self._base_text.replace("\u200B", "").strip()
        if clean_text.startswith("[") and clean_text.endswith("]"):
            clean_text = clean_text[1:-1].strip()
            
        max_text = f">>> {clean_text} <<<"
        w = width_func(max_text) + 12 # Reduced padding to keep buttons compact
        return QtCore.QSize(max(hint.width(), w), hint.height())

    def setText(self, text):
        self._base_text = text
        super().setText(text)

    def enterEvent(self, e):
        super().enterEvent(e)
        if not self.isEnabled(): return
        self._hover_ticks = 0
        self._hover_timer.start()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self._hover_timer.stop()
        self.setProperty("flicker", "")
        self.style().unpolish(self)
        self.style().polish(self)

    def _do_flicker(self):
        self._hover_ticks += 1
        if random.random() > 0.85:
            state = random.choice(["g1", "g2"])
        else:
            state = "p1" if (self._hover_ticks % 8) < 4 else "p2"
            
        self.setProperty("flicker", state)
        self.style().unpolish(self)
        self.style().polish(self)
        
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.trigger_flash()

    def trigger_flash(self):
        self.setProperty("flashing", True)
        self.style().unpolish(self)
        self.style().polish(self)
        
        self._click_step = 0
        self._click_timer.start(65)
        
    def _animate_click(self):
        self._click_step += 1
        
        if not self._base_text or len(self._base_text) <= 2:
            if self._click_step > 4:
                self._click_timer.stop()
                self.end_flash()
            return
            
        clean_base = self._base_text.replace("\u200B", "").strip()
        has_brackets = clean_base.startswith("[") and clean_base.endswith("]")
        inner_text = clean_base[1:-1].strip() if has_brackets else clean_base
        
        zws = "\u200B"
        frames = [
            f"{zws}  > {inner_text} <  {zws}",
            f"{zws} >> {inner_text} << {zws}",
            f"{zws}>>> {inner_text} <<<{zws}",
            f"{zws} >> {inner_text} << {zws}",
            f"{zws}  > {inner_text} <  {zws}"
        ]
        
        if self._click_step <= len(frames):
            super(CyberButton, self).setText(frames[self._click_step - 1])
        else:
            super(CyberButton, self).setText(self._base_text)
            self._click_timer.stop()
            self.end_flash()
            
    def end_flash(self):
        self.setProperty("flashing", False)
        self.style().unpolish(self)
        self.style().polish(self)


class CyberProgressButton(CyberButton):
    """Execution button that visually transforms into an inverted pixel-progress bar."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_progressing = False
        self._target_progress = 0.0
        self._current_progress = 0.0
        self._progress_text = ""
        
        self._color_fill = QtGui.QColor("#00f3ff")
        self._color_empty = QtGui.QColor(0, 243, 255, 40)
        self._color_text_base = QtGui.QColor("#00f3ff")
        self._color_text_inv = QtGui.QColor("#05060a")

    def set_progress_colors(self, fill_hex, text_base_hex, text_inv_hex="#05060a"):
        self._color_fill = QtGui.QColor(fill_hex)
        self._color_empty = QtGui.QColor(fill_hex)
        self._color_empty.setAlpha(40) # Faded empty dots
        self._color_text_base = QtGui.QColor(text_base_hex)
        self._color_text_inv = QtGui.QColor(text_inv_hex)

    def start_progress(self):
        self._is_progressing = True
        self._target_progress = 0.0
        self._current_progress = 0.0
        self.setProperty("flashing", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        QtWidgets.QApplication.processEvents()

    def set_progress_blocking(self, val, text):
        """Smoothly animates to the new value before freezing for Maya execution."""
        self._target_progress = val
        self._progress_text = text
        
        start_t = time.time()
        # Force a mini 0.15s animation loop right before the thread is locked
        while time.time() - start_t < 0.15:
            diff = self._target_progress - self._current_progress
            self._current_progress += diff * 0.3
            if abs(diff) < 0.005:
                self._current_progress = self._target_progress
            self.update()
            QtWidgets.QApplication.processEvents()
            time.sleep(0.016)
            
        self._current_progress = self._target_progress
        self.update()
        QtWidgets.QApplication.processEvents()

    def stop_progress(self):
        self._is_progressing = False
        self.update()
        QtWidgets.QApplication.processEvents()

    def paintEvent(self, event):
        if not self._is_progressing:
            super().paintEvent(event)
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Base deep void background
        painter.fillRect(0, 0, w, h, QtGui.QColor(10, 12, 18))
        painter.setPen(QtGui.QPen(self._color_fill, 1))
        painter.drawRect(0, 0, w-1, h-1)

        # Draw tech pixel grid
        cell_size = 5
        cols = int(w / cell_size) + 1
        rows = int(h / cell_size) + 1
        dot_r = cell_size * 0.35
        
        fill_w = w * self._current_progress
        
        painter.setPen(QtCore.Qt.NoPen)
        for r in range(rows):
            y = r * cell_size + cell_size / 2
            for c in range(cols):
                x = c * cell_size + cell_size / 2
                
                if x <= fill_w:
                    painter.setBrush(self._color_fill)
                else:
                    painter.setBrush(self._color_empty)
                    
                painter.drawEllipse(QtCore.QPointF(x, y), dot_r, dot_r)
        
        # Draw Overlapping High-Contrast Text 
        font = self.font()
        font.setBold(True)
        font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing, 1)
        painter.setFont(font)
        rect = QtCore.QRectF(0, 0, w, h)
        
        # Unfilled Right Side (Glowing Text)
        painter.setClipRect(QtCore.QRectF(fill_w, 0, w - fill_w, h))
        painter.setPen(self._color_text_base)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._progress_text)
        
        # Filled Left Side (Inverted Text)
        painter.setClipRect(QtCore.QRectF(0, 0, fill_w, h))
        painter.setPen(self._color_text_inv)
        painter.drawText(rect, QtCore.Qt.AlignCenter, self._progress_text)
        
        painter.end()


class CyberToggle(CyberButton):
    def __init__(self, text, checked=False, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.base_text = text
        self.setObjectName("ToggleBtn")
        self.setCheckable(True)
        
        self.blockSignals(True)
        self.setChecked(checked)
        self.blockSignals(False)
        
        self.toggled.connect(self._on_toggled)
        self._update_css_state()
        self._set_final_text()

    def sizeHint(self):
        return QtWidgets.QPushButton.sizeHint(self)

    def mousePressEvent(self, e):
        QtWidgets.QPushButton.mousePressEvent(self, e)

    def _update_css_state(self):
        state_str = "on" if self.isChecked() else "off"
        self.setProperty("toggle_state", state_str)
        self.style().unpolish(self)
        self.style().polish(self)

    def _set_final_text(self):
        final_text = f"   [X]   {self.base_text}" if self.isChecked() else f"   [ ]   {self.base_text}"
        QtWidgets.QPushButton.setText(self, final_text)

    def _on_toggled(self, checked):
        self._update_css_state()
        self.setProperty("flashing", True)
        self.style().unpolish(self)
        self.style().polish(self)
        
        self._click_step = 0
        self._click_timer.start(35) 

    def _animate_click(self):
        self._click_step += 1
        is_on = self.isChecked()
        
        if is_on:
            frames = [
                f"   [-]   {self.base_text}",
                f"  [ x ]  {self.base_text}",
                f" [  X  ] {self.base_text}",
                f"  [ X ]  {self.base_text}",
                f"   [X]   {self.base_text}"
            ]
        else:
            frames = [
                f"   [x]   {self.base_text}",
                f"  [ - ]  {self.base_text}",
                f" [     ] {self.base_text}",
                f"  [   ]  {self.base_text}",
                f"   [ ]   {self.base_text}"
            ]
            
        if self._click_step <= len(frames):
            QtWidgets.QPushButton.setText(self, frames[self._click_step - 1])
        else:
            self._click_timer.stop()
            self.end_flash()
            self._set_final_text()


class CyberLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setReadOnly(True)
        self._actual_text = ""
        self._anim_step = 0
        self._glitch_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*"
        
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._animate_text)
        
    def set_cyber_text(self, text):
        self._actual_text = text
        self._anim_step = 0
        self.setProperty("flashing", True)
        self.style().unpolish(self)
        self.style().polish(self)
        self._anim_timer.start(40) 
        
    def _animate_text(self):
        self._anim_step += 1
        if self._anim_step > 8:
            self._anim_timer.stop()
            self.setText(self._actual_text)
            self.setProperty("flashing", False)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            length = len(self._actual_text) if self._actual_text else 8
            glitched = "".join(random.choice(self._glitch_chars) for _ in range(length))
            self.setText(glitched)


class CyberComboBox(QtWidgets.QComboBox):
    """Custom combo box with an animated dropdown menu."""
    def showPopup(self):
        super().showPopup()
        popup = self.view().window()
        target_h = popup.geometry().height()
        
        self._popup_anim = QtCore.QPropertyAnimation(popup, b"maximumHeight")
        self._popup_anim.setDuration(200)
        self._popup_anim.setStartValue(0)
        self._popup_anim.setEndValue(target_h)
        self._popup_anim.setEasingCurve(QtCore.QEasingCurve.OutQuart)
        
        # Reset maximum height constraint so it doesn't break future usage
        try: self._popup_anim.finished.disconnect() 
        except Exception: pass
        self._popup_anim.finished.connect(lambda: popup.setMaximumHeight(16777215))
        
        self._popup_anim.start()


class PanelHeaderButton(CyberButton):
    def trigger_flash(self):
        pass
        
    def sizeHint(self):
        hint = QtWidgets.QPushButton.sizeHint(self)
        return QtCore.QSize(hint.width() + 6, hint.height())


class CyberPanel(QtWidgets.QWidget):
    def __init__(self, title, border_color="rgba(0, 243, 255, 0.15)"):
        super().__init__()
        self.border_color = border_color
        self.lay = QtWidgets.QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)

        self.title_base = title
        zws = "\u200B"
        self.header = PanelHeaderButton(f"{title}    [-]  {zws}")
        self.header.setObjectName("GroupLabel")
        self.header.clicked.connect(self.toggle)

        self.content = QtWidgets.QFrame()
        self.content.setObjectName("HudPanel")
        
        self._apply_base_style()
        
        self._opacity_eff = QtWidgets.QGraphicsOpacityEffect(self.content)
        self._opacity_eff.setOpacity(1.0)
        self.content.setGraphicsEffect(self._opacity_eff)
        
        self.content_lay = QtWidgets.QVBoxLayout(self.content)
        self.content_lay.setContentsMargins(6, 6, 6, 6)
        self.content_lay.setSpacing(4)

        self.lay.addWidget(self.header)
        self.lay.addWidget(self.content)

        self.is_collapsed = False
        
        # UI Animation Timers
        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._animate_brackets)
        self._anim_step = 0
        self._anim_frames = []

        self._flicker_timer = QtCore.QTimer(self)
        self._flicker_timer.timeout.connect(self._flicker_tick)
        self._flicker_step = 0

        self._h_anim = QtCore.QPropertyAnimation(self.content, b"maximumHeight")
        self._h_anim.setDuration(150)
        self._h_anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        self._h_anim.valueChanged.connect(self._on_height_change)
        
        self._o_anim = QtCore.QPropertyAnimation(self._opacity_eff, b"opacity")
        self._o_anim.setDuration(100) 
        self._o_anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

    def _apply_base_style(self):
        self.content.setStyleSheet(f"""
            QFrame#HudPanel {{
                border: 1px solid rgba(0, 243, 255, 0.15);
                border-left: 2px solid {self.border_color};
                background: rgba(10, 12, 18, 0.9);
            }}
        """)

    def _on_height_change(self, value):
        win = self.window()
        if hasattr(win, "optimize_space"):
            win.optimize_space()

    def update_title(self, new_title):
        self.title_base = new_title
        zws = "\u200B"
        if self.is_collapsed:
            self.header.setText(f"{self.title_base}    [+]  {zws}")
        else:
            self.header.setText(f"{self.title_base}    [-]  {zws}")

    def toggle(self):
        zws = "\u200B"
        try: self._h_anim.finished.disconnect()
        except Exception: pass

        if self.is_collapsed:
            # --- EXPANDING ---
            self._flicker_timer.stop()
            self.content.setVisible(True)
            self._apply_base_style()
            self.is_collapsed = False
            
            target_h = self.content.sizeHint().height()
            self._h_anim.setStartValue(0)
            self._h_anim.setEndValue(target_h)
            self._h_anim.finished.connect(lambda: self.content.setMaximumHeight(16777215))
            self._h_anim.start()
            
            self._anim_frames = [
                f"{self.title_base}   [ + ] {zws}",
                f"{self.title_base}  [  +  ]{zws}",
                f"{self.title_base}  [     ]{zws}",
                f"{self.title_base}  [  -  ]{zws}",
                f"{self.title_base}   [ - ] {zws}",
                f"{self.title_base}    [-]  {zws}"
            ]
            self._anim_step = 0
            self._anim_timer.start(35) 
            
            self._flash_type = "green"
            self._flicker_step = 0
            self._flicker_max = 8 
            self._flicker_timer.setInterval(40)
            self._flicker_timer.start()
        else:
            # --- COLLAPSING ---
            self.is_collapsed = True
            
            self._anim_frames = [
                f"{self.title_base}   [ - ] {zws}",
                f"{self.title_base}  [  -  ]{zws}",
                f"{self.title_base}  [     ]{zws}",
                f"{self.title_base}  [  +  ]{zws}",
                f"{self.title_base}   [ + ] {zws}",
                f"{self.title_base}    [+]  {zws}"
            ]
            self._anim_step = 0
            self._anim_timer.start(35) 
            
            self._flash_type = "red"
            self._flicker_step = 0
            self._flicker_max = 6 
            self._flicker_timer.setInterval(20)
            self._flicker_timer.start()

    def _flicker_tick(self):
        self._flicker_step += 1
        buttons = self.content.findChildren(QtWidgets.QPushButton)
        
        if self._flicker_step <= self._flicker_max:
            progress = self._flicker_step / float(self._flicker_max)
            
            if self._flash_type == "red":
                if random.random() > 0.4:
                    fade_op = random.uniform(0.0, 0.2) 
                else:
                    fade_op = random.uniform(0.5, 0.9) * (1.0 - progress)
                self._opacity_eff.setOpacity(fade_op)
                
                if random.random() > 0.4:
                    self.content.setStyleSheet("""
                        QFrame#HudPanel { 
                            border: 1px solid rgba(255, 68, 68, 0.8); 
                            border-left: 4px solid #ff4444; 
                            background: rgba(40, 10, 10, 0.9); 
                        }
                    """)
                else:
                    self._apply_base_style()
                
                self._flicker_timer.setInterval(random.randint(15, 50)) 
            else:
                surge_op = progress * random.uniform(0.8, 1.0)
                self._opacity_eff.setOpacity(surge_op)
                self._flicker_timer.setInterval(random.randint(20, 60)) 
            
            for btn in buttons:
                if not hasattr(btn, "_glitch_orig_text"):
                    btn._glitch_orig_text = btn.text()
                    
                if random.random() > 0.4: 
                    if self._flash_type == "green" and progress > 0.8:
                        btn.setProperty("flash_color", "white")
                    else:
                        btn.setProperty("flash_color", self._flash_type)
                        
                    if random.random() > 0.4:
                        chevs = [">>> <<<", ">> <<", " > < ", "xXx", "---"]
                        QtWidgets.QPushButton.setText(btn, f"\u200B{random.choice(chevs)}\u200B")
                else:
                    btn.setProperty("flash_color", "")
                    QtWidgets.QPushButton.setText(btn, btn._glitch_orig_text)
                    
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                
        else:
            self._flicker_timer.stop()
            
            for btn in buttons:
                btn.setProperty("flash_color", "")
                if hasattr(btn, "_glitch_orig_text"):
                    QtWidgets.QPushButton.setText(btn, btn._glitch_orig_text)
                    del btn._glitch_orig_text
                btn.style().unpolish(btn)
                btn.style().polish(btn)
            
            if self._flash_type == "red":
                self.content.setStyleSheet("""
                    QFrame#HudPanel { 
                        border: 1px solid rgba(255, 68, 68, 0.8); 
                        border-left: 4px solid #ff4444; 
                        background: rgba(30, 5, 5, 0.9); 
                    }
                """)
                current_h = self.content.height()
                self.content.setMaximumHeight(current_h)
                self._h_anim.setStartValue(current_h)
                self._h_anim.setEndValue(0)
                self._h_anim.finished.connect(lambda: self.content.setVisible(False))
                
                self._o_anim.setStartValue(self._opacity_eff.opacity())
                self._o_anim.setEndValue(0.0)
                
                self._h_anim.start()
                self._o_anim.start()
            else:
                self._opacity_eff.setOpacity(1.0)
                self._apply_base_style()

    def _animate_brackets(self):
        if self._anim_step < len(self._anim_frames):
            self.header.setText(self._anim_frames[self._anim_step])
            self._anim_step += 1
        else:
            self._anim_timer.stop()


class XYZDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, QtGui.QColor(0, 243, 255, 40))
        else:
            painter.fillRect(option.rect, QtGui.QColor(10, 12, 18))
            
        text = index.data()
        fm = painter.fontMetrics()
        width_func = fm.horizontalAdvance if hasattr(fm, "horizontalAdvance") else fm.width
        
        x_offset = option.rect.left() + 6
        y_offset = option.rect.top() + (option.rect.height() - fm.height()) // 2 + fm.ascent()
        
        for char in text:
            if char == 'X': painter.setPen(QtGui.QColor("#ff5555"))
            elif char == 'Y': painter.setPen(QtGui.QColor("#55ff55"))
            elif char == 'Z': painter.setPen(QtGui.QColor("#55aaff"))
            else: painter.setPen(QtGui.QColor("#e0e7ff"))
            painter.drawText(x_offset, y_offset, char)
            x_offset += width_func(char)
        painter.restore()


# ==============================================================================
# MAIN DASHBOARD UI
# ==============================================================================

class SpaceSwitchDashboard(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.logic = SpaceSwitcher()
        self.preview_loc = None
        
        self.settings = {
            "mode": "World", "translate": True, "rotate": True, "auto_detect": False, "rot_order": 0,
            "scale": 1.5, "offsets": 2, "hide_offset": True, "color": "yellow", "add_layer": False,
            "sample_by": 1, "euler": True, "clean_static": True, "threshold": 0.001,
            "bake_master": False, "bake_master_anim": False, "bake_offset_anim": False
        }
        
        self.setup_ui()
        self.populate_initial()

    def setup_ui(self):
        def make_lbl(text):
            lbl = QtWidgets.QLabel(text)
            lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-weight: bold;")
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setMinimumWidth(50) # Reduced minimum width to save horizontal space
            return lbl

        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumWidth(500) # Expanded minimum width to force the window wide enough for all 5 mode buttons
        self.resize(500, 750) # Set a wider, more natural starting portrait ratio
        self.setStyleSheet(QSS)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_lay = QtWidgets.QVBoxLayout(central)
        main_lay.setContentsMargins(10, 10, 10, 10)
        main_lay.setSpacing(6)

        # --- GLITCH HEADER ---
        header_lay = QtWidgets.QHBoxLayout()
        title_lbl = QtWidgets.QLabel("SPACE.SWITCH")
        title_lbl.setStyleSheet("color: white; font-size: 22px; font-weight: bold; letter-spacing: -1px;")
        ver_lbl = QtWidgets.QLabel("V1.0_CORE")
        ver_lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 8px;")
        header_lay.addWidget(title_lbl)
        header_lay.addStretch()
        header_lay.addWidget(ver_lbl, alignment=QtCore.Qt.AlignBottom)
        main_lay.addLayout(header_lay)
        
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("background: rgba(255,255,255,0.1); max-height: 1px; margin-bottom: 5px;")
        main_lay.addWidget(sep)

        # --- SCROLL AREA ---
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        
        # Absolutely ban horizontal scrolling to force components to fit the window
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        self.scroll_content = QtWidgets.QWidget()
        # Force a minimum internal width so elements never get squished, 
        # compelling the main window to adapt to this size
        self.scroll_content.setMinimumWidth(470) 
        
        self.scroll_lay = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_lay.setContentsMargins(0, 0, 0, 0)
        self.scroll_lay.setSpacing(4)
        self.scroll.setWidget(self.scroll_content)
        main_lay.addWidget(self.scroll)

        # --- 1. SELECTION PANEL ---
        p_sel = CyberPanel("SELECTION", border_color="rgba(0, 243, 255, 0.5)")
        self.scroll_lay.addWidget(p_sel)
        
        s_grid = QtWidgets.QGridLayout()
        s_grid.setContentsMargins(0, 0, 0, 0)
        s_grid.setSpacing(4)
        
        self.ui_source = CyberLineEdit()
        self.ui_source.setObjectName("SourceInput")
        self.ui_source.setPlaceholderText("...")
        s_btn = CyberButton("PICK")
        s_btn.setFixedWidth(45)
        s_btn.clicked.connect(lambda *args: self.pick_object("source"))
        
        s_grid.addWidget(make_lbl("SOURCE:"), 0, 0)
        s_grid.addWidget(self.ui_source, 0, 1)
        s_grid.addWidget(s_btn, 0, 2)

        self.ui_target = CyberLineEdit()
        self.ui_target.setObjectName("TargetInput")
        self.ui_target.setPlaceholderText("...")
        t_btn = CyberButton("PICK")
        t_btn.setFixedWidth(45)
        t_btn.clicked.connect(lambda *args: self.pick_object("target"))
        
        s_grid.addWidget(make_lbl("TARGET:"), 1, 0)
        s_grid.addWidget(self.ui_target, 1, 1)
        s_grid.addWidget(t_btn, 1, 2)
        
        p_sel.content_lay.addLayout(s_grid)

        # --- 2. SPACE MODE ---
        self.p_mode = CyberPanel("SPACE MODE // WORLD".ljust(22, "\xA0"))
        self.scroll_lay.addWidget(self.p_mode)

        mode_grp = QtWidgets.QHBoxLayout()
        mode_grp.setSpacing(2)
        self.mode_btns = QtWidgets.QButtonGroup(self)
        
        for i, m in enumerate(["World", "Local", "Object", "Camera", "Aim"]):
            b = CyberButton(m)
            b.setObjectName("ModeBtn")
            b.setCheckable(True)
            self.mode_btns.addButton(b, i)
            
            if i == 0:
                b.setChecked(True)
            
            b.clicked.connect(lambda *args, txt=m: self.set_space_mode(txt))
            mode_grp.addWidget(b)
            
        self.p_mode.content_lay.addLayout(mode_grp)

        tgl_lay = QtWidgets.QHBoxLayout()
        self.ui_trans = CyberToggle("TRANSLATION", checked=True)
        self.ui_trans.toggled.connect(lambda x: self.update_s("translate", x))
        self.ui_rot = CyberToggle("ROTATION", checked=True)
        self.ui_rot.toggled.connect(lambda x: self.update_s("rotate", x))
        tgl_lay.addWidget(self.ui_trans); tgl_lay.addWidget(self.ui_rot)
        self.p_mode.content_lay.addLayout(tgl_lay)

        rot_lay = QtWidgets.QHBoxLayout()
        rot_lay.addWidget(make_lbl("ROT_ORDER"))
        
        self.ui_rot_order = CyberComboBox()
        self.ui_rot_order.addItems(["XYZ", "YZX", "ZXY", "XZY", "YXZ", "ZYX"])
        self.ui_rot_order.setItemDelegate(XYZDelegate(self.ui_rot_order))
        
        rot_container = QtWidgets.QWidget()
        r_grid = QtWidgets.QGridLayout(rot_container)
        r_grid.setContentsMargins(0,0,0,0)
        self.ui_rot_order.setStyleSheet("QComboBox { color: transparent; }") 
        self.ui_rot_overlay = QtWidgets.QLabel()
        self.ui_rot_overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.ui_rot_overlay.setStyleSheet("background: transparent; border: none; padding-left: 5px;")
        
        r_grid.addWidget(self.ui_rot_order, 0, 0)
        r_grid.addWidget(self.ui_rot_overlay, 0, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        
        # Setup Flash Timer
        self._rot_flash_timer = QtCore.QTimer(self)
        self._rot_flash_timer.timeout.connect(self._rot_flash_tick)
        self._rot_flash_step = 0
        self._rot_target_text = ""
        
        self.ui_rot_order.currentIndexChanged.connect(self.trigger_rot_flash)
        self.trigger_rot_flash(0, initial=True)
        
        self.ui_auto_det = CyberToggle("AUTO_DETECT", checked=False)
        self.ui_auto_det.toggled.connect(self.toggle_auto_detect)
        
        rot_lay.addWidget(rot_container)
        rot_lay.addWidget(self.ui_auto_det)
        self.p_mode.content_lay.addLayout(rot_lay)

        # --- 3. LOCATOR SETTINGS ---
        p_loc = CyberPanel("LOCATOR_SYS")
        self.scroll_lay.addWidget(p_loc)
        
        btn_prev = CyberButton("[ CREATE PREVIEW LOCATOR ]")
        btn_prev.setStyleSheet("border-color: #55ff55; color: #55ff55;")
        btn_prev.clicked.connect(self.create_preview)
        p_loc.content_lay.addWidget(btn_prev)

        scale_lay = QtWidgets.QHBoxLayout()
        scale_lay.addWidget(make_lbl("SCALE"))
        btn_minus = CyberButton("-"); btn_minus.setFixedWidth(24); btn_minus.clicked.connect(lambda *args: self.adj_scale(-0.25))
        btn_plus = CyberButton("+"); btn_plus.setFixedWidth(24); btn_plus.clicked.connect(lambda *args: self.adj_scale(0.25))
        self.ui_scale = QtWidgets.QDoubleSpinBox()
        self.ui_scale.setValue(1.5); self.ui_scale.setSingleStep(0.1); self.ui_scale.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.ui_scale.valueChanged.connect(lambda x: self.update_s("scale", x))
        
        scale_lay.addWidget(btn_minus); scale_lay.addWidget(btn_plus); scale_lay.addWidget(self.ui_scale)
        scale_lay.addSpacing(10)
        
        scale_lay.addWidget(make_lbl("OFFSETS"))
        self.ui_offsets = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.ui_offsets.setRange(0, 5); self.ui_offsets.setValue(2)
        self.ui_offsets_lbl = QtWidgets.QLabel("2", styleSheet="color: #ff00ea; font-weight: bold; width: 15px;")
        self.ui_offsets.valueChanged.connect(self.sync_offsets)
        scale_lay.addWidget(self.ui_offsets)
        scale_lay.addWidget(self.ui_offsets_lbl)
        p_loc.content_lay.addLayout(scale_lay)

        color_lay = QtWidgets.QHBoxLayout()
        color_lay.addWidget(make_lbl("COLOR"))
        self.color_btns = {}
        for name, hex_val in UI_COLORS.items():
            cb = CyberButton()
            cb.setFixedSize(22, 16)
            cb.setStyleSheet(f"background: {hex_val}; border: none; opacity: 0.5;")
            cb.clicked.connect(lambda *args, n=name: self.set_color(n))
            self.color_btns[name] = cb
            color_lay.addWidget(cb)
        p_loc.content_lay.addLayout(color_lay)
        self.set_color("yellow") 

        loc_tgl_lay = QtWidgets.QHBoxLayout()
        self.ui_hide_off = CyberToggle("HIDE_OFFSETS", checked=True)
        self.ui_hide_off.toggled.connect(lambda x: self.update_s("hide_offset", x))
        self.ui_add_lyr = CyberToggle("ADD_TO_LAYER", checked=False)
        self.ui_add_lyr.toggled.connect(lambda x: self.update_s("add_layer", x))
        loc_tgl_lay.addWidget(self.ui_hide_off); loc_tgl_lay.addWidget(self.ui_add_lyr)
        p_loc.content_lay.addLayout(loc_tgl_lay)

        # --- 4. BAKE PARAMS ---
        p_bake = CyberPanel("BAKE_PARAMS", border_color="rgba(255, 0, 234, 0.5)")
        self.scroll_lay.addWidget(p_bake)

        bake_grid = QtWidgets.QGridLayout()
        bake_grid.setContentsMargins(0, 0, 0, 0)
        bake_grid.setSpacing(4)

        bake_grid.addWidget(make_lbl("SAMPLE"), 0, 0)
        self.ui_sample = CyberComboBox()
        self.ui_sample.addItems(["1", "2", "3"])
        self.ui_sample.currentIndexChanged.connect(lambda *args: self.update_s("sample_by", int(self.ui_sample.currentText())))
        bake_grid.addWidget(self.ui_sample, 0, 1)

        self.ui_euler = CyberToggle("EULER_FILTER", checked=True)
        self.ui_euler.toggled.connect(lambda x: self.update_s("euler", x))
        bake_grid.addWidget(self.ui_euler, 0, 2)

        bake_grid.addWidget(make_lbl("THRESH"), 1, 0)
        self.ui_thresh = QtWidgets.QDoubleSpinBox()
        self.ui_thresh.setDecimals(3); self.ui_thresh.setSingleStep(0.001); self.ui_thresh.setValue(0.001)
        self.ui_thresh.valueChanged.connect(lambda x: self.update_s("threshold", x))
        bake_grid.addWidget(self.ui_thresh, 1, 1)

        self.ui_clean = CyberToggle("CLEAN_STATIC", checked=True)
        self.ui_clean.toggled.connect(lambda x: self.update_s("clean_static", x))
        bake_grid.addWidget(self.ui_clean, 1, 2)

        self.ui_bake_master = CyberToggle("BAKE_MASTER_SPACE", checked=False)
        self.ui_bake_master.toggled.connect(lambda x: self.update_s("bake_master", x))
        bake_grid.addWidget(self.ui_bake_master, 2, 0, 1, 3)

        p_bake.content_lay.addLayout(bake_grid)

        # --- 5. EXECUTION ---
        p_exec = CyberPanel("EXECUTION_HOLDER")
        self.scroll_lay.addWidget(p_exec)

        e1_lay = QtWidgets.QHBoxLayout()
        self.ui_stage = CyberComboBox()
        self.ui_stage.addItems(["STAGE 1: Create Setup", "STAGE 2: Constrain & Bake"])
        e_run = CyberButton("RUN")
        e_run.clicked.connect(self.run_full_action)
        e1_lay.addWidget(self.ui_stage); e1_lay.addWidget(e_run)
        p_exec.content_lay.addLayout(e1_lay)

        self.btn_full = CyberProgressButton("[ RUN FULL SPACE SWITCH ]")
        self.btn_full.setObjectName("ActionPrimary")
        self.btn_full.set_progress_colors("#00f3ff", "#00f3ff", "#05060a")
        self.btn_full.clicked.connect(self.run_full_action)
        p_exec.content_lay.addWidget(self.btn_full)

        self.btn_down = CyberProgressButton("[ BAKE SOURCES DOWN ]")
        self.btn_down.setObjectName("ActionOrange")
        self.btn_down.set_progress_colors("#f6a226", "#f6a226", "#05060a")
        self.btn_down.clicked.connect(self.bake_sources_down)
        p_exec.content_lay.addWidget(self.btn_down)

        clean_lay = QtWidgets.QHBoxLayout()
        btn_sel = CyberButton("SELECT LOCATORS")
        btn_sel.clicked.connect(self.select_locators)
        btn_del = CyberButton("DELETE ALL")
        btn_del.setObjectName("Danger")
        btn_del.clicked.connect(self.logic.cleanup)
        clean_lay.addWidget(btn_sel); clean_lay.addWidget(btn_del)
        p_exec.content_lay.addLayout(clean_lay)
        
        self.scroll_lay.addStretch()

    # --- UI Dynamic Sizing Logic ---
    def optimize_space(self):
        content_h = self.scroll_content.sizeHint().height()
        
        if content_h < 850:
            self.scroll.setMinimumHeight(content_h)
            self.scroll.setMaximumHeight(content_h)
            self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        else:
            self.scroll.setMinimumHeight(200) 
            self.scroll.setMaximumHeight(850)
            self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            
        # Dynamically scale both height AND width to naturally frame the content
        target_h = self.centralWidget().sizeHint().height()
        target_w = self.centralWidget().sizeHint().width()
        
        # Added +20 padding buffer to the target width calculation to ensure borders don't crowd
        current_w = max(self.width(), target_w + 20, 500)
        self.resize(current_w, target_h)

    # --- UI Logic Methods ---
    def populate_initial(self):
        sel = cmds.ls(selection=True)
        if sel:
            self.ui_source.set_cyber_text(", ".join(sel))

    def update_s(self, key, value):
        self.settings[key] = value
        
    def set_space_mode(self, mode_str):
        self.update_s("mode", mode_str)
        
        padded_title = f"SPACE MODE // {mode_str.upper()}".ljust(22, "\xA0")
        self.p_mode.update_title(padded_title)
        
        for btn in self.mode_btns.buttons():
            is_active = btn.isChecked()
            anim = btn._opacity_anim
            anim.stop()
            anim.setStartValue(btn.effect.opacity())
            anim.setEndValue(1.0 if is_active else 0.3)
            anim.start()

    def trigger_rot_flash(self, idx=0, initial=False):
        self.settings["rot_order"] = self.ui_rot_order.currentIndex()
        self._rot_target_text = self.ui_rot_order.currentText()
        
        if initial:
            self._rot_flash_step = 10 
            self._rot_flash_tick()
        else:
            self._rot_flash_step = 0
            self._rot_flash_timer.start(40) # Rapid strobe
            
    def _rot_flash_tick(self):
        self._rot_flash_step += 1
        html = ""
        
        if self._rot_flash_step <= 6:
            # Flashing Sequence
            is_white = (self._rot_flash_step % 2 == 1)
            for char in self._rot_target_text:
                if char == 'X':
                    color = "#ffffff" if is_white else "#ff5555"
                    html += f"<span style='color:{color};'>X</span>"
                elif char == 'Y':
                    color = "#ffffff" if is_white else "#55ff55"
                    html += f"<span style='color:{color};'>Y</span>"
                elif char == 'Z':
                    color = "#ffffff" if is_white else "#55aaff"
                    html += f"<span style='color:{color};'>Z</span>"
                else:
                    html += char
        else:
            # Settle Sequence
            self._rot_flash_timer.stop()
            for char in self._rot_target_text:
                if char == 'X': html += "<span style='color:#ff5555;'>X</span>"
                elif char == 'Y': html += "<span style='color:#55ff55;'>Y</span>"
                elif char == 'Z': html += "<span style='color:#55aaff;'>Z</span>"
                else: html += char
                
        self.ui_rot_overlay.setText(html)

    def toggle_auto_detect(self, val):
        self.settings["auto_detect"] = val
        self.ui_rot_order.setEnabled(not val)
        opacity = "0.5" if val else "1.0"
        self.ui_rot_overlay.setStyleSheet(f"background: transparent; border: none; padding-left: 5px; opacity: {opacity};")

    def adj_scale(self, delta):
        val = max(0.1, self.ui_scale.value() + delta)
        self.ui_scale.setValue(val)

    def sync_offsets(self, val):
        self.ui_offsets_lbl.setText(str(val))
        self.settings["offsets"] = val

    def set_color(self, name): 
        self.settings["color"] = name
        for n, btn in self.color_btns.items():
            if n == name:
                btn.setStyleSheet(f"background: {UI_COLORS[n]}; border: 1px solid white; opacity: 1.0;")
            else:
                btn.setStyleSheet(f"background: {UI_COLORS[n]}; border: none; opacity: 0.3;")

        if self.preview_loc and cmds.objExists(self.preview_loc):
            shape = cmds.listRelatives(self.preview_loc, shapes=True)[0]
            cmds.setAttr(f"{shape}.overrideColor", LOCATOR_COLORS[name])

    def pick_object(self, target_fld):
        sel = cmds.ls(selection=True)
        text_val = ", ".join(sel) if sel else ""
        if target_fld == "source":
            self.ui_source.set_cyber_text(text_val)
        else:
            self.ui_target.set_cyber_text(sel[0] if sel else "")

    def create_preview(self):
        if self.preview_loc and cmds.objExists(self.preview_loc):
            cmds.delete(self.preview_loc)
            
        self.preview_loc = cmds.spaceLocator(n="SS_Preview_Loc")[0]
        s = self.settings["scale"]
        cmds.setAttr(f"{self.preview_loc}.localScale", s, s, s)
        
        shape = cmds.listRelatives(self.preview_loc, shapes=True)[0]
        cmds.setAttr(f"{shape}.overrideEnabled", 1)
        cmds.setAttr(f"{shape}.overrideColor", LOCATOR_COLORS[self.settings["color"]])
        
        src_text = self.ui_source.text()
        if src_text and cmds.objExists(src_text.split(", ")[0]):
            cmds.matchTransform(self.preview_loc, src_text.split(", ")[0], pos=True, rot=True)

    def select_locators(self):
        nodes = cmds.ls(f"*{LOCATOR_SUFFIX}", f"*{OFFSET_SUFFIX}*", "*_Master_Space")
        if nodes:
            cmds.select(nodes)
        else:
            cmds.warning("No Space Switch Locators found to select.")

    # --- Core Actions ---
    def run_full_action(self):
        src_str = self.ui_source.text()
        trg_str = self.ui_target.text()
        
        if not src_str:
            cmds.warning("Please pick a Source object first!")
            return
            
        sources = src_str.split(", ")
        start = cmds.playbackOptions(q=True, min=True)
        end = cmds.playbackOptions(q=True, max=True)
        
        self.btn_full.start_progress()
        
        for i, src in enumerate(sources):
            if not cmds.objExists(src): continue
            
            base_p = float(i) / len(sources)
            step = 1.0 / len(sources)
            
            short_src = src.split(':')[-1]
            
            self.btn_full.set_progress_blocking(base_p + step * 0.1, f"ANALYZING: {short_src}")
            if self.settings["auto_detect"]:
                best_order = self.logic.get_best_rotation_order(src, start, end)
            else:
                best_order = self.settings["rot_order"]
            cmds.setAttr(f"{src}.rotateOrder", best_order)
            
            self.btn_full.set_progress_blocking(base_p + step * 0.3, f"BUILDING SETUP: {short_src}")
            master, main_loc = self.logic.build_locator_setup(src, trg_str, self.settings)
            
            if self.settings["mode"] == "Object" and trg_str and cmds.objExists(trg_str):
                cmds.parentConstraint(trg_str, master, mo=True)
            
            cmds.parentConstraint(src, main_loc, mo=False)
            
            self.btn_full.set_progress_blocking(base_p + step * 0.7, f"BAKING: {short_src}")
            cmds.bakeResults(main_loc, t=(start, end), simulation=True, sampleBy=self.settings["sample_by"])
            cmds.delete(main_loc, constraints=True)
            
            self.btn_full.set_progress_blocking(base_p + step * 0.9, f"CLEANING: {short_src}")
            if self.settings["euler"]: cmds.filterCurve(f"{main_loc}_*")
            if self.settings["clean_static"]: self.logic.clean_static_keys([main_loc], self.settings["threshold"])

            cmds.parentConstraint(main_loc, src, mo=False)
            
        self.btn_full.set_progress_blocking(1.0, "SYS.COMPLETE")
        cmds.inViewMessage(amg="SPACE.SWITCH // SETUP COMPLETE", pos='midCenter', fade=True)
        QtCore.QTimer.singleShot(800, self.btn_full.stop_progress)

    def bake_sources_down(self):
        src_str = self.ui_source.text()
        if not src_str: 
            cmds.warning("No sources to bake down.")
            return
        
        sources = [s for s in src_str.split(", ") if cmds.objExists(s)]
        if not sources: return
        
        start = cmds.playbackOptions(q=True, min=True)
        end = cmds.playbackOptions(q=True, max=True)
        
        self.btn_down.start_progress()
        
        self.btn_down.set_progress_blocking(0.2, "PREPARING SOURCES...")
        self.btn_down.set_progress_blocking(0.5, "BAKING ANIMATIONS...")
        
        cmds.bakeResults(sources, t=(start, end), simulation=True, sampleBy=self.settings["sample_by"])
        
        self.btn_down.set_progress_blocking(0.7, "APPLYING FILTERS...")
        if self.settings["euler"]:
            for s in sources: cmds.filterCurve(f"{s}_*")
        if self.settings["clean_static"]:
            self.logic.clean_static_keys(sources, self.settings["threshold"])
            
        self.btn_down.set_progress_blocking(0.9, "CLEANING RIG DATA...")
        self.logic.cleanup()
        
        self.btn_down.set_progress_blocking(1.0, "BAKE.DOWN COMPLETE")
        cmds.inViewMessage(amg="SPACE.SWITCH // BAKED & CLEANED", pos='midCenter', fade=True)
        QtCore.QTimer.singleShot(800, self.btn_down.stop_progress)


# ==============================================================================
# ENTRY POINT
# ==============================================================================
_ss_window = None

def show():
    global _ss_window
    if _ss_window is not None:
        try:
            _ss_window.close()
            _ss_window.deleteLater()
        except Exception:
            pass
            
    _ss_window = SpaceSwitchDashboard()
    QtCore.QTimer.singleShot(0, _ss_window.optimize_space)
    _ss_window.show()

if __name__ == "__main__":
    show()