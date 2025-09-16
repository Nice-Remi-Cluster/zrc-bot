from nonebot import require
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.rule import Rule
from sqlalchemy import select, delete
from nonebot_plugin_alconna import Query as AlcQuery

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import on_alconna

require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session

require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import text_to_pic

from .alconna import alc
from .models import WordBankQA
from .config import Config

# 文本长度阈值，超过此长度的文本将渲染为图片
TEXT_TO_IMAGE_THRESHOLD = 100

__plugin_meta__ = PluginMetadata(
    name="word_bank_qa",
    description="词库问答",
    usage="",
    config=Config,
)


def group_only() -> Rule:
    """只在群聊中响应的规则"""

    async def _group_only(event) -> bool:
        return isinstance(event, GroupMessageEvent)

    return Rule(_group_only)


# 词库问答匹配器
word_qa_matcher = on_alconna(alc, rule=group_only())


@word_qa_matcher.assign("q")
async def query_word(
    event: GroupMessageEvent,
    session: async_scoped_session,
    question: AlcQuery[str] = AlcQuery("q.question"),
):
    """查询词库问答"""
    if not question.available:
        await word_qa_matcher.finish("请输入要查询的问题")
    question = question.result

    # 查询数据库
    stmt = select(WordBankQA).where(
        WordBankQA.group_id == event.group_id, WordBankQA.question == question
    )
    result = await session.execute(stmt)
    qa_record = result.scalar_one_or_none()

    if qa_record:
        # 根据答案长度决定是否渲染为图片
        answer_text = qa_record.answer
        if len(answer_text) > TEXT_TO_IMAGE_THRESHOLD:
            text_content = f"问题：{question}\n\n答案：{answer_text}"
            pic = await text_to_pic(text_content)
            await word_qa_matcher.finish(MessageSegment.image(pic))
        else:
            await word_qa_matcher.finish(answer_text)
    else:
        # 未找到答案的提示通常较短，直接发送文本
        await word_qa_matcher.finish(f"未找到问题「{question}」的答案")


@word_qa_matcher.assign("add")
async def add_word(
    event: GroupMessageEvent,
    session: async_scoped_session,
    question: AlcQuery[str] = AlcQuery("add.question"),
    answer_list: AlcQuery[list] = AlcQuery("add.answer", []),
):
    """添加词库问答"""
    if not question.available:
        await word_qa_matcher.finish("请输入问题")

    if not answer_list.available or not answer_list.result:
        await word_qa_matcher.finish("请输入答案")

    # 将答案列表合并为字符串
    answer = " ".join(answer_list.result)

    # 检查是否已存在
    stmt = select(WordBankQA).where(
        WordBankQA.group_id == event.group_id, WordBankQA.question == question.result
    )
    result = await session.execute(stmt)
    existing_record = result.scalar_one_or_none()

    if existing_record:
        # 更新现有记录
        existing_record.answer = answer
        await session.commit()
        await word_qa_matcher.finish(f"已更新问题「{question.result}」的答案")
    else:
        # 创建新记录
        new_qa = WordBankQA(
            group_id=event.group_id, question=question.result, answer=answer
        )
        session.add(new_qa)
        await session.commit()
        await word_qa_matcher.finish(f"已添加问题「{question.result}」的答案")


@word_qa_matcher.assign("remove")
async def remove_word(
    event: GroupMessageEvent,
    session: async_scoped_session,
    question: AlcQuery[str] = AlcQuery("remove.question"),
    all_flag: AlcQuery[bool] = AlcQuery("remove.all", False),
):
    """删除词库问答"""
    if not question.available:
        await word_qa_matcher.finish("请输入要删除的问题")

    if all_flag.result:
        # 删除所有匹配的记录
        stmt = delete(WordBankQA).where(
            WordBankQA.group_id == event.group_id,
            WordBankQA.question == question.result,
        )
        result = await session.execute(stmt)
        await session.commit()

        if result.rowcount > 0:
            await word_qa_matcher.finish(
                f"已删除问题「{question.result}」的所有答案（共{result.rowcount}条）"
            )
        else:
            await word_qa_matcher.finish(f"未找到问题「{question.result}」")
    else:
        # 删除单个记录
        stmt = select(WordBankQA).where(
            WordBankQA.group_id == event.group_id,
            WordBankQA.question == question.result,
        )
        result = await session.execute(stmt)
        qa_record = result.scalar_one_or_none()

        if qa_record:
            await session.delete(qa_record)
            await session.commit()
            await word_qa_matcher.finish(f"已删除问题「{question.result}」的答案")
        else:
            await word_qa_matcher.finish(f"未找到问题「{question.result}」")


@word_qa_matcher.assign("list")
async def list_words(event: GroupMessageEvent, session: async_scoped_session):
    """列出所有词库问答"""
    stmt = select(WordBankQA).where(WordBankQA.group_id == event.group_id)
    result = await session.execute(stmt)
    qa_records = result.scalars().all()

    if not qa_records:
        # 无记录的提示较短，直接发送文本
        await word_qa_matcher.finish("当前群聊暂无词库问答")

    # 构建回复消息
    message_lines = ["当前群聊的词库问答："]
    for i, qa in enumerate(qa_records, 1):
        # 限制显示长度
        question = qa.question[:20] + "..." if len(qa.question) > 20 else qa.question
        answer = qa.answer[:30] + "..." if len(qa.answer) > 30 else qa.answer
        message_lines.append(f"{i}. {question} -> {answer}")

    # 根据列表长度决定是否渲染为图片
    text_content = "\n".join(message_lines)
    if len(text_content) > TEXT_TO_IMAGE_THRESHOLD:
        pic = await text_to_pic(text_content)
        await word_qa_matcher.finish(MessageSegment.image(pic))
    else:
        await word_qa_matcher.finish(text_content)
