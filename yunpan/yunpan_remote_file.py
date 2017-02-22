import os
import requests
from . import yunpan_list, exceptions
from .yunpan_download import Downloader
from .conf import default_conf


class RemoteFileSet(dict):
    def __init__(self):
        super().__init__()
        self.has_been_inited = False

    def __iter__(self):
        return super().values().__iter__()


class RemoteFile:
    unit_list = ["B", "KB", "MB", "GB", "TB"]

    def __init__(self,
                 remote_path: str,
                 session: requests.Session,
                 is_dir: bool = None,
                 size: int = None,
                 sub_files: RemoteFileSet = RemoteFileSet(),
                 file_name: str = None):
        self.remote_path = process_remote_path(remote_path)
        self.session = session
        self.__lister = yunpan_list.Lister(self.session)

        self.__is_dir = is_dir
        self.__size = size
        self.__sub_files = sub_files
        self.__file_name = file_name

    def download_to(self, local_path: str = default_conf.target_dir, overwrite: bool = False):
        if self.is_dir:
            local_path = os.path.join(local_path, self.file_name)
            if os.path.isfile(local_path):
                raise exceptions.LocalDirPathCanNotSameAsFile(local_path)
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            for file in self.sub_files:
                assert isinstance(file, RemoteFile)
                file.download_to(local_path, overwrite)
        else:
            if os.path.isdir(local_path):
                local_path = os.path.join(local_path, self.file_name)
            pardir = os.path.dirname(local_path)
            if not os.path.exists(pardir):
                os.makedirs(pardir)
            Downloader(self.remote_path, self.session).download_to(local_path, overwrite)

    def re_cache_infos(self):
        if self.remote_path == "/":
            self.__is_dir = True
            self.__size = 0
            self.__file_name = "/"
            return self

        pardir = os.path.dirname(self.remote_path)
        for info_dict in self.__lister.list(pardir):
            if info_dict["path"] == self.remote_path:
                self.__is_dir = info_dict["isdir"] == 1
                self.__size = info_dict['size']
                self.__file_name = info_dict["server_filename"]
        return self

    # 这段写的好丑……
    # TO beautiful
    def refresh_sub_files(self):
        self.__sub_files = RemoteFileSet()
        for info_dict in self.__lister.list(self.remote_path):
            assert isinstance(info_dict, dict)
            is_dir = info_dict["isdir"]
            remote_path = info_dict["path"]
            size = info_dict["size"]
            file_name = info_dict["server_filename"]
            sub_files = RemoteFileSet()
            if info_dict.get("empty", False):
                sub_files.has_been_inited = True

            the_file = RemoteFile(
                remote_path=remote_path,
                session=self.session,
                is_dir=is_dir,
                size=size,
                sub_files=sub_files,
                file_name=file_name
            )
            self.__sub_files[file_name] = the_file
        return self

    @property
    def size(self):
        if self.__size is None:
            self.re_cache_infos()
        return self.__size

    @property
    def is_dir(self):
        if self.__is_dir is None:
            self.re_cache_infos()
        return self.__is_dir

    @property
    def sub_files(self):
        if not self.is_dir:
            raise exceptions.RemotePathIsFile(self.remote_path)
        if not self.__sub_files.has_been_inited:
            self.refresh_sub_files()
        return self.__sub_files

    @property
    def file_name(self):
        if self.__file_name is None:
            self.refresh_sub_files()
        return self.__file_name

    def __str__(self):
        size_number = self.size
        size_unit_index = 0
        while size_number >= 100:
            size_unit_index += 1
            size_number = size_number // 1024
        return "{file_name} {size_number}{size_unit}".format(file_name=self.file_name, size_number=size_number,
                                                             size_unit=RemoteFile.unit_list[size_unit_index])


def process_remote_path(remote_path: str):
    if not remote_path.startswith("/"):
        raise exceptions.RemoteFileNotExist(remote_path)
    if remote_path.endswith("/"):
        remote_path = os.path.dirname(remote_path)
    return remote_path
