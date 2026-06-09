from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib.auth import  get_user_model

User = get_user_model()


class Notification(models.Model):
    user             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    slug             = models.SlugField(max_length=255, unique=True, editable=False)
    objectif         = models.CharField(max_length=255)
    detail           = models.TextField()
    notif_statut     = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now_add=True)
    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user.full_name) + '-' + get_random_string(5)
        super(Notification, self).save(*args, **kwargs)

    class Meta:
        db_table = 'notification'
        verbose_name = 'notification'
        verbose_name_plural = 'notifications'