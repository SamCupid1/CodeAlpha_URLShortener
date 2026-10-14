from django.contrib import admin

from .models import ClickEvent, ShortURL


class ClickEventInline(admin.TabularInline):
    model = ClickEvent
    extra = 0
    can_delete = False
    fields = ("clicked_at",)
    readonly_fields = ("clicked_at",)
    ordering = ("-clicked_at",)


@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = ("short_code", "original_url", "user", "clicks", "created_at")
    list_filter = ("created_at",)
    search_fields = ("short_code", "original_url", "user__username", "user__email")
    readonly_fields = ("short_code", "created_at", "clicks")
    date_hierarchy = "created_at"
    inlines = (ClickEventInline,)
    list_select_related = ("user",)


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ("short_url", "clicked_at")
    list_filter = ("clicked_at",)
    search_fields = ("short_url__short_code", "short_url__original_url")
    readonly_fields = ("short_url", "clicked_at")
    date_hierarchy = "clicked_at"
    list_select_related = ("short_url",)
