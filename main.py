"""Aliyun-DDNS. By: RickyHao"""

import os
import json
import requests
import time
import signal
from xml.etree.ElementTree import fromstring
from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109 import UpdateDomainRecordRequest, DescribeDomainRecordsRequest


SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CONFIG_FOLDER = os.path.join(SCRIPT_FOLDER, 'conf.d')
LOG_PATH = os.path.join(SCRIPT_FOLDER, 'log.txt')
LOCK_PATH = os.path.join(SCRIPT_FOLDER, '.lock')


class Client:
    def __init__(self,filepath,ip):
        self.filepath = filepath
        with open(filepath, 'r') as f:
            self.config = json.load(f)
        self.clt = AcsClient(self.config.get('Key'), self.config.get('Secret'), self.config.get('Region'))
        if not self.config.get('RecordID'):
            self.GetRecordID()
        self.config['IP']=ip
        self.UpdateRecord()

    def GetRecordID(self):
        id_r = DescribeDomainRecordsRequest.DescribeDomainRecordsRequest()
        id_r.set_DomainName(self.config.get('Domain'))
        id_r.set_RRKeyWord(self.config.get('RR'))
        id_re = self.clt.do_action(id_r)
        id_xml = fromstring(id_re.decode())
        self.config['RecordID'] = id_xml.find('DomainRecords/Record/RecordId').text
        with open(self.filepath, "w") as f:
                f.write(json.dumps(self.config))

    def UpdateRecord(self):
        ur_r = UpdateDomainRecordRequest.UpdateDomainRecordRequest()
        ur_r.set_RR(self.config['RR'])
        ur_r.set_RecordId(self.config['RecordID'])
        ur_r.set_Type('A')
        ur_r.set_Value(self.config['IP'])
        ur_r.set_Line("default")
        ur_re = self.clt.do_action(ur_r)
        Log(ur_re)

def Log(s):
    if not is_log:
        return
    if isinstance(s, bytes):
        s = s.decode()
    with open(LOG_PATH, "a+") as f:
        f.write(s)
        f.write("\n")

def GetIP():
    r = requests.get("http://ipv4.icanhazip.com")
    return r.text.strip('\n')
    
def CheckLock():
    if os.path.exists(LOCK_PATH):
        with open(LOCK_PATH, 'r') as f:
            pid = f.read()
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError:
            pass
        os.remove(LOCK_PATH)
        CheckLock()
    else:
        with open(LOCK_PATH, 'w')as f:
            f.write(str(os.getpid()))

def RemoveLock():
    os.remove(LOCK_PATH)


if __name__ =='__main__':
    CheckLock()
    is_log = False
    w = os.walk(CONFIG_FOLDER)
    ip = GetIP()
    for a,b,c in w:
        for fn in c:
            if fn.endswith('.json'):
                client=Client(os.path.join(a,fn), ip)
    Log(time.ctime())
    RemoveLock()
    exit()
