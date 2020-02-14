import socket
import base64
import struct
import time
import random
import json
import os, select
from hashlib import sha1
from ssl import SSLError

class ClientHandler():
    def __init__(self, HTTPReqHandler):
        self.HTTPReqHandler = HTTPReqHandler
        self.addr = HTTPReqHandler.client_address
        self.hostname = None
        self.protocol = ''
        self.message = ['']
        self.closed = False
        self.session_id = None
        self.session = None
    #handsacking return protocol
    def handsacking(self):
        origin = self.HTTPReqHandler.headers.get("Origin")
        try:
            if origin in self.HTTPReqHandler.app.config["Access-Control-Allow"]["Origins"]:
                self.HTTPReqHandler.set_respone_header('Access-Control-Allow-Origin', origin)
        except:
            pass
        try:
            if self.HTTPReqHandler.app.config["Access-Control-Allow"]["Credentials"]:
                self.HTTPReqHandler.set_respone_header('Access-Control-Allow-Credentials', "true")
        except:
            pass
        
        key = self.HTTPReqHandler.headers.get('Sec-WebSocket-Key', '')
        protocol = self.HTTPReqHandler.headers.get('Sec-WebSocket-Protocol')
        
        self.HTTPReqHandler.set_respone_header('Upgrade', "WebSocket")
        self.HTTPReqHandler.set_respone_header('Connection', "Upgrade")
        self.HTTPReqHandler.set_respone_header('Sec-WebSocket-Accept', self.hashKey(key))
        if protocol:
            self.HTTPReqHandler.set_respone_header('Sec-WebSocket-Protocol', protocol)
        self.HTTPReqHandler.set_respone_header('Server', "Python-Websocket-Janoko")
        
        self.HTTPReqHandler.send_response_message(101, header_message = "Web Socket Protocol Handshake")
        if protocol:
            self.protocol = protocol
            return protocol
        else:
            self.protocol = None
            return True

    def hashKey(self, key):
        guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        combined = key + guid
        hashed = sha1(combined).digest()
        result = base64.b64encode(hashed)
        return result
    
    def decodeMessage(self, data):
        if len(self.message) != 3:
            self.message[0] += data
            data = self.message[0]
            lid = len(data)
            
            if ord(data[0]) == 136:
                self.close()
                return
            if lid < 6: # 1 + 1 + 4 (? + l_data + mask)
                return
            datalength = ord(data[1]) & 127
            mask_index = 2

            if datalength == 126:
                if lid < 8:
                    return
                mask_index = 4
                datalength = struct.unpack(">H", data[2:4])[0]
            elif datalength == 127:    
                if lid < 14:
                    return
                mask_index = 10
                datalength = struct.unpack(">Q", data[2:10])[0]
            self.message = [datalength, data[mask_index:mask_index+4], data[mask_index+4:]]
        else:
            self.message[2] += data
        
        if len(self.message[2]) < self.message[0]:
            return
        
        # Extract masks
        masks = [ord(m) for m in self.message[1]]
        msg = ''
        j = 0
        # Loop through each byte that was received
        for i in range(self.message[0]):
            # Unmask this byte and add to the decoded buffer
            msg += chr(ord(self.message[2][i]) ^ masks[j])
            j += 1
            if j == 4:
                j = 0
                
        self.onMessage(msg)
        if self.message[2][self.message[0]:] == '':
            self.message = ['']
        else:
            data = self.message[2][self.message[0]:]
            self.message = ['']
            self.decodeMessage(data)

    def sendMessage(self, s, binary = False):
        """
        Encode and send a WebSocket message
        """
        # Empty message to start with
        message = ""
        # always send an entire message as one frame (fin)
        # default text
        b1 = 0x81

        if binary:
            b1 = 0x02
        
        # in Python 2, strs are bytes and unicodes are strings
        if type(s) == unicode:
            payload = s.encode("UTF8")

        elif type(s) == str:
            payload = s
        # Append 'FIN' flag to the message
        message += chr(b1)
        # never mask frames from the server to the client
        b2 = 0

        # How long is our payload?
        length = len(payload)
        if length < 126:
            b2 |= length
            message += chr(b2)

        elif length < (2 ** 16):
            b2 |= 126
            message += chr(b2)
            l = struct.pack(">H", length)
            message += l

        else:
            l = struct.pack(">Q", length)
            b2 |= 127
            message += chr(b2)
            message += l
        # Append payload to message
        message += payload

        # Send to the client
        self.HTTPReqHandler.connection.send(str(message))

    def sendRespond(self, respMessage, code = 200, respData = None):
        resp = {
            "respond": respMessage,
            "code": code,
            "data": respData
        }
        self.sendMessage(json.dumps(resp))
        
    def onNew(self):
        print("new protocol ",self.protocol)
        print(self.addr)

    def onMessage(self, msg):
        print('MSG > ' + msg)
    def close(self):
        self.HTTPReqHandler.connection.shutdown(1)
        self.HTTPReqHandler.close_connection = 1
    def handle(self):
        if self.handsacking():
            self.onNew()
            self.HTTPReqHandler.connection.settimeout(1000)
            while not self.closed:
                try:
                    data = self.HTTPReqHandler.connection.recv(2048)
                    if not data:
                        print("ws sock > no data")
                        self.HTTPReqHandler.connection.shutdown(1)
                        self.HTTPReqHandler.close_connection = 1
                        break
                    self.decodeMessage(data)
                    self.HTTPReqHandler.wfile.flush()
                except socket.timeout, e:
                    print("ws sock>", e)
                    self.HTTPReqHandler.connection.shutdown(1)
                    self.HTTPReqHandler.close_connection = 1
                    break
                except SSLError, e:
                    print("ws sock e ssl >", e)
                    self.HTTPReqHandler.connection.shutdown(1)
                    self.HTTPReqHandler.close_connection = 1
                    break
                except Exception, e:
                    print("ws sock some error>", e)
                    self.HTTPReqHandler.close_connection = 1
                    break