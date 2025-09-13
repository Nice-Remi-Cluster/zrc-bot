from datetime import datetime as py_datetime, timedelta
from typing_extensions import deprecated
from nonebot import require, get_plugin_config
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot_plugin_orm import Model, async_scoped_session
from sqlalchemy import String, Boolean, DateTime, select
from sqlalchemy.orm import Mapped, mapped_column
import uuid
import httpx

require("union_account")
from ..union_account import get_or_create_union_uuid
from .config import Config

from sqlalchemy.sql import true

config = get_plugin_config(Config)


class MaimaiBinding(Model):
    """舞萌 (maimai) 账号绑定表"""

    __tablename__ = "maimai_bindings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_uuid: Mapped[str] = mapped_column(String(36))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    maimai_bind_name: Mapped[str] = mapped_column(String(100), nullable=True)

    maimai_user_id: Mapped[str] = mapped_column(String(50), nullable=True)
    divingfish_username: Mapped[str] = mapped_column(String(100), nullable=True)
    divingfish_password: Mapped[str] = mapped_column(String(100), nullable=True)

    lxns_friend_code: Mapped[str] = mapped_column(String(30), nullable=True)

    divingfish_latest_sync_at: Mapped[py_datetime] = mapped_column(
        DateTime, default=py_datetime.now
    )

    lxns_latest_sync_at: Mapped[py_datetime] = mapped_column(
        DateTime, default=py_datetime.now
    )

    # lxns_oauth_token: Mapped[str] = mapped_column(String(100), nullable=True)
    # lxns_oauth_token_expire_at: Mapped[py_datetime] = mapped_column(
    #     DateTime, default=py_datetime.now
    # )
    # lxns_oauth_refresh_token: Mapped[str] = mapped_column(String(100), nullable=True)
    # lxns_oauth_refresh_token_expire_at: Mapped[py_datetime] = mapped_column(
    #     DateTime, default=py_datetime.now
    # )

    # @staticmethod
    # @deprecated("测试阶段 暂不使用")
    # async def depend_get_lxns_oauth_token(
    #     session: async_scoped_session,
    #     matcher: Matcher,
    #     user_uuid: str = Depends(get_or_create_union_uuid),
    # ) -> str:
    # """获取或刷新 LXNS OAuth 访问令牌

    # 如果令牌已过期，则使用刷新令牌获取新的访问令牌

    # Args:
    #     session: 数据库会话
    #     matcher: NoneBot 匹配器
    #     user_uuid: 用户 UUID

    # Returns:
    #     str: 有效的访问令牌

    # Raises:
    #     ValueError: 当无法获取有效令牌时
    # """
    # # 查询用户绑定信息
    # stmt = select(MaimaiBinding).where(
    #     MaimaiBinding.user_uuid == user_uuid, MaimaiBinding.is_primary == true()
    # )
    # result = await session.execute(stmt)
    # binding = result.scalar_one_or_none()

    # if not binding:
    #     raise ValueError("未找到用户绑定信息")

    # # 检查是否有访问令牌
    # if not binding.lxns_oauth_token:
    #     raise ValueError("用户未授权 LXNS OAuth")

    # # 检查令牌是否过期（提前5分钟刷新）
    # now = py_datetime.now()
    # expire_time = binding.lxns_oauth_token_expire_at - timedelta(minutes=5)

    # if now < expire_time:
    #     # 令牌仍然有效
    #     return binding.lxns_oauth_token

    # # 令牌已过期或即将过期，尝试刷新
    # if not binding.lxns_oauth_refresh_token:
    #     raise ValueError("没有可用的刷新令牌")

    # # 调用 LXNS API 刷新令牌
    # async with httpx.AsyncClient() as client:
    #     try:
    #         response = await client.post(
    #             "https://maimai.lxns.net/api/v0/oauth/token",
    #             data={
    #                 "grant_type": "refresh_token",
    #                 "refresh_token": binding.lxns_oauth_refresh_token,
    #                 "client_id": config.lxns_oauth_client_id,
    #                 "client_secret": config.lxns_oauth_client_secret,
    #             },
    #         )
    #         response.raise_for_status()
    #         token_data = response.json()

    #         # 更新数据库中的令牌信息
    #         binding.lxns_oauth_token = token_data["access_token"]
    #         binding.lxns_oauth_token_expire_at = now + timedelta(
    #             seconds=token_data["expires_in"]
    #         )

    #         if "refresh_token" in token_data:
    #             binding.lxns_oauth_refresh_token = token_data["refresh_token"]
    #             binding.lxns_oauth_refresh_token_expire_at = now + timedelta(
    #                 days=30
    #             )

    #         await session.flush()

    #         return binding.lxns_oauth_token

    #     except httpx.HTTPStatusError as e:
    #         if e.response.status_code == 400:
    #             # 刷新令牌可能已过期
    #             binding.lxns_oauth_token = ""
    #             binding.lxns_oauth_refresh_token = ""
    #             await session.flush()
    #             await matcher.send("授权已过期，请重新进行授权")
    #             raise ValueError("授权已过期，需要重新授权")
    #         else:
    #             raise ValueError(f"刷新令牌失败: {e}")
    #     except Exception as e:
    #         raise ValueError(f"网络错误: {e}")
