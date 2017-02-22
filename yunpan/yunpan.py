import os
from . import yunpan_recode, exceptions, yunpan_remote_file
from .conf import default_conf
from .yunpan_download import Downloader


class YunPan:
    def __init__(self,
                 user_name: str,
                 password: str,
                 auto_load_recode: bool = False,
                 auto_save_recode: bool = False,
                 recode_path: str = default_conf.recode_path):
        self.login_recoder = yunpan_recode.LoginRecoder(
            user_name=user_name,
            password=password,
            recode_path=default_conf.recode_path,
            auto_save_recode=auto_save_recode,
            auto_load_recode=auto_load_recode
        )
        self.session = self.login_recoder.session

    # 登陆部分方法

    # 有用户值守的登陆，即由用户手动输入验证码
    def login_with_user(self):
        return self.login_recoder.login_with_user()

    def save_login_recode(self):
        return self.login_recoder.save()

    def load_login_recode(self):
        return self.login_recoder.load()

    @property
    def has_logined(self):
        return self.login_recoder.has_logined()

    def assert_logined(self):
        return self.login_recoder.assert_logined()

    # 获取远程文件对象
    def get_file(self, remote_path: str = "/"):
        self.login_recoder.assert_logined()
        return yunpan_remote_file.RemoteFile(remote_path, self.session)
