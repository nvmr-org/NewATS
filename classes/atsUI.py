import logging
import time
import java.io.File

from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.messengerFacade import Messenger
from classes.blockMap import BlockMap
from classes.atsWinListener import AtsWinListener

from java.lang import Runtime
from javax.swing import BorderFactory, Box
from javax.swing import JButton, JComboBox, JCheckBox, JLabel, JPanel
from javax.swing import JTextField, JTable, JTextPane, JTextArea
from javax.swing import JScrollPane, JOptionPane, JSpinner, SpinnerNumberModel
from javax.swing.text import DefaultCaret, StyleConstants
from javax.swing.table import DefaultTableModel
from java.awt import BorderLayout, Color, Dimension, FlowLayout, Font
from java.awt import GridBagConstraints, GridBagLayout, Insets, Toolkit, Rectangle
from java.awt.event import MouseAdapter

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
    atsFontSize = int(float(atsScreenSize.height) / 90)
    atsRowHeight = int(float(atsFontSize) * 1.25)
    atsMessageWindowWidth = int(float(atsWindowWidth) * 0.9)
    atsRosterWindowWidth = atsWindowWidth
    atsBlockStatusMessageWindowHeight= int(5*atsRowHeight)
    atsSegmentStatusMessageWindowHeight= int(5*atsRowHeight)
    atsRosterStatusMessageWindowHeight= int(10*atsRowHeight)
    atsStatusMessageWindowHeight= int(10*atsRowHeight)

    def __init__(self, automationObject=None, appName=None):
        # ------------------------------------------------------------------------------------------
        # create a frame to hold the buttons and fields
        # also create a window listener. This is used mainly to remove the property change listener
        # when the window is closed by clicking on the window close button
        # ------------------------------------------------------------------------------------------
        super(AtsUI, self).__init__()
        logger.info("Screen Size - Height:%s Width:%s", AtsUI.atsScreenSize.height, AtsUI.atsScreenSize.width)
        self.automationObject=automationObject
        self.w = AtsWinListener()
        atsMainFrameBounds = Rectangle(AtsUI.atsWindowPosX, AtsUI.atsWindowPosY, AtsUI.atsWindowWidth, AtsUI.atsWindowHeight)
        self.fr = jmri.util.JmriJFrame(appName, bounds = atsMainFrameBounds) #use this in order to get it to appear on webserver
        self.fr.setSaveSize(False)
        self.fr.setSavePosition(False)
        self.fr.contentPane.setLayout(GridBagLayout())
        self.createApplicationWindowComponents()
        self.addComponent(self.fr, self.getButtonPanel(), 0, 0, 2, 1, GridBagConstraints.PAGE_START, GridBagConstraints.NONE);
        self.addComponent(self.fr, self.ckBoxPanel1, 0, 1, 1, 2, GridBagConstraints.LINE_START, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.ckBoxPanel2, 1, 1, 1, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.ckBoxPanel3, 1, 2, 1, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.blockInfoPane, 0, 3, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.segmentInfoPane, 0, 4, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.rosterInfoPane, 0, 5, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.messageInfoPanel, 0, 6, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.BOTH)
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
        self.editRosterButton.setEnabled(True)
        self.tstopButton.setEnabled(False)
        self.tgoButton.setEnabled(True)
        self.quitButton.setEnabled(True)
        self.automationObject.stop()
        logger.info("Stop All Trolleys button pressed")
        trolleyRoster.stopAllTrolleys()
        trolleyRoster.dump()
        return


    def whenQuitButtonClicked(self,event):
        self.tstopButton.setEnabled(False)
        self.tgoButton.setEnabled(False)
        if self.automationObject.isRunning(): self.automationObject.stop()
        trolleyRoster.destroy()
        self.fr.dispose()
        return


    def whenTgoButtonClicked(self,event):
        self.editRosterButton.setEnabled(False)
        self.tstopButton.setEnabled(True)
        self.tgoButton.setEnabled(False)
        self.quitButton.setEnabled(False)
        self.automationObject.start()
        logger.info("Start Running button pressed")
        while self.automationObject.isRunning() == False:
            logger.info("Waiting for Automation to start")
            time.sleep(1.0)
        return


    def whenSimulatorButtonClicked(self,event):
        __simulatorState = self.automationObject.isSimulatorEnabled()
        logger.info("Simulator State:"+str(__simulatorState)+"-->"+str(not __simulatorState))
        __simulatorState = not __simulatorState
        self.automationObject.setSimulatorState(__simulatorState)
        if __simulatorState:
            self.simulatorButton.setText("Disable Simulator")
        else:
            self.simulatorButton.setText("Enable Simulator")


    def whenLoadLayoutMapButtonClicked(self,event):
        layoutMapFilePath = jmriFileUtilSupport.getUserFilesPath()
        logger.info("User Files Path: %s" + layoutMapFilePath)
        fileChooser = JFileChooser(FileSystemView.getFileSystemView().getHomeDirectory())
        fileFilter =  FileNameExtensionFilter("XML Files", ["XML", "xml"])
        logger.info("FileFilter:%s",str(fileFilter))
        fileChooser.setFileFilter(fileFilter)   # addChoosableFileFilter(fileFilter)
        fileChooser.setCurrentDirectory(java.io.File(layoutMapFilePath))
        logger.info("LOAD LAYOUT MAP:%s", str(fileChooser))
        returnValue = fileChooser.showOpenDialog(None);
        if (returnValue == JFileChooser.APPROVE_OPTION):
            selectedFile = fileChooser.getSelectedFile();
            logger.info("Selected File:%s",selectedFile.getAbsolutePath())
        return

        
    def whenRemoveButtonClicked(self,event):
        return


    def whenCheckboxClicked(self,event):
        msg.setDebugFlag('eTrace',self.eMsgDebugCheckBox.isSelected())
        msg.setDebugFlag('dTrace',self.dMsgDebugCheckBox.isSelected())
        msg.setDebugFlag('iTrace',self.iMsgDebugCheckBox.isSelected())
        msg.setDebugFlag('oTrace',self.oMsgDebugCheckBox.isSelected())
        trolleyRoster.setDebugFlag('eTrace',self.eRstrDebugCheckBox.isSelected())
        trolleyRoster.setDebugFlag('dTrace',self.dRstrDebugCheckBox.isSelected())
        return


    def whenEditRosterButtonClicked(self,event):
        self.editRosterButton.setEnabled(False)
        self.frameRoster = self.createEditRosterDataFrame(trolleyRoster)
        return


    def whenEditRosterCloseButtonClicked(self,event):
        self.editRosterButton.setEnabled(True)
        self.frameRoster.dispose()
        return


    def whenCancelAddTrolleyButtonClicked(self,event):
        self.frameAddTrolley.dispose()
        self.frameRoster.setVisible(True)
        return


    def whenSaveAddTrolleyButtonClicked(self,event):
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
        self.frameRoster.setVisible(False)
        self.frameAddTrolley = self.createAddToTrolleyRosterFrame()
        return


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


    def setRosterColumnProperties(self, table, column, width=5, resizable=False):
        table.getColumnModel().getColumn(column).setPreferredWidth(width)
        table.getColumnModel().getColumn(column).setResizable(resizable)
        return


    def getAddTrolleyButtonPanel(self):
        saveButton = self.createButtonWithAction("Save", self.whenSaveAddTrolleyButtonClicked )
        cancelButton = self.createButtonWithAction("Cancel", self.whenCancelAddTrolleyButtonClicked )
        addTrolleyPanel = JPanel()
        addTrolleyPanel.setLayout(FlowLayout(FlowLayout.LEFT))
        addTrolleyPanel.add(saveButton)
        addTrolleyPanel.add(Box.createHorizontalStrut(10))
        addTrolleyPanel.add(cancelButton)
        return addTrolleyPanel


    def getAddTrolleyDataPanel(self):
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
        # =================================
        # create buttons panel actions
        # =================================
        self.quitButton = self.createButtonWithAction("Quit", self.whenQuitButtonClicked)
        self.loadRosterButton = self.createButtonWithAction("Load Roster", None)
        self.loadRosterButton.setEnabled(False)
        self.loadLayoutButton = self.createButtonWithAction("Load Layout Map", self.whenLoadLayoutMapButtonClicked)
        self.loadLayoutButton.setEnabled(True)
        self.tgoButton = self.createButtonWithAction("Start Running", self.whenTgoButtonClicked)
        self.tstopButton = self.createButtonWithAction("Stop All Trolleys", self.whenStopAllButtonClicked)
        self.tstopButton.setEnabled(False)           #button starts as grayed out (disabled)
        simulatorButtonTxt = "Disable Simulator" if self.automationObject.simulatorEnabled else "Enable Simulator"
        self.simulatorButton = self.createButtonWithAction(simulatorButtonTxt, self.whenSimulatorButtonClicked)
        self.editRosterButton = self.createButtonWithAction("Edit Roster", self.whenEditRosterButtonClicked)
        self.editRosterButton.setEnabled(True)
        # =================================
        # create button panel
        # =================================
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
        butPanel.add(self.loadLayoutButton)
        butPanel.add(Box.createHorizontalStrut(20))
        butPanel.add(self.quitButton)
        return butPanel


    def createInfoPane(self,defaultText, title=None, paneHeight=15):
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


    def createScrollPanel(self, DefaultText, title=None, paneHeight=10):
        __panel = JPanel()
        __panel.add(JLabel(title))
        scrollArea = JTextArea(DefaultText, paneHeight, 0) # AtsUI.atsWindowWidth)
        scrollArea.getCaret().setUpdatePolicy(DefaultCaret.ALWAYS_UPDATE); # automatically scroll to last message
        scrollArea.font=Font("monospaced", Font.PLAIN, AtsUI.atsFontSize)
        scrollArea.setText(DefaultText)
        scrollField = JScrollPane(scrollArea) #put text area in scroll field
        scrollField.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER)
        scrollField.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED)
        __panel.setBorder(BorderFactory.createEmptyBorder(1, 8, 1, 8))
        __panel.setLayout(BorderLayout())
        __panel.add(scrollField)
        __panel.setSize(AtsUI.atsMessageWindowWidth, paneHeight)
        return __panel


    def createApplicationWindowComponents(self):
        self.logLabel1 = JLabel("Logging:")
        self.eMsgDebugCheckBox = JCheckBox("Message Function Entry/Exit", actionPerformed = self.whenCheckboxClicked)
        self.eMsgDebugCheckBox.setToolTipText("Display all function entry/exit messages")
        self.dMsgDebugCheckBox = JCheckBox("Message Details", actionPerformed = self.whenCheckboxClicked)
        self.dMsgDebugCheckBox.setToolTipText("Display detail debugging for messages")
        self.iMsgDebugCheckBox = JCheckBox("Incoming Messages", actionPerformed = self.whenCheckboxClicked)
        self.iMsgDebugCheckBox.setToolTipText("Display debugging for incoming loconet messages")
        self.oMsgDebugCheckBox = JCheckBox("Outgoing Messages", actionPerformed = self.whenCheckboxClicked)
        self.oMsgDebugCheckBox.setToolTipText("Display debugging for outgoing loconet messages")
        self.eRstrDebugCheckBox = JCheckBox("TrolleyRoster Function Entry/Exit", actionPerformed = self.whenCheckboxClicked)
        self.eRstrDebugCheckBox.setToolTipText("Display all Trolley Roster function entry/exit messages")
        self.dRstrDebugCheckBox = JCheckBox("TrolleyRoster Details", actionPerformed = self.whenCheckboxClicked)
        self.dRstrDebugCheckBox.setToolTipText("Display detail debugging for TrolleyRoster")
        self.dRstrDebugCheckBox.setEnabled(False)
        self.snChgCheckBox = JCheckBox("Show Sn Change")
        self.snChgCheckBox.setToolTipText("Display when a sensor state changes")
        self.snChgCheckBox.setEnabled(False)
        self.snSpkChgCheckBox = JCheckBox("Speak Sn Change")
        self.snSpkChgCheckBox.setToolTipText("Speak when a sensor state changes")
        self.snSpkChgCheckBox.setEnabled(False)
        self.msgSpkCheckBox = JCheckBox("Speak General Messages")
        self.msgSpkCheckBox.setToolTipText("Speak when a message is sent")
        self.msgSpkCheckBox.setSelected(True)

        # ====================================
        # create checkboxes panel
        # ====================================
        self.ckBoxPanel1 = JPanel()
        self.ckBoxPanel1.setLayout(FlowLayout(FlowLayout.RIGHT))
        self.ckBoxPanel1.add(self.logLabel1)

        self.ckBoxPanel2 = JPanel()
        self.ckBoxPanel2.setLayout(FlowLayout(FlowLayout.LEFT))
        self.ckBoxPanel2.add(self.eMsgDebugCheckBox)
        self.ckBoxPanel2.add(self.dMsgDebugCheckBox)
        self.ckBoxPanel2.add(self.iMsgDebugCheckBox)
        self.ckBoxPanel2.add(self.oMsgDebugCheckBox)

        self.ckBoxPanel3 = JPanel()
        self.ckBoxPanel3.setLayout(FlowLayout(FlowLayout.LEFT))
        self.ckBoxPanel3.add(self.eRstrDebugCheckBox)
        self.ckBoxPanel3.add(self.dRstrDebugCheckBox)
        self.ckBoxPanel3.add(self.snSpkChgCheckBox)
        self.ckBoxPanel3.add(self.msgSpkCheckBox)

        # =====================================
        # create text fields for status outputs
        # =====================================
        self.blockInfoPane = self.createInfoPane(layoutMap.getBlockStatus(trolleyRoster), title="Block Status")
        self.segmentInfoPane = self.createInfoPane(layoutMap.getSegmentStatus(trolleyRoster), title="Segment Status")
        self.rosterInfoPane = self.createInfoPane(trolleyRoster.getRosterStatus(), title="Trolley Roster Status")
        self.messageInfoPanel = self.createScrollPanel("Default Message Panel\n"+
                                             "Currently All messages will be written to the Script Output window",
                                             title = "Messages")


    class DeleteTrolleyButtonListener(MouseAdapter):
        logger = logging.getLogger(__name__)
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
                logger.info("DELETE Trolley Roster item %s - Address: %s", str(row), str(trolleyRoster[row].address))
                __response = self.deleteTrolleyFromRosterConfirmation("Delete Trolley #"+str(trolleyRoster[row].address),"Delete Trolley")
                logger.info("DELETE Trolley: %s - %s", str(trolleyRoster[row].address),
                            ("Confirmed" if __response == 0 else "Cancelled"))
                if __response == 0: 
                    trolleyRoster.delete(row)
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
            result = JOptionPane.showConfirmDialog(None, message,  title, JOptionPane.OK_CANCEL_OPTION)
            return result





