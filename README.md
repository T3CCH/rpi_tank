rpi_tank
========

Description

This project is a modification of the sample scripts given by piborg.org.
tankpi3.py is a modified version of tbJoystick.py. The main features are listed
below. This setup leverages pi-blaster, thunderborg controller, hostapd,
Bluetooth PS3 controller and web-rtc video for the raspberry pi.

New additions

-   Add 3 servo controls for camera operation. XY for camera and 1 additional to
    lift the camera

-   Pressing the circle button will center the camera (in theory) based on the
    travel limit adjustments

-   Added the ability to poweroff the Raspberry Pi 3 from the controller using a
    3 button salute. (Left Shoulder / Right Shoulder + the PS button) will force
    the Pi to shutdown.

-   Added a kill portion to the poweroff part of the script to kill the pid for
    web-rtc if you are using that for real time video. It was causing the OS to
    hang on shutdown.

-   Reversed the slowdown button so it runs slow by default and when depressed
    it goes in “turbo” mode if that makes sense.

-   Added tons of configurable variables. The big ones are – Travel adjustments
    for servos, and Change the GPIO pins easily.

Usage:

Install and setup pi-blaster

Connect a ps3 controller via usb or Bluetooth.

Clone the repo to your pi.

Edit tankpi3.py and set your GPIO pins on your pi or leave them default 17,22,27

Execute tankpi3.py elevated.

sudo ./tankpi3.py

For Automated execution on boot

Edit /etc/rc.local

Add the full path to tankpi3.py

IE /home/pi/rpi_tank/tankpi3.py &

Make sure you use the “&” after the line for automatic start. VERY IMPORTANT!!!

Also make sure you have either enabled the daemon for pi-blaster or are
executing it on startup. Else the script will just move the tank and you wont
have servo control.

I configured pi-blaster to just initialize the pins I was using.

TODO:

-   Create a button combo to reboot the Pi from the controller

-   Trigger the LED’s to change to a specific color for rebooting.

-   Create function to lower the boom/camera lift arm to return it to a storage
    position when powerdown or reboot is triggered.

-   Other fancy stuff as I think of it.
