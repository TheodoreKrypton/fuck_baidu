# coding:utf-8

import os
import re
import rsa
import json
import base64
import requests

import base, exceptions
from conf import default_conf


class LoginRecoder:
    def __init__(self,
                 user_name,
                 password,
                 recode_path,
                 auto_save_recode,
                 auto_load_recode):
        self.session = requests.session()
        self.gid = base.build_gid()
        self.user_name = user_name
        self.password = password
        self.recode_path = recode_path
        self.auto_load_recode = auto_load_recode
        self.auto_save_recode = auto_save_recode

        if self.auto_load_recode:
            self.try_load()
        self.__has_prepared_for_login = False

    def login_with_user(self):
        verify_image_url = self.get_verify_image_url()
        if verify_image_url != "":
            print("请访问以下网址查看验证码并输入\n{verify_image_url}".format(verify_image_url=verify_image_url))
            verify_code = raw_input()
        else:
            verify_code = ""
        self.login_with_verify_code(verify_code)
        if not self.has_logined():
            raise exceptions.LoginFail

    def get_verify_image_url(self):
        self.__prepare_for_login()
        if self.code_string == "":
            return None
        else:
            return "https://passport.baidu.com/cgi-bin/genimage?{code_string}".format(code_string=self.code_string)

    def login_with_verify_code(self, verify_code):
        self.__prepare_for_login()
        self.__login(verify_code)
        if self.auto_save_recode and self.has_logined():
            self.save()

    def __prepare_for_login(self):
        if not self.__has_prepared_for_login:
            # 1.获取cookies:BAIDUID
            self.__visit_home_page()
            # 2.获取token
            self.__get_api()
            # 3.获取cookies:UBI和PASSID
            self.__login_history()
            # 4.检查登陆选项
            self.__login_check()
            # 5.获取pubkey和key
            self.__get_public_key()
        self.__has_prepared_for_login = True

    def __visit_home_page(self):
        # 因为URL肯定不会变，所以直接写死
        url = "https://www.baidu.com/"

        # 其中请求报头User-Agent必须要有，否则不返回BAIDUID cookie
        # 无厘头bug:
        # 之前cookies名字都是从火狐浏览器里面直接复制的
        # “User-Agent”复制成了“User - Agent”
        # 于是一直没有返回BAIDUID……
        headers = default_conf.base_headers
        self.session.get(url=url, headers=headers)

    def __get_api(self):
        url = "https://passport.baidu.com/v2/api/?getapi&tpl=mn&apiver=v3&tt={tt}&class=login&gid={gid}&logintype=dialogLogin&callback=bd__cbs__tesnqc".format(
            tt=base.get_time_stamp(),
            gid=self.gid)
        temp_text = self.session.get(url).text
        # 由于百度返回的结果并不是标准的Json格式，所以无奈用正则进行匹配
        token = re.search('"token" : "([a-fA-F0-9]+?)"', temp_text).group(1)
        self.token = token

    def __login_history(self):
        headers = default_conf.base_headers
        url = "https://passport.baidu.com/v2/api/?loginhistory&token={token}&tpl=mn&apiver=v3&tt={tt}&gid={gid}&callback=bd__cbs__splnc1".format(
            token=self.token, tt=base.get_time_stamp(), gid=self.gid)
        self.session.get(url=url, headers=headers)
        # 因为未知原因,未能获得PASSID cookie

    def __login_check(self):
        # 有一个参数叫dv,但是不知道为什么没有这个参数也正常获得结果
        headers = default_conf.base_headers
        url = "https://passport.baidu.com/v2/api/?logincheck&token={token}&tpl=mn&apiver=v3&tt={tt}&sub_source=leadsetpwd&username={username}&isphone={is_phone}&dv={dv}&callback=bd__cbs__sehp6m".format(
            tt=base.get_time_stamp(),
            is_phone=False,
            token=self.token,
            username=self.user_name,
            dv=""
        )
        temp_text = self.session.get(url, headers=headers).text
        re_result = re.search('"codeString" : "(?P<code_string>.+?)".*?"vcodetype" : "(?P<v_code_type>.+?)"', temp_text)
        self.code_string = re_result.group("code_string")
        self.v_code_type = re_result.group("v_code_type")

    def __get_public_key(self):
        headers = default_conf.base_headers
        url = "https://passport.baidu.com/v2/getpublickey?token={token}&tpl=mn&apiver=v3&tt={tt}&gid={gid}&callback=bd__cbs__9t0drq".format(
            token=self.token, tt=base.get_time_stamp(), gid=self.gid)
        temp_text = self.session.get(url, headers=headers).text
        re_result = re.search('"pubkey":\'(?P<pubkey>[\s\S]+?)\',"key":\'(?P<key>.+?)\'', temp_text)
        self.key = re_result.group("key")
        self.pubkey = re_result.group("pubkey").replace("\\n", "\n")

        key = rsa.PublicKey.load_pkcs1_openssl_pem(self.pubkey)
        self.rsaed_password = base64.b64encode(rsa.encrypt(self.password.encode("utf-8"), key))

    def __login(self, verify_code):
        data = {
            'staticpage': "https://www.baidu.com/cache/user/html/v3Jump.html",
            'charset': "UTF-8",
            "token": self.token,
            "tpl": 'mn',
            "subpro": "",
            "apiver": "v3",
            "tt": base.get_time_stamp(),
            "codestring": self.code_string,
            "safeflg": "0",
            'u': "https://www.baidu.com/",
            "isPhone": "",
            "detect": "1",  # 不清楚什么意思
            'gid': self.gid,
            "quick_user": "0",
            "logintype": "dialogLogin",
            'logLoginType': "pc_loginDialog",
            'idc': "",
            'loginmerge': "true",
            'splogin': "rate",
            "username": self.user_name,
            "password": self.rsaed_password,
            "verifycode": verify_code,
            "mem_pass": "on",
            "rsakey": self.key,
            'crypttype': "12",
            'ppui_logintime': "10797",
            'countrycode': "",
            'dv': "",
            'callback': "parent.bd__pcbs__r6aj37"
        }
        headers = default_conf.base_headers
        headers["Host"] = "passport.baidu.com"
        url = "https://passport.baidu.com/v2/api/?login"
        self.session.post(url, data=data, headers=headers)

    def save(self):
        recode_file_dir = os.path.dirname(self.recode_path)
        if not os.path.exists(recode_file_dir):
            os.makedirs(recode_file_dir)

        with open(self.recode_path, 'w') as f:
            cookies = self.session.cookies.get_dict()
            json.dump(cookies, f)

    def try_load(self):
        if not os.path.exists(self.recode_path):
            return False
        else:
            with open(self.recode_path, 'r') as f:
                try:
                    cookies = json.load(f)
                    self.session.cookies.update(cookies)
                except json.JSONDecodeError:
                    return False
            return True

    def load(self):
        if not self.try_load():
            raise exceptions.RecodeNotExists(self.recode_path)

    def has_logined(self):
        url = "http://pan.baidu.com/disk/home"
        temp_req = self.session.get(url, headers=default_conf.base_headers)
        if temp_req.url == "http://pan.baidu.com/":
            return False
        else:
            return True

    def assert_logined(self):
        if not self.has_logined():
            raise exceptions.LoginError