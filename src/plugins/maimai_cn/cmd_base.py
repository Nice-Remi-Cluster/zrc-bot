from nonebot_plugin_alconna.matcher import AlconnaMatcher


from maimai_py import PlayerIdentifier
from wahlap_mai_ass_expander.model import PreviewInfo


import asyncio
import jaconv
from nonebot import require, logger
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    Message as OnebotV11Message,
)
from nonebot.params import Depends
from sqlalchemy import select
from wahlap_mai_ass_expander.exceptions import QrCodeExpired, QrCodeInvalid
from .alconna import maimai_cn_matcher
from .lib.mai_cn import get_maimai_uid, get_maimai_user_preview_info
from .models import MaimaiBinding

require("nonebot_plugin_alconna")
require("union_account")
require("nonebot_plugin_orm")

from nonebot_plugin_alconna import on_alconna, Query as AlcQuery
from nonebot_plugin_orm import async_scoped_session
from ..union_account import get_or_create_union_uuid


@maimai_cn_matcher.assign("bind")
async def bind_maimai_cn(
    event: MessageEvent,
    db_session: async_scoped_session,
    sgwcmaid: AlcQuery[str] = AlcQuery("bind.sgwcmaid"),
    bind_name: AlcQuery[str] = AlcQuery("bind.bind_name"),
    user_uuid: str = Depends(get_or_create_union_uuid),
):
    if not sgwcmaid.available:
        await maimai_cn_matcher.finish("缺少SGWCMAID参数")

    await maimai_cn_matcher.send("正在尝试绑定maimai账号，请稍后...")

    try:
        mai_uid = await get_maimai_uid(sgwcmaid.result)
    except QrCodeExpired:
        await maimai_cn_matcher.finish("二维码已过期")
    except QrCodeInvalid:
        await maimai_cn_matcher.finish("二维码无效，请重新获取")
    except Exception as e:
        logger.exception(f"获取maimai UID失败: {e}")
        await maimai_cn_matcher.finish("添加失败，请联系管理员")

    user_info = await get_maimai_user_preview_info(mai_uid)

    # 查询数据库中是否已存在相同的maimai_user_id
    existing = await db_session.scalars(
        select(MaimaiBinding).where(MaimaiBinding.maimai_user_id == mai_uid)
    )
    if existing.first():
        await maimai_cn_matcher.finish(
            f"{user_info['userName']} ({user_info['playerRating']})\n"
            "该maimai账号已被绑定，请使用其他账号。若确定本账号属于您个人，请联系管理员处理。"
        )

    try:
        result = await db_session.scalars(
            select(MaimaiBinding).where(MaimaiBinding.user_uuid == user_uuid)
        )

        mai_instance = MaimaiBinding(
            user_uuid=user_uuid,
            is_primary=not bool(result.first()),
            maimai_user_id=mai_uid,
            maimai_bind_name=bind_name.result,
        )
        if not bind_name.available:
            mai_instance.maimai_bind_name = jaconv.z2h(
                user_info["userName"], kana=True, ascii=True, digit=True
            )

        db_session.add(mai_instance)
        await db_session.flush()
        await db_session.commit()
    except Exception as e:
        logger.exception(f"maimai绑定失败: {e}")
        await maimai_cn_matcher.finish("添加失败，请联系管理员查看日志")
    else:
        await maimai_cn_matcher.finish(
            f"{user_info['userName']} ({user_info['playerRating']})\nmaimai 绑定成功"
        )


@maimai_cn_matcher.assign("list")
async def list_maimai_bindings(
    event: MessageEvent,
    db_session: async_scoped_session,
    user_uuid: str = Depends(get_or_create_union_uuid),
):
    # await maimai_cn_matcher.send(user_uuid)
    result = await db_session.scalars(
        select(MaimaiBinding).where(MaimaiBinding.user_uuid == user_uuid)
    )

    bindings = result.all()
    if not bindings:
        await maimai_cn_matcher.finish("您尚未绑定maimai账号")

    tasks = [
        asyncio.create_task(get_maimai_user_preview_info(int(b.maimai_user_id)))
        for b in bindings
    ]
    results: list[PreviewInfo] = await asyncio.gather(*tasks)

    ret: OnebotV11Message = OnebotV11Message("以下是您绑定的maimai账号：\n")
    for b, r in zip(bindings, results):
        t = "==========\n"
        t += (
            f"绑定id：{b.maimai_bind_name} {'（当前首选）' if b.is_primary else ''}\n"
            f"maimai账户：{r['userName']} ({r['playerRating']})\n"
            f"水鱼查分器{'已绑定' if b.divingfish_username else '未绑定'}\n"
            f"落雪查分器{'已绑定' if b.lxns_friend_code else '未绑定'}\n"
        )
        ret += t

    await maimai_cn_matcher.finish(ret)


@maimai_cn_matcher.assign("bind_diving_fish")
async def bind_diving_fish(
    event: MessageEvent,
    db_session: async_scoped_session,
    diving_fish_username: AlcQuery[str] = AlcQuery(
        "bind_diving_fish.diving_fish_username"
    ),
    diving_fish_password: AlcQuery[str] = AlcQuery(
        "bind_diving_fish.diving_fish_password"
    ),
    user_uuid: str = Depends(get_or_create_union_uuid),
):
    # 检查参数是否可用
    if not diving_fish_username.available:
        await maimai_cn_matcher.finish("缺少水鱼查分器用户名参数")
    if not diving_fish_password.available:
        await maimai_cn_matcher.finish("缺少水鱼查分器密码参数")

    # 获取用户当前的primary maimai绑定
    primary_binding = await db_session.scalar(
        select(MaimaiBinding)
        .where(MaimaiBinding.user_uuid == user_uuid)
        .where(MaimaiBinding.is_primary)
    )

    if not primary_binding:
        await maimai_cn_matcher.finish("您尚未绑定任何maimai账号，请先绑定账号")

    # 检查是否已经绑定水鱼查分器
    if primary_binding.divingfish_username:
        await maimai_cn_matcher.finish(
            f"您当前的首选账号 '{primary_binding.maimai_bind_name}' 已绑定水鱼查分器\n"
            f"当前绑定用户名：{primary_binding.divingfish_username}\n"
            f"如需换绑请联系管理员"
        )

    # 检查用户名重复性
    existing_username = await db_session.scalar(
        select(MaimaiBinding)
        .where(MaimaiBinding.divingfish_username == diving_fish_username.result)
        .where(MaimaiBinding.id != primary_binding.id)
    )

    if existing_username:
        await maimai_cn_matcher.finish(
            "该水鱼查分器用户名已被其他账号绑定，请使用其他用户名"
        )

    try:
        # 更新primary绑定的divingfish账号信息
        primary_binding.divingfish_username = diving_fish_username.result
        primary_binding.divingfish_password = diving_fish_password.result

        bind_name = primary_binding.maimai_bind_name

        await db_session.commit()

    except Exception as e:
        logger.exception(f"水鱼查分器绑定失败: {e}")
        await db_session.rollback()
        await maimai_cn_matcher.finish("绑定失败，请联系管理员查看日志")

    await maimai_cn_matcher.finish(
        f"水鱼查分器账户信息绑定成功！\n绑定账号：{bind_name}\n用户名：{diving_fish_username.result}"
    )


@maimai_cn_matcher.assign("bind_luoxue")
async def bind_luoxue(
    event: MessageEvent,
    db_session: async_scoped_session,
    luoxue_friend_code: AlcQuery[str] = AlcQuery("bind_luoxue.luoxue_friend_code"),
    user_uuid: str = Depends(get_or_create_union_uuid),
):
    # 检查参数是否可用
    if not luoxue_friend_code.available:
        await maimai_cn_matcher.finish("缺少落雪查分器好友码参数")

    # 获取用户当前的primary maimai绑定
    primary_binding = await db_session.scalar(
        select(MaimaiBinding)
        .where(MaimaiBinding.user_uuid == user_uuid)
        .where(MaimaiBinding.is_primary)
    )

    if not primary_binding:
        await maimai_cn_matcher.finish("您尚未绑定任何maimai账号，请先绑定账号")

    # 检查是否已经绑定落雪查分器
    if primary_binding.lxns_friend_code:
        await maimai_cn_matcher.finish(
            f"您当前的首选账号 '{primary_binding.maimai_bind_name}' 已绑定落雪查分器\n"
            f"当前绑定好友码：{primary_binding.lxns_friend_code}\n"
            f"如需换绑请联系管理员"
        )

    # 检查好友码重复性
    existing_friend_code = await db_session.scalar(
        select(MaimaiBinding)
        .where(MaimaiBinding.lxns_friend_code == luoxue_friend_code.result)
        .where(MaimaiBinding.id != primary_binding.id)
    )

    if existing_friend_code:
        await maimai_cn_matcher.finish(
            "该落雪查分器好友码已被其他账号绑定，请使用其他好友码"
        )

    friend_code = luoxue_friend_code.result.strip()

    try:
        # 更新primary绑定的lxns好友码信息
        primary_binding.lxns_friend_code = friend_code

        bind_name = primary_binding.maimai_bind_name

        await db_session.commit()

    except Exception as e:
        logger.exception(f"落雪查分器绑定失败: {e}")
        await db_session.rollback()
        await maimai_cn_matcher.finish("绑定失败，请联系管理员查看日志")

    await maimai_cn_matcher.finish(
        f"落雪查分器好友码绑定成功！\n绑定账号：{bind_name}\n好友码：{friend_code}"
    )


@maimai_cn_matcher.assign("set_primary")
async def set_primary_maimai_binding(
    event: MessageEvent,
    db_session: async_scoped_session,
    bind_id: AlcQuery[str] = AlcQuery("set_primary.bind_id"),
    user_uuid: str = Depends(get_or_create_union_uuid),
):
    # 检查参数是否可用
    if not bind_id.available:
        await maimai_cn_matcher.finish("缺少绑定ID参数")

    # 查找指定的绑定
    target_binding = await db_session.scalar(
        select(MaimaiBinding)
        .where(MaimaiBinding.user_uuid == user_uuid)
        .where(MaimaiBinding.maimai_bind_name == bind_id.result)
    )

    if not target_binding:
        await maimai_cn_matcher.finish(
            f"未找到绑定ID为 '{bind_id.result}' 的账号，请使用 /maimai_cn list 查看所有绑定"
        )

    # 获取当前的首选绑定
    current_primary = await db_session.scalar(
        select(MaimaiBinding)
        .where(MaimaiBinding.user_uuid == user_uuid)
        .where(MaimaiBinding.is_primary)
    )

    if current_primary and current_primary.id == target_binding.id:
        await maimai_cn_matcher.finish(f"绑定ID '{bind_id.result}' 已经是当前首选账号")

    try:
        # 将当前首选设为非首选
        if current_primary:
            current_primary.is_primary = False

        # 将目标设为新首选
        target_binding.is_primary = True

        bind_name = target_binding.maimai_bind_name

        await db_session.commit()

    except Exception as e:
        logger.exception(f"设置首选账号失败: {e}")
        await db_session.rollback()
        await maimai_cn_matcher.finish("设置失败，请联系管理员查看日志")

    await maimai_cn_matcher.finish(f"设置首选账号成功！\n绑定ID：{bind_name}")
