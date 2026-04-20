from django.test import TestCase

from gis.admin.models import RolePermissionRel, Role
from gis.admin.services import admin_service
from gis.admin.services.admin_service import (
    delete_role,
    update_role,
    get_role,
    get_user_all_permission_codes,
    get_user_permission_include_fields,
)


class RolePermissionTestCase(TestCase):
    fixtures = ["test_role"]

    def test_add_role(self):
        role = admin_service.add_role(1, "role4", None)
        self.assertTrue(role["id"] > 0)

    def test_add_role_with_permissions(self):
        permissions = list()
        permissions.append({"permission_id": 3, "include_fields": ["a", "b"]})
        permissions.append({"permission_id": 52})
        role = admin_service.add_role(1, "role4", permissions=permissions)
        self.assertTrue(role["id"] > 0)

        rps = list(RolePermissionRel.objects.filter(role_id=role["id"]).all())
        self.assertEqual(len(rps), 2)
        for each in rps:
            if each.permission_id == 3:
                self.assertEqual(each.include_fields, ["a", "b"])
            elif each.permission_id == 52:
                self.assertFalse(each.include_fields)
            else:
                self.fail("bind permissions fail")

    def test_delete_role(self):
        self.assertTrue(delete_role(1))
        self.assertFalse(RolePermissionRel.objects.filter(role_id=1).exists())

    def test_update_role(self):
        permissions = list()
        permissions.append({"permission_id": 51})
        update_role(1, "role_1_u", "desc1", permissions)

        role = Role.objects.get(pk=1)
        self.assertEqual(role.name, "role_1_u")
        self.assertEqual(role.description, "desc1")

        rps = list(RolePermissionRel.objects.filter(role=role).all())
        self.assertEqual(len(rps), 1)
        for each in rps:
            if each.permission_id == 51:
                self.assertFalse(each.include_fields)
            else:
                self.fail("bind permissions fail")

    def test_get_role(self):
        role = get_role(1, with_permissions=True)
        self.assertEqual(role["id"], 1)
        permissions = role["permissions"]
        self.assertEqual(len(permissions), 2)

    def test_get_total_permission_tree(self):
        tree = admin_service.get_total_permission_tree()
        self._print_tree(tree)
        self.assertEqual(len(tree), 1)
        self.assertEqual(len(tree[0]["children"]), 2)
        self.assertEqual(len(tree[0]["children"][0]["children"]), 2)
        self.assertEqual(len(tree[0]["children"][1]["children"]), 2)

    def _print_tree(self, tree):
        print("\n================ Permission Tree =========")

        def _f(node, level):
            print(2 * level * "-", node["id"])
            if "children" in node:
                for e in node["children"]:
                    _f(e, level + 1)

        for e in tree:
            _f(e, 1)

    def test_get_user_all_permission_codes(self):
        permissions = get_user_all_permission_codes(1)
        self.assertEqual(
            permissions,
            {
                "admin_group",
                "admin_user_group",
                "admin_user_add",
                "admin_role_group",
                "admin_role_update",
            },
        )

    def test_get_user_permission_include_fields(self):
        fields = get_user_permission_include_fields(1, "admin_user_add")
        self.assertEqual(fields, set({"a", "b"}))

    def test_get_user_permission_include_fields_1(self):
        fields = get_user_permission_include_fields(1, "admin_role_update")
        self.assertTrue(len(fields) == 0)
