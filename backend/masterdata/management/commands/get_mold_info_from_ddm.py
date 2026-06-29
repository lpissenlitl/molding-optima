from django.core.management.base import BaseCommand
from masterdata.services.ddm_service import sync_molds_from_ddm


class Command(BaseCommand):
    help = "从DDM中获取模具信息"

    def handle(self, *args, **options):
        result = sync_molds_from_ddm()
        self.stdout.write(self.style.SUCCESS(
            f"✅ DDM数据同步完成: 更新{result['updated']}条, 跳过{result['skipped']}条, 错误{result['errors']}条"
        ))

