# ******************************************
# * Define the sensor listener: Print some *
# * information on the status change.      *
# ******************************************
#import jmri
import java

from classes.messenger import Messenger

msg = Messenger()


class SensorListener(java.beans.PropertyChangeListener):

    def propertyChange(self, event):
        global snrStatusArr
        
        #tmsg = "event.propertyName = "+event.propertyName
        #scrollArea.setText(scrollArea.getText()+tmsg+"\n")
        #tmsg = "event.source.systemName = "+event.source.systemName
        #scrollArea.setText(scrollArea.getText()+tmsg+"\n")
        #print event.propertyName
        if (event.propertyName == "KnownState"):
            systemName = event.source.systemName
            mesg = "Sensor " + systemName
            mesg = mesg.replace(mesg[:2], '') #delete first two characters
            if (event.source.userName != None):
                mesg += " (" + event.source.userName + ")"
            mesg += " is now " + str(event.newValue)
            #mesg += " from "+stateName(event.oldValue)
            #mesg += " to "+stateName(event.newValue)
            # print mesg
            # display and/or speak if either range value is empty
            snrStatusArr[systemName] = event.newValue
        return


    