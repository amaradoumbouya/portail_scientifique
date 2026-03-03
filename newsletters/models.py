from django.db import models
from django.utils.text import slugify


class Newsletter(models.Model):
    email = models.EmailField()
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notifier cet : {self.email}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            last_pk = Newsletter.objects.order_by('pk').last()
            self.slug = slugify(self.email) + '-' + str(last_pk.pk + 1) if last_pk else '1'
        super(Newsletter, self).save(*args, **kwargs)

    class Meta:
        db_table = 'newsletter'
        verbose_name = 'newsletter'
        verbose_name_plural = 'newsletters'