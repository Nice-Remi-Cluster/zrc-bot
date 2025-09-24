from maimai_py import PlayerIdentifier
from datetime import datetime, timedelta

from nonebot import require, logger
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    Message as OnebotV11Message,
    MessageSegment as OnebotV11MessageSegment,
)
from nonebot.params import Depends
from sqlalchemy import select
from .alconna import maimai_cn_matcher
from .lib.mai_cn import (
    get_maimai_user_preview_info,
    maimai_py_client,
    divingfish_provider,
    lxns_provider,
    get_maimai_user_all_score,
    mai_cn_score_to_maimaipy,
)
from .lib.pics.b50 import gen_b50
from .models import MaimaiBinding
from ...consts import alias_luoxue, alias_divingfish

require("nonebot_plugin_alconna")
require("union_account")
require("nonebot_plugin_orm")

from nonebot_plugin_alconna import Query as AlcQuery
from nonebot_plugin_orm import async_scoped_session
from ..union_account import get_or_create_union_uuid


@maimai_cn_matcher.assign("update")
async def update_scores(
    event: MessageEvent,
    db_session: async_scoped_session,
    source: AlcQuery[str] = AlcQuery("update.source"),
    user_uuid: str = Depends(get_or_create_union_uuid),
):
    # 获取用户首选的maimai账号绑定信息
    primary_binding = await db_session.scalar(
        select(MaimaiBinding)
        .where(MaimaiBinding.user_uuid == user_uuid)
        .where(MaimaiBinding.is_primary)
    )

    if not primary_binding:
        await maimai_cn_matcher.finish("您尚未绑定任何maimai账号，无法更新成绩")


    # 提取绑定信息
    divingfish_username = primary_binding.divingfish_username
    divingfish_password = primary_binding.divingfish_password
    lxns_friend_code = primary_binding.lxns_friend_code
    maimai_uid = int(primary_binding.maimai_user_id)

    await maimai_cn_matcher.send("正在尝试更新数据，请稍后...")

    # 确定更新范围
    update_targets = []

    if source.available:
        source_value = source.result.lower()
        if source_value in [alias.lower() for alias in alias_luoxue]:
            if lxns_friend_code:
                update_targets.append(("luoxue", lxns_friend_code))
            else:
                await maimai_cn_matcher.finish(
                    "您尚未绑定落雪查分器，无法更新落雪数据源"
                )
        elif source_value in [alias.lower() for alias in alias_divingfish]:
            if divingfish_username and divingfish_password:
                update_targets.append(
                    ("divingfish", divingfish_username, divingfish_password)
                )
            else:
                await maimai_cn_matcher.finish(
                    "您尚未绑定水鱼查分器，无法更新水鱼数据源"
                )
        else:
            await maimai_cn_matcher.finish(
                f"未知的数据源 '{source.result}'，请使用 '落雪' 或 '水鱼'"
            )
    else:
        # 默认同时更新两个数据源
        has_luoxue = bool(lxns_friend_code)
        has_divingfish = bool(divingfish_username and divingfish_password)

        if not has_luoxue and not has_divingfish:
            await maimai_cn_matcher.finish(
                "您尚未绑定任何查分器，请先绑定水鱼或落雪查分器"
            )

        if has_luoxue:
            update_targets.append(("luoxue", lxns_friend_code))
        if has_divingfish:
            update_targets.append(
                ("divingfish", divingfish_username, divingfish_password)
            )

    # 获取原始成绩数据
    try:
        user_score = await mai_cn_score_to_maimaipy(
            await get_maimai_user_all_score(maimai_uid)
        )
    except Exception as e:
        logger.exception(f"获取用户成绩数据失败: {e}")
        await maimai_cn_matcher.finish("获取成绩数据失败，请稍后重试")

    # 执行成绩更新
    results = []

    for target in update_targets:
        try:
            if target[0] == "luoxue":
                _, friend_code = target
                identifier = PlayerIdentifier(friend_code=friend_code)
                provider = lxns_provider

                # 获取更新前的Rating
                old_scores = await maimai_py_client.scores(
                    identifier=identifier, provider=provider
                )
                old_rating = old_scores.rating

                # 执行更新
                await maimai_py_client.updates(
                    identifier=identifier, scores=user_score, provider=provider
                )

                # 获取更新后的Rating
                new_scores = await maimai_py_client.scores(
                    identifier=identifier, provider=provider
                )
                new_rating = new_scores.rating

                results.append(("落雪", old_rating, new_rating))

                # 更新落雪同步时间
                primary_binding.lxns_latest_sync_at = datetime.now()

            elif target[0] == "divingfish":
                _, username, password = target
                identifier = PlayerIdentifier(username=username, credentials=password)
                provider = divingfish_provider

                # 获取更新前的Rating
                old_scores = await maimai_py_client.scores(
                    identifier=identifier, provider=provider
                )
                old_rating = old_scores.rating

                # 执行更新
                await maimai_py_client.updates(
                    identifier=identifier, scores=user_score, provider=provider
                )

                # 获取更新后的Rating
                new_scores = await maimai_py_client.scores(
                    identifier=identifier, provider=provider
                )
                new_rating = new_scores.rating

                results.append(("水鱼", old_rating, new_rating))

                # 更新水鱼同步时间
                primary_binding.divingfish_latest_sync_at = datetime.now()

        except Exception as e:
            logger.exception(f"更新{target[0]}数据源失败: {e}")
            results.append((target[0], None, None, str(e)))

    preview_info = await get_maimai_user_preview_info(maimai_uid)

    # 生成反馈消息
    feedback_msg = f"数据更新完毕 ({preview_info['userName']})\n\n"

    for result in results:
        if len(result) == 4:  # 有错误信息
            source_name, _, _, error = result
            feedback_msg += f"{source_name}数据源更新失败：{error}\n"
        else:
            source_name, old_rating, new_rating = result
            if old_rating is not None and new_rating is not None:
                change = new_rating - old_rating
                if change > 0:
                    feedback_msg += (
                        f"{source_name}：{old_rating} → {new_rating} (+{change})\n"
                    )
                elif change < 0:
                    feedback_msg += (
                        f"{source_name}：{old_rating} → {new_rating} ({change})\n"
                    )
                else:
                    feedback_msg += f"{source_name}：{new_rating} (无变化)\n"
            else:
                feedback_msg += f"{source_name}：更新完成\n"

    # 提交数据库更改
    await db_session.commit()

    await maimai_cn_matcher.finish(feedback_msg)


@maimai_cn_matcher.assign("b50")
async def b50(
    event: MessageEvent,
    db_session: async_scoped_session,
    source: AlcQuery[str] = AlcQuery("b50.source"),
    user_uuid: str = Depends(get_or_create_union_uuid),
):
    # 获取用户首选的maimai账号绑定信息
    primary_binding = await db_session.scalar(
        select(MaimaiBinding)
        .where(MaimaiBinding.user_uuid == user_uuid)
        .where(MaimaiBinding.is_primary)
    )

    if not primary_binding:
        primary_binding = MaimaiBinding(
            user_uuid=user_uuid,
            is_primary=True,
            maimai_user_id="0",
            divingfish_latest_sync_at=datetime.now(),
            lxns_latest_sync_at=datetime.now(),
        )

    # 提取绑定信息
    divingfish_username = primary_binding.divingfish_username
    divingfish_password = primary_binding.divingfish_password
    lxns_friend_code = primary_binding.lxns_friend_code
    maimai_uid = int(primary_binding.maimai_user_id)

    # 确定使用的数据源
    target_source = None
    identifier = None
    provider = None

    if source.available:
        source_value = source.result.lower()
        if source_value in [alias.lower() for alias in alias_luoxue]:
            if lxns_friend_code:
                target_source = "luoxue"
                identifier = PlayerIdentifier(friend_code=int(lxns_friend_code))
                provider = lxns_provider
            else:
                await maimai_cn_matcher.send(
                    "您尚未绑定落雪查分器，将使用QQ号获取数据（无法更新成绩）"
                )
                target_source = "luoxue"
                identifier = PlayerIdentifier(qq=int(event.get_user_id()))
                provider = lxns_provider
        elif source_value in [alias.lower() for alias in alias_divingfish]:
            if divingfish_username and divingfish_password:
                target_source = "divingfish"
                identifier = PlayerIdentifier(
                    username=divingfish_username, credentials=divingfish_password
                )
                provider = divingfish_provider
            else:
                await maimai_cn_matcher.send(
                    "您尚未绑定水鱼查分器，将使用QQ号获取数据（无法更新成绩）"
                )
                target_source = "divingfish"
                identifier = PlayerIdentifier(qq=int(event.get_user_id()))
                provider = divingfish_provider
        else:
            await maimai_cn_matcher.finish(
                f"未知的数据源 '{source.result}'，请使用 '落雪' 或 '水鱼'"
            )
    else:
        # 默认数据源优先级：水鱼 > 落雪 > QQ号
        if divingfish_username and divingfish_password:
            target_source = "divingfish"
            identifier = PlayerIdentifier(
                username=divingfish_username, credentials=divingfish_password
            )
            provider = divingfish_provider
        elif lxns_friend_code:
            target_source = "luoxue"
            identifier = PlayerIdentifier(friend_code=int(lxns_friend_code))
            provider = lxns_provider
        else:
            # 使用QQ号作为特殊格式的identifier
            target_source = "divingfish"
            identifier = PlayerIdentifier(qq=int(event.get_user_id()))
            provider = divingfish_provider

    # 检查是否需要自动更新数据（仅当有绑定信息时才更新）
    need_update = False
    current_time = datetime.now()

    if target_source == "divingfish" and divingfish_username and divingfish_password:
        # 检查水鱼数据源同步时间
        if current_time - primary_binding.divingfish_latest_sync_at > timedelta(
            minutes=15
        ):
            need_update = True
    elif target_source == "luoxue" and lxns_friend_code:
        # 检查落雪数据源同步时间
        if current_time - primary_binding.lxns_latest_sync_at > timedelta(minutes=15):
            need_update = True

    # 执行自动数据更新
    if need_update:
        await maimai_cn_matcher.send("数据已超过15分钟未更新，正在自动更新...")

        try:
            # 获取原始成绩数据
            user_score = await mai_cn_score_to_maimaipy(
                await get_maimai_user_all_score(maimai_uid)
            )

            # 执行更新
            await maimai_py_client.updates(
                identifier=identifier, scores=user_score, provider=provider
            )

            # 更新同步时间
            if target_source == "divingfish":
                primary_binding.divingfish_latest_sync_at = current_time
            elif target_source == "luoxue":
                primary_binding.lxns_latest_sync_at = current_time

            await maimai_cn_matcher.send("数据更新完成，正在获取B50数据...")

        except Exception as e:
            logger.exception(f"自动更新{target_source}数据源失败: {e}")
            await maimai_cn_matcher.send(
                f"数据更新失败：{str(e)}，将使用现有数据获取B50"
            )
    else:
        await maimai_cn_matcher.send("正在获取B50数据...")


    result_msg = OnebotV11Message()
    # 获取B50数据
    try:
        b50_data = await maimai_py_client.bests(
            identifier=identifier, provider=provider
        )

        # 这里应该添加B50数据的处理和展示逻辑
        # 由于没有具体的展示模板，暂时返回基本信息
        if maimai_uid != 0:
            preview_info = await get_maimai_user_preview_info(maimai_uid)
            user_name = preview_info["userName"]
        else:
            user_name = "未知用户"

        ht = await gen_b50(
            user_name, b50_data, maimai_cn_matcher, qq_id=str(event.sender.user_id)
        )
        result_msg.append(OnebotV11MessageSegment.image(ht))

    except Exception as e:
        logger.exception(f"获取B50数据失败{target_source}: {e}; {identifier}")
        result_msg.append(OnebotV11MessageSegment.text(f"获取B50数据失败：{str(e)}"))
    finally:
        await db_session.commit()

    await maimai_cn_matcher.finish(result_msg)