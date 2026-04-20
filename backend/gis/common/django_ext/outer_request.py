import requests


def request_post(url, param, headers, flag=0):

    try:
        if flag and flag == 1:
            ret = requests.post(url, json=param, headers=headers)
        else:
            ret = requests.post(url, data=param, headers=headers)
        if ret.status_code == 200:
            return ret.text
        elif ret == "":
            return ret

    except Exception as e:
        print(e)
        print("网络连接出现问题, 正在尝试再次请求: ")


def request_get(url, param=None, **kwargs):
    try:
        ret = requests.get(url)
        if ret.status_code == 200:
            return ret.text
        elif ret == "":
            return ret

    except Exception as e:
        print(e)
        print("网络连接出现问题, 正在尝试再次请求: ")
