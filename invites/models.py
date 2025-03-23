from datetime import timedelta, datetime
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError

from utils.strings import random_string

INVITE_CODE_LENGTH = 14
INVITE_EXPIRATION_DAYS = 365
MAX_INVITES_PER_USER = 7


class Invite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    code = models.CharField(max_length=32, unique=True)
    user = models.ForeignKey("users.User", related_name="invites", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True)

    invited_email = models.CharField(max_length=255, null=True)
    invited_user = models.ForeignKey("users.User", related_name="my_invite", on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "invites"

    @property
    def expires_at(self):
        return self.created_at + timedelta(days=INVITE_EXPIRATION_DAYS)

    @property
    def is_expired(self):
        return self.expires_at < datetime.now()

    @property
    def is_used(self):
        return bool(self.used_at)

    def save(self, *args, **kwargs):
        if not self.code:
            attempt = 0
            while attempt < 5:
                code = random_string(length=INVITE_CODE_LENGTH).upper()
                if not Invite.objects.filter(code=code).exists():
                    self.code = code
                    break
        return super().save(*args, **kwargs)

    @classmethod
    def for_user(cls, user):
        return cls.objects.filter(user=user).select_related("invited_user").order_by("-created_at")

    @classmethod
    def can_create_invite(cls, user):
        if user.is_god:
            return True
        active_invites = cls.objects.filter(user=user, used_at__isnull=True).count()
        return active_invites < MAX_INVITES_PER_USER

    def to_dict(self):
        return {
            "code": self.code,
            "url": settings.APP_HOST + reverse("show_invite", kwargs={"invite_code": self.code}),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "used_at": self.used_at,
            "invited_user": self.invited_user.to_dict() if self.invited_user else None,
        }
