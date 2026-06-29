from identity.models import User, Role, Company, Organization
from extensions.exceptions import BizException
from identity.exceptions import ERROR_USER_PERMISSION_DENIED


class UserPermission:
    """用户管理相关的权限判断"""

    def __init__(self, user: User):
        self.user = user

    def _can_operate_user(self, target: User, permission_code: str, type: int = 0) -> bool:
        """
        判断当前用户是否有权对目标用户执行操作。
        
        检查顺序：
        1. 平台超级管理员 → 全局放行
        2. 用户状态（删除/禁用）
        3. 公司状态（删除/禁用）
        4. 游客用户仅允许操作自己
        5. 同公司用户：租户管理员 或 拥有指定权限
        
        :param target: 目标用户
        :param permission_code: 所需权限码（如 "user.update"）
        :param type: 0表示只按照权限码判断，1表示默认可以操作自己
        :return: 是否允许操作
        """
        
        # # 1. 平台超级管理员，拥有所有权限
        # if self.user.is_superuser:
        #     return True
        
        # 2. 用户状态检查
        if self.user.is_deleted or not self.user.is_active:
            return False  # 用户处于删除/禁用状态，无操作权限
        
        company: Company = self.user.company
        # 3. 游客用户（无公司归属）只能操作自己
        if company is None:
            return self.user.id == target.id  # 防止越权操作他人
        
        # 4. 公司状态检查
        if not company.is_accessible():
            return False  # 公司处于删除/禁用状态
        
        # 5. 公司用户内部操作
        if company.id == target.company_id:
            if type == 1 and self.user.id == target.id:
                return True
            if self.user.has_permission(permission_code):  
                if target.is_superuser:
                    return self.user.is_superuser
                if target.is_tenant_admin:
                    return self.user.is_tenant_admin
                return True

        return False  # 禁止其它访问行为
    

    def _can_read_user_list(self, company_id: int, permission_code: str) -> bool:
        """判断操作用户是否可以查看用户列表"""
        # 1. 平台超级管理员，拥有所有权限
        # if self.user.is_superuser:
        #     return True
        
        # 2. 用户状态检查
        if self.user.is_deleted or not self.user.is_active:
            return False  # 用户处于删除/禁用状态，无操作权限
        
        company: Company = self.user.company
        # 3. 游客用户（无公司归属）只能操作自己
        if company is None:
            return self.user.id == target.id  # 防止越权操作他人
        
        # 4. 公司状态检查
        if not company.is_accessible():
            return False  # 公司处于删除/禁用状态
        
        # 5. 公司用户内部操作
        if company.id == company_id:
            # if self.user.is_tenant_admin:
            #     return True  # 租户管理员用户可以操作同公司下的用户
            return self.user.has_permission(permission_code)  # 租户普通用户需要有指定权限才能操作    

        return False  # 禁止其它访问行为
    
    def _can_create_user(self, company_id: int = None, permission_code: str = "add_user"):
        """判断操作用户是否可以创建用户"""
        if self.user.is_superuser: 
            return True  # 允许超级管理员创建用户
        if self.user.is_deleted or not self.user.is_active:
            return False  # 禁用用户不允许创建用户
        company: Company = self.user.company
        if company is None:
            return False  # 游客用户不允许创建用户
        if not company.is_accessible():
            return False  # 公司处于删除/禁用状态
        if company.id == company_id:
            # 同公司用户，需查看权限
            return self.user.has_permission(permission_code)
        return False  # 禁止其它行为
    
    def _check(self, condition: bool, message: str):
        """通用检查方法"""
        if not condition:
            raise BizException(ERROR_USER_PERMISSION_DENIED, message)

    def check_can_create_user(self, company_id: int = None):
        """判断操作用户是否可以创建用户"""
        self._check(self._can_create_user(company_id, "add_user"), "无权限创建用户")

    def can_read_user(self, target: User):
        """判断操作用户是否可以查看指定用户"""
        return self._can_operate_user(target, "review_user", type=1)
    
    def check_can_read_user(self, target: User):
        """判断操作用户是否可以查看指定用户"""
        self._check(self.can_read_user(target), "无权限查看该用户信息")

    def can_update_user(self, target: User):
        """判断操作用户是否可以更新指定用户"""
        return self._can_operate_user(target, "update_user", type=1)
    
    def check_can_update_user(self, target: User):
        """判断操作用户是否可以更新指定用户"""        
        self._check(self.can_update_user(target), "无权限更新该用户信息")

    def can_update_users_role(self, target: User):
        """判断操作用户是否可以更新指定用户的角色"""
        return self._can_operate_user(target, "update_role", type=0)
    
    def check_can_update_users_role(self, target: User):
        """判断操作用户是否可以更新指定用户的角色"""        
        self._check(self.can_update_users_role(target), "无权限更新该用户的角色")
        
    def can_update_users_organization(self, target: User):
        """判断操作用户是否可以更新指定用户的所属组织"""
        return self._can_operate_user(target, "update_department", type=0)
    
    def check_can_update_users_organization(self, target: User):
        """判断操作用户是否可以更新指定用户的所属组织"""        
        self._check(self.can_update_users_organization(target), "无权限更新该用户的所属部门")
         
    def can_update_users_acc_orgs(self, target: User):
        """判断操作用户是否可以更新指定用户的数据访问权限"""
        return self._can_operate_user(target, "update_department", type=0)
    
    def check_can_update_users_acc_orgs(self, target: User):
        """判断操作用户是否可以更新指定用户的数据访问权限"""        
        self._check(self.can_update_users_acc_orgs(target), "无权限更新该用户的数据访问权限")
       
    def can_enable_user(self, target: User):
        """判断操作用户是否可以启用或禁用指定用户"""
        return self._can_operate_user(target, "update_user", type=0)
    
    def check_can_enable_user(self, target: User):
        """判断操作用户是否可以启用或禁用指定用户"""        
        self._check(self.can_enable_user(target), "无权限启用或禁用该用户")
        
    def can_delete_user(self, target: User):
        """判断操作用户是否可以删除指定用户"""
        return self._can_operate_user(target, "delete_user")
    
    def check_can_delete_user(self, target: User):
        """判断操作用户是否可以删除指定用户"""
        self._check(self.can_delete_user(target), "无权限删除用户")

    def can_reset_user_password(self, target: User):
        """判断操作用户是否可以重置指定用户的密码"""
        return self._can_operate_user(target, "update_user", type=0)
    
    def check_can_reset_user_password(self, target: User):
        """判断操作用户是否可以重置指定用户的密码"""
        self._check(self.can_reset_user_password(target), "无权限重置该用户密码")


class RolePermission:
    """角色管理相关的权限判断"""
    
    def __init__(self, user: User):
        self.user = user
    
    def _check(self, condition: bool, message: str):
        if not condition:
            raise BizException(ERROR_USER_PERMISSION_DENIED, message)
    
    def _can_operate_role(self, target: Role, permission_code: str):
        """
        判断当前用户是否有权操作目标角色。
        
        允许的情况：
        1. 平台超级管理员
        2. 当前用户是目标公司的租户管理员，且用户和公司均处于活跃状态
        
        :param target: 目标角色
        :return: 是否允许操作
        """
        # if self.user.is_superuser:
        #     return True  # 超级管理员用户，可以操作所有角色信息
        if self.user.is_deleted or not self.user.is_active:
            return False  # 禁用用户不允许操作角色信息
        user_company: Company = self.user.company
        if user_company is None:
            return False  # 游客用户不允许操作角色信息
        if not user_company.is_accessible():
            return False  # 公司处于删除/禁用状态
        if user_company.id == target.company_id:
            return self.user.has_permission(permission_code)
        return False
    
    def _can_create_role(self, company_id: int, permission_code: str = "add_role"):
        """检查当前用户是否可以创建指定公司的角色"""
        if self.user.is_superuser:
            return True  # 超级管理员用户，可以操作所有角色信息
        if self.user.is_deleted or not self.user.is_active:
            return False  # 禁用用户不允许操作角色信息
        user_company: Company = self.user.company
        if user_company is None:
            return False  # 游客用户不允许操作角色信息
        if not user_company.is_accessible():
            return False  # 公司处于删除/禁用状态
        if user_company.id == company_id:
            return self.user.has_permission(permission_code)
        return False  # 禁止其它行为
    
    def _can_get_role(self, company_id: int, permission_code: str = "review_role"):
        """检查当前用户是否可以读取指定公司的角色"""
        if self.user.is_deleted or not self.user.is_active:
            return False  # 禁用用户不允许操作角色信息
        user_company: Company = self.user.company
        if user_company is None:
            return False  # 游客用户不允许操作角色信息
        if not user_company.is_accessible():
            return False  # 公司处于删除/禁用状态
        if user_company.id == company_id:
            return self.user.has_permission(permission_code)
        return False  # 禁止其它行为
    
    def check_can_create_role(self, company_id: int):
        """判断当前用户是否可以创建指定公司的角色"""
        self._check(self._can_create_role(company_id, "add_role"), "无权限创建该公司角色")
        
    def check_can_manage_role(self, target: Role):
        """判断操作用户是否可以管理指定角色"""
        self._check(self._can_operate_role(target, "update_role"), "无权限管理该角色")
           
    def check_can_enable_role(self, target: Role):
        """判断操作用户是否可以启用或禁用指定角色"""
        self._check(self._can_operate_role(target, "update_role"), "无权限启用或禁用该角色")
       
    def check_can_delete_role(self, target: Role):
        """判断当前用户是否可以删除指定角色"""
        self._check(self._can_operate_role(target, "delete_role"), "无权限删除该角色")
              
    def check_can_get_role_permission_tree(self, company_id: int):
        """判断操作用户是否可以获取公司的角色权限树"""
        self._check(self._can_get_role(company_id, "review_role"), "无权限获取角色权限树")
      
class CompanyPermission:
    """公司管理相关的权限判断"""
    
    def __init__(self, user: User):
        self.user = user
        
    def _can_operate_company(self, target: Company):
        """
        判断当前用户是否有权操作目标公司。
        
        允许的情况：
        1. 平台超级管理员
        2. 当前用户是目标公司的租户管理员，且用户和公司均处于活跃状态
        
        :param target: 目标公司
        :return: 是否允许操作
        """
        if self.user.is_superuser:
            return True  # 超级管理员用户，可以操作所有公司
        # if self.user.is_deleted or not self.user.is_active:
        #     return False  # 禁用用户不允许操作公司信息
        # user_company: Company = self.user.company
        # if user_company is None:
        #     return False  # 游客用户不允许操作公司信息
        # if not user_company.is_accessible():
        #     return False  # 公司处于删除/禁用状态
        # if user_company.id == target.id and self.user.is_tenant_admin:
        #     return True  # 当前用户是指定公司的管理员用户
        return False  # 禁止其它行为
    
    def check_can_create_company(self):
        """判断当前用户是否允许创建公司（只有超级管理员允许创建公司）"""
        if not self.user.is_superuser:
            raise BizException(ERROR_USER_PERMISSION_DENIED, "用户无权限创建公司")

    def check_can_manage_company(self, target: Company):
        """判断当前用户是否允许管理指定公司"""
        if not self._can_operate_company(target):
            raise BizException(ERROR_USER_PERMISSION_DENIED, "用户无权限管理公司信息")


class OrganizationPermission:
    """组织管理相关的权限判断"""
    
    def __init__(self, user: User):
        self.user = user
        
    def _check(self, condition: bool, message: str):
        if not condition:
            raise BizException(ERROR_USER_PERMISSION_DENIED, message)
    
    def _can_operate_organization(self, target: Organization, permission_code: str):
        """
        判断当前用户是否有权操作目标角色。
        
        允许的情况：
        1. 平台超级管理员
        2. 当前用户是目标公司的租户管理员，且用户和公司均处于活跃状态
        
        :param target: 目标组织
        :return: 是否允许操作
        """
        # if self.user.is_superuser:
        #     return True  # 超级管理员用户，可以操作所有公司
        if self.user.is_deleted or not self.user.is_active:
            return False  # 禁用用户不允许操作公司信息
        user_company: Company = self.user.company
        if user_company is None:
            return False  # 游客用户不允许操作角色信息
        if not user_company.is_accessible():
            return False  # 公司处于删除/禁用状态
        if user_company.id == target.company_id:
            # if self.user.is_tenant_admin:
            #     return True  # 当前用户是指定公司的管理员用户
            if self.user.has_permission(permission_code):
                accessible_orgs = self.user.get_accessible_organizations()
                for accessible_org in accessible_orgs:
                    if accessible_org.id == target.id:
                        return True
        return False  # 禁止其它行为
    
    def _can_create_organization(self, company_id: int, permission_code: str = "add_department"):
        """检查当前用户是否可以创建指定公司的组织"""
        if self.user.is_superuser:
            return True
        if self.user.is_deleted or not self.user.is_active:
            return False  # 禁用用户不允许操作角色信息
        user_company: Company = self.user.company
        if user_company is None:
            return False  # 游客用户不允许操作角色信息
        if not user_company.is_accessible():
            return False  # 公司处于删除/禁用状态
        if user_company.id == company_id:
            # if self.user.is_tenant_admin:
            #     return True  # 当前用户是指定公司的管理员用户
            return self.user.has_permission("add_department")
        return False  # 禁止其它行为
    
    def _can_get_organizaiton_tree(self, company_id: int, permission_code: str = "review_department"):
        """判断当前用户是否可以获取指定公司的组织树"""
        # if self.user.is_superuser:
        #     return True  # 2025-12-24更新，超级管理员权限改为不可读
        if self.user.is_deleted or not self.user.is_active:
            return False  # 禁用用户不允许操作角色信息
        user_company: Company = self.user.company
        if user_company is None:
            return False  # 游客用户不允许操作角色信息
        if not user_company.is_accessible():
            return False  # 公司处于删除/禁用状态
        if user_company.id == company_id:
            return self.user.has_permission(permission_code)
        return False  # 禁止其它行为
    
    def check_can_create_organization(self, company_id: int):
        """判断当前用户是否可以创建指定公司的组织"""
        self._check(self._can_create_organization(company_id,"add_department"), "用户无权限创建该公司组织")
    
    def check_can_delete_organization(self, target: Organization):
        """判断当前用户是否可以删除指定公司的组织"""
        self._check(self._can_operate_organization(target,"delete_department"), "用户无此组织删除权限")
    
    def check_can_get_organizaiton_tree(self, company_id: int):
        """判断当前用户是否可以获取指定公司的组织树（与创建权限相同）"""
        self._check(self._can_get_organizaiton_tree(company_id,"review_department"), "用户无权限获取该公司组织树")
        return True

    def check_can_manage_organization(self, target: Organization):
        """判断操作用户是否可以管理指定组织"""
        self._check(self._can_operate_organization(target,"update_department"), "用户无此组织管理权限")
