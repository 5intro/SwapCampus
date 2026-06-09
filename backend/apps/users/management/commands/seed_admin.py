"""初始化管理员账号.

用法:
    python manage.py seed_admin

创建默认管理员账号：
- 用户名：administer
- 密码：123456
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "创建默认管理员账号（administer / 123456）"

    def handle(self, *args, **options):
        username = "administer"
        password = "123456"

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save(update_fields=["is_staff", "is_superuser", "password"])
            self.stdout.write(
                self.style.SUCCESS(f"管理员账号已更新：{username}（密码已重置为 {password}）")
            )
        else:
            User.objects.create_superuser(
                username=username,
                password=password,
                nickname="管理员",
                campus="校本部",
            )
            self.stdout.write(
                self.style.SUCCESS(f"管理员账号已创建：{username} / {password}")
            )
