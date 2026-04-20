import json

import requests

HOST = "http://47.114.4.24:8200/admin/"
SESSION = requests.session()

headers = {
    "Content-Type": "application/json",
    "X-AUTH-TOKEN": "e2a79e7a-1763-4e66-98e3-7729f251e2f5",
}


def register(name, password):
    data = json.dumps({"name": name, "password": password})
    resp = SESSION.post(HOST + "register/", headers=headers, data=data)
    print_resp(resp)


def login(name, password):
    data = json.dumps({"name": name, "password": password})
    resp = SESSION.post(HOST + "login/", headers=headers, data=data)
    print_resp(resp)


def logout():
    resp = SESSION.post(HOST + "logout/", headers=headers)
    print_resp(resp)


def get_user_info():
    resp = SESSION.get(HOST + "user_info/", headers=headers)
    print_resp(resp)


def list_users(page_no, page_size):
    data = json.dumps({"page_no": page_no, "page_size": page_size})
    resp = SESSION.get(HOST + "users/", headers=headers, data=data)
    print_resp(resp)


def add_user(name, password, role_ids):
    data = json.dumps({"name": name, "password": password, "role_ids": role_ids})
    resp = SESSION.post(HOST + "users/", headers=headers, data=data)
    print_resp(resp)


def get_user(user_id):
    resp = SESSION.get(HOST + "users/{}/".format(user_id), headers=headers)
    print_resp(resp)


def update_user(user_id, role_ids):
    data = json.dumps({"role_ids": role_ids})
    resp = SESSION.put(HOST + "users/{}/".format(user_id), headers=headers, data=data)
    print_resp(resp)


def delete_user(user_id):
    resp = SESSION.delete(HOST + "users/{}/".format(user_id), headers=headers)
    print_resp(resp)


def list_groups(page_no, page_size):
    data = json.dumps({"page_no": page_no, "page_size": page_size})
    resp = SESSION.get(HOST + "roles/", headers=headers, data=data)
    print_resp(resp)


def add_role(name, description, permissions):
    data = json.dumps({"name": name, "description": description, "permissions": permissions})
    resp = SESSION.post(HOST + "roles/", headers=headers, data=data)
    print_resp(resp)


def get_total_permission_tree():
    resp = SESSION.get(HOST + "permissions/", headers=headers)
    print_resp(resp)


def print_resp(resp):
    print(resp.status_code, "\n", resp.text)


if __name__ == "__main__":
    # login("admin", "123456")
    # add_user('platform005', '123aF456', [1, 2])
    # get_user(7)
    get_user_info()
    # update_user(2, [4])
    # delete_user(7)
    # list_groups(1, 10)
    # add_role('role_5', 'desc4', [{'permission_id': 6}, {'permission_id': 54}])
    # get_total_permission_tree()
