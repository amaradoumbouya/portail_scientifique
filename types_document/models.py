from django.db import models
from django.utils.text import slugify
from django.contrib.auth import  get_user_model

User = get_user_model()

class TypeDocument(models.Model):
    libelle = models.CharField(max_length=100, verbose_name='Type Document')
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    def __str__(self):
        return self.libelle
    

    def save(self, *args, **kwargs):
        if not self.slug:
            last_pk = TypeDocument.objects.order_by('pk').last()
            self.slug = slugify(self.libelle) + '-' + str(last_pk.pk + 1) if last_pk else '1'
        super(TypeDocument, self).save(*args, **kwargs)

    class Meta:
        db_table = 'type_document'
        verbose_name = 'types_document'
        verbose_name_plural = 'types_document'

