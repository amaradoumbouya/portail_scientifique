from django.contrib import admin
from .models import Actualite


@admin.register(Actualite)
class ActualiteAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_publication', 'is_actif', 'created_at')
    list_filter = ('is_actif', 'date_publication')
    search_fields = ('titre', 'resume', 'contenu')
    list_editable = ('is_actif',)
    readonly_fields = ('slug', 'created_at', 'updated_at')
