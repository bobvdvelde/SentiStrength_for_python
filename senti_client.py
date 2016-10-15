#!/bin/python
'''
Made for python 3.X
assumes sentistrength is available in the current folder, 
i.e.: the folder contains 'SentiStrengthCom.jar'. 
The language files should be in folders with 2-letter ISO 
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

Example use (single-core client):

>>> senti = sentistrength('EN')
>>> res = senti.get_sentiment('I love using sentistrength!')
>>> print(res)

... {'negative': '-1', 'neutral': '1', 'positive': '4'}

Example use (multi-core client):

>>> ms    = multisent('EN')
>>> texts = ['This is great!!'] * 10000
>>> res   = ms.run_stream(texts)
>>> print(res[0])

... {'negative': '-1', 'neutral': '1', 'positive': '4'}

 
'''
import logging
import socket
import urllib
import subprocess
import os
import time
from joblib import Parallel, delayed

logging.basicConfig(level='INFO')
logger = logging.getLogger(__file__)


class sentistrength():

    def __init__(self,language, port=8181):
        self.language = language
        self.sentistrength = ""
        self.port = port 

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
            sock.connect(('0.0.0.0',port))
        except ConnectionRefusedError:
            try:
                print("server not found, trying to launch server")
                self.sentistrength = subprocess.Popen(["java -jar SentiStrengthCom.jar sentidata ./%s/ listen 8181 trinary" %language], shell=True, preexec_fn=os.setsid)
                time.sleep(1)
                sock.connect(('0.0.0.0',port))
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

class multisent():
    '''
    This is the multicore implementation of the sentistrength wrapper. 

    Description
    ---

    The multisent object has a specified language. On the first query to 
    'run_batch' or 'run_stream', the object will create a number of 
    sentistrengths equal to the specfied number of cores. Incomming texts
    will be uniformly divided over these instances. Calls to these systems 
    are threaded.
    
    Parameters
    ---
    language: str
        Should be an ISO two-letter designation for the language, such as
        'EN', 'NL' or 'PT'
    startport: int[default=8222]
        This is the first port used for the sentistrength instances. Ports are 
        designated range(startport, startport+i) for each instance, where ports
        with existing but unassociated sentistrength instances are ignored (!)
    cores: int[default=-2]
        Cores as per joblib notation. -1 = equal to available CPUs, lower is 
        CPU - cores, i.e. -3 on a 4 CPU system is 2. 
    batchsize: int[default=10000]
        When using the run_stream method, the stream is actually cut into 
        batches of this size. This is to reduce overhead of the joblib call
        while still enabeling bigger-than memory data streams. 

    Examples
    ---
    
    >>> ms    = multisent('EN')
    >>> texts = ['This is great!!'] * 10000
    >>> res   = ms.run_stream(texts)
    >>> print(res[0])

        {'negative': '-1', 'neutral': '1', 'positive': '4'}

    '''


    def __init__(self, language, startport=8222, cores=-2, batchsize=1000):
        self.language  = language
        self.cores     = cores
        self.instances = []
        self.status    = "initialized"
        self.startport = startport
        self.batchsize = batchsize

    def __del__(self):
        self.stop_all()

    def _top_port(self):
        return max([instance['port'] for instance in self.instances]+[self.startport-1]) 
    
    def get_status(self):
        no_instances = len(self.instances)
        if not no_instances:
            if self.status!='initialized': 
                self.status='stopped'
        else:
            self.status = 'Running {no_instances} instances'.format(**locals())
        return self.status    

    def check_instances(self):
        if not self.instances:
            print('No instances to check')
        for instance in self.instances:
            port  = instance.get('port','UNKNOWN')
            pid   = instance.get('pid','UNKNOWN')
            works = check_exists(instance['port']) and "WORKS" or "FAILED"
            print("Instance {pid:5} at port {port:5} status {works:8}".format(**locals()))

    def start_server(self, port=None, attempts=5):
        if not port:
            port = self._top_port()+1
        if check_exists(port): 
            logger.info("server at {port} already exists!".format(**locals()))
            start_server(port+1)
            return 
        instance = subprocess.Popen(["java -jar SentiStrengthCom.jar sentidata ./%s/ listen %s trinary" %(self.language,port)], 
                                    shell=True, preexec_fn=os.setsid)
        while not check_exists(port):
            time.sleep(1)
            attempts -= 1
            if not attempts: 
                logger.warn('failed to start {language} server at port {port}'.format(**locals()))
                return False
        instance = {'instance':instance, 'pid':instance.pid, 'language':self.language,'port':port}
        logger.info("started instance {pid} at port {port}".format(**instance))
        self.instances.append(instance)
        return True

    def stop_server(self, port=None,pid=None):
        if port and pid:
            logger.warn("this function requires EITHER a port OR a pid, ignores pid if both")
        if port:
            instance = [instance for instance in self.instances if instance['port']==port]
        elif pid:
            instance = [instance for instance in self.instances if instance['pid']==pid]
        else:
            instance = self.instances

        if not instance:
            logger.warn("Instance not found!")
            return False
        instance = instance[0]
        
        os.killpg(instance['instance'].pid, 15)
        time.sleep(1)
        if not check_exists(instance['port']):
            logger.info('Stopped {pid} instance at port {port}'.format(**instance))
            self.instances.remove(instance)
            return True
        else:
            logger.warn('Unable to stop {pid} instance running at {port}!!'.format(**instance))
            return False

    def _loop_over(self, looped_iterable, fixed_iterable):
        iterator = 0
        for item in fixed_iterable:
            if iterator==len(looped_iterable):
                iterator=0
            yield looped_iterable[iterator], item
            iterator +=1
    
    def _batch_up(self, iterable):
        batch = []
        for num, item in enumerate(iterable):
            batch.append(item)
            if not (num+1) % self.batchsize :
                yield batch
                batch = []
        if batch: yield batch

    def start_all(self):
        if self.cores < 0:
            no_servers = os.cpu_count() + (self.cores+1)
        else:
            no_servers = self.cores
        logger.info('Starting {no_servers} servers in {self.language}'.format(**locals()))
        for i in range(no_servers):
            self.start_server()
        self.get_status()

    def stop_all(self):
        while self.instances:
            self.stop_server(pid=instance['pid'])

    def run_batch(self, texts):
        if not self.instances: 
            logger.info('No servers found, starting servers')
            self.start_all()
        ports = [instance['port'] for instance in self.instances]
        return Parallel(n_jobs=min(self.cores,len(ports)), backend='threading')(delayed(query_instance)(port,text) for port,text in self._loop_over(ports, texts))

    def run_stream(self, texts):
        for batch in self._batch_up(texts):
            for item in self.run_batch(batch):
                yield item

def query_instance(port, string_to_code):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('0.0.0.0',port))
    except:
        raise Exception("unable to reach server")
    url_encoded = urllib.parse.quote(string_to_code)
    request_string = "GET /%s HTTP/1.0 \r\n\r\n" %url_encoded
    sock.sendall(str.encode(request_string,'UTF-8'))
    response = sock.recv(4096)
    resp_string = response.decode()
    positive, negative, score = resp_string.split()
    return {'positive':positive,'negative':negative,'neutral':score}


def check_exists(port):
    try:
        query_instance(port,'test string')
    except:
        return False
    return True


