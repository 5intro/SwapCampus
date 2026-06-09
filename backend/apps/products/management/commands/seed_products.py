# -*- coding: utf-8 -*-
"""
初始化分类和标签数据，适合校园闲置交易场景。
Usage: python manage.py seed_products
"""
from django.core.management.base import BaseCommand
from apps.products.models import Category, Tag


CATEGORIES = [
    # (name, icon, sort_order, children)
    ("数码电子", "📱", 1, [
        ("手机通讯", "📞", 1),
        ("电脑平板", "💻", 2),
        ("影音娱乐", "🎧", 3),
        ("数码配件", "🔌", 4),
    ]),
    ("书籍教材", "📚", 2, [
        ("教材教辅", "📖", 1),
        ("课外读物", "📘", 2),
        ("考研考公", "📝", 3),
    ]),
    ("生活用品", "🏠", 3, [
        ("日用品", "🧴", 1),
        ("收纳整理", "📦", 2),
        ("装饰摆件", "🖼️", 3),
    ]),
    ("服饰鞋包", "👗", 4, [
        ("男装", "👔", 1),
        ("女装", "👚", 2),
        ("鞋子", "👟", 3),
        ("箱包", "🎒", 4),
    ]),
    ("运动户外", "⚽", 5, [
        ("运动器材", "🏓", 1),
        ("户外装备", "⛺", 2),
        ("健身用品", "💪", 3),
    ]),
    ("宿舍神器", "🏫", 6, [
        ("小家电", "🔌", 1),
        ("床品", "🛏️", 2),
        ("台灯照明", "💡", 3),
    ]),
    ("其他", "📋", 99, []),
]

TAGS = [
    "可议价", "急出", "仅面交", "包送货", "赠品",
]


class Command(BaseCommand):
    help = "Seed categories and tags for campus marketplace"

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories and tags...")
        self._create_categories()
        self._create_tags()
        self.stdout.write("Done: categories=%d, tags=%d" % (
            Category.objects.count(), Tag.objects.count()
        ))

    def _create_categories(self):
        for name, icon, sort_order, children in CATEGORIES:
            parent, created = Category.objects.get_or_create(
                name=name,
                defaults={"icon": icon, "sort_order": sort_order},
            )
            self.stdout.write("  %s %s %s" % ("+" if created else "=", icon, name))
            for child_name, child_icon, child_order in children:
                _, created = Category.objects.get_or_create(
                    name=child_name,
                    parent=parent,
                    defaults={"icon": child_icon, "sort_order": child_order},
                )
                self.stdout.write("     %s %s %s" % ("+" if created else "=", child_icon, child_name))

    def _create_tags(self):
        for tag_name in TAGS:
            _, created = Tag.objects.get_or_create(name=tag_name)
            self.stdout.write("  %s #%s" % ("+" if created else "=", tag_name))
