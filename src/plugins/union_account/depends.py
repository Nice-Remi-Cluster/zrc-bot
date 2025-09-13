from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.internal.matcher import Matcher
from nonebot_plugin_orm import SQLDepends, async_scoped_session
from sqlalchemy import select
from nonebot.params import Depends
from .models import UnionUser, QQBinding
from .consts import MessageTemplates


def get_qq_number(event: MessageEvent) -> str:
    """从MessageEvent中提取QQ号"""
    return str(event.sender.user_id)


async def get_or_create_union_uuid(
    session: async_scoped_session,
    matcher: Matcher,
    qq_number: str = Depends(get_qq_number),
) -> str:
    """根据QQ号获取或创建统一账号的UUID"""
    # 首先查找是否已存在QQ绑定
    qq_binding = await session.scalar(
        select(QQBinding).where(QQBinding.qq_number == qq_number)
    )

    if qq_binding:
        # 如果存在绑定，返回对应的UUID
        return qq_binding.user_uuid

    # 如果不存在绑定，创建新    的统一用户
    new_user = UnionUser()
    session.add(new_user)
    await session.flush()  # 刷新以获取生成的UUID

    # 创建QQ绑定
    new_binding = QQBinding(user_uuid=new_user.uuid, qq_number=qq_number)
    session.add(new_binding)
    await session.flush()

    await matcher.send(MessageTemplates.UNION_ACCOUNT_CREATED)

    return new_user.uuid


# 使用SQLDepends的方式获取统一用户UUID（仅查询，不创建）
UnionUUID = SQLDepends(
    select(QQBinding.user_uuid).where(QQBinding.qq_number == Depends(get_qq_number))
)


# 使用示例：
#
# 方式1：使用函数依赖（推荐，支持自动创建）
# @matcher.handle()
# async def handle_message(uuid: str = Depends(get_or_create_union_uuid)):
#     # uuid 是用户的统一账号UUID，如果不存在会自动创建
#     pass
#
# 方式2：使用SQLDepends（仅查询已存在的绑定）
# @matcher.handle()
# async def handle_message(uuid: str | None = UnionUUID):
#     # uuid 可能为None，如果用户没有绑定记录
#     if uuid is None:
#         # 处理未绑定的情况
#         pass
#     else:
#         # 处理已绑定的情况
#         pass
