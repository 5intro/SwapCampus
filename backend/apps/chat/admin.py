"""站内通讯 Django Admin 配置."""

from django.contrib import admin

from apps.chat.models import Conversation, Message


class MessageInline(admin.TabularInline):
    """消息内联（在会话详情页展示）."""

    model = Message
    fields = ["sender", "content", "is_read", "created_at"]
    readonly_fields = ["sender", "content", "is_read", "created_at"]
    extra = 0
    can_delete = False
    max_num = 50


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """会话 Admin."""

    list_display = ["id", "title", "product", "created_at", "updated_at"]
    search_fields = ["title", "participants__username", "participants__nickname"]
    filter_horizontal = ["participants"]
    inlines = [MessageInline]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """消息 Admin."""

    list_display = ["id", "conversation", "sender", "content_preview", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["content", "sender__username", "sender__nickname"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["conversation", "sender"]

    @admin.display(description="内容预览")
    def content_preview(self, obj):
        return obj.content[:80]
