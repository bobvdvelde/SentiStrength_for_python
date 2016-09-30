#!/bin/python
'''
Made for python 3.X
assumes sentistrength is available in the current folder, 
i.e.: the folder contains 'SentiStrengthCom.jar'. The 
language files should be in folders with 2-letter ISO 
language codes. 

AR = Arabic
CY = Welsh 
DE = German
EL = Greek
EN = English
FA = Persian
FR = French
IL = Italian
NL = Dutch
PL = Polish
PT = Portuguese
RU = Russian
SP = Spanish
SW = Swedish
TU = Turkish

Current language sets (except EN) drawn from https://github.com/felipebravom/StaticTwitterSent/tree/master/extra/SentiStrength
Sentistrength java file can be obtained from sentistrength.wlv.ac.uk/ by emailing Professor Thelwall (address on website) 

Example use:

>> senti = sentistrength('EN')
>> res = senti.get_sentiment('I love using sentistrength!')
>> print(res)
 
{'negative': '-1', 'neutral': '1', 'positive': '4'}

'''

import socket
import urllib
import subprocess
import os
import time

class sentistrength():

    def __init__(self,language):
        self.language = language
        self.sentistrength = ""

    def __del__(self):
        if self.sentistrength:
            os.killpg(self.sentistrength.pid,15)

    def run_server(self, language):
        if language!=self.language and self.sentistrength:
            print("wrong language running, trying to switch")
            os.killpg(self.sentistrength.pid,15)
            time.sleep(1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(('0.0.0.0',8181))
        except ConnectionRefusedError:
            try:
                print("server not found, trying to launch server")
                self.sentistrength = subprocess.Popen(["java -jar SentiStrengthCom.jar sentidata ./%s/ listen 8181 trinary" %language], shell=True, preexec_fn=os.setsid)
                time.sleep(1)
                sock.connect(('0.0.0.0',8181))
                self.language = language
            except:
                raise "unable to start server, is there a process already running? "
        return sock
    

    def get_sentiment(self, string_to_code, language="EN"):
        url_encoded = urllib.parse.quote(string_to_code)
        request_string = "GET /%s HTTP/1.0 \r\n\r\n" %url_encoded
        sock = self.run_server(language)
        sock.sendall(str.encode(request_string,'UTF-8'))
        response = sock.recv(4096)
        resp_string = response.decode()
        positive, negative, score = resp_string.split()
        return {'positive':positive,'negative':negative,'neutral':score}


