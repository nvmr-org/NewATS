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
from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.blockMap import BlockMap
from classes.block import Block
from classes.announcer import MessageAnnouncer
from classes.messengerFacade import Messenger
import datetime
import time
import logging
import os.path
from random import randint
import javax.swing
import java.awt.Color
from javax.swing.text import DefaultCaret, StyleConstants
from javax.swing.border import EmptyBorder
from java.awt import Font, GridBagConstraints
from java.awt import Insets as awtInsets
from javax.swing import JLabel

print "ATS Start"

try:
    jmriFlag = True
    import jmri
    print('Successfully Imported jmri')
except ImportError:
    jmriFlag = False
    print('Failed to import jmir - bypassing')

TROLLEY_ROSTER_ADDRESS_FILE = "trolleyRosterAddresses.cfg"

__apNameVersion = "New Automatic Trolley Sequencer"
enableSimulator = False
__fus = jmri.util.FileUtilSupport()

# *************************************************************************
# WindowListener is a interface class and therefore all of it's           *
# methods should be implemented even if not used to avoid AttributeErrors *
# *************************************************************************
class WinListener(java.awt.event.WindowListener):

    def windowClosing(self, event):
        global killed
        killed = True #this will signal scanReporter thread to exit
        trolleyRoster.destroy()
        msg.destroyListener()
        fr.dispose()         #close the pane (window)
        return

    def windowActivated(self, event):
        return

    def windowDeactivated(self, event):
        return

    def windowOpened(self, event):
        return

    def windowClosed(self, event):
        trolleyRoster.destroy()
        time.sleep(3.0) #wait 3 seconds before moving on to allow last free to complete
        print 'slots freed and exited'
        msg.destroyListener()
        fr.dispose()         #close the pane (window)
        return

    def windowIconified(self, event):
        return

    def windowDeiconified(self, event):
        return


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',
                    handlers=[logging.FileHandler("{0}/{1}.log".format(__fus.getUserFilesPath(),'NewATS')),
                    logging.StreamHandler()])
logger = logging.getLogger("NewATS")

msg = Messenger()
msg.createListener()

#Trolley.setMessageManager(msgManager = msg)        
logger.info("Initialize Empty Layout Map")
layoutMap = BlockMap() # Initialize and empty block map to define the layout
logger.info("Initialize Empty Trolley Roster")
trolleyRoster = TrolleyRoster(layoutMap=layoutMap)  # Initialize an empty roster of trolley devices


class TrolleyAutomation(jmri.jmrit.automat.AbstractAutomaton):
    def init(self):
        logger.info("Initialize Trolley Automation")
        pass

    
    def handle(self):
        # handle() is called repeatedly until it returns false.
        #
        # We wait until handle gets called to check if trolleys
        # in the roster have been assigned slots.  If at least 
        # one trolley is not assigned we register it.  We wait
        # for all trolleys to be registered before starting the
        # movement checks.
        #
        # This is where we should also check that all the trolleys
        # in the roster are current.
        if self.isRunning():
            logger.debug("Automation is running")
            if trolleyRoster.checkIfAllTrolleysAreRegistered():
                trolleyRoster.processAllTrolleyMovement()
                if enableSimulator : simulateAllMovement(trolleyRoster)
                #if event: trolleyRoster.processBlockEvent(event)
                trolleyRoster.refreshTrolleysSlots()
            else:
                trolleyRoster.registerOneTrolley()
        else:
            logger.info("Automation is NOT running")
        self.waitMsec(1000)      
        return True


def simulateAllMovement(trolleyRoster):
    event = None
    for trolley in trolleyRoster:
        if trolley.getSpeed() > 0:
            travelTime = (datetime.datetime.now() - trolley.startTime).seconds
            if travelTime > (trolley.currentPosition.length / 4):
                logger.info("Simulating event for SensorID: %s by Trolley: %s", trolley.nextPosition.address, trolley.address)
                event =  trolley.nextPosition.address
            # Simulate random noise on used block
            if randint(0, 999) > 990:
                event =  trolley.currentPosition.address
    if event: msg.sendSenorReportMsg(event)
    return event


def buildLayoutMap(layout):
    # Create a layoutMap map that consists of consecutive blocks representing a complete 
    # circuit. The map also identifies the segment associated with each block. This is
    # done because so a multiple block area can be identified as occupied.
    #        -100/1--                                                     ---103/3---
    #      /          \                                                  /            \
    #     |            -----106/4--------------\                       /              /
    #      \                                    >--102/3--|---107/3---<_____104/3____/
    #        ------------101/2-----------------/
    #
    #    
    #        --100/1--                                                                                      ----103/6---*
    #      /          \                                                                                    /             \
    #     /            *                                                                                  /               \
    #     *             \                                                                                *                |
    #      \             --106/10---*----121/9-----*---123/8---*-----120/7----*-\                       /                /
    #       \                                                                    >--102/6--*---107/6---<-*----104/6----/ 
    #         -----101/2-----*------118/3------*-----116/4-----*-----119/5----*-/
    #
    # Trolley Sequencing
    # Block 100 - Thomas Loop
    # Block 101 - Spencer Station Isle Side
    # Block 118 - Spencer Boulevard Isle Side
    # Block 116 - Traffic Intersection Isle Side
    # Block 119 - Single Track Signal Block Isle Side
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
    layout.append(Block(blockAddress=119, newSegment=True,  stopRequired=False, length=20,  description='Single Track Signal Block Isle Side'))
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

    trolleyRoster.append(Trolley(blockMap, address=501, maxSpeed=50, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=502, maxSpeed=40, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=503, maxSpeed=80, currentPosition=106)) 
    trolleyRoster.append(Trolley(blockMap, address=504, maxSpeed=50, currentPosition=106)) 


# *************************************
# start to initialize the display GUI *
# *************************************
def whenStopAllButtonClicked(event):
    global automationObject
    global tstopButton, tgoButton, simulatorButton, quitButton
    tstopButton.setEnabled(False)
    tgoButton.setEnabled(True)
    quitButton.setEnabled(True)
    automationObject.stop()
    msg1t = "Stop All Trolleys button pressed"
    print msg1t
    print
    trolleyRoster.stopAllTrolleys()
    trolleyRoster.dump()
    return


def whenQuitButtonClicked(event):
    global autommationObject
    global tstopButton, tgoButton, simulatorButton, quitButton
    tstopButton.setEnabled(False)           #button starts as grayed out (disabled)
    tgoButton.setEnabled(False)           #button starts as grayed out (disabled)
    if automationObject.isRunning(): automationObject.stop()
    trolleyRoster.destroy()
    fr.dispose()         #close the pane (window)
    return


def whenTgoButtonClicked(event):
    global automationObject
    global tstopButton, tgoButton, simulatorButton, quitButton
    tstopButton.setEnabled(True)           #button starts as grayed out (disabled)
    tgoButton.setEnabled(False)           #button starts as grayed out (disabled)
    quitButton.setEnabled(False)
    automationObject.start()
    msg1t = "Start Running button pressed"
    print msg1t
    print
    while automationObject.isRunning() == False:
        print "Waiting for Automation to start"
        time.sleep(1.0)
    return


def whenSimulatorButtonClicked(event):
    global tstopButton, tgoButton, simulatorButton, quitButton
    global enableSimulator
    print("Simulator State:"+str(enableSimulator)+"-->"+str(not enableSimulator))
    enableSimulator = not enableSimulator
    if enableSimulator:
        simulatorButton.setText("Disable Simulator")
    else:
        simulatorButton.setText("Enable Simulator")


def whenRemoveButtonClicked(event):
    global automationObject
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


def getButtonPanel():
    global editRosterButton, tstopButton, tgoButton, simulatorButton, quitButton
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
    simulatorButtonTxt = "Disable Simulator" if enableSimulator else "Enable Simulator"
    simulatorButton = javax.swing.JButton(simulatorButtonTxt)
    simulatorButton.actionPerformed = whenSimulatorButtonClicked
    editRosterButton = javax.swing.JButton("Edit Roster")
    editRosterButton.setEnabled(False)
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


# -------------------------------------------------------------------
# create a trolley roster panel to define the trolleys for this run
# -------------------------------------------------------------------
def getRosterPanel(trolleyRoster):
    # =================================
    # create roster panel actions
    # =================================
    removeButton = javax.swing.JButton("Remove")
    removeButton.actionPerformed = whenRemoveButtonClicked

    rosterPanel = javax.swing.JPanel()
    rosterPanel.setLayout(java.awt.FlowLayout(java.awt.FlowLayout.LEFT))
    for trolley in trolleyRoster:
        rosterPanel.add(javax.swing.JLabel("Address"))
        rosterPanel.add(javax.swing.JTextField(trolley.address,5))
        rosterPanel.add(javax.swing.Box.createHorizontalStrut(50))
        rosterPanel.add(javax.swing.JLabel("Max Speed"))
        rosterPanel.add(javax.swing.JTextField(trolley.maxSpeed,5))
        rosterPanel.add(javax.swing.Box.createHorizontalStrut(50))
        rosterPanel.add(javax.swing.JLabel("Starting Position"))
        rosterPanel.add(javax.swing.JTextField(trolley.currentPosition,5))
        rosterPanel.add(javax.swing.Box.createHorizontalStrut(50))
        rosterPanel.add(removeButton)
    return rosterPanel


def createInfoPane(defaultText, title = None):
    __pane = javax.swing.JTextPane()
    __doc = __pane.getStyledDocument()
    __style = __pane.addStyle("Color Style", None)
    __pane.setFont(Font("monospaced",Font.BOLD,24))
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
    scrollArea = javax.swing.JTextArea(10, 45)
    scrollArea.getCaret().setUpdatePolicy(DefaultCaret.ALWAYS_UPDATE); # automatically scroll to last message
    scrollArea.font=Font("monospaced", Font.PLAIN, 24)
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
w = WinListener()
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

# create a TrolleyAutomation object
automationObject = TrolleyAutomation()

# set the name - This will show in the threat monitor
automationObject.setName("Trolley Automation Script")
trolleyRoster.setAutomationObject(automationObject)
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

logger.info("Setup Complete  - ")
layoutMap.printBlocks(trolleyRoster)
layoutMap.printSegments(trolleyRoster)
