import os
import time
import math
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from . import exceptions, base
from .conf import default_conf


class Downloader:
    def __init__(self, remote_path: str, session: requests.Session):
        self.session = session
        self.remote_path = remote_path
        self.url = "http://c.pcs.baidu.com/rest/2.0/pcs/file?method=download&app_id=250528&path={path}".format(
            path=remote_path)

        response = self.session.head(self.url, headers=default_conf.base_headers)
        if response.status_code == 404:
            raise exceptions.RemoteFileNotExist(self.remote_path)
        response_headers = response.headers
        self.file_size = int(response_headers["x-bs-file-size"])
        self.etag = response_headers["Etag"]
        self.remote_md5 = response_headers["Content-MD5"]

        # math.ceil => 向上取整
        self.block_number = math.ceil(self.file_size / default_conf.download_block_size)

    def download_to(self, target_path: str, overwirte: bool):
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        temp_file_path = ".".join((target_path, self.remote_md5, "fktd"))
        download_info = DownloadInfo(target_path, self.remote_md5)

        # 直接使用"rb+"方式打开，如果文件不存在，会抛出一场
        # 直接使用“wb”或者"wb+"打开，会清空文件内容
        # 直接使用"ab+"方式打开，文件指针在文件末尾，且无法使用seek移动到前面
        if os.path.exists(temp_file_path):
            temp_file = open(temp_file_path, 'rb+')

            if os.path.exists(download_info.info_path):
                download_info.load()
                if download_info.block_size != default_conf.download_block_size or download_info.etag != self.etag:
                    raise exceptions.DownloadInfoUnMatched(download_info.info_path)
            else:
                download_info.set_info(self.etag, set([i for i in range(self.block_number)]),
                                       default_conf.download_block_size)
        else:
            temp_file = open(temp_file_path, 'wb')
            download_info.set_info(self.etag, set([i for i in range(self.block_number)]),
                                   default_conf.download_block_size)

        download_info.save()

        executor = ThreadPoolExecutor(default_conf.thread_pool_size)
        all_future = [executor.submit(self.__download_one_block, i) for i in download_info.to_download_blocks]
        while download_info.to_download_blocks:
            for the_future in [i for i in all_future if i.done()]:
                if the_future.exception() is None:
                    block_index, data = the_future.result()
                    if block_index in download_info.to_download_blocks:
                        temp_file.seek(default_conf.download_block_size * block_index)
                        temp_file.write(data)
                        temp_file.flush()
                        download_info.to_download_blocks.remove(block_index)
                        download_info.save()
                else:
                    raise the_future.exception()
        temp_file.close()
        executor.shutdown()

        if os.path.exists(target_path):
            if overwirte:
                os.remove(target_path)
            else:
                raise exceptions.TargetFileExists(target_path)
        os.rename(temp_file_path, target_path)
        os.remove(download_info.info_path)

    def __download_one_block(self, block_index):
        start = block_index * default_conf.download_block_size
        end = (block_index + 1) * default_conf.download_block_size - 1
        # 坑爹BUG
        # 开始没有用base.user_agent_headers的copy方法
        # 瞎几把引用，浅拷贝然后下文Range的时候相互影响出错了
        headers = default_conf.base_headers
        headers["Range"] = "bytes={start}-{end}".format(start=start,
                                                        end=end)
        temp_response = self.session.get(url=self.url, headers=headers)
        if temp_response.headers["Etag"] != self.etag:
            raise exceptions.RemoteFileHasBeenModified

        if temp_response.status_code == 206:
            return (block_index, temp_response.content)
        else:
            base.process_remote_error_message(temp_response.text, self.remote_path)


class DownloadInfo:
    def __init__(self, target_path: str, md5: str):
        self.target_path = target_path
        self.md5 = md5
        self.info_path = ".".join((target_path, md5, "fkinfo"))

    def load(self):
        with open(self.info_path) as f:
            info_dict = json.load(f)
            self.block_size = info_dict["block_size"]
            self.etag = info_dict['etag']
            self.to_download_blocks = set(info_dict["to_download_blocks"])

    def save(self):
        info_dict = {
            "block_size": self.block_size,
            "etag": self.etag,
            "to_download_blocks": list(self.to_download_blocks)
        }
        with open(self.info_path, 'w')as f:
            json.dump(info_dict, f)

    def set_info(self, etag: str, to_download_blocks: set, block_size: int):
        self.etag = etag
        self.to_download_blocks = to_download_blocks
        self.block_size = block_size
