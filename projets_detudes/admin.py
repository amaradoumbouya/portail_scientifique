from django.contrib import admin
from projets_detudes.models.chat import MessageChat


@admin.register(MessageChat)
class MessageChatAdmin(admin.ModelAdmin):
    list_display = ("projet", "auteur", "contenu_court", "lu", "created_at")
    list_filter = ("lu", "created_at")
    search_fields = ("contenu", "auteur__nom", "auteur__prenoms", "projet__titre")
    readonly_fields = ("created_at",)

    def contenu_court(self, obj):
        return obj.contenu[:60] + ("…" if len(obj.contenu) > 60 else "")

    contenu_court.short_description = "Message"
