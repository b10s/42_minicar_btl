import machine
from netwrk import *
import tof
from time import *



# ap_mode()
# conn = conn()
tof.init_sensors()
while True:
    sleep(0.5)
    # send_to(conn, "hey")
    print(tof.tof_cm(1), " cm")
    print(tof.tof_cm(2), " cm")
    print(tof.tof_cm(3), " cm")
    print(tof.tof_cm(4), " cm")
    print(tof.tof_cm(5), " cm")
    print(tof.tof_cm(6), " cm")
    print("---")