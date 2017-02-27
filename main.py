#!/usr/bin/python2.7
from aliyunsdkcore import client as acsclient
from aliyunsdkalidns.request.v20150109 import UpdateDomainRecordRequest
from aliyunsdkalidns.request.v20150109 import DescribeDomainRecordsRequest
import time
import json
import re
import requests
import os 

class Client:
    def __init__(self,filepath,ip):
        self.filepath=filepath
        self.config=json.load(file(self.filepath))
        self.clt=acsclient.AcsClient(self.config['Key'].encode(),self.config['Secret'].encode(),self.config['Region'].encode());
        if not self.config.has_key('RecordID'):
            self.GetRecordID()
        self.config['IP']=ip
        self.UpdateRecord()

    def GetRecordID(self):
        id_r=DescribeDomainRecordsRequest.DescribeDomainRecordsRequest()
        id_r.set_DomainName(self.config['Domain'].encode())
        id_r.set_RRKeyWord(self.config['RR'].encode())
        id_re=self.clt.do_action(id_r)
        self.config['RecordID']=re.findall(pattern="<RecordId>(\d*)</RecordId>",string=id_re)[0]
        with open(self.filepath,"w") as f:
                f.write(json.dumps(self.config))

    def UpdateRecord(self):
        ur_r=UpdateDomainRecordRequest.UpdateDomainRecordRequest()
        ur_r.set_RR(self.config['RR'].encode())
        ur_r.set_RecordId(self.config['RecordID'].encode())
        ur_r.set_Type('A')
        ur_r.set_Value(self.config['IP'].encode())
        ur_r.set_Line("default")
        ur_re=self.clt.do_action(ur_r)
        Log(ur_re)

def Log(s):
    if not is_log:
        return
    with open(os.path.split(os.path.realpath(__file__))[0]+"/output.log","a+") as f:
        f.write(s)
        f.write("\n")

def GetIP():
    r=requests.get("http://icanhazip.com")
    return r.text.strip('\n')
    

if __name__ =='__main__':
    is_log=0
    ma=re.compile("(.*\.json)")
    w=os.walk(os.path.split(os.path.realpath(__file__))[0]+"/conf.d")
    ip=GetIP()
    for a,b,c in w:
        for fn in c:
            if ma.match(fn) and fn!="config.json.sample":
                client=Client(os.path.join(a,fn),ip)
    Log(time.ctime())
    exit()
