from django.contrib import admin
from .models import Evenement, InscriptionEvenement


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_evenement', 'date_evenement', 'lieu', 'is_actif')
    list_filter = ('type_evenement', 'is_actif', 'date_evenement')
    search_fields = ('titre', 'description', 'lieu')
    list_editable = ('is_actif',)
    readonly_fields = ('slug', 'created_at', 'updated_at')


@admin.register(InscriptionEvenement)
class InscriptionEvenementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenoms', 'email', 'evenement', 'created_at')
    list_filter = ('evenement', 'created_at')
    search_fields = ('nom', 'prenoms', 'email', 'institution')
    readonly_fields = ('created_at',)
