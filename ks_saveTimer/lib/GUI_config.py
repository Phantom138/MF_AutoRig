from __future__ import absolute_import
try:
    from PySide2 import QtCore, QtWidgets, QtGui
    from PySide2.QtCore import Signal
except ImportError:
    from PySide import QtCore, QtGui
    from PySide import QtGui as QtWidgets
    from PySide.QtCore import Signal

from ks_saveTimer.lib import timer, config

class saveTimer_config_GUI(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(saveTimer_config_GUI, self).__init__(parent=parent)
        self.setWindowTitle('KS_SaveTimer Config')
        self.setStyleSheet('QLabel#Header {color:Orange}')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self._CONFIG_ = config.configuration()

        self.TIMER = timer.timerObject(self)
        self._timerControlWidgets = {}

        self.rootLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.rootLayout)

        self.buildUI()
        self.parseConfig_all()

        self.setFixedSize(self.rootLayout.sizeHint())
        self.center()


    def center(self):
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def closeEvent(self, event):
        self._CONFIG_.readConfigs()   # To reset any unsaved changed made.
        self.parseConfig_all()

    def saveConfig(self):
        self._CONFIG_.writeConfig()
        self.close()


    def buildUI(self):

        self.font_header = QtGui.QFont()
        self.font_header.setPixelSize(20)
        self.font_header.setWeight(120)

        self.label_title = QtWidgets.QLabel('KS_SaveTimer')
        self.label_title.setObjectName('Header')
        self.label_title.setFont(self.font_header)
        self.label_title.setAlignment(QtCore.Qt.AlignCenter)
        self.rootLayout.addWidget(self.label_title)

        self.font_subHeader = QtGui.QFont()
        self.font_subHeader.setPixelSize(16)
        self.font_subHeader.setWeight(120)

        self.label_subTitle = QtWidgets.QLabel('Config')
        self.label_subTitle.setObjectName('Header')
        self.label_subTitle.setFont(self.font_subHeader)
        self.label_subTitle.setAlignment(QtCore.Qt.AlignCenter)
        self.rootLayout.addWidget(self.label_subTitle)

        separator = sectionSeparator()
        self.rootLayout.addWidget(separator)

        self.buildUI_timerOptions(self.rootLayout)

        separator = sectionSeparator()
        self.rootLayout.addWidget(separator)


        layout = QtWidgets.QHBoxLayout()
        self.rootLayout.addLayout(layout)

        label = QtWidgets.QLabel('Auto Mute:')
        label.setFixedWidth(60)
        self.checkbox_autoMute = checkbox = QtWidgets.QCheckBox()
        checkbox.stateChanged.connect(lambda state: self._CONFIG_.set('general', 'timer_autoMute', value=bool(state)))
        # layout.addRow(label, checkbox)
        layout.addWidget(label)
        layout.addWidget(checkbox)

        layout.addStretch()

        label = QtWidgets.QLabel('Auto Pause: ')
        label.setFixedWidth(70)
        self.checkbox_autoPause = checkbox = QtWidgets.QCheckBox()
        checkbox.stateChanged.connect(lambda state: self._CONFIG_.set('general', 'timer_autoPause', value=bool(state)))
        # layout.addRow(label, checkbox)

        layout.addWidget(label)
        layout.addWidget(checkbox)

        self.commandsLayout = QtWidgets.QHBoxLayout()
        self.rootLayout.addLayout(self.commandsLayout)

        self.btn_cancel = QtWidgets.QPushButton('Cancel')
        self.btn_cancel.setFixedWidth(80)
        self.commandsLayout.addWidget(self.btn_cancel)
        self.btn_cancel.clicked.connect(self.close)

        self.btn_confirm = QtWidgets.QPushButton('Confirm')
        self.btn_confirm.setFixedWidth(80)
        self.commandsLayout.addWidget(self.btn_confirm)
        self.btn_confirm.clicked.connect(self.saveConfig)


    def openLink(self, linkStr):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(linkStr))

    def buildUI_timerOptions(self, parent):
        self.layout_timerOptions = QtWidgets.QVBoxLayout()
        self.layout_timerOptions.setContentsMargins(0,0,0,0)
        self.layout_timerOptions.setSpacing(0)
        self.layout_timerOptions.setAlignment(QtCore.Qt.AlignTop)
        parent.addLayout(self.layout_timerOptions)



        self.timerControl_pause = self.addTimerControl('timer_pause', timerLabel='Paused:', startTimeFallback=0)
        self.timerControl_pause.previewField.setText('| |')
        self.layout_timerOptions.addWidget(self.timerControl_pause)

        self.timerControl_default = self.addTimerControl('timer_default', timerLabel='Default:', startTimeFallback=0)
        self.layout_timerOptions.addWidget(self.timerControl_default)

        self.timerControl_warning_A = self.addTimerControl('timer_a', timerLabel='Warning A:', startTimeFallback=5)
        self.layout_timerOptions.addWidget(self.timerControl_warning_A)

        self.timerControl_warning_B = self.addTimerControl('timer_b', timerLabel='Warning B:', startTimeFallback=10)
        self.timerControl_warning_B.startTime.setMinimum(int(self.timerControl_warning_A.startTime.value()+1))
        self.timerControl_warning_A.startTime.valueChanged.connect(lambda:self.timerControl_warning_B.startTime.setMinimum(int(self.timerControl_warning_A.startTime.value()+1)))
        self.layout_timerOptions.addWidget(self.timerControl_warning_B)

        self.timerControl_warning_C = self.addTimerControl('timer_c', timerLabel='Warning C:', startTimeFallback=15)
        self.timerControl_warning_C.startTime.setMinimum(int(self.timerControl_warning_B.startTime.value()+1))
        self.timerControl_warning_B.startTime.valueChanged.connect(lambda:self.timerControl_warning_C.startTime.setMinimum(int(self.timerControl_warning_B.startTime.value()+1)))
        self.layout_timerOptions.addWidget(self.timerControl_warning_C)

        self.timerControl_flash_A = self.addTimerControl('timer_flash_a', timerLabel='Flash A:', startTimeFallback=20)
        self.timerControl_flash_A.startTime.setMinimum(int(self.timerControl_warning_C.startTime.value()+1))
        self.timerControl_warning_C.startTime.valueChanged.connect(lambda:self.timerControl_flash_A.startTime.setMinimum(int(self.timerControl_warning_C.startTime.value()+1)))
        self.layout_timerOptions.addWidget(self.timerControl_flash_A)

        self.timerControl_flash_B = self.addTimerControl('timer_flash_b', timerLabel='Flash B:', startTimeFallback=0)
        self.timerControl_flash_B.btn_setTextColor.hide()
        self.timerControl_flash_A.startTime.valueChanged.connect(lambda:self.timerControl_flash_B.startTime.setValue(int(self.timerControl_flash_A.startTime.value())))
        self.timerControl_flash_A.updatedColor.connect(lambda: self.timerControl_flash_B.setColor('text', self._CONFIG_._DICT_['timerOptions']['timer_flash_a_textcolor']))
        self.layout_timerOptions.addWidget(self.timerControl_flash_B)

        self.flashFreq = QtWidgets.QSpinBox()
        self.flashFreq.setToolTip('Sets the duration of each note_warn-flash in milliseconds.')
        self.flashFreq.setSingleStep(50)
        self.flashFreq.setFixedWidth(60)
        self.flashFreq.setAlignment(QtCore.Qt.AlignRight)
        self.flashFreq.setMaximum(3000)
        self.flashFreq.setMinimum(200)
        self.flashFreq.setSuffix('ms')
        self.flashFreq.valueChanged.connect(lambda value:self._CONFIG_.set('timerOptions', 'timer_flash_freq', value))
        self.timerControl_flash_B.layout_ctrl.addWidget(self.flashFreq)

    def addTimerControl(self, name, timerLabel, startTimeFallback=None):
        widget = widget_timerSetting(timerLabel=timerLabel)
        self._timerControlWidgets[name] = widget
        self.parseConfig(name)

        if startTimeFallback:
            widget.startTime.setMinimum(0)
            widget.startTime.valueChanged.connect(lambda value:self._CONFIG_.set('timerOptions', '%s_startTime' %(name), value=value))
        else:
            widget.startTime.hide()


        widget.btn_setTime.clicked.connect(lambda: self.TIMER.setTime(widget.startTime.value()))
        widget.updatedColor.connect(lambda key, qcolor: self._CONFIG_.set('timerOptions', '%s_%s' %(name, key), value=qcolor))
        return widget

    def parseConfig_all(self):
        for key in self._timerControlWidgets.keys():
            self.parseConfig(key)
        self.flashFreq.setValue(self._CONFIG_.get('timerOptions', 'timer_flash_freq'))

        autoMute = self._CONFIG_.get('general', 'timer_automute', fallback=False)
        self.checkbox_autoMute.setChecked(autoMute)

        autoPause = self._CONFIG_.get('general', 'timer_autopause', fallback=False)
        self.checkbox_autoPause.setChecked(autoPause)


    def parseConfig(self, timerName):
        widget = self._timerControlWidgets[timerName]
        bgColor = self._CONFIG_.get('timerOptions', '%s_bgcolor' %(timerName))
        widget.setColor('background', bgColor, updateConfig=False)

        textColor = self._CONFIG_.get('timerOptions', '%s_textcolor' %(timerName))
        widget.setColor('text', textColor, updateConfig=False)

        startTime = self._CONFIG_.get('timerOptions', '%s_startTime' %(timerName))
        if startTime:
            widget.startTime.setValue(int(startTime))




class widget_timerSetting(QtWidgets.QWidget):
    updatedColor = Signal(str, QtGui.QColor)

    def __init__(self, parent=None, timerLabel=None):
        super(widget_timerSetting, self).__init__(parent=parent)

        self.buildUI()
        self.label.setText(timerLabel)

        self.palette = self.previewField.palette()
        self.previewField.setPalette(self.palette)

        self.btn_setBGColor.clicked.connect(lambda: self.setColor('background', colorPicker=True))
        self.btn_setTextColor.clicked.connect(lambda: self.setColor('text', colorPicker=True))


    def setColor(self, target, color=None, updateConfig=True, colorPicker=False):
        if target is 'background':
            colorSwatchName = 'bgcolor'
            paletteRole = QtGui.QPalette.Base
        elif target is 'text':
            colorSwatchName = 'textcolor'
            paletteRole = QtGui.QPalette.Text

        if colorPicker:
            currentColor = self.palette.color(paletteRole)
            NewQColor = QtWidgets.QColorDialog.getColor(currentColor)

        else:
            if type(color) == QtGui.QColor:
                NewQColor = color
            else:
                NewQColor = QtGui.QColor()

        if not NewQColor.isValid():
            return

        self.palette.setColor(paletteRole, NewQColor)
        self.previewField.setPalette(self.palette)

        if updateConfig:
            self.updatedColor.emit(colorSwatchName, NewQColor)


    def buildUI(self):
        self.rootLayout = QtWidgets.QVBoxLayout()
        self.rootLayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.rootLayout)

        self.layout_ctrl = layout_ctrl = QtWidgets.QHBoxLayout()
        layout_ctrl.setContentsMargins(0,0,0,0)
        layout_ctrl.setSpacing(1)
        layout_ctrl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.rootLayout.addLayout(layout_ctrl)

        self.label = QtWidgets.QLabel()
        self.label.setFixedWidth(60)
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.layout_ctrl.addWidget(self.label)


        self.btn_setTime = btn = QtWidgets.QPushButton()
        btn.setFixedWidth(10)
        self.layout_ctrl.addWidget(self.btn_setTime)

        self.previewField = previewField = QtWidgets.QLineEdit()
        timerFont = QtGui.QFont()
        timerFont.setBold(True)
        timerFont.setWeight(75)
        previewField.setFont(timerFont)
        previewField.setFixedWidth(50)
        previewField.setAlignment(QtCore.Qt.AlignCenter)
        previewField.setFocusPolicy(QtCore.Qt.NoFocus)
        previewField.setEnabled(False)
        previewField.setFixedHeight(25)
        previewField.setText('0')
        self.layout_ctrl.addWidget(self.previewField)

        self.btn_setBGColor = QtWidgets.QPushButton('bg')
        self.btn_setBGColor.setToolTip('Sets the background color.')
        self.btn_setBGColor.setFixedWidth(20)
        self.btn_setBGColor.setFocusPolicy(QtCore.Qt.NoFocus)
        self.layout_ctrl.addWidget(self.btn_setBGColor)

        self.btn_setTextColor = QtWidgets.QPushButton('#')
        self.btn_setTextColor.setToolTip('Sets the color of the text.')
        self.btn_setTextColor.setFixedWidth(20)
        self.btn_setTextColor.setFocusPolicy(QtCore.Qt.NoFocus)
        self.layout_ctrl.addWidget(self.btn_setTextColor)

        self.startTime = QtWidgets.QSpinBox()
        self.startTime.setToolTip('Sets which minute this note_warn will activate.')
        self.startTime.setMinimum(-1)
        self.startTime.setFixedWidth(40)
        self.startTime.setAlignment(QtCore.Qt.AlignCenter)
        self.layout_ctrl.addWidget(self.startTime)

        self.startTime.valueChanged.connect(lambda:self.previewField.setText(str(self.startTime.value())))


class sectionSeparator(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super(sectionSeparator, self).__init__()
        self.setStyleSheet("background:rgba(0,0,0, 50);")
        self.setFixedHeight(1)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = saveTimer_config_GUI()
    win.show()
    sys.exit(app.exec_())
