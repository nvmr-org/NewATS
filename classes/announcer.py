import java

class MessageAnnouncer(object):

    __instance = None

    def __init__(self,swingControlToMonitor):
        super(MessageAnnouncer,self).__init__()
        self.__swingControl = swingControlToMonitor
        pass


    def __new__(cls,swingControlToMonitor):
        if MessageAnnouncer.__instance is None:
            MessageAnnouncer.__instance = object.__new__(cls,swingControlToMonitor)
        return MessageAnnouncer.__instance

    def announceMessage(self, messageToAnnounce):
        if self.__swingControl is None: return
        if self.__swingControl.isSelected():
            javaexec = getattr(java.lang.Runtime.getRuntime(), "exec")
            javaexec('nircmd speak text "'+messageToAnnounce+'" 0 100')
        return
