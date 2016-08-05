from aliyunsdkcore import client
from aliyunsdkalidns.request.v20150109 import UpdateDomainRecordRequest
from aliyunsdkalidns.request.v20150109 import DescribeDomainRecordsRequest
import json
import re
import requests

class Client:
    config=json.load(file("config.json"))
    clt=client.AcsClient(config['Key'].encode(),config['Secret'].encode(),config['Region'].encode());

    def GetRecordID(self):
        id_r=DescribeDomainRecordsRequest.DescribeDomainRecordsRequest()
        id_r.set_DomainName(config['Domain'].encode())
        id_r.set_RRKeyWord(config['RR'].encode())
        id_re=clt.do_action(id_r)
        config['RecordID']=re.findall(pattern="<RecordId>(\d*)</RecordId>",string=id_re)[0]
        with open("config.json","w") as f:
            f.write(json.dumps(config))

    def GetIP(self):
        r=requests.get("http://icanhazip.com")
        config['IP']=r.text.strip('\n')
    
    def UpdateRecord(self):
        ur_r=UpdateDomainRecordRequest.UpdateDomainRecordRequest()
        ur_r.set_RR(config['RR'].encode())
        ur_r.set_RecordId(config['RecordID'].encode())
        ur_r.set_Type('A')
        ur_r.set_Value(config['IP'].encode())
        ur_re=clt.do_action(ur_r)
        print(ur_re)

if __name__ =='__main__':
    client=Client()
    if !client.config.has_key('RecordID'):
        client.GetRecordID();
    client.GetIP()
    client.UpdateRecord()