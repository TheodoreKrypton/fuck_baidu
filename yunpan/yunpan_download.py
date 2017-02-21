import os
import time
import math
import requests
import queue
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
        print(self.url)
        temp_file_path = ".".join((target_path, self.remote_md5, "fktd"))
        temp_file = open(temp_file_path, 'wb')
        self.index_and_data_queue = queue.Queue()

        executor = ThreadPoolExecutor(default_conf.thread_pool_size)
        all_future = [executor.submit(self.__download_one_block, i) for i in range(self.block_number)]
        has_download_blocks = set()
        while len(has_download_blocks) < self.block_number:
            for (block_index, the_future) in enumerate(all_future):
                if block_index not in has_download_blocks and the_future.done():
                    has_download_blocks.add(block_index)
                    if the_future.exception():
                        raise the_future.exception()
                    else:
                        block_index, data = the_future.result()
                        temp_file.seek(block_index * default_conf.download_block_size)
                        temp_file.write(data)
                        temp_file.flush()
            time.sleep(default_conf.poll_interval)

        temp_file.close()
        executor.shutdown()
        if os.path.exists(target_path):
            if overwirte:
                os.remove(target_path)
            else:
                raise exceptions.TargetFileExists(target_path)
        os.rename(temp_file_path, target_path)

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
