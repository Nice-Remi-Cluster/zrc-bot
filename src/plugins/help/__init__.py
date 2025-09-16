import json

from arclet.alconna import Alconna, Args, MultiVar
from markdown_it import MarkdownIt
from markdown_it.presets import gfm_like
from mdit_py_plugins.dollarmath import dollarmath_plugin
from nepattern import AnyString
from nonebot import get_plugin_config, require
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
from nonebot.exception import FinishedException
from nonebot.plugin import PluginMetadata
from nonebot_plugin_alconna import on_alconna, CommandResult
import os
from loguru import logger
import httpx

require("nonebot_plugin_htmlrender")

from nonebot_plugin_htmlrender import md_to_pic, text_to_pic, html_to_pic, get_new_page

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="help",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

alc = Alconna(
    "/help",
    Args["options", MultiVar(AnyString, flag="*")],
)
help_cmd = on_alconna(alc, priority=5, use_cmd_start=False)


async def get_coze_response(content: str, user_id: str) -> str:
    """
    获取Coze API的响应

    Args:
        content: 用户输入的问题内容
        user_id: 用户ID

    Returns:
        str: Coze API返回的回答内容

    Raises:
        Exception: 当API请求失败时抛出异常
    """
    reply = ""

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            "https://api.coze.cn/v3/chat?",
            headers={
                "Authorization": f"Bearer {config.coze_api_token}",
                "Content-Type": "application/json",
            },
            json={
                "bot_id": config.coze_workflow_id_help_str,
                "user_id": user_id,
                "stream": True,  # 关键：开启流式
                "additional_messages": [
                    {
                        "role": "user",
                        "type": "question",
                        "content_type": "text",
                        "content": content,
                    }
                ],
                "publish_status": "published_online",
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                logger.trace(f"Received line: {line}")
                if not line.startswith("data:"):
                    continue
                chunk = line[len("data:") :].strip()
                if chunk == '"[DONE]"':
                    break
                try:
                    obj = json.loads(chunk)
                except json.JSONDecodeError:
                    continue
                # 按 Coze 事件格式取回答文本
                if (
                    obj.get("content_type") == "text"
                    and obj.get("role") == "assistant"
                    and obj.get("type") == "answer"
                    and obj.get("created_at", None) is not None
                ):
                    reply = obj.get("content", {})

    return reply


async def render_markdown_to_image(markdown_content: str) -> bytes:
    """
    将Markdown内容渲染为图片

    Args:
        markdown_content: Markdown格式的文本内容

    Returns:
        bytes: 渲染后的图片数据
    """
    logger.debug(f"\n{markdown_content}")

    # 配置Markdown解析器
    md = MarkdownIt(
        config=gfm_like.make(),
        options_update={
            "html": False,
            "linkify": False,
        },
    ).use(dollarmath_plugin)
    md.enable(["replacements", "smartquotes"])

    # 渲染Markdown为HTML
    md_html_content = md.render(markdown_content)

    html = (
        open(f"{os.path.dirname(__file__)}/template/text.html").read()
        .replace("{{css}}", open(f"{os.path.dirname(__file__)}/template/markdown.css").read())
        .replace("{{content}}", md_html_content)
    )

    # 使用浏览器渲染HTML为图片
    async with get_new_page(viewport={"width": 500, "height": 300}) as page:
        await page.set_content(html, wait_until="networkidle")
        pic = await page.screenshot(full_page=True)

    return pic


@help_cmd.handle()
async def handle_help(event: MessageEvent, arp: CommandResult):
    """
    处理help命令的主函数
    """
    options = arp.result.main_args["options"]

    if not options:
        await help_cmd.finish(
            "哎哟，不问问题我怎么回答你呢。试着在help后跟着要问的问题吧。"
        )

    # await help_cmd.send("稍等哦，我帮你查一下")

    content = " ".join(options)

    try:
        # 获取Coze API响应
        reply = await get_coze_response(content, str(event.get_user_id()))

        if reply:
            # 渲染Markdown为图片
            pic = await render_markdown_to_image(reply)
            await help_cmd.finish(MessageSegment.image(pic))
        else:
            await help_cmd.finish("我好像没有找到相关的答案，你可以试着联系管理员。")

    except FinishedException:
        pass
    except Exception as e:
        await help_cmd.finish(f"出错了，请联系管理员。\n错误信息：{e}")
