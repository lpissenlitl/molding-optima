## 项目相关配置
* python 3.8.3
* django 3.0.7

## 代码规范
```bash
pip install pre-commit
pre-commit install --allow-missing-config
```

* 详细依赖见文件 requirements.txt
pip install -r requirements.txt

## 一键部署
python deploy/fabfile.py

**note：部署需要安装依赖**
pip install -r deploy/requirements.txt

## 项目简要架构
* gis组件
通用组件，包括登陆权限系统
初始化admin相关的表(数据库里面没有admin开头前缀表)，可以使用如下命令
```bash
python manage.py makemigrations admin
python manage.py make
```

* fixtures
初始化admin权限相关
当数据库中没有任何权限相关数据的时候，可以用如下命令初始化权限相关数据
```bash
python manage.py loaddata gis/admin/fixtures/init_data.yaml
```

## 支持长链接 websocket
* 使用channels
https://channels.readthedocs.io/en/latest/installation.html

## 本地测试
在项目的目录文件下，后端使用如下命令，使本地程序在8200端口上运行
python manage.py runserver 127.0.0.1:8200

或者命令
daphne base.asgi:application -b 0.0.0.0 -p 8200


为了定期向前端发布长链接数据，需要另外开一个终端，运行如下命令
python manage.py sensor_publish
该命令会运行 hsmolding/management/commands/sensor_publish.py 脚本，该脚本中，会向组名为 sensor_11 的长链接订阅组推送数据

前端的本地长链接demo地址是
http://127.0.0.1:8200/hsmolding/lobby/

## 线上环境相关
* 使用python环境管理工具，pyenv + virtualenv
[pyenv](https://github.com/pyenv/pyenv) - Simple Python version management.
[pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) - A tool to create isolated Python environments.

* 使用[nginx](https://www.nginx.com/)做web服务器

* 使用[supervisor](http://supervisord.org/)做为守护进程

* 使用uwsgi服务做为django和nginx通信服务

* test
