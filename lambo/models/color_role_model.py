from datetime import timedelta
from enum import IntEnum
from typing import Optional, TypedDict

from tortoise import fields
from tortoise.models import Model


class ColorRoleModel(Model):
    role_id = fields.CharField(max_length=22, pk=True, unique=True)  # role id
    owner_id = fields.CharField(max_length=22)  # owner id
