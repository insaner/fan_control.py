#!/usr/bin/env python

# https://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python
# https://wiki.gnome.org/Projects/PyGObject/Threading

# for x in `ls /sys/class/hwmon/hwmon2/pwm2_*`; do echo $x = `cat $x`; done

# NOTE:
# needs to be run with superuser privileges
# and you need to set /sys/class/hwmon/hwmon?/pwm?_enabled to the right setting in order to actually control the fans


import signal

import sys
import time
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, Gtk

import glob
import os

hwmons = glob.glob('/sys/class/hwmon/hwmon*/pwm?')
# pwm_file = ['/sys/class/hwmon/hwmon2/pwm1', '/sys/class/hwmon/hwmon2/pwm2', '/sys/class/hwmon/hwmon2/pwm3']
pwm_file = sorted(hwmons)

num_fans = len(pwm_file)
#print(os.path.commonprefix(hwmons))
#print(os.pardir(hwmons[0]))

# set() gets only uniques
# list() turns it back into a list
hwmon_dirs = list(set(map(os.path.dirname, hwmons)))
#print("hwmon_dirs is   "  + ', '.join(hwmon_dirs) )

# cool python "list comprehension":
types_files = [x + "/name" for x in hwmon_dirs]

types_list = []
for filename in types_files:
    with open(filename) as f:
        # content = f.readlines() # whole file "lineS"
        types_list.append(f.readline()) 
    
print("pwm types:   "  + ', '.join(types_list) )

DEBUG = 0
last_error = ""
insert_time_stamp = 0

if DEBUG == 1:
    print("hwmons is   "  + ', '.join(hwmons) )


class StressTestWindow(Gtk.Window):

    ########## 
    def __init__(self):
        super(StressTestWindow, self).__init__(
            default_width=250, default_height=30, title="fan speed control")

        self.cancellable = Gio.Cancellable()
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, border_width=12)

        ## https://stackoverflow.com/a/18776386
        # self.fan_controller = [None]*num_fans
        ## https://stackoverflow.com/questions/348196/creating-a-list-of-objects-in-python
        self.fan_controller = [ type('MyObject', (object,), {}) for _ in range(num_fans) ]
        

        # two adjustments (initial value, min value, max value,
        #   step increment - press cursor keys to see!,
        #   page increment - click around the handle to see!,
        #   page size - not used here)
        # fan_slider_adj = Gtk.Adjustment(0, 0, 100, 5, 10, 0)
        # fan_slider_adj = Gtk.Adjustment(0, 0, 255, 25, 10, 0)

                
                
        for x in range(num_fans):
                self.fan_controller[x].fan_pwm_path = pwm_file[x]
                self.fan_controller[x].label = Gtk.Label(self.fan_controller[x].fan_pwm_path)
                self.fan_controller[x].fan_num = x
                self.fan_controller[x].fan_id = str(x)
                self.fan_controller[x].stress_state = 0
                
                # https://docs.python.org/release/3.1.3/library/multiprocessing.html
                # self.fan_controller[x].proc =  Process(target=self.proc_func, args=(self.fan_controller[x].core_num,))
               
                # a horizontal scale
                # self.fan_controller[x].h_scale = Gtk.Scale( orientation=Gtk.Orientation.HORIZONTAL, adjustment=fan_slider_adj )
                initial_value = 0
                initial_value =  int(self.get_pwm_cur_value(self.fan_controller[x].fan_pwm_path))
                
                self.fan_controller[x].h_scale = Gtk.Scale( orientation=Gtk.Orientation.HORIZONTAL, adjustment=Gtk.Adjustment(initial_value, 0, 255, 25, 10, 0) )
                self.fan_controller[x].h_scale.set_digits(0)  # of integers (no digits)
                self.fan_controller[x].h_scale.set_hexpand(True)
                self.fan_controller[x].h_scale.set_valign(Gtk.Align.START)

                self.fan_controller[x].h_scale.connect("value-changed", self.scale_moved, self.fan_controller[x])
                
                # print("fan_pwm_path is " + self.fan_controller[x].fan_pwm_path )
                self.fan_controller[x].enabled = self.get_pwm_enabled_state(self.fan_controller[x].fan_pwm_path)
                print(self.fan_controller[x].fan_pwm_path + "_enabled is   " +  self.fan_controller[x].enabled )
                #print("Horizontal scale is " + str(self.fan_controller[x].h_scale.get_value()) )
                self.fan_controller[x].h_scale.set_sensitive(False)
                
                # for meanings of "enabled", look up:    https://www.kernel.org/doc/Documentation/hwmon/ {it87, etc}
                if self.fan_controller[x].enabled == "1":
                        self.fan_controller[x].h_scale.set_sensitive(True)
        
                box.pack_start(self.fan_controller[x].label, False, True, 0)
                box.pack_start(self.fan_controller[x].h_scale, False, True, 0)

                
        self.quit_button = Gtk.Button(label="Quit")
        self.quit_button.connect("clicked", self.on_quit_clicked)

        textview = Gtk.TextView()
        self.textbuffer = textview.get_buffer()
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(textview)

        box.pack_start(self.quit_button, False, True, 0)
        box.pack_start(scrolled, True, True, 0)

        self.add(box)



    ########## 
    def scale_moved(self, event, fan_controller):
        self.print_to_pwm(fan_controller.fan_pwm_path, int(fan_controller.h_scale.get_value()))

    ########## 
    def get_pwm_enabled_state(self, pwmpath):
        global last_error
        ret = ""
        
        pwm_enabled_path = pwmpath + "_enable"
        try:
            pwm_fh = open(pwm_enabled_path, 'r')
            ret = pwm_fh.read().rstrip() # remove all trailing whitespace
            pwm_fh.close()
        
        except IOError, (error, message):
            cur_error = "Error: " + message + " for " + pwm_enabled_path
            if last_error != cur_error:
                # self.append_text(cur_error)
                last_error = cur_error
                print("EXCEPTION: " + cur_error)
        return ret

    ########## 
    def get_pwm_cur_value(self, pwmpath):
        global last_error
        ret = ""
        
        try:
            pwm_fh = open(pwmpath, 'r')
            ret = pwm_fh.read().rstrip() # remove all trailing whitespace
            pwm_fh.close()
        
        except IOError, (error, message):
            cur_error = "Error: " + message + " for " + pwmpath
            if last_error != cur_error:
                # self.append_text(cur_error)
                last_error = cur_error
                print("EXCEPTION: " + cur_error)
        return ret



    ########## 
    def on_quit_clicked(self, button):
        if DEBUG == 1:
            self.append_text("quit clicked...")
        self.cancellable.cancel()
        exit()


    ########## 
    def print_to_pwm(self, pwm_file, text):
	# https://docs.python.org/3/faq/programming.html#why-am-i-getting-an-unboundlocalerror-when-the-variable-has-a-value
        global last_error
        
        if DEBUG == 1:
            print('Sending cmd: [' + str(text) + "] to " + pwm_file)
            
        try:
            pwm_fh = open(pwm_file, 'w')
            print >>pwm_fh, text
            pwm_fh.close()
        
        #   https://www.oreilly.com/library/view/python-standard-library/0596000960/ch02s12.html
        # except IOError as e:
        #    self.append_text("Error: " + e.message)
        except IOError, (error, message):
            # print('exception')
            cur_error = "Error: " + message + " for " + pwm_file
            if last_error != cur_error:
                self.append_text(cur_error)
                last_error = cur_error
                print("EXCEPTION: " + cur_error)
        # sys.stdout = original
 

        

    ########## 
    def append_text(self, text):
        iter_ = self.textbuffer.get_end_iter()
        if insert_time_stamp == 1:
            self.textbuffer.insert(iter_, "[%s] %s\n" % (str(time.time()), text))
        else:
            self.textbuffer.insert(iter_, " %s\n" % (text))


if __name__ == "__main__":
    win = StressTestWindow()
    win.show_all()
    win.connect("delete-event", Gtk.main_quit)
    
    # https://stackoverflow.com/questions/16410852/keyboard-interrupt-with-with-python-gtk
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    Gtk.main()
    
