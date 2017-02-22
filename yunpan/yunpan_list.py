import re
import json
import time
import random
import requests
from .conf import default_conf


# 不面向使用者的Lister实现
# 暂时未考虑参数校验和返回结果校验
class RawLister:
    def __init__(self, session: requests.Session):
        self.session = session
        self.__bdstoken = None

    def list_by_dict(self, remote_path: str):
        url = "http://pan.baidu.com/api/list?dir={remote_path}&bdstoken={bdstoken}&logid={logid}&num=100&order=time&desc=1&clienttype=0&showempty=0&web=1&page=1&channel=chunlei&web=1&app_id=250528".format(
            remote_path=remote_path,
            bdstoken=self.bdstoken,
            logid=self.log_id
        )
        temp_text = self.session.get(url, headers=default_conf.base_headers).text
        list_dict = json.loads(temp_text)

        return list_dict

    @property
    def bdstoken(self):
        if self.__bdstoken is None:
            url = "http://pan.baidu.com/disk/home"
            temp_respone = self.session.get(url, headers=default_conf.base_headers)
            temp_text = temp_respone.text
            self.__bdstoken = re.search('"bdstoken":"(?P<bdstoken>.+?)"', temp_text).group("bdstoken")
        return self.__bdstoken

    # 构建LogId的算法是看百度的JS源码得来的
    # 百度JS源码经过混淆，变量名均替换成了无意义字母
    # 为了省事，自己在写代码的时候使用了跟百度基本一样的变量名
    @property
    def log_id(self):
        u = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/~"
        the_time = time.time() * 1000
        temp_text = str(the_time) + str(random.random())
        temp_list = []
        for i in range(0, len(temp_text), 3):
            temp_list.append(temp_text[i: i + 3].encode("ASCII"))

        result = ""
        for e in temp_list:
            n = [0, 2, 1][len(e) % 3]
            e_length = len(e)
            t = e[0] << 16 | (e[1] if e_length > 1 else 0) << 8 | e[2] if e_length > 2 else 0

            o = [u[t >> 18], u[t >> 12 & 63], ord("=") if n >= 2 else u[t >> 6 & 63], ord("=") if n >= 1 else u[63 & t]]
            o = [chr(i) for i in o]
            result += "".join(o)
        result = result[:42]
        return result
