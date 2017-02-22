# coding:utf-8

import json
import random
import time

import exceptions


# 从百度的JS里面看到的，用Python重新实现了一下
def build_gid():
    template = list("xxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx")
    for (index, the_char) in enumerate(template):
        rand_num = random.randint(0, 15)
        if the_char == 'x':
            temp_char = "%x" % rand_num
            template[index] = temp_char
        if the_char == 'y':
            rand_num = 3 & rand_num | 8
            temp_char = "%x" % rand_num
            template[index] = temp_char
    return ''.join(template).upper()


def get_time_stamp():
    return str(int(time.time() * 1000))


def process_remote_error_message(error_text, remote_path):
    try:
        error_info = json.loads(error_text)
        error_code = error_info['error_code']
        error_message = error_info['error_msg']

        if error_code == 31066:
            raise exceptions.RemoteFileNotExist(remote_path)
        elif error_code == 31074:
            raise exceptions.CanNotDownload
        else:
            raise exceptions.UnExceptedRemoteReturnErrorMessage(error_text)

    except (KeyError, json.JSONDecodeError) as e:
        exceptions.UnExceptedRemoteReturnErrorMessage(error_text)
