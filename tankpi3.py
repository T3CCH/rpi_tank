#!/usr/bin/env python
# coding: Latin-1

# Load library functions we want
import os
import signal
import subprocess
import sys
import time
import ThunderBorg
import pygame

# Re-direct our output to standard error, we need to ignore standard out to hide some nasty print statements from pygame
sys.stdout = sys.stderr

# Setup the ThunderBorg
TB = ThunderBorg.ThunderBorg()
# TB.i2cAddress = 0x15                  # Uncomment and change the value if you have changed the board address
TB.Init()
if not TB.foundChip:
    boards = ThunderBorg.ScanForThunderBorg()
    if len(boards) == 0:
        print 'No ThunderBorg found, check you are attached :)'
    else:
        print 'No ThunderBorg at address %02X, but we did find boards:' % TB.i2cAddress
        for board in boards:
            print '    %02X (%d)' % (board, board)
        print 'If you need to change the I²C address change the setup line so it is correct, e.g.'
        print 'TB.i2cAddress = 0x%02X' % (boards[0])
    sys.exit()
# Ensure the communications failsafe has been enabled!
failsafe = False
for i in range(5):
    TB.SetCommsFailsafe(True)
    failsafe = TB.GetCommsFailsafe()
    if failsafe:
        break
if not failsafe:
    print 'Board %02X failed to report in failsafe mode!' % TB.i2cAddress
    sys.exit()

# Settings for the joystick
axisUpDown = 1  # Joystick axis to read for up / down position
axisUpDownInverted = False  # Set this to True if up and down appear to be swapped
axisLeftRight = 2  # Joystick axis to read for left / right position
axisLeftRightInverted = False  # Set this to True if left and right appear to be swapped
buttonSlow = 8  # Joystick button number for driving slowly whilst held (L2)
slowFactor = 0.65  # Speed to slow to when the drive slowly button is held, e.g. 0.5 would be half speed
buttonFastTurn = 9  # Joystick button number for turning fast (R2)
interval = 0.1  # Time between updates in seconds, smaller responds faster but uses more processor time

# Poweroff Buttons
psButton = 16  # PlayStation Button mapping
leftShoulder = 10  # Left Shoulder Button Mapping
rightShoulder = 11  # Right Shoulder Button Mapping

# DPAD MAP for Camera
dpadUP = 4
dpadDOWN = 6
dpadLEFT = 7
dpadRIGHT = 5
buttonCircleCamCenter = 13

# Boom up and down
buttonTriangleDown = 12
buttonXUp = 14

# Variables to initialize the servos with
camXaxis = 0.05  # intended start point for the servos
camYaxis = 0.05
boomYaxis = 0.05
servoNudge = 0.0004  # Amount for the servos to move
# CHANGE these to use different GPIO Pins
boomservo = 17
servoXaxis = 22
servoYaxis = 27
# Travel Limits - Adjust these to set the physical endpoints on the servos
camservoXHigh = .0999
camservoXLow = .02
camservoYHigh = .0999
camservoYLow = .02
boomservoYHigh = .0999
boomservoYLow = .04

# initialize servos turn on then set starting point
f = open('/dev/pi-blaster', 'w')
f.write('%s=1\n' % boomservo)
f.write('%s=1\n' % servoXaxis)
f.write('%s=1\n' % servoYaxis)
f.write('%s=%s\n' % (boomservo, boomYaxis))
f.write('%s=%s\n' % (servoXaxis, camXaxis))
f.write('%s=%s\n' % (servoYaxis, camYaxis))
f.close()

# Power settings
voltageIn = 16.8  # Total battery voltage to the ThunderBorg
voltageOut = 9.6  # Maximum motor voltage

# Setup the power limits
if voltageOut > voltageIn:
    maxPower = 1.0
else:
    maxPower = voltageOut / float(voltageIn)

# Show battery monitoring settings
battMin, battMax = TB.GetBatteryMonitoringLimits()
battCurrent = TB.GetBatteryReading()
print 'Battery monitoring settings:'
print '    Minimum  (red)     %02.2f V' % battMin
print '    Half-way (yellow)  %02.2f V' % ((battMin + battMax) / 2)
print '    Maximum  (green)   %02.2f V' % battMax
print
print '    Current voltage    %02.2f V' % battCurrent
print

# Setup pygame and wait for the joystick to become available
TB.MotorsOff()
TB.SetLedShowBattery(False)
TB.SetLeds(0, 0, 1)
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Removes the need to have a GUI window
pygame.init()
# pygame.display.set_mode((1,1))
print 'Waiting for joystick... (press CTRL+C to abort)'
while True:
    try:
        try:
            pygame.joystick.init()
            # Attempt to setup the joystick
            if pygame.joystick.get_count() < 1:
                # No joystick attached, set LEDs blue
                TB.SetLeds(0, 0, 1)
                pygame.joystick.quit()
                time.sleep(0.1)
            else:
                # We have a joystick, attempt to initialise it!
                joystick = pygame.joystick.Joystick(0)
                break
        except pygame.error:
            # Failed to connect to the joystick, set LEDs blue
            TB.SetLeds(0, 0, 1)
            pygame.joystick.quit()
            time.sleep(0.1)
    except KeyboardInterrupt:
        # CTRL+C exit, give up
        print '\nUser aborted'
        TB.SetCommsFailsafe(False)
        TB.SetLeds(0, 0, 0)
        sys.exit()
print 'Joystick found'
joystick.init()
TB.SetLedShowBattery(True)
ledBatteryMode = True
try:
    print 'Press CTRL+C to quit'
    driveLeft = 0.0
    driveRight = 0.0
    running = True
    hadEvent = False
    upDown = 0.0
    leftRight = 0.0
    # Loop indefinitely
    while running:
        # Get the latest events from the system
        hadEvent = False
        events = pygame.event.get()
        # Handle each event individually
        for event in events:
            if event.type == pygame.QUIT:
                # User exit
                running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                # A button on the joystick just got pushed down
                hadEvent = True
            elif event.type == pygame.JOYAXISMOTION:
                # A joystick has been moved
                hadEvent = True
            if hadEvent:
                # Read axis positions (-1 to +1)
                if axisUpDownInverted:
                    upDown = -joystick.get_axis(axisUpDown)
                else:
                    upDown = joystick.get_axis(axisUpDown)
                if axisLeftRightInverted:
                    leftRight = -joystick.get_axis(axisLeftRight)
                else:
                    leftRight = joystick.get_axis(axisLeftRight)
                # Apply steering speeds
                if not joystick.get_button(buttonFastTurn):
                    leftRight *= 0.5
                # Determine the drive power levels
                driveLeft = -upDown
                driveRight = -upDown
                if leftRight < -0.05:
                    # Turning left
                    driveLeft *= 1.0 + (2.0 * leftRight)
                elif leftRight > 0.05:
                    # Turning right
                    driveRight *= 1.0 - (2.0 * leftRight)
                # Check for button presses
                if not joystick.get_button(buttonSlow):
                    driveLeft *= slowFactor
                    driveRight *= slowFactor
                # Check for Boom Command button presses
                if joystick.get_button(buttonXUp):
                    if boomYaxis <= boomservoYHigh:
                        boomYaxis = boomYaxis + servoNudge
                        f = open('/dev/pi-blaster', 'w')
                        f.write('%s=%s\n' % (boomservo, boomYaxis))
                        f.close()
                        print(boomYaxis)
                        # time.sleep (.5)
                if joystick.get_button(buttonTriangleDown):
                    if boomYaxis >= boomservoYLow:
                        boomYaxis = boomYaxis - servoNudge
                        f = open('/dev/pi-blaster', 'w')
                        f.write('%s=%s\n' % (boomservo, boomYaxis))
                        f.close()
                        print(boomYaxis)
                        # time.sleep (.5)
                # Check for Camera Y Axis Command button presses
                if joystick.get_button(dpadDOWN):
                    if camYaxis <= camservoYHigh:
                        camYaxis = camYaxis + servoNudge
                        f = open('/dev/pi-blaster', 'w')
                        f.write('%s=%s\n' % (servoYaxis, camYaxis))
                        f.close()
                        print(camYaxis)
                if joystick.get_button(dpadUP):
                    if camYaxis >= camservoYLow:
                        camYaxis = camYaxis - servoNudge
                        f = open('/dev/pi-blaster', 'w')
                        f.write('%s=%s\n' % (servoYaxis, camYaxis))
                        f.close()
                        print(camYaxis)
                # Check for Camera X Axis Command button presses
                if joystick.get_button(dpadLEFT):
                    if camXaxis <= camservoXHigh:
                        camXaxis = camXaxis + servoNudge
                        f = open('/dev/pi-blaster', 'w')
                        f.write('%s=%s\n' % (servoXaxis, camXaxis))
                        f.close()
                        print(camXaxis)
                if joystick.get_button(dpadRIGHT):
                    if camXaxis >= camservoXLow:
                        camXaxis = camXaxis - servoNudge
                        f = open('/dev/pi-blaster', 'w')
                        f.write('%s=%s\n' % (servoXaxis, camXaxis))
                        f.close()
                        print(camXaxis)
                # Re-center the camera based on the travel limits
                if joystick.get_button(buttonCircleCamCenter):
                        camXaxis = ((camservoXHigh - camservoXLow) / 2) + camservoXLow
                        camYaxis = ((camservoYHigh - camservoYLow) / 2) + camservoYLow
                        f = open('/dev/pi-blaster', 'w')
                        f.write('%s=%s\n' % (servoXaxis, camXaxis))
                        f.write('%s=%s\n' % (servoYaxis, camYaxis))
                        f.close()
                        print(camXaxis)
                        print(camYaxis)
                # Check for shutdown button combinations
                if joystick.get_button(psButton):
                    if joystick.get_button(leftShoulder) and joystick.get_button(rightShoulder):
                        p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
                        out, err = p.communicate()
                        for line in out.splitlines():
                            if 'web-rtc' in line:
                                pid = int(line.split(None, 1)[0])
                                os.kill(pid, signal.SIGKILL)
                        if ledBatteryMode:
                            TB.SetLedShowBattery(False)
                            TB.SetLeds(0, 0, 0)
                            ledBatteryMode = False
                            TB.SetCommsFailsafe(False)
                            TB.MotorsOff()
                        os.system("shutdown now -h")
                        sys.exit()
                # Set the motors to the new speeds
                TB.SetMotor1(driveRight * maxPower)
                TB.SetMotor2(driveLeft * maxPower)
        # Change LEDs to purple to show motor faults
        if TB.GetDriveFault1() or TB.GetDriveFault2():
            if ledBatteryMode:
                TB.SetLedShowBattery(False)
                TB.SetLeds(1, 0, 1)
                ledBatteryMode = False
        else:
            if not ledBatteryMode:
                TB.SetLedShowBattery(True)
                ledBatteryMode = True
        # Wait for the interval period
        time.sleep(interval)
    # Disable all drives
    TB.MotorsOff()
except KeyboardInterrupt:
    # CTRL+C exit, disable all drives
    TB.MotorsOff()
    TB.SetCommsFailsafe(False)
    TB.SetLedShowBattery(False)
    TB.SetLeds(0, 0, 0)
print
