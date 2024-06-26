'''
Created on Nov 18, 2016

@author: ttb
'''
import sys
import logging
#import java.beans
import jmri
#from jmri import Sensor
from classes.sensorListener import SensorListener
#from classes.sensorListener import ManagerListener


logger = logging.getLogger("ATS."+__name__)
logger.setLevel(logging.INFO)
thisFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name


class Block(object):
    """The layout class defines blocks and segments of a layout.  Blocks should be 
    added to the layout in the order in which devices traverse.  The blocks should
    define a continuous running loop and the last block should connect back to the
    first block.  Segments can be associated with each block and define a larger 
    group of block that will drive a single occupancy status.
    
    Layouts have the following properties:

    Attributes:
        address: An integer representing the address reported by the block occupancy detector.
        segment: An integer representing a collective group of blocks to combine for occupancy.
        occupied: true or false indication of whether the block is occupied.
        length: An integer representing the relative length of the block.
        stopRequired: true or false indication if whether trolleys should stop in this block.
        waitTime: Time in seconds that a trolley must wait in a block if a stop is required.
        next: A linked list representation of the next block in the chain.
        description: A verbal description of the block.
        
    Class Properties:
        segmentCount: The total number of segments
    """
    segmentCount = 0
    listener = SensorListener()
    blockManager = jmri.BlockManager()

    def __init__(self, blockAddress=-1, newSegment=False, stopRequired=True, waitTime=15, blockOccupied=False, length=10,
                 curvature=None, speed=None, description=None):
        """Return a Layout object whose id is *blockAddress* and *segmentAddress* 
        are negative if not provided.  Blocks should be added in the order they
        will be traversed."""
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        if newSegment == True:
            Block.segmentCount += 1

        self.address = blockAddress
        self.segment = Block.segmentCount
        self.occupied = blockOccupied
        self.stopRequired = stopRequired
        self.waitTime = waitTime 
        if not stopRequired: self.waitTime = 0
        self.length = length
        self.description = description
        self.next = None
        self.sensor = jmri.InstanceManager.sensorManagerInstance().provideSensor(str(blockAddress))
        self.sensor.addPropertyChangeListener(Block.listener)
        if self.sensor.getRawState() == jmri.Sensor.UNKNOWN :
            self.sensor.setKnownState(jmri.Sensor.INACTIVE)
        systemName="IB:BRTPL:"+str(blockAddress).zfill(4)
        userName="BK"+str(blockAddress)
        self.block = jmri.InstanceManager.getDefault(jmri.BlockManager).getBlock(systemName)
        if self.block == None:
            logger.info("Could not get block with systemName:%s - Creating",systemName)
            self.block = jmri.InstanceManager.getDefault(jmri.BlockManager).createNewBlock(systemName, userName);
            if self.block == None:
                logger.error("BlockManager not block with systemName:%s and userName:%s",systemName,userName)
            else:
                self.block.setComment(self.description)
                self.block.setLength(25.4*self.length)
                self.block.setSensor("LS"+str(blockAddress))
                logger.info("BlockManager created block %s",str(self.block))
        logger.info("Block Added - "+repr(self))


    def __repr__(self):
        return ("Address:"+str(self.address)+
                    " Segment:"+str(self.segment)+
                    " Occupied:"+str(self.occupied)+
                    " StopReqd:"+str(self.stopRequired)+
                    " WaitTime:"+str(self.waitTime)+
                    " Length:"+str(self.length)+
                    " Description:"+str(self.description))

    def __str__(self):
        return ("Addr:"+str(self.address)+
                    " Seg:"+str(self.segment)+
                    " Stop:"+str(self.stopRequired)+
                    " Time:"+str(self.waitTime)+
                    " Len:"+str(self.length)+
                    " Desc:"+str(self.description))

    def setDebugLevel(self,state):
        logger.setLevel(logging.DEBUG if state else logging.INFO)
        for handler in logging.getLogger("ATS").handlers:
            handler.setLevel(logging.DEBUG)
        Block.listener.setDebugLevel(state)
        logger.debug("%s.%s - Logger:%s - Set Debug Flag:%s", __name__, thisFuncName(),str(logger),str(state))


    def getDebugLevel(self):
        return logger.level


    def set_blockAddress(self, blockAddress=-1):
        logger.debug("%s.%s: Setting block to address %s to segment %s", __name__, thisFuncName(), self.address)
        self.address = blockAddress


    def set_segmentAddress(self, segmentAddress=-1):
        logger.debug("%s.%s: Setting block %s to segment %s", __name__, thisFuncName(), self.address, self.segment)
        self.segment = segmentAddress


    def set_blockOccupied(self):
        logger.debug("%s.%s: Setting block %s to OCCUPIED", __name__, thisFuncName(), self.address)
        self.occupied = True
        #self.sensor.setKnownState(jmri.Sensor.ACTIVE)


    def set_blockClear(self):
        logger.debug("%s.%s: Setting block %s to CLEAR", __name__, thisFuncName(), self.address)
        self.occupied = False
        #self.sensor.setKnownState(jmri.Sensor.INACTIVE)


    def get_blockAddress(self):
        return self.address


    def get_segmentAddress(self):
        return self.segment


    def isBlockOccupied(self):
        return self.occupied


    def isStopRequired(self):
        return self.stopRequired


    def get_waitTime(self):
        return self.waitTime