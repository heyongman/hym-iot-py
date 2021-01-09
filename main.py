from machine import Pin
from machine import reset
import esp
import network
import _thread
import usocket as _socket
import ussl as ssl
import utime
import ujson
import ntptime

led = Pin(2, Pin.OUT)


def led_info():
    led.value(1)
    utime.sleep(2)
    led.value(0)


def led_warn():
    for i in range(0, 4):
        led.value(1)
        utime.sleep_ms(80)
        led.value(0)
        utime.sleep_ms(80)


def pin_fun(pid, mode, value, delay=0):
    # pin
    led.value(0)
    pin = Pin(pid, mode, value=value)
    pin.value(value)
    led.value(1)
    if delay > 0:
        utime.sleep(delay)
        pin.value(0 if value == 1 else 1)
    else:
        utime.sleep_ms(100)
    led.value(0)


def ntp_time():
    ntptime.NTP_DELTA = 3155644800
    ntptime.host = 'ntp1.aliyun.com'
    ntptime.settime()


class IOT:
    def __init__(self, ssid, pwd, host, port):
        self.ssid = ssid
        self.pwd = pwd
        self.host = host
        self.port = port
        self.is_exit = False
        # wlan
        self.wlan = network.WLAN(network.STA_IF)

    def wlan_connect(self):
        self.wlan.active(False)
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.pwd)
        while not self.wlan.isconnected():
            print('.')
            utime.sleep_ms(500)
        print(self.wlan.ifconfig())
        led_info()

    def big_iot_receive(self):
        try:
            while True:
                msg = self.skt.readline()
                if msg == b'' or msg == b'\r\n':
                    continue
                # 解析
                msg_json = ujson.loads(msg)

                method = msg_json['M']
                if method == 'checkinok':
                    print('checkinok:' + msg_json['NAME'])
                elif method == 'b':
                    self.skt.write(b'{"M":"beat"}\n')
                elif method == 'login':
                    print('login:' + msg_json['NAME'])
                elif method == 'logout':
                    print('logout:' + msg_json['NAME'])
                elif method == 'say':
                    print(msg_json)
                    c = msg_json['C']
                    cs = c.split('_')
                    # 示例：2_1/2_0_3 分别代表IO2设为高电平，IO2设为低电平3秒后逆转
                    if len(cs) >= 2:
                        pid = int(cs[0])
                        value = int(cs[1])
                        pin_fun(pid, Pin.OUT, value)
                        if len(cs) == 3:
                            pin_fun(pid, Pin.OUT, value, int(cs[2]))
                        data = {
                            "M": "update",
                            "ID": "20129",
                            "V": {"18360", pid + value * 0.1}
                        }
                        self.skt.write((ujson.dumps(data) + "\n").encode('utf-8'))
                    else:
                        print('unknown control:', c)
                else:
                    print('unknown method:', method)
        except Exception as e:
            self.is_exit = True
            print('receive ', e)
            self.skt.close()
            return 0

    def monitor(self):
        while True:
            try:
                if not self.wlan.isconnected() or self.is_exit:
                    led_warn()
                    print('restarting...')
                    reset()
                self.skt.write(b'{"M":"beat"}\n')
                utime.sleep(40)
            except Exception as e:
                print("monitor exception", e)
                self.skt.close()

    def big_iot(self):
        # wlan
        if not self.wlan.isconnected():
            self.wlan_connect()

        # socket
        self.skt = _socket.socket()
        addr = _socket.getaddrinfo(self.host, self.port)[0][-1]
        self.skt.connect(addr)
        # ssl
        self.skt = ssl.wrap_socket(self.skt)
        print('connected:', addr)

        # login
        self.skt.write(b'{"M": "checkin", "ID": "20129", "K": "343747140"}\n')
        self.is_exit = False

        # receive thread
        _thread.start_new_thread(self.big_iot_receive, ())

        # monitor thread
        _thread.start_new_thread(self.monitor, ())


if __name__ == '__main__':
    w_ssid = 'ziroom3004-1'
    w_pwd = '4001001111'
    b_host = 'www.bigiot.net'
    b_port = 8585

    esp.osdebug(None)
    IOT(w_ssid, w_pwd, b_host, b_port).big_iot()

    import webrepl
    webrepl.start()
