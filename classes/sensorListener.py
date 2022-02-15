# ******************************************
# * Define the sensor listener: Print some *
# * information on the status change.      *
# ******************************************
import logging
import sys
import java
import jmri

logger = logging.getLogger("ATS."+__name__)
logger.setLevel(logging.INFO)
thisFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name

class SensorListener(java.beans.PropertyChangeListener):
    # Define routine to map status numbers to text
    rosterManager = None

    def stateName(self, state) :
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        if (state == jmri.Sensor.ACTIVE) :
            return "OCCUPIED"
        if (state == jmri.Sensor.INACTIVE) :
            return "CLEAR"
        if (state == jmri.Sensor.INCONSISTENT) :
            return "INCONSISTENT"
        if (state == jmri.Sensor.UNKNOWN) :
            return "UNKNOWN"
        return "(invalid)"


    def propertyChange(self, event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        if (event.propertyName == "KnownState") :
            mesg = "Sensor "+event.source.systemName
            sensor_num = int(event.source.systemName[2:])
            logger.debug("SensorListener: Event Detected for block %s", sensor_num)
            logger.debug("SensorListener: Block OldState=%s NewState=%s Active=%s",event.oldValue,event.newValue,jmri.Sensor.ACTIVE)
            if event.newValue == jmri.Sensor.ACTIVE :
                logger.debug("SensorListener: Block Event Detected for block %s", sensor_num)
                if SensorListener.rosterManager : SensorListener.rosterManager.processBlockEvent(sensor_num)
            if (event.source.userName != None) :
                mesg += " ("+event.source.userName+")"
            mesg += " from "+self.stateName(event.oldValue)
            mesg += " to "+self.stateName(event.newValue)
        logger.debug(mesg)
        return


    def registerRoster(self, rosterManager = None):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        SensorListener.rosterManager = rosterManager
        return


# Define a Manager listener.  When invoked, a new
# item has been added, so go through the list of items removing the 
# old listener and adding a new one (works for both already registered
# and new sensors)
class ManagerListener(java.beans.PropertyChangeListener):
    def propertyChange(self, event):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        sensorList = event.source.getNamedBeanSet()
        for sensor in sensorList :
            sensor.removePropertyChangeListener(SensorListener())
            sensor.addPropertyChangeListener(SensorListener())


class ATSSensorMessenger(jmri.jmrix.loconet.LocoNetListener):
    def delayForMsec(self, delayInMsec=1000):
        jmri.jmrit.automat.AbstractAutomaton.waitMsec(delayInMsec,delayInMsec)


    def createPacket(self,msgLength,opcode,ARGS):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        logger.debug("MsgLen: %s  OpCode: %s  ARGS: %s" ,msgLength, hex(opcode), ARGS)
        try:
            packet = jmri.jmrix.loconet.LocoNetMessage(msgLength)
            packet.setElement(0, opcode)
            packet.setElement(1, ARGS[1])
            packet.setElement(2, ARGS[2])
            if msgLength > 4:
                for i in range(3,13):
                    packet.setElement(i, ARGS[i])
        except:
            logger.warn("Message Send Failed")
            raise
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return packet


    # **********************
    # Send LocoNet Message
    # **********************
    def sendLnMsg(self,msgLength,opcode,ARGS) :
        # format and send the specific LocoNet message
        # send up to 16 bytes in the message - includes checksum
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        packet = self.createPacket(msgLength,opcode,ARGS)
        logger.trace("Just prior to send message")
        logger.trace("Packet ==>> %s", packet)           # print packet to Script Output window
        try:
            jmri.InstanceManager.getList(jmri.jmrix.loconet.LocoNetSystemConnectionMemo).get(0).getLnTrafficController().sendLocoNetMessage(packet)
        except:
            logger.warn("Skipping JRMI.sendLoconetMessage")
            pass
        return


    # ***********************************
    # * Create and send a sensor report *
    # ***********************************
    def sendSenorReportMsg(self,sensorId):
        logger.trace("Entering %s.%s", __name__, thisFuncName())
        ARGS = [0]*14 # args 0 thru 15 filled later (0 ignored, 1 thru 14 args + cksum)
        snrAddr = sensorId -1
        in1 = (snrAddr & 0xFF) >> 1 # lower 7 address bits left shifted once
        b2I = (snrAddr % 2) << 5 # remainder odd/even
        b2XL = 0x50 # X = 1 and L = 1
        b2XIL = b2I | b2XL
        in2 = b2XIL + (snrAddr >> 8) # XIL plus upper 4 address bits
        msgLength = 4
        opcode = jmri.jmrix.loconet.LnConstants.OPC_INPUT_REP #0xB2 OPC_INPUT_REP
        ARGS[1] = in1
        ARGS[2] = in2
        self.sendLnMsg(msgLength,opcode,ARGS)
        logger.debug("Sent Sensor Message for SensorId:" + str(sensorId))
        logger.trace("Exiting %s.%s", __name__, thisFuncName())
        return


