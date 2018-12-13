'''
Created on Nov 18, 2016

@author: ttb
'''
import logging


logger = logging.getLogger(__name__)

class BlockMap(object):
    """A trolley object that consists of the following properties:

    Attributes:
        address: The DCC address of the trolley object.
        speed: The speed of the trolley, non-zero indicates it is moving.
        currentPosition:  This indicates the block that the trolley is currently in.
        nextPosition: This should always be currentPosition + 1.
    """
    
    __instance = None  # Make sure there is only one version of the blockmap
    def __init__(self, blockObjects=None):
        """Initialize the class"""
        super(BlockMap, self).__init__()
        if blockObjects is not None:
            self._blockmap = list(blockObjects)
            self.first = None
            self.last = None
            #self.next = blockObjects
        else:
            self._blockmap = list()
            self.first = None
            self.last = None
            #self.next = blockObjects


    def __new__(cls, blockObjects=None): # __new__ always a class method
        if BlockMap.__instance is None:
            BlockMap.__instance = object.__new__(cls,blockObjects)
        return BlockMap.__instance


    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self._blockmap)
    

    def __len__(self):
        """List length"""
        return(len(self._blockmap))
    

    def size(self):
        return(len(self._blockmap))
    

    def __getitem__(self, ii):
        """Get a list item"""
        return self._blockmap[ii]
    

    def __delitem__(self, ii):
        """Delete an item"""
        del self._blockmap[ii]
        

    def __setitem__(self, ii, val):
        # optional: self._acl_check(val)
        self._blockmap[ii] = val


    def __str__(self):
        return str(self._blockmap)
    

    def insert(self, ii, val):
        # optional: self._acl_check(val)
        self._blockmap.insert(len(self._blockmap), val)
        if self.first is None:
            self.first = val
            self._blockmap[ii].next = self._blockmap[ii]
        else:
            self.last.next = val
            self._blockmap[ii].next=self.first
            self.last = val
        self.last = val


    def append(self, val):
        self.insert(len(self._blockmap), val)
        

    def dump(self):
        print "**************"
        print "Layout Map"
        print "**************"
        print "Number of Blocks: ", self.size()
        m = max(self, key=lambda x: x.segment)
        print 'Number of Segments: ', m.segment
        for block in self._blockmap:
            print "Id:", block.index, 
            print " Address:", block.address, 
            print " Segment:", block.segment, 
            print " Occupied:", block.occupied,
            print " StopReqd:", block.stopRequired,
            print " WaitTime:", block.waitTime,
            print " Length:", block.length,
            print " Next Block:", block.next.address,
            print " Description:", block.description

            
    def getNextBlock(self, val):
        return val.next
    

    def getBlockAddressList(self):
        blockList = ""
        for block in self._blockmap:
            blockList.append(block.address)
        return list
    

    def isSegmentOccupied(self, segment):
        for block in self._blockmap:
            if block.segment == segment:
                if block.occupied == True:
                    return True
        return False
    

    def findBlockByAddress(self,address):
        for block in self._blockmap:
            if block.address == address:
                return block
        return None
    

    def findSegmentByAddress(self,address):
        for block in self._blockmap:
            if block.address == address:
                return block.segment
        return None
    

    def findNextBlockByAddress(self,address):
        for block in self._blockmap:
            if block.address == address:
                return block.next
        return None
    

    def printBlocks(self,trolleyRoster):
        print "*****************"
        print "PrintBlockStatus"
        print "*****************"
        for block in self._blockmap:
            print "{:<4}".format(block.address), ' ',
        print ""
        for block in self._blockmap:
            #print seg.blockAddress
            if block.isBlockOccupied()== True:
                print "{:<4}".format(trolleyRoster.findByCurrentBlock(block.address).address), " ",
                #print "ttt  ",
            else:
                print "****  ",
        print ""
  

    def printSegments(self,trolleyRoster):   
        print "******************************"
        print "PrintSegmentStatus"
        print "******************************"
        #segments = {self.segment for segment in self._blockmap}
        segments = list(set([block.segment for block in self._blockmap]))
        segments.sort()
        for segment in segments:
            print "{:<4}".format(segment), " ",
        print ""
        for segment in segments:
            if self.isSegmentOccupied(segment)== True:
                print "{:<4}".format(trolleyRoster.findByCurrentSegment(segment, self).address), " ",
            else:
                print "****  ",
        print ""
        
