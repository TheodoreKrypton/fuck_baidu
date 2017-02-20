import os
from . import yunpan_recode, exceptions
from .conf import default_conf
from .yunpan_download import RemoteFile


class YunPan:
    def __init__(self,
                 user_name: str,
                 password: str,
                 recode_path: str = default_conf.recode_path,
                 auto_load_recode: bool = False,
                 auto_save_recode: bool = False):
        self.log_recode = yunpan_recode.LogRecode(
            user_name=user_name,
            password=password,
            recode_path=default_conf.recode_path,
            auto_save_recode=auto_save_recode,
            auto_load_recode=auto_load_recode
        )
        self.__session = self.log_recode.session

    # 登陆部分方法

    # 有用户值守的登陆，即由用户手动输入验证码
    def login_with_user(self):
        return self.log_recode.login_with_user()

    def save_login_recode(self):
        return self.log_recode.save()

    def load_login_recode(self):
        return self.log_recode.load()

    @property
    def has_logined(self):
        return self.log_recode.has_logined()

    def assert_logined(self):
        return self.log_recode.assert_logined()

    # 下载部分方法

    def download_one_file(self, remote_path: str, local_path: str = None):
        self.log_recode.assert_logined()
        if "/" not in remote_path or not remote_path.startswith("/"):
            raise exceptions.RemoteFileNotExistException(remote_path)
        if remote_path.endswith("/"):
            raise exceptions.CanNotDownloadException
        if local_path is None:
            local_path = os.path.join(default_conf.target_dir, remote_path.split("/")[-1])

        the_remote_file = RemoteFile(remote_path, self.__session)
        the_remote_file.download_to(local_path)
