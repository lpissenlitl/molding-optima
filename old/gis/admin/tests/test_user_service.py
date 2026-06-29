import traceback
from django.test import TestCase

from gis.admin.exceptions import (
    ERROR_USER_NOT_EXISTS,
    ERROR_USER_DISABLED,
    ERROR_USER_PASSWORD_INCORRECT,
    ERROR_USER_PASSWORD_DIFFERENT,
)
from gis.admin.models import User
from gis.admin.services.admin_service import (
    get_or_create_user,
    delete_user,
    get_user_by_id,
    disable_user,
    enable_user,
    verify_password,
    reset_password,
)
from gis.common.exceptions import BizException


class UserRoleTestCase(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        pass

    def test_create_user(self):
        user = get_or_create_user(1, "test02", "thishaF1rdp@wdd", role_ids=[1, 2])
        self.assertTrue(user["id"] > 0)
        roles = list(User.objects.get(pk=user["id"]).roles.all())
        self.assertEqual(len(roles), 2)
        self.assertEqual(sorted([e.id for e in roles]), [1, 2])

    def test_delete_user(self):
        delete_user(1)
        try:
            get_user_by_id(1)
        except BizException as e:
            self.assertEqual(e.error_code, ERROR_USER_NOT_EXISTS)

    def test_disable_user(self):
        disable_user(1)
        try:
            get_user_by_id(1)
        except BizException as e:
            self.assertEqual(e.error_code, ERROR_USER_DISABLED)

    def test_enable_user(self):
        enable_user(2)
        user = get_user_by_id(2)
        self.assertEqual(user["enable"], True)

    def test_verify_password_fail_for_pwd_incorrect(self):
        try:
            verify_password(1, "platform001", "pwddfdf")
        except BizException as e:
            self.assertEqual(e.error_code, ERROR_USER_PASSWORD_INCORRECT)

    def test_verify_password_fail_for_name_not_existed(self):
        try:
            verify_password(1, "test02", "pwddfdf")
        except BizException as e:
            self.assertEqual(e.error_code, ERROR_USER_NOT_EXISTS)

    def test_verify_password_success(self):
        user = verify_password(1, "platform001", "123456")
        self.assertEqual(user["id"], 1)

    def test_reset_password_fail(self):
        try:
            reset_password(1, "23434df#fFA")
        except BizException as e:
            self.assertEqual(e.error_code.code, ERROR_USER_PASSWORD_DIFFERENT)

    def test_reset_password(self):
        try:
            reset_password(1, "sdfKf98#2")
        except BizException:
            traceback.print_exc()
            self.fail("reset password fail")
