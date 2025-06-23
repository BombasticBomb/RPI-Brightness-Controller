# RPI-Brightness-Controller
A simple yet elegant UI to control the brightness of supported hdmi monitors for Raspberry PI Boards. It uses the DDC protocol found in most modern monitors to communicate with the display controller and control the brightness. This can only be used if the monitor is new enough to support DDC protocol. As a daily Raspberry Pi user who uses it to get online, I found no way to control the brightness of my monitor in Raspberry PI OS, so to solve this problem I decided to create my own simple solution. Hope you like it :)

- Run the run.sh file to automatically download the dependencies required to run this application.
- The repository includes both the python source code and also a binary compiled using the Nuitka Python Compiler that converts python code into C for compilation.
  
