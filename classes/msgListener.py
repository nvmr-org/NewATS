# **************************************************
#class to handle a listener event loconet messages *
#                                                  *
# OpCode values: 131 = 0x83 = OPC_GPON             *
#                229 = 0xE5 = OPC_PEER_XFER        *
#                                                  *
#                176 = 0xB0 = OPC_SW_REQ           *
#                177 = 0xB1 = OPC_SW_REP           *
#                178 = 0xB2 = OPC_INPUT_REP        *
#                231 = 0xE7 = OPC_SL_RD_DATA       *
#                237 = 0xED = OPC_IMM_PACKET       *
#                                                  *
# **************************************************

import time
import jmri

class MsgListener(jmri.jmrix.loconet.LocoNetListener):


    def message(self, msg):
        global aspectColor
        global accumByteCnt
        global address
        global address2
        global fbAddress
        global fbAddress2
        global command
        global command2
        
        ##global opcode
        global newMsgOpCodeHex,ARGS
        global BFsent
        global hiAddrByte
        global loAddrByte
        global firstBFE7
        global noSlotID
        
        global trolleyCnt
        global trolleyA,trolleyB,trolleyC
        global slotA,slotB,slotC
        global slotID
        global slotCnt
        global respCnt0xE7
        global notAlt0xE7
        global motionState
        
        global msgA
        global msgB
        global msgC
        
        if self.iTrace :
            print
        if self.iTrace :
            print "==>>entering MsgListener <--"
        newMsgOpCodeHex = msg.getOpCodeHex()
        newMsgLength = msg.getNumDataElements()
        accumByteCnt += newMsgLength
        # Note: accumByteCnt background task will read and be reset to zero and plotted every 1 second
        
        if self.lTrace : print "rcvd " + str(newMsgOpCodeHex)
        if self.sTrace : print "rcvd " + str(newMsgOpCodeHex)
        if self.bTrace : print "len = ",str(newMsgLength) + " msg = " + str(msg)

        ######################################################################################
        ## only listen for OPC_INPUT_REP message from trolley BODs (0xB2) going active (hi) ##
        ######################################################################################
        if (msg.getOpCode() == 178) and ((msg.getElement(2) & 0x10) == 0x10) :
            eventAddr = msg.sensorAddr() + 1
            if self.sTrace : print "== eventAddr = " + str(eventAddr)
            if eventAddr >= 100 and eventAddr <= 107 :
                if self.bTrace : print "eventAddr Rcvd = " + str(eventAddr) #gaw-debug
                if self.debounce :
                    sectionOccupied = checkSectionState(eventAddr)
                    if not sectionOccupied : #ignore if block is already occupied, signal must be due to contact bounce
                        doTrolleyStatusUpdate(eventAddr)
                else :
                    doTrolleyStatusUpdate(eventAddr) #direct call, no track contact bounce
                #autoTrolleySequencer(eventAddr)
                
                    
        #############################################################
        ## only listen for slot data response message (opcode 231) ##
        ## triggered by throttle requests 0xBF #OPC_LOCO_ADR       ##
        #############################################################
        if (msg.getOpCode() == 0xE7) and BFsent and (msg.getElement(4) == hiAddrByte) and (msg.getElement(9) == loAddrByte) : 
        ####if msg.getOpCode() == 0xE7 :
        ####if BFsent and (hiAddrByte == ARGS[4]) and (loAddrByte == ARGS[9]) :
            opcode = msg.getOpCode()
            if self.bTrace :
                print "opcode = " + hex(opcode)
            if self.sTrace : print "opcode = " + hex(opcode)
            self.ARGS[1] = msg.getElement(1)
            self.ARGS[2] = msg.getElement(2)
            self.ARGS[3] = msg.getElement(3)
            self.ARGS[4] = msg.getElement(4)
            self.ARGS[5] = msg.getElement(5)
            self.ARGS[6] = msg.getElement(6)
            self.ARGS[7] = msg.getElement(7)
            self.ARGS[8] = msg.getElement(8)
            self.ARGS[9] = msg.getElement(9)
            self.ARGS[10] = msg.getElement(10)
            self.ARGS[11] = msg.getElement(11)
            self.ARGS[12] = msg.getElement(12)
            #print "2 = " + str(ARGS[2])
            #print "4 = " + str(hex(ARGS[4]))
            #print "9 = " + str(hex(ARGS[9]))
            # check for E7 (opcode 231) response message after sending a BF query message (opcode 191)
            ####if BFsent and (hiAddrByte == ARGS[4]) and (loAddrByte == ARGS[9]) :
            if self.bTrace :
                print "BFsent4 = " + str(BFsent)
            slotID = ARGS[2] #set for later use
            if self.sTrace : print ">>slotID from ARGS[2] = " + str(ARGS[2])
            if firstBFE7 :
                firstBFE7 = False #only printed on first BFE7 pair
                if self.bTrace : print "2nd-trolleyA = " + str(trolleyA) + " and maps to slot " + str(slotA)
                if self.bTrace : print "2nd-trolleyB = " + str(trolleyB) + " and maps to slot " + str(slotB)
                if self.bTrace : print "2nd-trolleyC = " + str(trolleyC) + " and maps to slot " + str(slotC)
                if self.bTrace : print "E7slotID = " + hex(slotID)
                
        ####################################################
        ## prepare for automatic trolley sequencing if on ##
        ####################################################
        ####if BFsent :
            if respCnt0xE7 != -1 :
                respCnt0xE7 += 1
                if self.bTrace : print "respCnt0xE7 = " + str(respCnt0xE7)
                
                if respCnt0xE7 == 1 :
                    if self.bTrace : print "respCnt0xE7 = " + str(respCnt0xE7)
                    ####slotID = slotA #setup for update and inuse requests
                    motionState[str(slotID)] = '0' #inital state is "stopped"
                    slotA = slotID #store slotA value for later use
                    msgA = "trolleyA = " + str(trolleyA) + " and maps to slot " + str(slotA)
                    setSlotInuse() #got response to 0xBF request, now send 0xBA to set slot INUSE
                elif respCnt0xE7 == 2 :
                    BFsent = False #ignore any 0xE7s until this stuff is done
                    if self.sTrace : print "BFsent is now False"
                    writeSlotData() #got response to 0xBA request, now send 0xEF to set  INUSE slot data
                    print msgA
                    scrollArea.setText(scrollArea.getText() + msgA + "\n")
                    #>>>ringBell()
                    blinkOn() #blink headlight 5 times and leave on
                    #>>>time.sleep(5.0) #wait 3 secs before listening for next 0xE7
                    requestSlot(trolleyB) #get slot for next trolley address 
                elif respCnt0xE7 == 3 :
                    if bTrace : print "respCnt0xE7 = " + str(respCnt0xE7)
                    ####slotID = slotB #setup for update and inuse requests
                    motionState[str(slotID)] = '0' #inital state is "stopped"
                    setSlotInuse()  #response to 0xBF request, follow by sending 0xBA to set slot INUSE
                    slotB = slotID #store slotB value for later use
                    msgB = "trolleyB = " + str(trolleyB) + " and maps to slot " + str(slotB)
                elif respCnt0xE7 == 4 :
                    BFsent = False #ignore any 0xE7s until this stuff is done
                    if sTrace : print "BFsent is now False"
                    writeSlotData()
                    print msgB
                    scrollArea.setText(scrollArea.getText() + msgB + "\n")
                    #>>>ringBell()
                    blinkOn() #blink headlight 5 times and leave on
                    #>>>time.sleep(5.0) #wait 3 secs before listening for next 0xE7
                    requestSlot(trolleyC)
                elif respCnt0xE7 == 5 :
                    if self.bTrace : print "respCnt0xE7 = " + str(respCnt0xE7)
                    ####slotID = slotC #setup for update and inuse requests
                    motionState[str(slotID)] = '0' #inital state is "stopped"
                    setSlotInuse()  #response to 0xBF request, follow by sending 0xBA to set slot INUSE
                    slotC =  slotID #store slotC value for later use
                    msgC = "trolleyC = " + str(trolleyC) + " and maps to slot " + str(slotC)
                else : # can only be respCnt0xE7 == 6
                    BFsent = False #ignore any 0xE7s until this stuff is done
                    ####print "Last 0xBF done, no more will be sent"
                    #ignore 0xE7 response to 0xBA request, follow by sending 0xEF to set INUSE slot data
                    writeSlotData()
                    print msgC
                    scrollArea.setText(scrollArea.getText() + msgC + "\n")
                    #>>>ringBell()
                    blinkOn() #blink headlight 5 times and leave on
                    #>>>time.sleep(5.0) #wait 3 secs before announcing done
                    respCnt0xE7 = -1 #all done setting slots
                    
                    ATSmsg = "The Automatic Trolley Sequencer is now running."
                    print ATSmsg
                    scrollArea.setText(scrollArea.getText() + ATSmsg + "\n")
                    # this is where you select the voice synthesizer (speak, espeak, or nircmd)
                    ##if snSpkChgCheckBox.isSelected():
                        #pid = java.lang.Runtime.getRuntime().exec(["speak", msg])
                        # #pid = java.lang.Runtime.getRuntime().exec(["C:\Program Files (x86)\eSpeak\command_line\espeak", msg])
                        ##pid = java.lang.Runtime.getRuntime().exec('nircmd speak text "' + ATSmsg + '" -2 100')
                        ##pid.waitFor()
                        
        if self.oTrace : print "<<==exiting MsgListener"
        return


