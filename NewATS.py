'''
ATS (Automatic Trolley Sequencer)
@author: ttb

This script has been modified to read in trolley block 
occupancy messages and control the speed of the related
trolleys as they move around the same track loop.

This is built on a set of code which can display
each sensor event and/or speak it for debugging purposes.

Based on ATS.py written by 
    Gerry Wolfson, 
    October 9, 1942 - April 8, 2018
    Member: Northern Virginia Model Railroad
    URL: http://nvmr.org
'''
import time
import logging
import os.path
from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.blockMap import BlockMap
from classes.block import Block
from classes.announcer import MessageAnnouncer
from classes.messengerFacade import Messenger
from classes.atsWinListener import AtsWinListener
from classes.atsTrolleyAutomation import TrolleyAutomation

import javax.swing
import java.awt.Color
from javax.swing.text import DefaultCaret, StyleConstants
from javax.swing.border import EmptyBorder
from java.awt import Font, GridBagConstraints, BorderLayout
from java.awt import Insets as awtInsets
from javax.swing import JLabel, JScrollPane, JOptionPane
from javax.swing.table import DefaultTableModel
from java.awt.event import MouseAdapter

print "ATS Start"

try:
    jmriFlag = True
    import jmri
    print('Successfully Imported jmri')
except ImportError:
    jmriFlag = False
    print('Failed to import jmir - bypassing')

TROLLEY_ROSTER_ADDRESS_FILE = "trolleyRosterAddresses.cfg"
ATS_MESSAGE_FONT_SIZE = 30
ATS_MESSAGE_WINDOW_PANE_WIDTH = 2400
ATS_ROSTER_WINDOW_PANE_WIDTH = 1500
ATS_MESSAGE_WINDOW_WIDTH = 100
ATS_ROSTER_ROW_HEIGHT = 30
__apNameVersion = "New Automatic Trolley Sequencer"
enableSimulator = False
__fus = jmri.util.FileUtilSupport()

#logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger("ATS")
if not len(logger.handlers):
    fileHandler = logging.FileHandler("{0}/{1}.log".format(__fus.getUserFilesPath(),'NewATS'))
    fileHandler.setLevel(logging.INFO)
    fileHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)
    logger.setLevel(logging.INFO)

print("Log File Path:"+__fus.getUserFilesPath())

msg = Messenger()
msg.createListener()
# create a TrolleyAutomation object
trolleyAutomationObject = TrolleyAutomation()


#Trolley.setMessageManager(msgManager = msg)        
logger.info("Initialize Empty Layout Map")
layoutMap = BlockMap() # Initialize and empty block map to define the layout
logger.info("Initialize Empty Trolley Roster")
trolleyRoster = TrolleyRoster(layoutMap=layoutMap)  # Initialize an empty roster of trolley devices


def buildLayoutMap(layout):
    # Create a layoutMap map that consists of consecutive blocks representing a complete 
    # circuit. The map also identifies the segment associated with each block. This is
    # done because so a multiple block area can be identified as occupied.
    #    
    #        --100/1--                                                                                      ----103/6---*
    #      /          \                                                                                    /             \
    #     /            *                                                                                  /               \
    #     *             \                                                                                *                |
    #      \             --106/10---*----121/9-----*---123/8---*-----120/7----*-\                       /                /
    #       \                                                                    >--102/6--*---107/6---<-*----104/6----/ 
    #         -----101/2-----*------118/3------*-----116/4-----*-----117/5----*-/
    #
    # Trolley Sequencing
    # Block 100 - Thomas Loop
    # Block 101 - Spencer Station Isle Side
    # Block 118 - Spencer Boulevard Isle Side
    # Block 116 - Traffic Intersection Isle Side
    # Block 117 - Single Track Signal Block Isle Side
    # Block 102 - Single Track Spencer Side
    # Block 107 - Single Track Majolica Side
    # Block 104 - Majolica Outbound Loop
    # Block 103 - Majolica Return Loop
    # Block 107 - Single Track Majolica End
    # Block 102 - Single Track Spencer End
    # Block 120 - Spencer Boulevard Interchange Yard Side 
    # Block 123 - Spencer Boulevard Shelter Yard Side
    # Block 121 - Spencer Boulevard Buckholtz Yard Side
    # Block 106 - Spencer Station Yard Side
    #
    layout.append(Block(blockAddress=100, newSegment=True,  stopRequired=True,  length=24,  description='Thomas Loop'))
    layout.append(Block(blockAddress=101, newSegment=True,  stopRequired=False, length=130, description='Spencer Station Isle Side'))
    layout.append(Block(blockAddress=118, newSegment=True,  stopRequired=False, length=30,  description='Spencer Boulevard Isle Side'))
    layout.append(Block(blockAddress=116, newSegment=True,  stopRequired=True,  length=135, description='Traffic Intersection Isle Side'))
    layout.append(Block(blockAddress=117, newSegment=True,  stopRequired=False, length=20,  description='Single Track Signal Block Isle Side'))
    layout.append(Block(blockAddress=102, newSegment=True,  stopRequired=False, length=48,  description='Single Track Spencer Side'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica Side'))
    layout.append(Block(blockAddress=104, newSegment=False, stopRequired=False, length=40,  description='Majolica Outbound Loop'))
    layout.append(Block(blockAddress=103, newSegment=False, stopRequired=False, length=30,  description='Majolica Return Loop'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica End'))
    layout.append(Block(blockAddress=102, newSegment=False, stopRequired=False, length=48,  description='Single Track Spencer End'))
    layout.append(Block(blockAddress=120, newSegment=True,  stopRequired=False, length=114, description='Spencer Boulevard Interchange Yard Side'))
    layout.append(Block(blockAddress=123, newSegment=True,  stopRequired=True,  length=72,  description='Spencer Boulevard Shelter Yard Side'))
    layout.append(Block(blockAddress=121, newSegment=True,  stopRequired=False, length=84,  description='Spencer Boulevard Buckholtz Yard Side'))
    layout.append(Block(blockAddress=106, newSegment=True,  stopRequired=True,  length=28,  description='Spencer Station Yard Side'))


def buildTrolleyRoster(trolleyRoster, blockMap):
    # When building a roster you need to provide the layout map so that the starting 
    # potisions of the trolleys can be validated. The roster is built prior to sending any
    # requests to JMRI for slots. Slot registration should occur in the handler on a one by one
    # basis to avoid conflicts.
    trolleyRosterFile = __fus.getUserFilesPath() + TROLLEY_ROSTER_ADDRESS_FILE
    if os.path.isfile(trolleyRosterFile):
        logger.info("Trolley Roster Address File: %s",trolleyRosterFile)
    else:
        logger.info("Creating default trolley Roster")
    trolleyRoster.append(Trolley(blockMap, address=501, maxSpeed=50, soundEnabled=True, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=502, maxSpeed=40, soundEnabled=False, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=503, maxSpeed=80, soundEnabled=True, currentPosition=106)) 
    trolleyRoster.append(Trolley(blockMap, address=504, maxSpeed=50, soundEnabled=False, currentPosition=106)) 


# *************************************
# start to initialize the display GUI *
# *************************************
def whenStopAllButtonClicked(event):
    global trolleyAutomationObject
    global editRosterButton, tstopButton, tgoButton, simulatorButton, quitButton
    editRosterButton.setEnabled(True)
    tstopButton.setEnabled(False)
    tgoButton.setEnabled(True)
    quitButton.setEnabled(True)
    trolleyAutomationObject.stop()
    logger.info("Stop All Trolleys button pressed")
    trolleyRoster.stopAllTrolleys()
    trolleyRoster.dump()
    return


def whenQuitButtonClicked(event):
    global trolleyAutomationObject
    global tstopButton, tgoButton, simulatorButton, quitButton
    tstopButton.setEnabled(False)           #button starts as grayed out (disabled)
    tgoButton.setEnabled(False)           #button starts as grayed out (disabled)
    if trolleyAutomationObject.isRunning(): trolleyAutomationObject.stop()
    trolleyRoster.destroy()
    fr.dispose()         #close the pane (window)
    return


def whenTgoButtonClicked(event):
    global trolleyAutomationObject
    global editRosterButton, tstopButton, tgoButton, simulatorButton, quitButton
    editRosterButton.setEnabled(False)
    tstopButton.setEnabled(True)           #button starts as grayed out (disabled)
    tgoButton.setEnabled(False)           #button starts as grayed out (disabled)
    quitButton.setEnabled(False)
    trolleyAutomationObject.start()
    logger.info("Start Running button pressed")
    while trolleyAutomationObject.isRunning() == False:
        logger.info("Waiting for Automation to start")
        time.sleep(1.0)
    return


def whenSimulatorButtonClicked(event):
    global tstopButton, tgoButton, simulatorButton, quitButton
    simulatorState = trolleyAutomationObject.isSimulatorEnabled()
    logger.info("Simulator State:"+str(simulatorState)+"-->"+str(not simulatorState))
    simulatorState = not simulatorState
    trolleyAutomationObject.setSimulatorState(simulatorState)
    if simulatorState:
        simulatorButton.setText("Disable Simulator")
    else:
        simulatorButton.setText("Enable Simulator")


def whenRemoveButtonClicked(event):
    global trolleyAutomationObject
    return


def whenCheckboxClicked(event):
    msg.setDebugFlag('eTrace',eMsgDebugCheckBox.isSelected())
    msg.setDebugFlag('dTrace',dMsgDebugCheckBox.isSelected())
    msg.setDebugFlag('iTrace',iMsgDebugCheckBox.isSelected())
    msg.setDebugFlag('oTrace',oMsgDebugCheckBox.isSelected())
    trolleyRoster.setDebugFlag('eTrace',eRstrDebugCheckBox.isSelected())
    trolleyRoster.setDebugFlag('dTrace',dRstrDebugCheckBox.isSelected())
    return


def whenEditRosterButtonClicked(event):
    global frameRoster
    editRosterButton.setEnabled(False)
    frameRoster = createEditRosterDataFrame(trolleyRoster)
    #frameRoster.setVisible(True)
    return


def whenEditRosterCloseButtonClicked(event):
    global frameRoster
    editRosterButton.setEnabled(True)
    #frameRoster.setVisible(False)
    frameRoster.dispose()
    return


def whenCancelAddTrolleyButtonClicked(event):
    global frameAddTrolley
    #editRosterButton.setEnabled(True)
    #frameRoster.setVisible(False)
    frameAddTrolley.dispose()
    frameRoster.setVisible(True)
    return


def whenSaveAddTrolleyButtonClicked(event):
    global frameAddTrolley, frameRoster
    __address = int(addTrolleyAddress.getText())
    __maxSpeed = int(addTrolleyMaxSpeed.getText())
    __block = layoutMap.findBlockByAddress(int(addTrolleyStartingPosition.getSelectedItem().split('-')[0]))
    if __block is None : return
    if not trolleyRoster.isTrolleyAddressValid(__address): return
    if not trolleyRoster.isTrolleyMaxSpeedValid(__maxSpeed): return
    logger.info("Address: "+str(__address)+" MaxSpeed: "+
          str(__maxSpeed)+" SoundEnabled: "+
          str(addTrolleySoundEnabled.isSelected())+" Starting Position: "+
          str(__block.address)+" Starting Position Description: "+
          str(__block.description))
    trolleyRoster.append(Trolley(layoutMap, address=__address, maxSpeed=__maxSpeed, 
                                 soundEnabled=addTrolleySoundEnabled.isSelected(), currentPosition=__block.address))
    #frameRoster.setVisible(False)
    trolleyRoster.dump()
    frameAddTrolley.dispose()
    # The revalidate and repaint methods don't seem to work so for now we just dispose of the
    # original roster frame and recreate it so the new trolley is displayed.
    #frameRoster.revalidate() 
    #frameRoster.repaint()
    frameRoster.dispose()
    frameRoster = createEditRosterDataFrame(trolleyRoster)
    frameRoster.setVisible(True)
    return


def whenAddToRosterButtonClicked(event):
    global frameAddTrolley
    frameRoster.setVisible(False)
    frameAddTrolley = createAddToTrolleyRosterFrame()
    return


def sendAudibleMessage(checkboxToMonitor, messageToAnnounce):
    if checkboxToMonitor.isSelected() :
        javaexec = getattr(java.lang.Runtime.getRuntime(), "exec")
        pid = javaexec('nircmd speak text "' + messageToAnnounce +'" -2 100')
        pid.waitFor()
    return


def addComponent(container, component, gridx, gridy, gridwidth, gridheight, anchor, fill):
    insets=awtInsets(5, 5, 5, 5)
    ipadx = 0
    ipady = 5
    weightx = weighty = 0.0
    gbc = GridBagConstraints(gridx, gridy, gridwidth, gridheight, weightx, weighty, anchor, fill, insets, ipadx, ipady)
    container.add(component, gbc)


def setRosterColumnProperties(table, column, width=5, resizable=False):
    table.getColumnModel().getColumn(column).setPreferredWidth(width)
    table.getColumnModel().getColumn(column).setResizable(resizable)
    return

def getAddTrolleyButtonPanel():
    global editRosterButton, tstopButton, tgoButton, simulatorButton, quitButton
    # =================================
    # create buttons panel actions
    # =================================
    saveButton = javax.swing.JButton("Save")
    saveButton.actionPerformed = whenSaveAddTrolleyButtonClicked 
    cancelButton = javax.swing.JButton("Cancel")
    cancelButton.actionPerformed = whenCancelAddTrolleyButtonClicked
    addTrolleyPanel = javax.swing.JPanel()
    addTrolleyPanel.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
    addTrolleyPanel.add(saveButton)
    addTrolleyPanel.add(javax.swing.Box.createHorizontalStrut(10)) #empty vertical space between buttons
    addTrolleyPanel.add(cancelButton)
    return addTrolleyPanel


def getAddTrolleyDataPanel():
    global addTrolleyAddress, addTrolleyMaxSpeed, addTrolleySoundEnabled, addTrolleyStartingPosition
    __panel = javax.swing.JPanel()
    __panel.add(JLabel("Address:"))
    addTrolleyAddress = javax.swing.JTextField('',5)
    __panel.add(addTrolleyAddress)
    __panel.add(JLabel("Max Speed:"))
    addTrolleyMaxSpeed = javax.swing.JTextField('',5)
    __panel.add(addTrolleyMaxSpeed)
    __panel.add(JLabel("Sound Enabled:"))
    addTrolleySoundEnabled = javax.swing.JCheckBox()
    __panel.add(addTrolleySoundEnabled)
    __panel.add(JLabel("Starting Position:"))
    comboChoices = []
    for block in layoutMap:
        comboChoices.append(str(block.address)+'-'+block.description)
    addTrolleyStartingPosition = javax.swing.JComboBox(comboChoices)
    __panel.add(addTrolleyStartingPosition)
    return __panel


def createAddToTrolleyRosterFrame():
    frameAddTrolley = jmri.util.JmriJFrame("Add Trolley To Roster")
    frameAddTrolley.setSize(ATS_MESSAGE_WINDOW_PANE_WIDTH,ATS_ROSTER_ROW_HEIGHT+50)
    frameAddTrolley.setLayout(java.awt.GridBagLayout())
    addComponent(frameAddTrolley, getAddTrolleyButtonPanel(), 0, 0, 2, 1, GridBagConstraints.PAGE_START, GridBagConstraints.NONE)
    addComponent(frameAddTrolley, getAddTrolleyDataPanel(), 0, 2, 2, 1, GridBagConstraints.CENTER, GridBagConstraints.NONE)
    frameAddTrolley.setDefaultCloseOperation(frameRoster.DO_NOTHING_ON_CLOSE); # Disable the Close button
    #frameAddTrolley.setDefaultCloseOperation(frameRoster.DISPOSE_ON_CLOSE); # Disable the Close button
    frameAddTrolley.pack()
    frameAddTrolley.setVisible(True)
    return frameAddTrolley


class DeleteTrolleyButtonListener(MouseAdapter):
    logger = logging.getLogger(__name__)
    def mousePressed(self, event):
        global frameRoster
        __target = event.getSource()
        __row = __target.getSelectedRow()
        __column = __target.getSelectedColumn()
        if __column == 5: 
            logger.info("Request to DELETE Trolley Roster item %s - Address: %s", str(__row), str(trolleyRoster[__row].address))
            __response = deleteTrolleyFromRosterConfirmation("Delete Trolley #"+str(trolleyRoster[__row].address))
            logger.info("Request to DELETE Trolley: %s - %s", str(trolleyRoster[__row].address),
                        ("Confirmed" if __response == 0 else "Cancelled"))
            if __response == 0: 
                trolleyRoster.delete(__row)
                trolleyRoster.dump()
                    # The revalidate and repaint methods don't seem to work so for now we just dispose of the
                    # original roster frame and recreate it so the new trolley is displayed.
                    #frameRoster.revalidate() 
                    #frameRoster.repaint()
                frameRoster.dispose()
                frameRoster = createEditRosterDataFrame(trolleyRoster)
                frameRoster.setVisible(True)


def deleteTrolleyFromRosterConfirmation(message):
    result = JOptionPane.showConfirmDialog(None, message,  "Delete Trolley", JOptionPane.OK_CANCEL_OPTION)
    return result


def createEditRosterDataFrame(trolleyRoster):
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
    rosterTable.addMouseListener(DeleteTrolleyButtonListener())
    setRosterColumnProperties(rosterTable, 0)
    setRosterColumnProperties(rosterTable, 1)
    setRosterColumnProperties(rosterTable, 2, width=10)
    setRosterColumnProperties(rosterTable, 3, width=75)
    setRosterColumnProperties(rosterTable, 4, width=200)
    setRosterColumnProperties(rosterTable, 5, width=10)
    rosterScrollPane = JScrollPane()
    rosterScrollPane.setPreferredSize(java.awt.Dimension(ATS_ROSTER_WINDOW_PANE_WIDTH,len(trolleyRoster)*ATS_ROSTER_ROW_HEIGHT+100))
    rosterScrollPane.getViewport().setView(rosterTable)
    rosterPanel = javax.swing.JPanel()
    rosterPanel.add(rosterScrollPane)
    rosterAddButton = javax.swing.JButton("Add To Roster - Not Yet Functional")
    rosterAddButton.actionPerformed = whenAddToRosterButtonClicked
    rosterAddButton.setEnabled(True)
    rosterCloseButton = javax.swing.JButton("Close")
    rosterCloseButton.actionPerformed = whenEditRosterCloseButtonClicked
    frameRoster.add(rosterAddButton, BorderLayout.PAGE_START)
    frameRoster.add(rosterPanel, BorderLayout.CENTER)
    frameRoster.add(rosterCloseButton, BorderLayout.PAGE_END)
    frameRoster.setDefaultCloseOperation(frameRoster.DO_NOTHING_ON_CLOSE); # Disable the Close button
    frameRoster.pack()
    frameRoster.setVisible(True)
    return frameRoster


def getButtonPanel():
    global trolleyAutomationObject, editRosterButton, tstopButton, tgoButton, simulatorButton, quitButton
    # =================================
    # create buttons panel actions
    # =================================
    quitButton = javax.swing.JButton("Quit")
    quitButton.actionPerformed = whenQuitButtonClicked
    tgoButton = javax.swing.JButton("Start Running")
    tgoButton.actionPerformed = whenTgoButtonClicked
    tstopButton = javax.swing.JButton("Stop All Trolleys")
    tstopButton.setEnabled(False)           #button starts as grayed out (disabled)
    tstopButton.actionPerformed = whenStopAllButtonClicked
    simulatorButtonTxt = "Disable Simulator" if trolleyAutomationObject.simulatorEnabled else "Enable Simulator"
    simulatorButton = javax.swing.JButton(simulatorButtonTxt)
    simulatorButton.actionPerformed = whenSimulatorButtonClicked
    editRosterButton = javax.swing.JButton("Edit Roster")
    editRosterButton.setEnabled(True)
    editRosterButton.actionPerformed = whenEditRosterButtonClicked
    # =================================
    # create button panel
    # =================================
    butPanel = javax.swing.JPanel()
    butPanel.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
    butPanel.add(editRosterButton)
    butPanel.add(javax.swing.Box.createHorizontalStrut(20)) #empty vertical space between buttons
    butPanel.add(tgoButton)
    butPanel.add(javax.swing.Box.createHorizontalStrut(20)) #empty vertical space between buttons
    butPanel.add(tstopButton)
    butPanel.add(javax.swing.Box.createHorizontalStrut(20)) #empty vertical space between buttons
    butPanel.add(simulatorButton)
    butPanel.add(javax.swing.Box.createHorizontalStrut(20)) #empty vertical space between buttons
    butPanel.add(quitButton)
    return butPanel


def createInfoPane(defaultText, title = None):
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


def createScrollPanel(DefaultText, title = None):
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


def toggleFlag(flag = None):
    if flag is not None:
        flag[0] = not flag[0]


# ====================================
# create checkboxes and define action
# ====================================
logLabel1 = javax.swing.JLabel("Logging:")
eMsgDebugCheckBox = javax.swing.JCheckBox("Message Function Entry/Exit", actionPerformed = whenCheckboxClicked)
eMsgDebugCheckBox.setToolTipText("Display all function entry/exit messages")
dMsgDebugCheckBox = javax.swing.JCheckBox("Message Details", actionPerformed = whenCheckboxClicked)
dMsgDebugCheckBox.setToolTipText("Display detail debugging for messages")
iMsgDebugCheckBox = javax.swing.JCheckBox("Incoming Messages", actionPerformed = whenCheckboxClicked)
iMsgDebugCheckBox.setToolTipText("Display debugging for incoming loconet messages")
oMsgDebugCheckBox = javax.swing.JCheckBox("Outgoing Messages", actionPerformed = whenCheckboxClicked)
oMsgDebugCheckBox.setToolTipText("Display debugging for outgoing loconet messages")

eRstrDebugCheckBox = javax.swing.JCheckBox("TrolleyRoster Function Entry/Exit", actionPerformed = whenCheckboxClicked)
eRstrDebugCheckBox.setToolTipText("Display all Trolley Roster function entry/exit messages")
dRstrDebugCheckBox = javax.swing.JCheckBox("TrolleyRoster Details", actionPerformed = whenCheckboxClicked)
dRstrDebugCheckBox.setToolTipText("Display detail debugging for TrolleyRoster")
dRstrDebugCheckBox.setEnabled(False)

#logLabel2 = javax.swing.JLabel("        ")
snChgCheckBox = javax.swing.JCheckBox("Show Sn Change")
snChgCheckBox.setToolTipText("Display when a sensor state changes")
snChgCheckBox.setEnabled(False)
snSpkChgCheckBox = javax.swing.JCheckBox("Speak Sn Change")
snSpkChgCheckBox.setToolTipText("Speak when a sensor state changes")
snSpkChgCheckBox.setEnabled(False)
msgSpkCheckBox = javax.swing.JCheckBox("Speak General Messages")
msgSpkCheckBox.setToolTipText("Speak when a message is sent")
msgSpkCheckBox.setSelected(True)

# ====================================
# create checkboxes panel
# ====================================
ckBoxPanel1 = javax.swing.JPanel()
ckBoxPanel1.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
ckBoxPanel1.add(logLabel1)

ckBoxPanel2 = javax.swing.JPanel()
ckBoxPanel2.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
ckBoxPanel2.add(eMsgDebugCheckBox)
ckBoxPanel2.add(dMsgDebugCheckBox)
ckBoxPanel2.add(iMsgDebugCheckBox)
ckBoxPanel2.add(oMsgDebugCheckBox)

ckBoxPanel3 = javax.swing.JPanel()
ckBoxPanel3.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
ckBoxPanel3.add(eRstrDebugCheckBox)
ckBoxPanel3.add(dRstrDebugCheckBox)
ckBoxPanel3.add(snSpkChgCheckBox)
ckBoxPanel3.add(msgSpkCheckBox)


# =====================================
# create text fields for status outputs
# =====================================
blockInfoPane = createInfoPane(layoutMap.getBlockStatus(trolleyRoster), title="Block Status")
segmentInfoPane = createInfoPane(layoutMap.getSegmentStatus(trolleyRoster), title="Segment Status")
rosterInfoPane = createInfoPane(trolleyRoster.getRosterStatus(), title="Trolley Roster Status")
messageInfoPanel = createScrollPanel("Default Message Panel\n"+
                                     "Currently All messages will be written to the Script Output window",
                                     title = "Messages")

# ------------------------------------------------------------------------------------------
# create a frame to hold the buttons and fields
# also create a window listener. This is used mainly to remove the property change listener
# when the window is closed by clicking on the window close button
# ------------------------------------------------------------------------------------------
w = AtsWinListener()
fr = jmri.util.JmriJFrame(__apNameVersion) #use this in order to get it to appear on webserver
fr.contentPane.setLayout(java.awt.GridBagLayout())
addComponent(fr, getButtonPanel(), 0, 0, 2, 1, GridBagConstraints.PAGE_START, GridBagConstraints.NONE);
addComponent(fr, ckBoxPanel1, 0, 1, 1, 2, GridBagConstraints.LINE_START, GridBagConstraints.NONE)
addComponent(fr, ckBoxPanel2, 1, 1, 1, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
addComponent(fr, ckBoxPanel3, 1, 2, 1, 1, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
#addComponent(fr, getRosterPanel(trolleyRoster), 0, 4, 1, 1, GridBagConstraints.LINE_START, GridBagConstraints.HORIZONTAL)
addComponent(fr, blockInfoPane, 0, 5, 2, 5, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
addComponent(fr, segmentInfoPane, 0, 15, 2, 5, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
addComponent(fr, rosterInfoPane, 0, 20, 2, 7, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
addComponent(fr, messageInfoPanel, 0, 30, 2, 7, GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL)
fr.addWindowListener(w)
fr.pack()
fr.setVisible(True)

# set the name - This will show in the threat monitor
trolleyAutomationObject.setName("Trolley Automation Script")
trolleyRoster.setAutomationObject(trolleyAutomationObject)
audible = MessageAnnouncer(msgSpkCheckBox)
trolleyRoster.setMessageAnnouncer(audible)
audible.announceMessage("Welcome to the "+__apNameVersion)

# Set output locations for 
#layoutMap.setBlockDumpOutput(output=messageInfoPanel)
layoutMap.setBlockInfoOutput(output=blockInfoPane)
layoutMap.setSegmentInfoOutput(output=segmentInfoPane)
trolleyRoster.setRosterInfoOutput(output=rosterInfoPane)
trolleyRoster.setMessageInfoOutput(output=messageInfoPanel)

logger.info("Building Layout Map")
buildLayoutMap(layoutMap)  # Build the layout
layoutMap.dump()

logger.info("Building Trolley Roster")
buildTrolleyRoster(trolleyRoster, layoutMap)  # Build the roster of trolleys
trolleyRoster.dump()
#frameRoster = createEditRosterDataFrame(trolleyRoster)

logger.info("Setup Complete  - ")
layoutMap.printBlocks(trolleyRoster)
layoutMap.printSegments(trolleyRoster)
