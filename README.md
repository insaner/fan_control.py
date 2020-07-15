# fan_control.py
Simple python script to control PWM fans in Linux

Generates sliders to control PWM fans. The script sets the initial values to whatever the PWM setting was at the time of launching the script, but does not (currently) update those values automatically when they are changed outside the script (like through Power Management or Cool'N'Quiet). 

It is especially useful for enthusiasts who want to test how noisy their fans are at maximum speed, or to test their CPU + Heatsink thermals without disconnecting fans or messing around with kernel /proc settings on the commandline.

The script needs to be run with superuser privileges if you want to change values, and you need to set `/sys/class/hwmon/hwmon?/pwm?_enabled` to the right setting (most likely "1") in order to actually control the fans. The script disables the controls if changing those values would not affect the fan speed. A future version might include the option to use a checkbox to change the setting from the script itself.

I have kept useful comments and links within the code for python newbies like myself.

Tested only on Linux. Requires GTK 3.

**Use at your own risk!**
