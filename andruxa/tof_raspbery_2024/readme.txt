The usage of wifi is simple:
uncomment two lines of code in main
```
ap_mode()
conn = conn()
```

Run main. Connect to wifi from any device 

```
    ssid='myc00lcar'
    password='esttesttestt'
```

and run
```
nc 192.168.4.1 80
```

You'll start to get a stream of measurements from sensors in real time.

Comment it back when not needed. It's for debugging. Threads are not required. Pretty simple code.


# tof info
White is TX
Yellow is SDA
Green is SLC
Red is power
Black is ground

https://akizukidenshi.com/download/ds/socle/mtof171000c0_application_notes.pdf


# useful links
https://docs.micropython.org/en/v1.19.1/rp2/quickref.html#software-i2c-bus


# code example of very basic tof for raspbery pico
```
from machine import Pin, I2C
from time import sleep

pin = machine.Pin(0, machine.Pin.OUT)
pin.value(1)
sleep(1)
print("GPIO 0 pin value:", pin.value())

i2c = I2C(1, sda=Pin(18), scl=Pin(19), freq=100000)

addr = i2c.scan()[0]
print("addr", addr)
data = bytearray(2)

while True:
    pin.value(0)
    i2c.writeto(0x52, (b'\xD3'))
    data_bytes = i2c.readfrom(0x52, 2)
    print(data_bytes)
    data = data_bytes[0]<<8 | data_bytes[1]
    print(data, ' mm')
```

The main thing was to set signal on TX pin to 1 and switch to 0 before writing/reading.



