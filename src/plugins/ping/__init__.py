from arclet.alconna import Alconna, CommandMeta
from nonebot import require
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11.event import MessageEvent

from src.consts import alc_header_cn

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import on_alconna  # noqa

__plugin_meta__ = PluginMetadata(
    name="ping",
    description="轻量级机器人状态检测插件，用于验证机器人在线状态和响应能力",
    usage="""ping 插件使用说明：

连通性测试：
• /ping - 执行基础连通性测试，验证机器人在线状态
• 在吗 - 中文自然语言查询""",
    type="application",
    config=None,
    extra={
        "author": "ZRC Bot Team",
        "version": "1.0.0",
        "supported_adapters": ["OneBot V11"],
        "homepage": "https://github.com/ZRC-Bot/zrc-bot",
    },
)

# ping 命令
ping_alc = Alconna(
    f"/ping",
    meta=CommandMeta(
        description="轻量级机器人状态检测插件",
        usage="快速检测机器人连通性和响应状态",
    ),
)
ping = on_alconna(ping_alc, priority=5, use_cmd_start=False)

ping.shortcut(f"{alc_header_cn}在吗", command="/ping")


@ping.handle()
async def _(e: MessageEvent):
    await ping.finish("我在")
