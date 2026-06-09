from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string


class Newsletter(models.Model):
    email = models.EmailField()
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notifier cet : {self.email}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.email) + '-' + get_random_string(5)
        super(Newsletter, self).save(*args, **kwargs)

    class Meta:
        db_table = 'newsletter'
        verbose_name = 'newsletter'
        verbose_name_plural = 'newsletters'