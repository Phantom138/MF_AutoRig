# -*- coding: utf-8 -*-

from __future__ import absolute_import
try:
    from PySide2 import QtCore, QtWidgets, QtGui
    from PySide2.QtCore import Signal, Property
except ImportError:
    from PySide import QtCore, QtGui
    from PySide import QtGui as QtWidgets
    from PySide.QtCore import Signal, Property


from ks_saveTimer.lib import timer, config


class saveTimer_widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(saveTimer_widget, self).__init__(parent=parent)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self._MUTED = False
        self._CONFIG_ = config.configuration()
        self.TIMER = timer.timerObject(self)

        self.TIMER_WIDGET = counterWidget(self)
        layout.addWidget(self.TIMER_WIDGET)

        self.build_contextMenu()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.ContextMenuEvent)

        self.TIMER.tick.connect(lambda counter, idleState: self.refreshTimer(counter, idleState))
        self.TIMER.timerStop.connect(self._timer_stop)
        self.TIMER.timerReset.connect(lambda:self.anim_action_run('reset'))
        self.TIMER.fileSaved.connect(lambda:self.anim_action_run('save'))

        self.ANIM_FLASH = self.anim_flash_build()
        self.ANIM_SAVE = self.anim_saved_build()
        self.ANIM_RESET = self.anim_reset_build()

        self._CONFIG_.configUpdated.connect(self.updatedSettings)

        self.TIMER.start()

        self._MUTED = False
        if self._CONFIG_.get('general', 'timer_automute', fallback=False):
            self.setMuteToggle(True)

        if self._CONFIG_.get('general', 'timer_autopause', fallback=False):
            self.setPauseToggle(True)

        self._timer_refresh(0)

    def build_contextMenu(self):
        self.contextMenu = QtWidgets.QMenu(self) #Parent is self, self is the root GUI

        self.menuAction_pause = action = QtWidgets.QAction('Paused', self.contextMenu, checkable=True)
        action.toggled.connect(lambda arg1:self.setPauseToggle(arg1))
        self.contextMenu.addAction(action)

        self.menuAction_mute = action = QtWidgets.QAction('Muted', self.contextMenu, checkable=True)
        action.toggled.connect(lambda arg1:self.setMuteToggle(arg1))
        self.contextMenu.addAction(action)

        self.contextMenu.addAction("Reset", self.TIMER.reset)


    def ContextMenuEvent(self, pos):
        self.contextMenu.exec_(self.mapToGlobal(pos))


    def setPauseToggle(self, state):
        if state == True:
            self.menuAction_pause.setChecked(True)
            self.TIMER.stop()
        else:
            self.menuAction_pause.setChecked(False)
            self.TIMER.start()


    def setMuteToggle(self, state):
        if state == True:
            self._MUTED = True
            self.menuAction_mute.setChecked(True)
            if self.ANIM_FLASH.state():
                self.anim_flash_stop()
            self.TIMER_WIDGET._set_color_bg(self._CONFIG_._DICT_['timerOptions']['timer_pause_bgcolor'])
            self.TIMER_WIDGET._set_color_text(self._CONFIG_._DICT_['timerOptions']['timer_pause_textcolor'])

        else:
            self._MUTED = False
            self.menuAction_mute.setChecked(False)
            self.refreshTimer(idleState=False)


    def updatedSettings(self, *args):
        #Force-update certain properties when configGUI is used.
        self.ANIM_FLASH.setStartValue(self._CONFIG_._DICT_['timerOptions']['timer_flash_b_bgcolor'])
        self.ANIM_FLASH.setKeyValueAt(0.1, self._CONFIG_._DICT_['timerOptions']['timer_flash_a_bgcolor'])
        self.ANIM_FLASH.setDuration(self._CONFIG_._DICT_['timerOptions']['timer_flash_freq'])
        if self.ANIM_FLASH.state():
            self.TIMER_WIDGET._set_color_text(self._CONFIG_._DICT_['timerOptions']['timer_flash_a_textcolor'])

        self.refreshTimer()

    def refreshTimer(self, counterValue=None, idleState=False):
        if idleState:
            if not counterValue:
                counterValue = self.TIMER.counterIdle
            self._timer_refresh_idle(counterValue)
        else:
            if not counterValue:
                counterValue = self.TIMER.counter
            self._timer_refresh(counterValue)

    def setCounterText(self, text):
        if self.TIMER.isActive() == False:
            self.TIMER_WIDGET.setText('| |')
        else:
            self.TIMER_WIDGET.setText(text)

    def _timer_stop(self):
        if self.ANIM_FLASH.state():
            self.anim_flash_stop()

        self.setCounterText(None)
        self.TIMER_WIDGET._set_color_bg(self._CONFIG_._DICT_['timerOptions']['timer_pause_bgcolor'])
        self.TIMER_WIDGET._set_color_text(self._CONFIG_._DICT_['timerOptions']['timer_pause_textcolor'])


    def _timer_refresh_idle(self, counterValue):
        self.setCounterText('(%s)'%(str(counterValue)))

        if self.ANIM_FLASH.state():
            self.anim_flash_stop()

        self.TIMER_WIDGET._set_color_bg(self._CONFIG_._DICT_['timerOptions']['timer_pause_bgcolor'])
        self.TIMER_WIDGET._set_color_text(self._CONFIG_._DICT_['timerOptions']['timer_pause_textcolor'])

    def _timer_refresh(self, counterValue):
        self.setCounterText(str(counterValue))

        if self._MUTED is True:
            return

        # Timer is above Flash-threshold
        if self.TIMER.counter >= self._CONFIG_._DICT_['timerOptions']['timer_flash_starttime']:
            if self.ANIM_FLASH.state():
                return
            else:
                self.TIMER_WIDGET._set_color_text(self._CONFIG_._DICT_['timerOptions']['timer_flash_a_textcolor'])
                self.ANIM_FLASH.start()
                return

        # Timer is below Flash-threshold
        if self.ANIM_FLASH.state():
            self.anim_flash_stop()

        if self.TIMER.counter >= self._CONFIG_._DICT_['timerOptions']['timer_c_starttime']:
            self.TIMER_WIDGET._set_color_bg(self._CONFIG_._DICT_['timerOptions']['timer_c_bgcolor'])
            self.TIMER_WIDGET._set_color_text(self._CONFIG_._DICT_['timerOptions']['timer_c_textcolor'])

        elif self.TIMER.counter >= self._CONFIG_._DICT_['timerOptions']['timer_b_starttime']:
            self.TIMER_WIDGET._set_color_bg(self._CONFIG_._DICT_['timerOptions']['timer_b_bgcolor'])
            self.TIMER_WIDGET._set_color_text(self._CONFIG_._DICT_['timerOptions']['timer_b_textcolor'])

        elif self.TIMER.counter >= self._CONFIG_._DICT_['timerOptions']['timer_a_starttime']:
            self.TIMER_WIDGET._set_color_bg(self._CONFIG_._DICT_['timerOptions']['timer_a_bgcolor'])
            self.TIMER_WIDGET._set_color_text(self._CONFIG_._DICT_['timerOptions']['timer_a_textcolor'])

        else:
            self.TIMER_WIDGET._set_color_bg(self._CONFIG_._DICT_['timerOptions']['timer_default_bgcolor'])
            self.TIMER_WIDGET._set_color_text(self._CONFIG_._DICT_['timerOptions']['timer_default_textcolor'])
            return

    def anim_flash_build(self):
        self.ANIM_FLASH = anim_flash_bg = QtCore.QPropertyAnimation(self.TIMER_WIDGET, b"color_bg")
        anim_flash_bg.setDuration(self._CONFIG_._DICT_['timerOptions']['timer_flash_freq'])
        anim_flash_bg.setLoopCount(-1)
        anim_flash_bg.setStartValue(self._CONFIG_._DICT_['timerOptions']['timer_flash_b_bgcolor'])
        anim_flash_bg.setKeyValueAt(0.1, self._CONFIG_._DICT_['timerOptions']['timer_flash_a_bgcolor'])
        anim_flash_bg.setEndValue(self._CONFIG_._DICT_['timerOptions']['timer_flash_b_bgcolor'])
        return anim_flash_bg

    def anim_flash_stop(self):
        self.ANIM_FLASH.stop()

    def anim_saved_build(self):
        self.anim_save_bg = anim_save_bg = QtCore.QPropertyAnimation(self.TIMER_WIDGET, b"color_bg")
        anim_save_bg.setDuration(1500)
        anim_save_bg.setLoopCount(1)
        color = self.TIMER_WIDGET.palette().color(QtGui.QPalette.Base)
        anim_save_bg.setStartValue(color)
        anim_save_bg.setKeyValueAt(0.2, QtGui.QColor(0, 220, 0))
        anim_save_bg.setEndValue(color)
        return self.anim_save_bg

    def anim_reset_build(self):
        self.anim_reset_bg = anim_reset_bg = QtCore.QPropertyAnimation(self.TIMER_WIDGET, b"color_bg")
        anim_reset_bg.setDuration(1000)
        anim_reset_bg.setLoopCount(1)
        color = self.TIMER_WIDGET.palette().color(QtGui.QPalette.Base)
        anim_reset_bg.setStartValue(color)
        anim_reset_bg.setEndValue(color)
        return self.anim_reset_bg


    def anim_action_run(self, action):
        if self._MUTED:
            self.refreshTimer()
            return

        currentColor = self.TIMER_WIDGET.getCurrentColor()

        self.TIMER.blockSignals(True)
        timerActive = self.TIMER.isActive()

        if timerActive:
            self.TIMER.stop()
            self.anim_reset_bg.setEndValue(self._CONFIG_._DICT_['timerOptions']['timer_default_bgcolor'])
            self.anim_save_bg.setEndValue(self._CONFIG_._DICT_['timerOptions']['timer_default_bgcolor'])
        else:
            self.anim_reset_bg.setEndValue(self._CONFIG_._DICT_['timerOptions']['timer_pause_bgcolor'])
            self.anim_save_bg.setEndValue(self._CONFIG_._DICT_['timerOptions']['timer_pause_bgcolor'])

        self.anim_reset_bg.setStartValue(currentColor)
        self.anim_save_bg.setStartValue(currentColor)

        if action == 'save':
            self.ANIM_SAVE.start()
        elif action == 'reset':
            self.ANIM_RESET.start()

        if timerActive:
            self.TIMER.start()
            self.refreshTimer()

        self.TIMER.blockSignals(False)





class counterWidget(QtWidgets.QWidget):
    _BRUSH_COL = QtGui.QBrush(QtGui.QColor(70, 70, 70))
    _PEN_COL = QtGui.QPen(QtGui.QColor(0, 0, 255))
    _PEN_FRAME_COL = QtGui.QPen(QtGui.QColor(0, 0, 0, 25))

    def __init__(self, parent=None):
        super(counterWidget, self).__init__(parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setMinimumSize(20, 20)

        self.rootLayout = QtWidgets.QGridLayout()
        self.rootLayout.setContentsMargins(2, 2, 2, 2)
        self.rootLayout.setSpacing(0)
        self.setLayout(self.rootLayout)

        self._DISPLAY_TEXT_ = '0'

        self.font = QtGui.QFont()
        self.font.setBold(False)
        self.font.setWeight(87)
        self.font.setPointSize(9)
        self.font.setFamily("Arial")
        self.font.setLetterSpacing(QtGui.QFont.PercentageSpacing, 113)

    def setText(self, text):
        self._DISPLAY_TEXT_ = str(text)
        self.update()

    def paintEvent(self, event):
        self.borderRadius = 5

        s = self.size()
        self.qp = QtGui.QPainter()
        self.qp.begin(self)
        self.qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.qp.setBrush(self._BRUSH_COL)
        self.qp.setPen(self._PEN_FRAME_COL)
        self.qp.drawRoundedRect(0, 0, s.width(), s.height(), self.borderRadius, self.borderRadius)
        self.qp.setPen(self._PEN_COL)
        self.qp.setFont(self.font)
        self.qp.drawText(QtCore.QRectF(0.0,0.0,s.width(),s.height()), QtCore.Qt.AlignCenter|QtCore.Qt.AlignTop, self._DISPLAY_TEXT_)
        self.qp.end()

    def _set_color_bg(self, col):
        self._BRUSH_COL.setColor(col)
        self.update()

    def _set_color_text(self, col):
        self._PEN_COL.setColor(col)
        self.update()

    def getCurrentColor(self):
        return self._BRUSH_COL.color()

    color_bg = Property(QtGui.QColor, fset=_set_color_bg)
    color_text = Property(QtGui.QColor, fset=_set_color_text)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = saveTimer_widget()
    win.show()
    sys.exit(app.exec_())