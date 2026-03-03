from django.db import models
from django.utils.text import slugify
from django.contrib.auth import  get_user_model

User = get_user_model()


class Notification(models.Model):
    user             = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    slug             = models.SlugField(max_length=255, unique=True, editable=False)
    objectif         = models.CharField(max_length=255)
    detail           = models.TextField()
    notif_statut     = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now_add=True)
    

    def save(self, *args, **kwargs):
        if not self.slug:
            last_pk = Notification.objects.order_by('pk').last()
            self.slug = slugify(self.user) + '-' + str(last_pk.pk + 1) if last_pk else '1'
        super(Notification, self).save(*args, **kwargs)

    class Meta:
        db_table = 'notification'
        verbose_name = 'notification'
        verbose_name_plural = 'notifications'