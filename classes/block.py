'''
Created on Nov 18, 2016

@author: ttb
'''
import logging

logger = logging.getLogger("ATS."+__name__)

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
        blockCount: The total number of blocks
        segmentCount: The total number of segments
    """
    segmentCount = 0

    def __init__(self, blockAddress=-1, newSegment=False, stopRequired=True, waitTime=15, blockOccupied=False, length=10, description=None):
        """Return a Layout object whose id is *blockAddress* and *segmentAddress* 
        are negative if not provided.  Blocks should be added in the order they
        will be traversed."""
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


    def set_blockAddress(self, blockAddress=-1):
        # Set the Layout Block Address.
        self.address = blockAddress


    def set_segmentAddress(self, segmentAddress=-1):
        # Set the Layout Segment Address.
        self.segment = segmentAddress


    def set_blockOccupied(self):
        self.occupied = True


    def set_blockClear(self):
        self.occupied = False


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