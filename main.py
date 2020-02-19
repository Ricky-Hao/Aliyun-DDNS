"""Aliyun-DDNS. By: RickyHao"""

import os
import json
import requests
import signal
import logging
from xml.etree.ElementTree import fromstring
from aliyunsdkcore.client import AcsClient
from aliyunsdkalidns.request.v20150109 import UpdateDomainRecordRequest, DescribeDomainRecordsRequest

SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CONFIG_FOLDER = os.path.join(SCRIPT_FOLDER, 'conf.d')
LOCK_PATH = os.path.join(SCRIPT_FOLDER, '.lock')

logger = logging.getLogger('Aliyun-DDNS')


class Client:
    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'r') as f:
            self._config = json.load(f)

        self.domain_name = self._config['Domain']
        self.rr = self._config['RR']
        self.domain = '{0}.{1}'.format(self.rr, self.domain_name)
        self.record_id = self._config.get('RecordID')
        self.ip = self._config.get('IP')

        logger.debug('Read config: {0}'.format(filepath))

        self._client = AcsClient(self._config.get('Key'), self._config.get('Secret'), self._config.get('Region'))

        if self.record_id is None:
            self.get_record_id()

        if self.ip_changed():
            self.update_record()

    def get_record_id(self) -> None:
        id_req = DescribeDomainRecordsRequest.DescribeDomainRecordsRequest()
        id_req.set_DomainName(self.domain_name)
        id_req.set_RRKeyWord(self.rr)
        id_res = self._client.do_action_with_exception(id_req)
        id_xml = fromstring(id_res.decode())
        self.record_id = id_xml.find('DomainRecords/Record/RecordId').text
        logger.debug('Get RecordID for domain: {0}.'.format(self.domain))

    def ip_changed(self) -> bool:
        ip = self.get_ip()
        if self.ip is None or self.ip != ip:
            self.ip = ip
            return True
        else:
            return False


    def update_record(self) -> None:
        update_req = UpdateDomainRecordRequest.UpdateDomainRecordRequest()
        update_req.set_RR(self.rr)
        update_req.set_RecordId(self.record_id)
        update_req.set_Type('A')
        update_req.set_Value(self.ip)
        update_req.set_Line("default")
        update_res = self._client.do_action_with_exception(update_req)
        logger.debug(update_res.decode())
        logger.info('Update record for domain: {0} with ip: {1}'.format(self.domain, self.ip))
        self.save()

    def save(self) -> None:
        self._config['RecordID'] = self.record_id
        self._config['IP'] = self.ip
        with open(self.filepath, "w") as f:
            f.write(json.dumps(self._config))
        logger.debug('Save config: {0}.'.format(self.filepath))

    @staticmethod
    def get_ip() -> str:
        res = requests.get("http://ipv4.icanhazip.com")
        if res.status_code != 200:
            logger.error('Invalid IP:\nStatus Code: {0}\nResponse: {1}'.format(res.status_code, res.text))
        ip = res.text.strip('\n')
        logger.debug('Get ip: {0}'.format(ip))
        return ip

    @staticmethod
    def check_lock() -> None:
        if os.path.exists(LOCK_PATH):
            with open(LOCK_PATH, 'r') as f:
                pid = f.read()
            try:
                os.kill(int(pid), signal.SIGTERM)
            except OSError:
                pass
            os.remove(LOCK_PATH)
            Client.check_lock()
        else:
            with open(LOCK_PATH, 'w')as f:
                f.write(str(os.getpid()))

    @staticmethod
    def remove_lock() -> None:
        os.remove(LOCK_PATH)


if __name__ == '__main__':
    Client.check_lock()
    for dir_paths, dir_names, file_names in os.walk(CONFIG_FOLDER):
        for filename in file_names:
            if filename.endswith('.json'):
                client = Client(os.path.join(dir_paths, filename))
    Client.remove_lock()
    exit()
