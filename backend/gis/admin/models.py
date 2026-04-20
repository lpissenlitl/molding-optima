from django.db import models
from gis.common.django_ext.models import BaseModel, ListField, ExtraBaseModel


class Company(ExtraBaseModel):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=45)
    description = models.CharField(max_length=255, default="", null=True)
    admin_id = models.IntegerField(null=True)
    level = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    deleted = models.SmallIntegerField(default=False)
    parent_id = models.IntegerField(null=True)  # 父节点名称
    order_num = models.IntegerField(null=True)  # 显示顺序

    class Meta:
        db_table = "company"


class Group(ExtraBaseModel):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    parent_id = models.IntegerField(null=True)
    sort_index = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    deleted = models.SmallIntegerField(default=False)

    class Meta:
        db_table = "group"
        ordering = ["sort_index"]


class Department(ExtraBaseModel):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    parent_id = models.IntegerField(null=True)  # 父部门名称
    order_num = models.IntegerField(null=True)  # 显示顺序
    name = models.CharField(max_length=45)
    abbreviation = models.CharField(max_length=45, default="")
    attribute = models.CharField(max_length=45, default="")
    serial_number = models.CharField(max_length=45, default="")
    header = models.CharField(max_length=45, default="")
    description = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    deleted = models.SmallIntegerField(default=False)

    class Meta:
        db_table = "department"


class User(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    group_id = models.IntegerField()
    name = models.CharField(max_length=50)
    password = models.CharField(max_length=100, null=True)
    engineer = models.CharField(max_length=45)  # 工程师的名字
    email = models.CharField(max_length=45)
    phone = models.CharField(max_length=11)
    app_id = models.CharField(max_length=45)
    is_super = models.BooleanField(default=False)
    enable = models.BooleanField(default=True)
    login_count = models.IntegerField(default=0)  # 登陆次数
    last_login_at = models.DateTimeField(null=True)  # 最后登录时间
    roles = models.ManyToManyField("Role")
    groups = models.ManyToManyField("Group")
    deleted = models.SmallIntegerField(default=False)


class Token(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, db_index=True)
    ua = models.CharField(max_length=512, null=True)


class Role(BaseModel):
    company_id = models.IntegerField()
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, null=True)
    permissions = models.ManyToManyField("Permission", through="RolePermissionRel")
    deleted = models.SmallIntegerField(default=False)


class Permission(BaseModel):
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50, unique=True)
    sort_index = models.IntegerField(default=1)
    description = models.CharField(max_length=200, null=True)
    full_path = models.CharField(max_length=100)
    is_leaf = models.BooleanField(default=False)
    fields = ListField(max_length=1000, null=True)
    level = models.IntegerField(null=True)
    deleted = models.SmallIntegerField(default=False)

    class Meta:
        ordering = ["sort_index"]


class RolePermissionRel(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    include_fields = ListField(max_length=1000, null=True)

    class Meta:
        unique_together = ("role", "permission")


# class UserGroupRel(ExtraBaseModel):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     group = models.ForeignKey(Group, on_delete=models.CASCADE)

#     class Meta:
#         db_table = "admin_user_groupss"


class Record(BaseModel):
    resource = models.CharField(max_length=100)
    resource_id = models.IntegerField()
    action = models.SmallIntegerField()
    content = models.TextField()
    operator = models.IntegerField()
    ip = models.CharField(max_length=100)
    user_agent = models.CharField(max_length=100)


# class UserGroupRel(BaseModel):
#     user_id = models.IntegerField()
#     group_id = models.IntegerField()

    # class Meta:
    #     db_table = "admin_user_groups"
    #     unique_together = ("user_id", "group_id")


        