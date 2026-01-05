from machine import Pin, I2C, SoftI2C
from time import sleep
import machine

sensors = [0]
data = bytearray(2)

def init_sensors():
    # sensor #1
    pin = machine.Pin(28, machine.Pin.OUT)
    pin.value(1)
    i2c = SoftI2C(scl=Pin(1), sda=Pin(0), freq=100_000)
    s = {"pin": pin, "i2c": i2c}
    sensors.append(s)
    
    # sensor #2
    pin = machine.Pin(20, machine.Pin.OUT)
    pin.value(1)
    i2c = SoftI2C(scl=Pin(11), sda=Pin(10), freq=100_000)
    s = {"pin": pin, "i2c": i2c}
    sensors.append(s)
        
    # sensor #2
    pin = machine.Pin(27, machine.Pin.OUT)
    pin.value(1)
    i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=100_000)
    s = {"pin": pin, "i2c": i2c}
    sensors.append(s)

    # sensor #4
    pin = machine.Pin(21, machine.Pin.OUT)
    pin.value(1)
    i2c = SoftI2C(scl=Pin(9), sda=Pin(8), freq=100_000)
    s = {"pin": pin, "i2c": i2c}
    sensors.append(s)

    # sensor #5
    pin = machine.Pin(26, machine.Pin.OUT)
    pin.value(1)
    i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=100_000)
    s = {"pin": pin, "i2c": i2c}
    sensors.append(s)
    print(sensors)
    
    # sensor #6
    pin = machine.Pin(22, machine.Pin.OUT)
    pin.value(1)
    i2c = SoftI2C(scl=Pin(7), sda=Pin(6), freq=100_000)
    s = {"pin": pin, "i2c": i2c}
    sensors.append(s)       

def tof_cm(sensor_id):
    s = sensors[sensor_id]
    s["pin"].value(0)
    s["i2c"].writeto(82, (b'\xD3'))
    data_bytes = s["i2c"].readfrom(82, 2)
    data = data_bytes[0]<<8 | data_bytes[1]
    data = data / 10
    s["pin"].value(1)
    return (data)