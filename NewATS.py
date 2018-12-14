#from argparse import _StoreFalseAction
#from classes.layoutMap import LayoutMap
#from classes import layoutMap
print "ATS Start"
from classes.trolley import Trolley
from classes.trolleyRoster import TrolleyRoster
from classes.blockMap import BlockMap
from classes.block import Block
from classes.messengerFacade import Messenger
import datetime
import time
import logging
from random import randint
import java
import javax.swing
#from javax.swing import SwingUtilities
from javax.swing.text import DefaultCaret
from java.awt import Font

apNameVersion = "New Automatic Trolley Sequencer"

# *************************************************************************
# WindowListener is a interface class and therefore all of it's           *
# methods should be implemented even if not used to avoid AttributeErrors *
# *************************************************************************
class WinListener(java.awt.event.WindowListener):

    def windowClosing(self, event):
        global killed
        
        #print "window closing"
        killed = True #this will signal scanReporter thread to exit
        #time.sleep(2.0) #give it a chance to happen before going on
        #jmri.jmrix.loconet.LnTrafficController.instance().removeLocoNetListener(0xFF, lnListen)
        #list = sensors.getSystemNameList()
        
        #for i in range(list.size()):    #remove each of the sensor listeners that were added
        
            #sensors.getSensor(list.get(i)).removePropertyChangeListener(listener)
            # print "remove"
            
        #fr.dispose()         #close the pane (window)
        trolleyRoster.destroy()
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
        print
        return
        
    def windowIconified(self, event):
        return
        
    def windowDeiconified(self, event):
        return


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',
                    handlers=[logging.FileHandler("{0}.log".format('NewATS')),
                              logging.StreamHandler()])
logger = logging.getLogger("NewATS")

msg = Messenger()
#msg.enableAllDebug()

#Trolley.setMessageManager(msgManager = msg)        
logger.info("Initialize Empty Layout Map")
layoutMap = BlockMap() # Initialize and empty block map to define the layout
logger.info("Initialize Empty Trolley Roster")
trolleyRoster = TrolleyRoster()  # Initialize an empty roster of trolley devices

try:
    jmriFlag = True
    import jmri
    logger.info('Successfully Imported jmri', exc_info=True)
    #jmri.jmrix.loconet.LocoNetListener
except ImportError:
    jmriFlag = False
    logger.info('Failed to import jmir - bypassing', exc_info=True)
#logger.info("Initialize Empty Layout Map")
#layoutMap = BlockMap() # Initialize and empty block map to define the layout
#logger.info("Initialize Empty Trolley Roster")
#trolleyRoster = TrolleyRoster()  # Initialize an empty roster of trolley devices


class TrolleyAutomation(jmri.jmrit.automat.AbstractAutomaton):
    def init(self):
        pass
        #logger.info("Initialize Empty Layout Map")
        #layoutMap = BlockMap() # Initialize and empty block map to define the layout
        #logger.info("Initialize Empty Trolley Roster")
        #trolleyRoster = TrolleyRoster()  # Initialize an empty roster of trolley devices
        #logger.info("Build Layout Map")
        #buildLayoutMap(layoutMap)  # Build the layout
        #logger.info("Build Trolley Roster")
        #buildTrolleyRoster(trolleyRoster, layoutMap)  # Build the roster of trolleys
        #logger.info("Dumping Trolley Roster")
        #trolleyRoster.dump()
        #logger.info("Dumping Layout Map")
        #layoutMap.dump()
        #layoutMap.printBlocks(trolleyRoster)
        #layoutMap.printSegments(trolleyRoster)

    
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
        if trolleyRoster.checkIfAllTrolleysAreRegistered():
            trolleyRoster.checkAllTrolleyMovement(layoutMap)
            event = simulateAllMovement(trolleyRoster,layoutMap)
            if event: msg.sendSenorReportMsg(event)
            #if event: trolleyRoster.processBlockEvent(event)
        else:
            trolleyRoster.registerOneTrolley()
        self.waitMsec(1000)    
        return True
        #layoutMap.printBlocks(trolleyRoster)
        #layoutMap.printSegments(trolleyRoster)
        #trolleyRoster.dump()


    # handle adding to message window
    def msgText(self, txt) :
        self.scrollArea.append(txt)
        if (self.autoScroll.isSelected() == True) :
            self.scrollArea.setCaretPosition(self.scrollArea.getDocument().getLength())
        return
    


def simulateAllMovement(trolleyRoster, layoutMap):
    for trolley in trolleyRoster:
        if trolley.getSpeed() > 0:
            travelTime = (datetime.datetime.now() - trolley.startTime).seconds
            if travelTime > (trolley.currentPosition.length / 4):
                logger.info("Simulating event for SensorID: %s by Trolley: %s", trolley.nextPosition.address, trolley.address)
                return trolley.nextPosition.address
            # Simulate ramdom noise on used block
            if randint(0, 999) > 990:
                return trolley.currentPosition.address
    return None
    
    
# def moveAllTrolleys(trolleyRoster, layout):
#     layoutLength = len(layout)
#     nextList = []
#     for trolley in trolleyRoster:
#         if layout[trolley.nextPosition].get_isBlockOccupied() == False:
#             print "Next Block Free:",
#             if trolley.nextPosition in nextList:
#                 print "Next Block Already Scheduled"
#                 continue
#             else:
#                 print "Nothing Scheduled for Next Block:",
#                 nextList.append(trolley.nextPosition)
#                 trolley.move(layoutLength)
#                 print 'new nextposition = ', trolley.nextPosition
                

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
    # Block 101 - Spencer Station Isle
    # Block 118 - Spencer Blvd Isle
    # Block 116 - Traffic Intersection Isle
    # Block 119 - Single Track Signal Block Isle
    # Block 102 - Single Track Spencer Side
    # Block 107 - Single Track Majolica Side
    # Block 104 - Majolica Outbound Loop
    # Block 103 - Majolica Return Loop
    # Block 107 - Single Track Majolica Side
    # Block 102 - Single Track Spencer Side
    # Block 120 - Spencer Blvd Interchange Yard Side 
    # Block 123 - Spencer Blvd Shelter Yard Side
    # Block 121 - Spencer Blvd Buckholtz Yard Side
    # Block 106 - Spencer Station Yard Side
    #
    layout.append(Block(blockAddress=100, newSegment=True,  stopRequired=True,  length=24,  description='Thomas Loop'))
    layout.append(Block(blockAddress=101, newSegment=True,  stopRequired=False, length=130, description='Spencer Station Isle'))
    layout.append(Block(blockAddress=118, newSegment=True,  stopRequired=False, length=30,  description='Spencer Blvd Isle'))
    layout.append(Block(blockAddress=116, newSegment=True,  stopRequired=True,  length=135, description='Traffic Intersection Isle'))
    layout.append(Block(blockAddress=119, newSegment=True,  stopRequired=False, length=20,  description='Single Track Signal Block Isle'))
    layout.append(Block(blockAddress=102, newSegment=True,  stopRequired=False, length=48,  description='Single Track Spencer Side'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica Side'))
    layout.append(Block(blockAddress=104, newSegment=False, stopRequired=False, length=40,  description='Majolica Outbound Loop'))
    layout.append(Block(blockAddress=103, newSegment=False, stopRequired=False, length=30,  description='Majolica Return Loop'))
    layout.append(Block(blockAddress=107, newSegment=False, stopRequired=False, length=40,  description='Single Track Majolica Side'))
    layout.append(Block(blockAddress=102, newSegment=False, stopRequired=False, length=48,  description='Single Track Spencer Side'))
    layout.append(Block(blockAddress=120, newSegment=True,  stopRequired=False, length=114, description='Spencer Blvd Interchange Yard Side'))
    layout.append(Block(blockAddress=123, newSegment=True,  stopRequired=True,  length=72,  description='Spencer Blvd Shelter Yard Side'))
    layout.append(Block(blockAddress=121, newSegment=True,  stopRequired=False, length=84,  description='Spencer Blvd Buckholtz Yard Side'))
    layout.append(Block(blockAddress=106, newSegment=True,  stopRequired=True,  length=28,  description='Spencer Station Yard Side'))

def buildTrolleyRoster(trolleyRoster, blockMap):
    # When building a roster you need to provide the layout map so that the starting 
    # potisions of the trolleys can be validated. The roster is built prior to sending any
    # requests to JMRI for slots. Registration should occur in the handler on a one by one
    # basis to avoid conflicts.
    trolleyRoster.append(Trolley(blockMap, address=501, maxSpeed=50, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=502, maxSpeed=40, currentPosition=100))
    trolleyRoster.append(Trolley(blockMap, address=503, maxSpeed=80, currentPosition=106)) 
    trolleyRoster.append(Trolley(blockMap, address=504, maxSpeed=50, currentPosition=106)) 
    

#logger.info("Initialize Empty Layout Map")
#layoutMap = BlockMap() # Initialize and empty block map to define the layout
#logger.info("Initialize Empty Trolley Roster")
#trolleyRoster = TrolleyRoster()  # Initialize an empty roster of trolley devices

# create a TrolleyAutomation object
a = TrolleyAutomation()

# set the name - This will show in the threat monitor
a.setName("Trolley Automation Script")

# Start it running
a.start()

logger.info("Building Layout Map")
buildLayoutMap(layoutMap)  # Build the layout
layoutMap.dump()

logger.info("Building Trolley Roster")
buildTrolleyRoster(trolleyRoster, layoutMap)  # Build the roster of trolleys
trolleyRoster.dump()

logger.info("Setup Complete  - ")
layoutMap.printBlocks(trolleyRoster)
layoutMap.printSegments(trolleyRoster)
