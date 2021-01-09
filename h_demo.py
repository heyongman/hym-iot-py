from machine import Pin, I2C
import _thread
import utime
import ssd1306
import dht


def i2d():
    i2c = I2C(1, scl=Pin(16), sda=Pin(17), freq=100000)
    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    display.text('adsa', 0, 0,-1)


def dht11():
    d = dht.DHT11(Pin(4))
    d.measure()
    d.temperature()  # eg. 23 (°C) d.humidity() # eg. 41 (% RH)
    d.humidity()


if __name__ == '__main__':
    dht11()
