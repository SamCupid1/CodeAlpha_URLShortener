import secrets
import string

from django.conf import settings
from django.db import IntegrityError, models, transaction


CODE_ALPHABET = string.ascii_letters + string.digits


class ShortURL(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="short_urls",
        null=True,
        blank=True,
    )
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=8, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    clicks = models.PositiveBigIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"

    @classmethod
    def create(cls, *, original_url, user=None):
        for _ in range(5):
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(7))
            try:
                with transaction.atomic():
                    return cls.objects.create(
                        original_url=original_url,
                        short_code=code,
                        user=user,
                    )
            except IntegrityError:
                if cls.objects.filter(short_code=code).exists():
                    continue
                raise
        raise RuntimeError("Could not generate a unique short code after five attempts.")


class ClickEvent(models.Model):
    short_url = models.ForeignKey(ShortURL,on_delete=models.CASCADE,related_name="click_events", )
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-clicked_at"]
        indexes = [models.Index(fields=["short_url", "-clicked_at"])]

    def __str__(self):
        return f"Click for {self.short_url.short_code} at {self.clicked_at:%Y-%m-%d %H:%M}"
