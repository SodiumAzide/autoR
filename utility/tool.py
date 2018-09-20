import requests
import logging
import base64
import json
import time
import math
import hashlib
import random
import zlib
logging.basicConfig(filename='app.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(message)s',
                    datefmt='%m-%d %H:%M:%S')


class Tool:
    version_url = "http://version.jr.moefantasy.com/index/checkVer/3.6.0/100011/2&version=3.1.0" +\
                       "&channel=100011&market=2"
    headers = {
        'Accept-Encoding': 'identity',
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.1.1; GT-P5210 Build/LMY48Z)'
    }
    login_server = ""

    def __init__(self, username, password):
        self.session = requests.Session()
        self.session.headers = self.headers
        self.username = username
        self.password = password
        self.server = ""
        res = self.session.get(self.version_url).json()
        logging.debug(json.dumps(res))
        self.version = res["version"]["newVersionId"]
        self.login_server = res["loginServer"]
        logging.info("version: {0}; server: {1}".format(self.version, self.login_server))

    def complete_url(self, url):
        add = '&gz=1&market=2&channel=10012'
        secret_key = 'ade2688f1904e9fb8d2efdb61b5e398a'
        ts = str(math.trunc(time.time()))
        rand = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        checksum = hashlib.md5((ts + rand + secret_key).encode('utf-8')).hexdigest()
        return url + '&t=' + ts + rand + '&e=' + checksum + add + '&version=' + self.version

    def get(self, url, data=None):
        url = self.complete_url(self.server + url)
        while True:
            if data is not None:
                r = self.session.post(url, data=data).content
            else:
                r = self.session.post(url).content
            try:
                r = zlib.decompress(r).decode()
            except zlib.error:
                r = r.decode()
            r = json.loads(r)
            try:
                if r["eid"] == -103:
                    time.sleep(3)
                    continue
            except KeyError:
                pass
            return r

    def login(self):
        url = self.login_server + "/index/passportLogin"
        server_url = "/index/login/{}"
        username = base64.encodebytes(str(self.username).encode())
        password = base64.encodebytes(str(self.password).encode())
        r = self.session.post(url, data={"username": username, "pwd": password}).json()
        logging.info(json.dumps(r))
        self.session.cookies.update({"hf_skey": r["hf_skey"]})
        user_id = r["userId"]
        default_server = int(r["defaultServer"]) - 2
        self.server = r["serverList"][default_server]["host"]
        r = self.get(server_url.format(user_id))
        logging.info(json.dumps(r))

    def data(self):
        return self.get("/api/initGame")

    def explore(self):
        _res_url = "/explore/getResult/{}/"
        _start_url = "/explore/start/{0}/{1}/"
        now = int(time.time())
        for _ in self.data()["pveExploreVo"]["levels"]:
            if now > _["endTime"]:
                r = self.get(_res_url.format(_["exploreId"]))
                logging.info(json.dumps(r))
                logging.info("explore: fleet {} finished exploring".format(_["fleetId"]))
                r = self.get(_start_url.format(_["fleetId"], _["exploreId"]))
                logging.info(json.dumps(r))


if __name__ == "__main__":
    # 账号, 密码
    a = Tool(4, 4)
    a.login()
    logging.info(json.dumps(a.data()))
    while True:
        a.explore()
        time.sleep(5 * 60)
