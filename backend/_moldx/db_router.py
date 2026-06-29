"""
数据库路由配置 - molding-optima 重构版本（精简）

molding-optima 仅使用单 MySQL 数据库，无 PostgreSQL/MongoDB。
"""
from django.conf import settings


class MySQLRouter:
    """
    MySQL 数据库路由（单库版本）
    
    molding-optima 的所有业务 app 都使用 MySQL 单库：
    - identity: 用户、权限、认证
    - masterdata: 主数据（模具、注塑机、聚合物等）
    - process: 工艺参数
    - search: 全文搜索
    - filecenter: 文件管理
    - reporting: 报表与导出
    - bootstrap: 引导数据
    """
    mysql_apps = {
        'identity',
        'masterdata',
        'process',
        'search',
        'filecenter',
        'reporting',
        'bootstrap',
    }

    def db_for_read(self, model, **hints):
        app_label = model._meta.app_label
        if app_label in self.mysql_apps:
            return 'default'
        return None

    def db_for_write(self, model, **hints):
        app_label = model._meta.app_label
        if app_label in self.mysql_apps:
            return 'default'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        允许跨 app 关联（molding-optima 单库，所有 app 可关联）
        """
        app1 = obj1._meta.app_label
        app2 = obj2._meta.app_label
        
        # 单库：允许所有关联
        if app1 in self.mysql_apps and app2 in self.mysql_apps:
            return True
        
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.mysql_apps:
            return db == 'default'
        return None