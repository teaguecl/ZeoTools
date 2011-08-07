#!/usr/bin/python -d
# -*- coding: utf-8 -*-

# DynamicAlarm.py
#
# Alarms the user after a dynamically declared series of events has occured
import platform
import subprocess
import time

DEEP_SLEEP_TOTAL_SECONDS = 3600

class AlarmStateMachine( object ):
    def __init__(self):
        self.state = "START"
        self.totalDeepSleepSeconds = 0
        self.currentSleepState = "Unknown"

    def handleEvent(self, event):
        print "state is: %s" % (self.state)
        if self.state == "START":
            if event == "NIGHT_START":
                self.state = "ACQUIRING_DEEP_SLEEP"
            if event == "SLEEP_ONSET":
                self.state = "ACQUIRING_DEEP_SLEEP"
        elif self.state == "ACQUIRING_DEEP_SLEEP":
            if event == "DEEP_SLEEP_DONE":
                self.state = "WAIT_FOR_REM_TRANSITION"
        elif self.state == "WAIT_FOR_REM_TRANSITION":
            if event == "REM_TRANSITION":
                self.state = "ALARMING"
                print "ALARM!!!"
                file='78562_joedeshon_alarm_clock_ringing_01.wav'
                if platform.system().lower().find('win') > -1:
                    from winsound import PlaySound, SND_FILENAME, SND_ASYNC
                    PlaySound(file, SND_FILENAME|SND_ASYNC)
                elif platform.system().lower().find('linux') > -1:
                    print "TODO: can't figure out how to play audio in Linux without Mplayer installed yet!"
                    print "Press 'Q' or 'ESC' to stop the alarm"
                    try:
                        subprocess.call(['mplayer -msglevel all=-1 '+file], shell=True)
                    except OSError, e:
                        print >>sys.stderr, "Execution failed:", e
                else:
                    print "TODO: unsupported OS: %s" % (platform.system())
    

        elif self.state == "ALARMING":
            print "foobar alarming"

    def handleDeepSleep(self, deep_sleep_seconds):
        self.totalDeepSleepSeconds += deep_sleep_seconds
        print "%s seconds deep sleep accumulated" % (self.totalDeepSleepSeconds)
        if self.totalDeepSleepSeconds >= DEEP_SLEEP_TOTAL_SECONDS:
            print "One hour of Deep Sleep acquired!"
            self.handleEvent("DEEP_SLEEP_DONE")
        self.currentSleepState = "Deep"

    def handleLightSleep(self, light_sleep_seconds):
        print "handleLightSleep"
        if self.currentSleepState == "REM":
            # then we just transitioned from REM to Light
            self.handleEvent("REM_TRANSITION")
        self.currentSleepState = "Light"

    def handleREM(self, rem_seconds):
        print "handleREM"
        self.currentSleepState = "REM"

    def handleAwake(self, awake_seconds):
        print "handleAwake"
        if self.currentSleepState == "REM":
            # then we just transitioned from REM to Awake
            self.handleEvent("REM_TRANSITION")
        self.currentSleepState = "Awake"


class DynamicAlarm( object ):
    def __init__(self):
        self.stateMachine=AlarmStateMachine()

    def updateEvent(self, timestamp, version, event):
        if event == "NightStart":            
            self.stateMachine.handleEvent("NIGHT_START")
        elif event == "SleepOnset":
            self.stateMachine.handleEvent("SLEEP_ONSET")

    def updateSlice(self, slice):        
        timestamp = slice['ZeoTimestamp']
        # todo: use bad signal indicator?
        if not slice['SleepStage'] == None:
            stage = slice['SleepStage']
            if str(stage) == "Deep":
                self.stateMachine.handleDeepSleep(30)  # TODO: always accumulate 30 seconds?!
            elif str(stage) == "Light":
                self.stateMachine.handleLightSleep(30)  # TODO: always accumulate 30 seconds?!
            elif str(stage) == "REM":
                self.stateMachine.handleREM(30)  # TODO: always accumulate 30 seconds?!
            elif str(stage) == "Awake":
                self.stateMachine.handleAwake(30)  # TODO: always accumulate 30 seconds?!


# This function never runs except during testing.  You should run DataRecorder.pyw for a live trial
def main():
    print "hello!"
    alarm=DynamicAlarm()
    alarm.updateEvent(0, 3, "HeadbandUnDocked")
    alarm.updateEvent(0, 3, "HeadbandDocked")
    alarm.updateEvent(0, 3, "NightStart")
    alarm.updateEvent(0, 3, "SleepOnset")

    Slice = {'ZeoTimestamp'  : None, # String %m/%d/%Y %H:%M:%S
                      'Version'       : None, # Integer value
                      'SQI'           : None, # Integer value (0-30)
                      'Impedance'     : None, # Integer value as read by the ADC
                                              # Unfortunately left raw/unitless due to
                                              # nonlinearity in the readings.
                      'Waveform'      : [],   # Array of signed ints
                      'FrequencyBins' : {},   # Dictionary of frequency bins which are relative to the 2-30hz power
                      'BadSignal'     : None, # Boolean
                      'SleepStage'    : None  # String
                     }

    Slice['ZeoTimestamp'] = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(time.time()))
    Slice['Version'] = 3
    Slice['SleepStage'] = 'REM'
    alarm.updateSlice(Slice)
    ###
    Slice['SleepStage'] = 'Deep'
    count = 0
    while (count < 121):
        alarm.updateSlice(Slice)
        count = count + 1
    ###
    Slice['SleepStage'] = 'REM'
    count = 0
    while (count < 4):
        alarm.updateSlice(Slice)
        count = count + 1
    ###
    Slice['SleepStage'] = 'Deep'
    alarm.updateSlice(Slice)
    ###
    Slice['SleepStage'] = 'REM'
    alarm.updateSlice(Slice)
    ###
    Slice['SleepStage'] = 'Light'
    alarm.updateSlice(Slice)

if __name__ == "__main__":
    main()
