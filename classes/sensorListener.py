# ******************************************
# * Define the sensor listener: Print some *
# * information on the status change.      *
# ******************************************
import logging
import sys
import java
import jmri

logger = logging.getLogger("ATS."+__name__)
logger.setLevel(logging.DEBUG)
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
            logger.debug("Block Event Detected for block %s", sensor_num)
            logger.debug("Block OldState=%s NewState=%s Active=%s",event.oldValue,event.newValue,jmri.Sensor.ACTIVE)
            if event.newValue == jmri.Sensor.ACTIVE :
                logger.debug("Block Event Detected for block %s", sensor_num)
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
