from django.db import models
from django.conf import settings


class MessageChat(models.Model):
    """Message d'échange entre étudiant(s) et encadrant(s) d'un projet."""

    projet = models.ForeignKey(
        "ProjetEtude",
        on_delete=models.CASCADE,
        related_name="messages_chat",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_chat_envoyes",
    )
    contenu = models.TextField(verbose_name="Message")
    lu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Message chat"
        verbose_name_plural = "Messages chat"

    def __str__(self):
        return f"{self.auteur} — {self.projet.titre[:40]}"
