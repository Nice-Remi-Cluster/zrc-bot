from nonebot_plugin_orm import Model
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import datetime
import uuid
from typing import Annotated
from nonebot.params import Depends


class UnionUser(Model):
    """统一用户账户表 - 核心用户表，用于唯一标识和管理所有用户"""

    __tablename__ = "union_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now, onupdate=datetime.datetime.now
    )


class QQBinding(Model):
    """QQ 账号绑定表 - 支持一个用户绑定多个 QQ 账号"""

    __tablename__ = "qq_bindings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_uuid: Mapped[str] = mapped_column(String(36))
    qq_number: Mapped[str] = mapped_column(String(20), unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)



