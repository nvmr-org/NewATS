import logging
import time
import re
import sys
import java.io.File
import xml.etree.ElementTree as ET

from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.messengerFacade import Messenger
from classes.blockMap import BlockMap
from classes.atsWinListener import AtsWinListener
from xml.dom import minidom

from java.lang import Runtime
from javax.swing import BorderFactory, Box
from javax.swing import JButton, JComboBox, JCheckBox, JLabel, JPanel
from javax.swing import JTextField, JTable, JTextPane
from javax.swing import JScrollPane, JOptionPane, JSpinner, SpinnerNumberModel
from javax.swing.text import StyleConstants
from javax.swing.table import DefaultTableModel
from java.awt import BorderLayout, Color, Dimension, FlowLayout, Font
from java.awt import GridBagConstraints, GridBagLayout, Insets, Toolkit, Rectangle
from java.awt.event import MouseAdapter
from jmri.util.swing import TextAreaFIFO

from javax.swing import JFileChooser;
from javax.swing.filechooser import FileSystemView
from javax.swing.filechooser import FileNameExtensionFilter


try:
    jmriFlag = True
    import jmri
    print('Successfully Imported jmri')
except ImportError:
    jmriFlag = False
    print('Failed to import jmir - bypassing')

logger = logging.getLogger("ATS."+__name__)
logger.setLevel(logging.INFO)
thisFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name

trolleyRoster = TrolleyRoster()
layoutMap = BlockMap()
msg = Messenger()
jmriFileUtilSupport = jmri.util.FileUtilSupport()

class AtsUI(object):
    
    instance = None
    atsScreenSize = Toolkit.getDefaultToolkit().getScreenSize()
    atsWindowWidth = int(float(atsScreenSize.width) * 0.8)
    atsWindowHeight = int(float(atsScreenSize.height) * 0.8)
    atsWindowPosX = (atsScreenSize.width - atsWindowWidth) >> 1
    atsWindowPosY = (atsScreenSize.height - atsWindowHeight) >> 1
    atsFontSize = int(float(atsScreenSize.height) / 60)
    atsRowHeight = int(float(atsFontSize) * 1.25)
    atsMessageWindowWidth = int(float(atsWindowWidth) * 0.9)
    atsRosterWindowWidth = atsWindowWidth
    atsBlockStatusMessageWindowHeight= int(5*atsRowHeight)
    atsSegmentStatusMessageWindowHeight= int(5*atsRowHeight)
    atsRosterStatusMessageWindowHeight= int(10*atsRowHeight)
    atsStatusMessageWindowHeight= int(10*atsRowHeight)
    messageInfoText = None
    MAX_LOG_LINES = 500

    def __init__(self, automationObject=None, appName=None):
        # ------------------------------------------------------------------------------------------
        # create a frame to hold the buttons and fields
        # also create a window listener. This is used mainly to remove the property change listener
        # when the window is closed by clicking on the window close button
        # ------------------------------------------------------------------------------------------
        super(AtsUI, self).__init__()
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.info("Screen Size - Height:%s Width:%s", AtsUI.atsScreenSize.height, AtsUI.atsScreenSize.width)
        self.automationObject=automationObject
        self.w = AtsWinListener()
        atsMainFrameBounds = Rectangle(AtsUI.atsWindowPosX, AtsUI.atsWindowPosY, AtsUI.atsWindowWidth, AtsUI.atsWindowHeight)
        self.fr = jmri.util.JmriJFrame(appName, bounds = atsMainFrameBounds) #use this in order to get it to appear on webserver
        self.fr.setSaveSize(False)
        self.fr.setSavePosition(False)
        self.fr.contentPane.setLayout(GridBagLayout())
        self.createLoggingComponents()
        self.addComponent(self.fr, self.getButtonPanel(), 0, 0, 2, 1, GridBagConstraints.PAGE_START, GridBagConstraints.NONE);
        self.addComponent(self.fr, self.ckBoxPanel1, 0, 1, 1, 2, GridBagConstraints.LINE_START, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.ckBoxPanel2, 1, 1, 1, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.blockInfoPane, 0, 3, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.segmentInfoPane, 0, 4, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.rosterInfoPane, 0, 5, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.messageInfoPane, 0, 6, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.BOTH)
        self.fr.addWindowListener(self.w)
        #self.fr.pack()
        self.fr.setVisible(True)


    def __new__(cls, automationObject=None, appName=None):
        if AtsUI.instance is None:
            logger.info("Creating NEW AtsUI")
            AtsUI.instance = object.__new__(cls, automationObject, appName)
        return AtsUI.instance


    def getCurrent(self):
        return self


# *************************************
# start to initialize the display GUI *
# *************************************
    def whenStopAllButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.editRosterButton.setEnabled(True)
        self.tstopButton.setEnabled(False)
        self.tgoButton.setEnabled(True)
        self.quitButton.setEnabled(True)
        self.loadRosterButton.setEnabled(True)
        self.saveRosterButton.setEnabled(True)
        self.loadLayoutButton.setEnabled(True)
        self.automationObject.stop()
        logger.info("Stop All Trolleys button pressed")
        trolleyRoster.stopAllTrolleys()
        trolleyRoster.dump()
        return


    def whenQuitButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.tstopButton.setEnabled(False)
        self.tgoButton.setEnabled(False)
        if self.automationObject.isRunning(): self.automationObject.stop()
        trolleyRoster.destroy()
        self.fr.dispose()
        return


    def whenTgoButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.editRosterButton.setEnabled(False)
        self.tstopButton.setEnabled(True)
        self.tgoButton.setEnabled(False)
        self.quitButton.setEnabled(False)
        self.loadRosterButton.setEnabled(False)
        self.saveRosterButton.setEnabled(False)
        self.loadLayoutButton.setEnabled(False)
        self.automationObject.start()
        logger.info("Start Running button pressed")
        while self.automationObject.isRunning() == False:
            logger.info("Waiting for Automation to start")
            time.sleep(1.0)
        return


    def whenSimulatorButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        __simulatorState = self.automationObject.isSimulatorEnabled()
        logger.info("Simulator State:"+str(__simulatorState)+"-->"+str(not __simulatorState))
        __simulatorState = not __simulatorState
        self.automationObject.setSimulatorState(__simulatorState)
        if __simulatorState:
            self.simulatorButton.setText("Disable Simulator")
        else:
            self.simulatorButton.setText("Enable Simulator")


    def whenLoadLayoutMapButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        selectedFile = self.getUserSelectedFile("XML Files",["XML", "xml"])
        if (selectedFile != None):
            logger.info("Selected LayoutMap File:%s",selectedFile.getAbsolutePath())
        layoutMap.loadLayoutMapFromXml(selectedFile)
        logger.info("Layout Load Successful - Reload of roster required")
        trolleyRoster.reset()
        #trolleyRoster.validatePositions(layoutMap)
        trolleyRoster.dump()
        layoutMap.printBlocks(trolleyRoster)
        layoutMap.printSegments(trolleyRoster)
        return


    def whenSaveRosterButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        selectedFile = self.getUserSelectedFile("XML Files",["XML", "xml"], Mode='SAVE')
        if (selectedFile != None):
            logger.info("Selected LayoutMap File:%s",selectedFile.getAbsolutePath())
        self.saveFileAsXml(selectedFile.getAbsolutePath(), trolleyRoster.getRosterAsXml())
        return


    def whenLoadRosterButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        selectedFile = self.getUserSelectedFile("XML Files",["XML", "xml"])
        if (selectedFile != None):
            logger.info("Selected Roster File:%s",selectedFile.getAbsolutePath())
        trolleyRoster.loadRosterFromXmlFile(selectedFile)
        trolleyRoster.dump()
        layoutMap.printBlocks(trolleyRoster)
        layoutMap.printSegments(trolleyRoster)
        return

        
    def whenRemoveButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        return


    def whenCheckboxClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.setDebugFlag(self.UiDebugCheckBox.isSelected())
        layoutMap[0].setDebugFlag(self.BlockDebugCheckBox.isSelected())
        layoutMap.setDebugFlag(self.BlockMapDebugCheckBox.isSelected())
        msg.setDebugFlag(self.MsgDebugCheckBox.isSelected())
        trolleyRoster[0].setDebugFlag(self.TrolleyDebugCheckBox.isSelected())
        trolleyRoster.setDebugFlag(self.RosterDebugCheckBox.isSelected())
        self.automationObject.setDebugFlag(self.AutoDebugCheckBox.isSelected())
        logger.info("Debug Levels - UI:%s Block:%s BlockMap:%s Trolley:%s Roster:%s Automation:%s Messages:%s",
                    "DEBUG" if self.getDebugLevel()==logging.DEBUG else "INFO",
                    "DEBUG" if self.BlockDebugCheckBox.isSelected() else "INFO",
                    "DEBUG" if self.BlockMapDebugCheckBox.isSelected() else "INFO",
                    "DEBUG" if self.TrolleyDebugCheckBox.isSelected() else "INFO",
                    "DEBUG" if self.RosterDebugCheckBox.isSelected() else "INFO",
                    "DEBUG" if self.AutoDebugCheckBox.isSelected() else "INFO",
                    "DEBUG" if self.MsgDebugCheckBox.isSelected() else "INFO")
        return


    def whenEditRosterButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.editRosterButton.setEnabled(False)
        self.frameRoster = self.createEditRosterDataFrame(trolleyRoster)
        return


    def whenEditRosterCloseButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.editRosterButton.setEnabled(True)
        self.frameRoster.dispose()
        return


    def whenCancelAddTrolleyButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.frameAddTrolley.dispose()
        self.frameRoster.setVisible(True)
        return


    def whenSaveAddTrolleyButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        __address = int(self.addTrolleyAddress.getText())
        __maxSpeed = int(self.addTrolleyMaxSpeed.getText())
        __block = layoutMap.findBlockByAddress(int(self.addTrolleyStartingPosition.getSelectedItem().split('-')[0]))
        if __block is None : return
        if not trolleyRoster.isTrolleyAddressValid(__address): return
        if not trolleyRoster.isTrolleyMaxSpeedValid(__maxSpeed): return
        if trolleyRoster.findByAddress(__address): return
        logger.info("Address: "+str(__address)+" MaxSpeed: "+
              str(__maxSpeed)+" SoundEnabled: "+
              str(self.addTrolleySoundEnabled.isSelected())+" Starting Position: "+
              str(__block.address)+" Starting Position Description: "+
              str(__block.description))
        trolleyRoster.append(Trolley(layoutMap, address=__address, maxSpeed=__maxSpeed, 
                                     soundEnabled=self.addTrolleySoundEnabled.isSelected(), currentPosition=__block.address))
        trolleyRoster.dump()
        layoutMap.printBlocks(trolleyRoster)
        layoutMap.printSegments(trolleyRoster)
        self.frameAddTrolley.dispose()
        self.frameRoster.dispose()
        self.frameRoster = self.createEditRosterDataFrame(trolleyRoster)
        self.frameRoster.setVisible(True)
        return


    def whenAddToRosterButtonClicked(self,event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.frameRoster.setVisible(False)
        self.frameAddTrolley = self.createAddToTrolleyRosterFrame()
        return


    def getUserSelectedFile(self, description, extensionFilterList, Mode='OPEN'):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        layoutMapFilePath = jmriFileUtilSupport.getUserFilesPath()
        logger.info("User Files Path: %s" + layoutMapFilePath)
        fileChooser = JFileChooser(FileSystemView.getFileSystemView().getHomeDirectory())
        fileFilter =  FileNameExtensionFilter(description, extensionFilterList)
        logger.debug("FileFilter:%s",str(fileFilter))
        fileChooser.setFileFilter(fileFilter)
        fileChooser.setCurrentDirectory(java.io.File(layoutMapFilePath))
        if Mode == 'OPEN': fileChooser.showOpenDialog(None)
        if Mode == 'SAVE': fileChooser.showSaveDialog(None)
        logger.info("LOADING FILE:%s", str(fileChooser.getSelectedFile()))
        return fileChooser.getSelectedFile();


    def sendAudibleMessage(self,checkboxToMonitor, messageToAnnounce):
        if checkboxToMonitor.isSelected() :
            javaexec = getattr(Runtime.getRuntime(), "exec")
            pid = javaexec('nircmd speak text "' + messageToAnnounce +'" -2 100')
            pid.waitFor()
        return


    def addComponent(self, container, component, gridx, gridy, gridwidth, gridheight, anchor, fill):
        insets=Insets(5, 20, 5, 20)
        ipadx = 5
        ipady = 5
        weightx = 1.0
        weighty = 0.0
        gbc = GridBagConstraints(gridx, gridy, gridwidth, gridheight, weightx, weighty, anchor, fill, insets, ipadx, ipady)
        container.add(component, gbc)


    def setDebugFlag(self,state):
        logger.setLevel(logging.DEBUG if state else logging.INFO)
        for handler in logging.getLogger("ATS").handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("%s.%s - Logger:%s - Set Debug Flag:%s", __name__, thisFuncName(),str(logger),str(state))


    def getDebugLevel(self):
        return logger.level


    def setRosterColumnProperties(self, table, column, width=5, resizable=False):
        table.getColumnModel().getColumn(column).setPreferredWidth(width)
        table.getColumnModel().getColumn(column).setResizable(resizable)
        return


    def getAddTrolleyButtonPanel(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        saveButton = self.createButtonWithAction("Save", self.whenSaveAddTrolleyButtonClicked )
        cancelButton = self.createButtonWithAction("Cancel", self.whenCancelAddTrolleyButtonClicked )
        addTrolleyPanel = JPanel()
        addTrolleyPanel.setLayout(FlowLayout(FlowLayout.LEFT))
        addTrolleyPanel.add(saveButton)
        addTrolleyPanel.add(Box.createHorizontalStrut(10))
        addTrolleyPanel.add(cancelButton)
        return addTrolleyPanel


    def getAddTrolleyDataPanel(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        __panel = JPanel()
        __panel.add(JLabel("Address:"))
        self.addTrolleyAddress = JTextField('',5)
        __panel.add(self.addTrolleyAddress)
        __panel.add(JLabel("Max Speed:"))
        self.addTrolleyMaxSpeed = JTextField('',5)
        __panel.add(self.addTrolleyMaxSpeed)
        __panel.add(JLabel("Sound Enabled:"))
        self.addTrolleySoundEnabled = JCheckBox()
        __panel.add(self.addTrolleySoundEnabled)
        __panel.add(JLabel("Starting Position:"))
        comboChoices = []
        for block in layoutMap:
            comboChoices.append(str(block.address)+'-'+block.description)
        self.addTrolleyStartingPosition = JComboBox(comboChoices)
        __panel.add(self.addTrolleyStartingPosition)
        return __panel


    def createButtonWithAction(self,title,action):
        __button = JButton(title)
        __button.actionPerformed = action
        return __button


    def createAddToTrolleyRosterFrame(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        frameAddTrolley = jmri.util.JmriJFrame("Add Trolley To Roster")
        frameAddTrolley.setSize(AtsUI.atsRosterWindowWidth,10*AtsUI.atsRowHeight)
        frameAddTrolley.setLayout(GridBagLayout())
        self.addComponent(frameAddTrolley, self.getAddTrolleyButtonPanel(), 0, 0, 2, 1, GridBagConstraints.PAGE_START, GridBagConstraints.NONE)
        self.addComponent(frameAddTrolley, self.getAddTrolleyDataPanel(), 0, 2, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.NONE)
        frameAddTrolley.setDefaultCloseOperation(self.frameRoster.DO_NOTHING_ON_CLOSE); # Disable the Close button
        frameAddTrolley.setSaveSize(False)
        frameAddTrolley.setSavePosition(False)
        frameAddTrolley.pack()
        frameAddTrolley.setVisible(True)
        return frameAddTrolley


    def createEditRosterDataFrame(self,trolleyRoster):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        frameRoster = jmri.util.JmriJFrame("Trolley Roster")
        frameRoster.setSize(AtsUI.atsRosterWindowWidth,(len(trolleyRoster)+3)*AtsUI.atsRowHeight)
        frameRoster.setLayout(BorderLayout())
        frameRoster.setSaveSize(False)
        frameRoster.setSavePosition(False)
        rosterData = []
        for trolley in trolleyRoster:
            deleteRosterRowButton = JButton("Delete")
            deleteRosterRowButton.actionPerformed = None #whenDeleteRosterRowButtonClicked
            rosterData.append([trolley.address, trolley.maxSpeed, trolley.soundEnabled,
                               trolley.currentPosition.address, trolley.currentPosition.description,'DELETE'])
        colNames = ['Address', 'Max Speed', 'Sound', 'Starting Position', 'Position Description', '']
        dataModel = DefaultTableModel(rosterData,colNames)
        rosterTable = JTable(dataModel)
        rosterTable.getTableHeader().setReorderingAllowed(False)
        rosterTable.setRowHeight(AtsUI.atsRowHeight)
        rosterTable.setEnabled(True)
        rosterTable.addMouseListener(self.DeleteTrolleyButtonListener())
        rosterScrollPane = JScrollPane()
        rosterScrollPane.setPreferredSize(Dimension(AtsUI.atsRosterWindowWidth,(len(trolleyRoster)+3)*AtsUI.atsRowHeight))
        rosterScrollPane.getViewport().setView(rosterTable)
        rosterPanel = JPanel()
        rosterPanel.add(rosterScrollPane)
        rosterAddButton = self.createButtonWithAction("Add To Roster", self.whenAddToRosterButtonClicked)
        rosterAddButton.setEnabled(True)
        rosterCloseButton = self.createButtonWithAction("Close", self.whenEditRosterCloseButtonClicked)
        frameRoster.add(rosterAddButton, BorderLayout.PAGE_START)
        frameRoster.add(rosterPanel, BorderLayout.CENTER)
        frameRoster.add(rosterCloseButton, BorderLayout.PAGE_END)
        frameRoster.setDefaultCloseOperation(frameRoster.DO_NOTHING_ON_CLOSE); # Disable the Close button
        frameRoster.pack()
        frameRoster.setVisible(True)
        return frameRoster


    def getButtonPanel(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.createButtonPanelButtons()
        butPanel = JPanel()
        butPanel.setLayout(FlowLayout(FlowLayout.LEFT))
        butPanel.add(self.editRosterButton)
        butPanel.add(Box.createHorizontalStrut(20))
        butPanel.add(self.tgoButton)
        butPanel.add(Box.createHorizontalStrut(20))
        butPanel.add(self.tstopButton)
        butPanel.add(Box.createHorizontalStrut(20))
        butPanel.add(self.simulatorButton)
        butPanel.add(Box.createHorizontalStrut(40))
        butPanel.add(self.loadRosterButton)
        butPanel.add(Box.createHorizontalStrut(20))
        butPanel.add(self.saveRosterButton)
        butPanel.add(Box.createHorizontalStrut(20))
        butPanel.add(self.loadLayoutButton)
        butPanel.add(Box.createHorizontalStrut(20))
        butPanel.add(self.quitButton)
        return butPanel


    def createButtonPanelButtons(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.quitButton = self.createButtonWithAction("Quit", self.whenQuitButtonClicked)
        self.loadRosterButton = self.createButtonWithAction("Load Roster", self.whenLoadRosterButtonClicked)
        self.loadRosterButton.setEnabled(True)
        self.saveRosterButton = self.createButtonWithAction("Save Roster", self.whenSaveRosterButtonClicked)
        self.saveRosterButton.setEnabled(True)
        self.loadLayoutButton = self.createButtonWithAction("Load Layout Map", self.whenLoadLayoutMapButtonClicked)
        self.loadLayoutButton.setEnabled(True)
        self.tgoButton = self.createButtonWithAction("Start Running", self.whenTgoButtonClicked)
        self.tstopButton = self.createButtonWithAction("Stop All Trolleys", self.whenStopAllButtonClicked)
        self.tstopButton.setEnabled(False)           #button starts as grayed out (disabled)
        simulatorButtonTxt = "Disable Simulator" if self.automationObject.simulatorEnabled else "Enable Simulator"
        self.simulatorButton = self.createButtonWithAction(simulatorButtonTxt, self.whenSimulatorButtonClicked)
        self.editRosterButton = self.createButtonWithAction("Edit Roster", self.whenEditRosterButtonClicked)
        self.editRosterButton.setEnabled(True)
        return

    def createInfoPane(self,defaultText, title=None):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        __pane = JTextPane()
        __doc = __pane.getStyledDocument()
        __style = __pane.addStyle("Color Style", None)
        __pane.setFont(Font("monospaced",Font.BOLD,AtsUI.atsFontSize))
        __pane.setBorder(BorderFactory.createLineBorder(Color.black));
        if title is not None:
            __pane.insertComponent(JLabel(title))
        StyleConstants.setForeground(__style, Color.BLUE)
        __doc.insertString(__doc.getLength(),defaultText,__style)
        return __pane


    def createMessagePane(self, DefaultText, title=None, paneHeight=10):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        __panel = JPanel()
        __panel.add(JLabel(title))
        self.messageInfoText = TextAreaFIFO(AtsUI.MAX_LOG_LINES)
        self.messageInfoText.setAutoScroll(True)
        scrollField = JScrollPane(self.messageInfoText) #put text area in scroll field
        scrollField.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER)
        scrollField.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS)
        scrollField.setMinimumSize(Dimension(AtsUI.atsMessageWindowWidth, int(paneHeight*AtsUI.atsFontSize*1.4)))
        __panel.setBorder(BorderFactory.createEmptyBorder(1, 8, 1, 8))
        __panel.setLayout(BorderLayout())
        __panel.add(scrollField)
        __panel.setSize(AtsUI.atsMessageWindowWidth, paneHeight)
        return __panel


    def createLoggingComponents(self):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        self.logLabel1 = JLabel("Logging:")
        self.UiDebugCheckBox = JCheckBox("UI", actionPerformed = self.whenCheckboxClicked)
        self.UiDebugCheckBox.setToolTipText("Display all UI debug messages")
        self.UiDebugCheckBox.setSelected(self.getDebugLevel()==logging.DEBUG)
        self.BlockDebugCheckBox = JCheckBox("Block", actionPerformed = self.whenCheckboxClicked)
        self.BlockDebugCheckBox.setToolTipText("Display Block debug messages")
        self.BlockMapDebugCheckBox = JCheckBox("BlockMap", actionPerformed = self.whenCheckboxClicked)
        self.BlockMapDebugCheckBox.setToolTipText("Display BlockMap debug messages")
        self.BlockMapDebugCheckBox.setSelected(layoutMap.getDebugLevel()==logging.DEBUG)
        self.TrolleyDebugCheckBox = JCheckBox("Trolley", actionPerformed = self.whenCheckboxClicked)
        self.TrolleyDebugCheckBox.setToolTipText("Display debugging for outgoing loconet messages")
        self.RosterDebugCheckBox = JCheckBox("TrolleyRoster", actionPerformed = self.whenCheckboxClicked)
        self.RosterDebugCheckBox.setToolTipText("Display all roster debug messages")
        self.RosterDebugCheckBox.setSelected(trolleyRoster.getDebugLevel()==logging.DEBUG)
        self.AutoDebugCheckBox = JCheckBox("Automation", actionPerformed = self.whenCheckboxClicked)
        self.AutoDebugCheckBox.setToolTipText("Display automation debug messages")
        self.AutoDebugCheckBox.setSelected(self.automationObject.getDebugLevel()==logging.DEBUG)
        self.MsgDebugCheckBox = JCheckBox("Messaging", actionPerformed = self.whenCheckboxClicked)
        self.MsgDebugCheckBox.setToolTipText("Display messaging debug messages")
        self.MsgDebugCheckBox.setSelected(msg.getDebugLevel()==logging.DEBUG)
        self.msgSpkCheckBox = JCheckBox("Announcer")
        self.msgSpkCheckBox.setToolTipText("Speak when alert is sent")
        self.msgSpkCheckBox.setSelected(True)

        # ====================================
        # create checkboxes panel
        # ====================================
        self.ckBoxPanel1 = JPanel()
        self.ckBoxPanel1.setLayout(FlowLayout(FlowLayout.RIGHT))
        self.ckBoxPanel1.add(self.logLabel1)

        self.ckBoxPanel2 = JPanel()
        self.ckBoxPanel2.setLayout(FlowLayout(FlowLayout.LEFT))
        self.ckBoxPanel2.add(self.UiDebugCheckBox)
        self.ckBoxPanel2.add(self.BlockDebugCheckBox)
        self.ckBoxPanel2.add(self.BlockMapDebugCheckBox)
        self.ckBoxPanel2.add(self.TrolleyDebugCheckBox)
        self.ckBoxPanel2.add(self.RosterDebugCheckBox)
        self.ckBoxPanel2.add(self.AutoDebugCheckBox)
        self.ckBoxPanel2.add(self.MsgDebugCheckBox)
        self.ckBoxPanel2.add(self.msgSpkCheckBox)

        # =====================================
        # create text fields for status outputs
        # =====================================
        self.blockInfoPane = self.createInfoPane(layoutMap.getBlockStatus(trolleyRoster), title="Block Status")
        self.segmentInfoPane = self.createInfoPane(layoutMap.getSegmentStatus(trolleyRoster), title="Segment Status")
        self.rosterInfoPane = self.createInfoPane(trolleyRoster.getRosterStatus(), title="Trolley Roster Status")
        self.messageInfoPane = self.createMessagePane("Default Message Panel\n"+
                                             "Currently All messages will be written to the Script Output window\n",
                                             title = "Messages")


    def saveFileAsXml(self, fileName, xmlString):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        try:
            text_file = open(fileName, "w")
            text_file.write(self.getFormattedXml(xmlString))
            text_file.close()
            logger.info("File Created: %s", fileName)
        except Exception, e:
            logger.error(e)
            logger.error('Unable to save file: %s', fileName)


    def getFormattedXml(self, xmlParent):
        xmlstr = minidom.parseString(ET.tostring(xmlParent)).toprettyxml(indent="   ")
        text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
        prettyXml = text_re.sub('>\g<1></', xmlstr)
        return prettyXml


    class DeleteTrolleyButtonListener(MouseAdapter):
        def mousePressed(self, event):
            __target = event.getSource()
            __row = __target.getSelectedRow()
            __column = __target.getSelectedColumn()
            if __column == 1:
                self.updateTrolleyRowMaxSpeed(__row)
            if __column == 3 or __column == 4:
                self.updateTrolleyPosition(__row)
            if __column == 5: 
                self.deleteTrolleyRowFromRoster(__row)



        def updateTrolleyRowMaxSpeed(self, row):
            logger.trace("Entering %s.%s", __name__, thisFuncName())
            logger.info("UPDATE SPEED for Trolley Roster item %s - Address: %s", str(row), str(trolleyRoster[row].address))
            spinner = JSpinner( SpinnerNumberModel( trolleyRoster[row].maxSpeed, 1, 99, 1) )
            __response = JOptionPane.showOptionDialog(None, spinner, "Update Max Speed", JOptionPane.OK_CANCEL_OPTION, JOptionPane.QUESTION_MESSAGE, None, None, None)
            logger.info("UPDATE SPEED for Trolley: %s to %s - %s", str(trolleyRoster[row].address),
                        str(spinner.getValue()), ("Confirmed" if __response == 0 else "Cancelled"))
            if __response == JOptionPane.OK_OPTION:
                trolleyRoster[row].maxSpeed = int(spinner.getValue())
                trolleyRoster.dump()
                AtsUI.instance.frameRoster.dispose()
                AtsUI.instance.frameRoster = AtsUI.instance.createEditRosterDataFrame(trolleyRoster)
                AtsUI.instance.frameRoster.setVisible(True)


        def updateTrolleyPosition(self, row):
            logger.trace("Entering %s.%s", __name__, thisFuncName())
            logger.info("UPDATE POSITION for Trolley Roster item %s - Address: %s", str(row), str(trolleyRoster[row].address))
            __positionChoices = []
            for block in layoutMap:
                __positionChoices.append(str(block.address)+'-'+block.description)
            index = __positionChoices.index(str(trolleyRoster[row].currentPosition.address)+'-'+trolleyRoster[row].currentPosition.description)
            __response = JOptionPane.showInputDialog(None, "Choice", "Update Position", JOptionPane.OK_CANCEL_OPTION, None, __positionChoices, __positionChoices[index])
            logger.info("UPDATE POSITION Trolley: %s to %s - %s", str(trolleyRoster[row].address),
                        str(__response), ("Confirmed" if __response else "CANCELLED"))
            if __response:
                _oldPosition = trolleyRoster[row].currentPosition
                logger.info("UPDATE POSITION - Old Position: %s", str(_oldPosition.address))
                trolleyRoster[row].currentPosition = layoutMap.findBlockByAddress(int(__response.split('-')[0]))
                trolleyRoster[row].nextPosition = trolleyRoster[row].currentPosition.next
                trolleyRoster[row].currentPosition.set_blockOccupied()
                if not trolleyRoster.findByCurrentBlock(_oldPosition.address):
                    logger.info("UPDATE POSITION - Clearing old block: %s", str(_oldPosition.address))
                    _oldPosition.set_blockClear()
                trolleyRoster.dump()
                layoutMap.printBlocks(trolleyRoster)
                layoutMap.printSegments(trolleyRoster)
                AtsUI.instance.frameRoster.dispose()
                AtsUI.instance.frameRoster = AtsUI.instance.createEditRosterDataFrame(trolleyRoster)
                AtsUI.instance.frameRoster.setVisible(True)


        def deleteTrolleyRowFromRoster(self, row):
            logger.trace("Entering %s.%s", __name__, thisFuncName())
            logger.info("DELETE Trolley Roster item %s - Address: %s", str(row), str(trolleyRoster[row].address))
            __response = self.deleteTrolleyFromRosterConfirmation("Delete Trolley #"+str(trolleyRoster[row].address),"Delete Trolley")
            logger.info("DELETE Trolley: %s - %s", str(trolleyRoster[row].address),
                        ("Confirmed" if __response == 0 else "Cancelled"))
            if __response == 0:
                position = trolleyRoster[row].currentPosition
                trolleyRoster.delete(row)
                logger.debug("Trolley Deleted - Checking if block %s is CLEAR", str(position.address))
                if trolleyRoster.findByCurrentBlock(position.address) == None:
                    logger.debug("Setting block %s to CLEAR", str(position.address))
                    position.set_blockClear()
                trolleyRoster.validatePositions(layoutMap)
                trolleyRoster.dump()
                layoutMap.printBlocks(trolleyRoster)
                layoutMap.printSegments(trolleyRoster)
                # The revalidate and repaint methods don't seem to work so for now we just dispose of the
                # original roster frame and recreate it so the new trolley is displayed.
                #frameRoster.revalidate()
                #frameRoster.repaint()
                AtsUI.instance.frameRoster.dispose()
                AtsUI.instance.frameRoster = AtsUI.instance.createEditRosterDataFrame(trolleyRoster)
                AtsUI.instance.frameRoster.setVisible(True)


        def deleteTrolleyFromRosterConfirmation(self, message, title):
            logger.trace("Entering %s.%s", __name__, thisFuncName())
            result = JOptionPane.showConfirmDialog(None, message,  title, JOptionPane.OK_CANCEL_OPTION)
            return result



