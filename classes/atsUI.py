import logging
import time

from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.messengerFacade import Messenger
from classes.blockMap import BlockMap
from classes.block import Block
from classes.atsWinListener import AtsWinListener

import javax.swing
import java.awt.Color
from javax.swing.text import DefaultCaret, StyleConstants
from javax.swing.border import EmptyBorder
from java.awt import Font, GridBagConstraints, BorderLayout
from java.awt import Insets as awtInsets
from javax.swing import JLabel, JScrollPane, JOptionPane, JSpinner,\
    SpinnerListModel, SpinnerNumberModel
from javax.swing.table import DefaultTableModel
from java.awt.event import MouseAdapter
from com.sun.beans.editors import NumberEditor

try:
    jmriFlag = True
    import jmri
    print('Successfully Imported jmri')
except ImportError:
    jmriFlag = False
    print('Failed to import jmir - bypassing')

ATS_MESSAGE_FONT_SIZE = 12
ATS_MESSAGE_WINDOW_PANE_WIDTH = 1500
ATS_ROSTER_WINDOW_PANE_WIDTH = 1200
ATS_MESSAGE_WINDOW_WIDTH = 100
ATS_ROSTER_ROW_HEIGHT = 30


logger = logging.getLogger("ATS."+__name__)
trolleyRoster = TrolleyRoster()
layoutMap = BlockMap()
msg = Messenger()

class AtsUI(object):
    
    instance = None
    
    def __init__(self, automationObject=None, appName=None):
        # ------------------------------------------------------------------------------------------
        # create a frame to hold the buttons and fields
        # also create a window listener. This is used mainly to remove the property change listener
        # when the window is closed by clicking on the window close button
        # ------------------------------------------------------------------------------------------
        super(AtsUI, self).__init__()
        self.automationObject=automationObject
        self.w = AtsWinListener()
        self.fr = jmri.util.JmriJFrame(appName) #use this in order to get it to appear on webserver
        self.fr.contentPane.setLayout(java.awt.GridBagLayout())
        self.createAtsApplicatinWindowComponents()
        self.addComponent(self.fr, self.getButtonPanel(), 0, 0, 2, 1, GridBagConstraints.PAGE_START, GridBagConstraints.NONE);
        self.addComponent(self.fr, self.ckBoxPanel1, 0, 1, 1, 2, GridBagConstraints.LINE_START, GridBagConstraints.NONE)
        self.addComponent(self.fr, self.ckBoxPanel2, 1, 1, 1, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.ckBoxPanel3, 1, 2, 1, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        #self.addComponent(self.fr, getRosterPanel(trolleyRoster), 0, 4, 1, 1, GridBagConstraints.LINE_START, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.blockInfoPane, 0, 5, 2, 5, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.segmentInfoPane, 0, 15, 2, 5, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.rosterInfoPane, 0, 20, 2, 7, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.addComponent(self.fr, self.messageInfoPanel, 0, 30, 2, 7, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
        self.fr.addWindowListener(self.w)
        self.fr.pack()
        self.fr.setVisible(True)


    def __new__(cls, automationObject=None, appName=None): # __new__ always a class method
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
        #global editRosterButton, tstopButton, tgoButton, simulatorButton, quitButton
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
        #global tstopButton, tgoButton, simulatorButton, quitButton
        self.tstopButton.setEnabled(False)           #button starts as grayed out (disabled)
        self.tgoButton.setEnabled(False)           #button starts as grayed out (disabled)
        if self.automationObject.isRunning(): self.automationObject.stop()
        trolleyRoster.destroy()
        self.fr.dispose()         #close the pane (window)
        return


    def whenTgoButtonClicked(self,event):
        #global editRosterButton, tstopButton, tgoButton, simulatorButton, quitButton
        self.editRosterButton.setEnabled(False)
        self.tstopButton.setEnabled(True)           #button starts as grayed out (disabled)
        self.tgoButton.setEnabled(False)           #button starts as grayed out (disabled)
        self.quitButton.setEnabled(False)
        self.automationObject.start()
        logger.info("Start Running button pressed")
        while self.automationObject.isRunning() == False:
            logger.info("Waiting for Automation to start")
            time.sleep(1.0)
        return


    def whenSimulatorButtonClicked(self,event):
        #global tstopButton, tgoButton, simulatorButton, quitButton
        simulatorState = self.automationObject.isSimulatorEnabled()
        logger.info("Simulator State:"+str(simulatorState)+"-->"+str(not simulatorState))
        simulatorState = not simulatorState
        self.automationObject.setSimulatorState(simulatorState)
        if simulatorState:
            self.simulatorButton.setText("Disable Simulator")
        else:
            self.simulatorButton.setText("Enable Simulator")


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
        #global frameRoster
        self.editRosterButton.setEnabled(False)
        self.frameRoster = self.createEditRosterDataFrame(trolleyRoster)
        #frameRoster.setVisible(True)
        return


    def whenEditRosterCloseButtonClicked(self,event):
        #global frameRoster
        self.editRosterButton.setEnabled(True)
        #frameRoster.setVisible(False)
        self.frameRoster.dispose()
        return


    def whenCancelAddTrolleyButtonClicked(self,event):
        #global frameAddTrolley
        #editRosterButton.setEnabled(True)
        #frameRoster.setVisible(False)
        self.frameAddTrolley.dispose()
        self.frameRoster.setVisible(True)
        return


    def whenSaveAddTrolleyButtonClicked(self,event):
        #global frameAddTrolley, frameRoster
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
        #frameRoster.setVisible(False)
        trolleyRoster.dump()
        self.frameAddTrolley.dispose()
        # The revalidate and repaint methods don't seem to work so for now we just dispose of the
        # original roster frame and recreate it so the new trolley is displayed.
        #frameRoster.revalidate() 
        #frameRoster.repaint()
        self.frameRoster.dispose()
        self.frameRoster = self.createEditRosterDataFrame(trolleyRoster)
        self.frameRoster.setVisible(True)
        return
    
    
    def whenAddToRosterButtonClicked(self,event):
        #global frameAddTrolley
        self.frameRoster.setVisible(False)
        self.frameAddTrolley = self.createAddToTrolleyRosterFrame()
        return
    
    
    def sendAudibleMessage(self,checkboxToMonitor, messageToAnnounce):
        if checkboxToMonitor.isSelected() :
            javaexec = getattr(java.lang.Runtime.getRuntime(), "exec")
            pid = javaexec('nircmd speak text "' + messageToAnnounce +'" -2 100')
            pid.waitFor()
        return
    
    
    def addComponent(self, container, component, gridx, gridy, gridwidth, gridheight, anchor, fill):
        insets=awtInsets(5, 5, 5, 5)
        ipadx = 0
        ipady = 5
        weightx = weighty = 0.0
        gbc = GridBagConstraints(gridx, gridy, gridwidth, gridheight, weightx, weighty, anchor, fill, insets, ipadx, ipady)
        container.add(component, gbc)
    
    
    def setRosterColumnProperties(self, table, column, width=5, resizable=False):
        table.getColumnModel().getColumn(column).setPreferredWidth(width)
        table.getColumnModel().getColumn(column).setResizable(resizable)
        return
    
    def getAddTrolleyButtonPanel(self):
        #global editRosterButton, tstopButton, tgoButton, simulatorButton, quitButton
        # =================================
        # create buttons panel actions
        # =================================
        saveButton = javax.swing.JButton("Save")
        saveButton.actionPerformed = self.whenSaveAddTrolleyButtonClicked 
        cancelButton = javax.swing.JButton("Cancel")
        cancelButton.actionPerformed = self.whenCancelAddTrolleyButtonClicked
        addTrolleyPanel = javax.swing.JPanel()
        addTrolleyPanel.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
        addTrolleyPanel.add(saveButton)
        addTrolleyPanel.add(javax.swing.Box.createHorizontalStrut(10)) #empty vertical space between buttons
        addTrolleyPanel.add(cancelButton)
        return addTrolleyPanel
    
    
    def getAddTrolleyDataPanel(self):
        #global addTrolleyAddress, addTrolleyMaxSpeed, addTrolleySoundEnabled, addTrolleyStartingPosition
        __panel = javax.swing.JPanel()
        __panel.add(JLabel("Address:"))
        self.addTrolleyAddress = javax.swing.JTextField('',5)
        __panel.add(self.addTrolleyAddress)
        __panel.add(JLabel("Max Speed:"))
        self.addTrolleyMaxSpeed = javax.swing.JTextField('',5)
        __panel.add(self.addTrolleyMaxSpeed)
        __panel.add(JLabel("Sound Enabled:"))
        self.addTrolleySoundEnabled = javax.swing.JCheckBox()
        __panel.add(self.addTrolleySoundEnabled)
        __panel.add(JLabel("Starting Position:"))
        comboChoices = []
        for block in layoutMap:
            comboChoices.append(str(block.address)+'-'+block.description)
        self.addTrolleyStartingPosition = javax.swing.JComboBox(comboChoices)
        __panel.add(self.addTrolleyStartingPosition)
        return __panel
    
    
    def createAddToTrolleyRosterFrame(self):
        frameAddTrolley = jmri.util.JmriJFrame("Add Trolley To Roster")
        frameAddTrolley.setSize(ATS_MESSAGE_WINDOW_PANE_WIDTH,ATS_ROSTER_ROW_HEIGHT+50)
        frameAddTrolley.setLayout(java.awt.GridBagLayout())
        self.addComponent(frameAddTrolley, self.getAddTrolleyButtonPanel(), 0, 0, 2, 1, GridBagConstraints.PAGE_START, GridBagConstraints.NONE)
        self.addComponent(frameAddTrolley, self.getAddTrolleyDataPanel(), 0, 2, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.NONE)
        frameAddTrolley.setDefaultCloseOperation(self.frameRoster.DO_NOTHING_ON_CLOSE); # Disable the Close button
        #frameAddTrolley.setDefaultCloseOperation(frameRoster.DISPOSE_ON_CLOSE); # Disable the Close button
        frameAddTrolley.pack()
        frameAddTrolley.setVisible(True)
        return frameAddTrolley


    def createEditRosterDataFrame(self,trolleyRoster):
        frameRoster = jmri.util.JmriJFrame("Trolley Roster")
        frameRoster.setSize(ATS_ROSTER_WINDOW_PANE_WIDTH,len(trolleyRoster)*ATS_ROSTER_ROW_HEIGHT+100)
        frameRoster.setLayout(java.awt.BorderLayout())
        rosterData = []
        for trolley in trolleyRoster:
            deleteRosterRowButton = javax.swing.JButton("Delete")
            deleteRosterRowButton.actionPerformed = None #whenDeleteRosterRowButtonClicked
            rosterData.append([trolley.address, trolley.maxSpeed, trolley.soundEnabled,
                               trolley.currentPosition.address, trolley.currentPosition.description,'DELETE'])
        colNames = ['Address', 'Max Speed', 'Sound', 'Starting Position', 'Position Description', '']
        dataModel = DefaultTableModel(rosterData,colNames)
        rosterTable = javax.swing.JTable(dataModel)
        rosterTable.getTableHeader().setReorderingAllowed(False)
    #    rosterTable.setDefaultRenderer(rosterTable.getColumnClass(5), rosterTable.DefaultTableCellRenderer.setHorizontalAlignment(javax.swing.SwingConstants.CENTER))
        rosterTable.setRowHeight(ATS_ROSTER_ROW_HEIGHT)
        rosterTable.setEnabled(True)
        rosterTable.addMouseListener(self.DeleteTrolleyButtonListener())
        self.setRosterColumnProperties(rosterTable, 0)
        self.setRosterColumnProperties(rosterTable, 1)
        self.setRosterColumnProperties(rosterTable, 2, width=10)
        self.setRosterColumnProperties(rosterTable, 3, width=75)
        self.setRosterColumnProperties(rosterTable, 4, width=200)
        self.setRosterColumnProperties(rosterTable, 5, width=10)
        rosterScrollPane = JScrollPane()
        rosterScrollPane.setPreferredSize(java.awt.Dimension(ATS_ROSTER_WINDOW_PANE_WIDTH,len(trolleyRoster)*ATS_ROSTER_ROW_HEIGHT+100))
        rosterScrollPane.getViewport().setView(rosterTable)
        rosterPanel = javax.swing.JPanel()
        rosterPanel.add(rosterScrollPane)
        rosterAddButton = javax.swing.JButton("Add To Roster")
        rosterAddButton.actionPerformed = self.whenAddToRosterButtonClicked
        rosterAddButton.setEnabled(True)
        rosterCloseButton = javax.swing.JButton("Close")
        rosterCloseButton.actionPerformed = self.whenEditRosterCloseButtonClicked
        frameRoster.add(rosterAddButton, BorderLayout.PAGE_START)
        frameRoster.add(rosterPanel, BorderLayout.CENTER)
        frameRoster.add(rosterCloseButton, BorderLayout.PAGE_END)
        frameRoster.setDefaultCloseOperation(frameRoster.DO_NOTHING_ON_CLOSE); # Disable the Close button
        frameRoster.pack()
        frameRoster.setVisible(True)
        return frameRoster
    
    
    def getButtonPanel(self):
        #global editRosterButton, tstopButton, tgoButton, simulatorButton, quitButton
        # =================================
        # create buttons panel actions
        # =================================
        self.quitButton = javax.swing.JButton("Quit")
        self.quitButton.actionPerformed = self.whenQuitButtonClicked
        self.tgoButton = javax.swing.JButton("Start Running")
        self.tgoButton.actionPerformed = self.whenTgoButtonClicked
        self.tstopButton = javax.swing.JButton("Stop All Trolleys")
        self.tstopButton.setEnabled(False)           #button starts as grayed out (disabled)
        self.tstopButton.actionPerformed = self.whenStopAllButtonClicked
        simulatorButtonTxt = "Disable Simulator" if self.automationObject.simulatorEnabled else "Enable Simulator"
        self.simulatorButton = javax.swing.JButton(simulatorButtonTxt)
        self.simulatorButton.actionPerformed = self.whenSimulatorButtonClicked
        self.editRosterButton = javax.swing.JButton("Edit Roster")
        self.editRosterButton.setEnabled(True)
        self.editRosterButton.actionPerformed = self.whenEditRosterButtonClicked
        # =================================
        # create button panel
        # =================================
        butPanel = javax.swing.JPanel()
        butPanel.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
        butPanel.add(self.editRosterButton)
        butPanel.add(javax.swing.Box.createHorizontalStrut(20)) #empty vertical space between buttons
        butPanel.add(self.tgoButton)
        butPanel.add(javax.swing.Box.createHorizontalStrut(20)) #empty vertical space between buttons
        butPanel.add(self.tstopButton)
        butPanel.add(javax.swing.Box.createHorizontalStrut(20)) #empty vertical space between buttons
        butPanel.add(self.simulatorButton)
        butPanel.add(javax.swing.Box.createHorizontalStrut(20)) #empty vertical space between buttons
        butPanel.add(self.quitButton)
        return butPanel


    def createInfoPane(self,defaultText, title = None):
        __pane = javax.swing.JTextPane()
        __doc = __pane.getStyledDocument()
        __style = __pane.addStyle("Color Style", None)
        __pane.setFont(Font("monospaced",Font.BOLD,ATS_MESSAGE_FONT_SIZE))
        __pane.setBorder(EmptyBorder(10,10,10,10))
        __pane.setBorder(javax.swing.BorderFactory.createLineBorder(java.awt.Color.BLACK))
        if title is not None:
            __pane.insertComponent(JLabel(title))
        StyleConstants.setForeground(__style,java.awt.Color.BLUE)
        __doc.insertString(__doc.getLength(),defaultText,__style)
        return __pane


    def createScrollPanel(self, DefaultText, title = None):
        __panel = javax.swing.JPanel()
        __panel.add(JLabel(title))
        scrollArea = javax.swing.JTextArea(10, ATS_MESSAGE_WINDOW_WIDTH)
        scrollArea.getCaret().setUpdatePolicy(DefaultCaret.ALWAYS_UPDATE); # automatically scroll to last message
        scrollArea.font=Font("monospaced", Font.PLAIN, ATS_MESSAGE_FONT_SIZE)
        scrollArea.setText(DefaultText)
        scrollField = javax.swing.JScrollPane(scrollArea) #put text area in scroll field
        scrollField.setHorizontalScrollBarPolicy(javax.swing.JScrollPane.HORIZONTAL_SCROLLBAR_NEVER)
        scrollField.setVerticalScrollBarPolicy(javax.swing.JScrollPane.VERTICAL_SCROLLBAR_ALWAYS)
        __panel.setBorder(javax.swing.BorderFactory.createEmptyBorder(1, 8, 1, 8))
        __panel.setLayout(java.awt.BorderLayout())
        __panel.add(scrollField)
        return __panel



    def createAtsApplicatinWindowComponents(self):
        self.logLabel1 = javax.swing.JLabel("Logging:")
        self.eMsgDebugCheckBox = javax.swing.JCheckBox("Message Function Entry/Exit", actionPerformed = self.whenCheckboxClicked)
        self.eMsgDebugCheckBox.setToolTipText("Display all function entry/exit messages")
        self.dMsgDebugCheckBox = javax.swing.JCheckBox("Message Details", actionPerformed = self.whenCheckboxClicked)
        self.dMsgDebugCheckBox.setToolTipText("Display detail debugging for messages")
        self.iMsgDebugCheckBox = javax.swing.JCheckBox("Incoming Messages", actionPerformed = self.whenCheckboxClicked)
        self.iMsgDebugCheckBox.setToolTipText("Display debugging for incoming loconet messages")
        self.oMsgDebugCheckBox = javax.swing.JCheckBox("Outgoing Messages", actionPerformed = self.whenCheckboxClicked)
        self.oMsgDebugCheckBox.setToolTipText("Display debugging for outgoing loconet messages")
        
        self.eRstrDebugCheckBox = javax.swing.JCheckBox("TrolleyRoster Function Entry/Exit", actionPerformed = self.whenCheckboxClicked)
        self.eRstrDebugCheckBox.setToolTipText("Display all Trolley Roster function entry/exit messages")
        self.dRstrDebugCheckBox = javax.swing.JCheckBox("TrolleyRoster Details", actionPerformed = self.whenCheckboxClicked)
        self.dRstrDebugCheckBox.setToolTipText("Display detail debugging for TrolleyRoster")
        self.dRstrDebugCheckBox.setEnabled(False)
        
        #logLabel2 = javax.swing.JLabel("        ")
        self.snChgCheckBox = javax.swing.JCheckBox("Show Sn Change")
        self.snChgCheckBox.setToolTipText("Display when a sensor state changes")
        self.snChgCheckBox.setEnabled(False)
        self.snSpkChgCheckBox = javax.swing.JCheckBox("Speak Sn Change")
        self.snSpkChgCheckBox.setToolTipText("Speak when a sensor state changes")
        self.snSpkChgCheckBox.setEnabled(False)
        self.msgSpkCheckBox = javax.swing.JCheckBox("Speak General Messages")
        self.msgSpkCheckBox.setToolTipText("Speak when a message is sent")
        self.msgSpkCheckBox.setSelected(True)

        # ====================================
        # create checkboxes panel
        # ====================================
        self.ckBoxPanel1 = javax.swing.JPanel()
        self.ckBoxPanel1.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
        self.ckBoxPanel1.add(self.logLabel1)
        
        self.ckBoxPanel2 = javax.swing.JPanel()
        self.ckBoxPanel2.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
        self.ckBoxPanel2.add(self.eMsgDebugCheckBox)
        self.ckBoxPanel2.add(self.dMsgDebugCheckBox)
        self.ckBoxPanel2.add(self.iMsgDebugCheckBox)
        self.ckBoxPanel2.add(self.oMsgDebugCheckBox)
        
        self.ckBoxPanel3 = javax.swing.JPanel()
        self.ckBoxPanel3.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
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
            #global frameRoster
            __target = event.getSource()
            __row = __target.getSelectedRow()
            __column = __target.getSelectedColumn()
            if __column == 1:
                self.updateTrolleyRowMaxSpeed(__row)
            if __column == 3:
                self.updateTrolleyPosition(__row)
            if __column == 5: 
                self.deleteTrolleyRowFromRoster(__row)



        def updateTrolleyRowMaxSpeed(self, row):
                logger.info("Request to UPDATE SPEED for Trolley Roster item %s - Address: %s", str(row), str(trolleyRoster[row].address))
                spinner = JSpinner( SpinnerNumberModel( trolleyRoster[row].maxSpeed, 1, 99, 1) )
                __response = JOptionPane.showOptionDialog(None, spinner, "Update Max Speed", JOptionPane.OK_CANCEL_OPTION, JOptionPane.QUESTION_MESSAGE, None, None, None)
                #JOptionPane.showOptionDialog(null, spinner, "Enter valid number", JOptionPane.OK_CANCEL_OPTION, JOptionPane.QUESTION_MESSAGE, null, null, null);
                #__response = self.deleteTrolleyFromRosterConfirmation("Update Trolley #"+str(trolleyRoster[row].address),"Update Trolley")
                #result = JOptionPane.showInputDialog(None, message,  "Delete Trolley", JOptionPane.OK_CANCEL_OPTION)
                #__response = self.deleteTrolleyFromRosterConfirmation("Update Trolley #"+str(trolleyRoster[row].address), "Update Trolley")
                logger.info("Request to Update Trolley: %s to %s - %s", str(trolleyRoster[row].address),
                            str(spinner.getValue()), ("Confirmed" if __response == 0 else "Cancelled"))
                if __response == JOptionPane.OK_OPTION: 
                    trolleyRoster[row].maxSpeed = int(spinner.getValue())
                    trolleyRoster.dump()
                    AtsUI.instance.frameRoster.dispose()
                    AtsUI.instance.frameRoster = AtsUI.instance.createEditRosterDataFrame(trolleyRoster)
                    AtsUI.instance.frameRoster.setVisible(True)


        def updateTrolleyPosition(self, row):
                logger.info("Request to UPDATE POSITION for Trolley Roster item %s - Address: %s", str(row), str(trolleyRoster[row].address))
                positionChoices = []
                for block in layoutMap:
                    positionChoices.append(str(block.address)+'-'+block.description)
                index = trolleyRoster[row].currentPosition.index
                spinner = JSpinner( SpinnerListModel( positionChoices ) )
                __response = JOptionPane.showInputDialog(None, "Choice", "Update Position", JOptionPane.OK_CANCEL_OPTION, None, positionChoices, positionChoices[index])
                #JOptionPane.showOptionDialog(null, spinner, "Enter valid number", JOptionPane.OK_CANCEL_OPTION, JOptionPane.QUESTION_MESSAGE, null, null, null);
                #__response = self.deleteTrolleyFromRosterConfirmation("Update Trolley #"+str(trolleyRoster[row].address),"Update Trolley")
                #result = JOptionPane.showInputDialog(None, message,  "Delete Trolley", JOptionPane.OK_CANCEL_OPTION)
                #__response = self.deleteTrolleyFromRosterConfirmation("Update Trolley #"+str(trolleyRoster[row].address), "Update Trolley")
                logger.info("Request to UPDATE POSITION Trolley: %s to %s - %s", str(trolleyRoster[row].address),
                            str(__response), ("Confirmed" if __response else "CANCELLED"))
                if __response: 
                    #trolleyRoster[row].maxSpeed = int(spinner.getValue())
                    trolleyRoster[row].currentPosition = layoutMap.findBlockByAddress(int(__response.split('-')[0]))
                    trolleyRoster[row].nextPosition = trolleyRoster[row].currentPosition.next
                    trolleyRoster.dump()
                    AtsUI.instance.frameRoster.dispose()
                    AtsUI.instance.frameRoster = AtsUI.instance.createEditRosterDataFrame(trolleyRoster)
                    AtsUI.instance.frameRoster.setVisible(True)

            
            
        def deleteTrolleyRowFromRoster(self, row):
                logger.info("Request to DELETE Trolley Roster item %s - Address: %s", str(row), str(trolleyRoster[row].address))
                __response = self.deleteTrolleyFromRosterConfirmation("Delete Trolley #"+str(trolleyRoster[row].address),"Delete Trolley")
                logger.info("Request to DELETE Trolley: %s - %s", str(trolleyRoster[row].address),
                            ("Confirmed" if __response == 0 else "Cancelled"))
                if __response == 0: 
                    trolleyRoster.delete(row)
                    trolleyRoster.dump()
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





