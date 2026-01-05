import network
import socket

def ap_mode():
    ssid='myc00lcar'
    password='esttesttestt'
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    while ap.active() == False:
        pass
    print('AP Mode Is Active, You can Now Connect')
    print('IP Address To Connect to:: ' + ap.ifconfig()[0])

def conn():
    global message_to_send
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creating socket object
    s.bind(('', 80))
    s.listen(5)

    while True:
      print('waiting for conn')
      conn, addr = s.accept()
      print('Got a connection from %s' % str(addr))
      return(conn)

def send_to(conn, msg):
    dbg = 0
    try:
        conn.send(msg)
        conn.send("\n")
        
    except Exception as e:
        if dbg:
            print("can't send", e)