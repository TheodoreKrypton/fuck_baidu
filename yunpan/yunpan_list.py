import re
import json
import time
import random
import requests
from .conf import default_conf
from . import exceptions


# 不面向使用者的Lister实现
# 需要注意的是，由于百度网盘API限制
# Lister需要list的远程路径是一个文件时
# 其返回结果与空文件夹无异
class Lister:
    def __init__(self, session: requests.Session):
        self.session = session
        self.__bdstoken = None

    # 一次性获取文件夹下所有文件信息，当文件夹下项目过多时将会耗费较长时间
    # 后期准备做成懒加载的模式
    # TO improve
    def list(self, remote_path):
        result = []
        page_index = 1
        temp_result = self.list_one_page(remote_path, page_index)
        while temp_result:
            page_index += 1
            result += temp_result
            temp_result = self.list_one_page(remote_path, page_index)
        return result

    # 一次性显示最多一百个结果，可返回空list
    def list_one_page(self, remote_path: str, page_index: int):
        url = "http://pan.baidu.com/api/list?dir={remote_path}&bdstoken={bdstoken}&logid={logid}&num=100&order=time&desc=1&clienttype=0&showempty=0&web=1&page={page_index}&channel=chunlei&web=1&app_id=250528".format(
            remote_path=remote_path,
            bdstoken=self.bdstoken,
            logid=self.log_id,
            page_index=page_index
        )
        temp_text = self.session.get(url, headers=default_conf.base_headers).text
        list_dict = json.loads(temp_text)
        # 坑爹BUG
        # 键值不是error而是errno
        error_code = list_dict["errno"]
        if error_code == 0:
            return list_dict["list"]
        elif error_code == -9:
            raise exceptions.RemoteFileNotExist(remote_path)
        else:
            raise exceptions.UnExceptedRemoteReturnErrorMessage(temp_text)

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
