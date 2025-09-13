import random
from arclet.alconna import CommandMeta
from nepattern import AnyString
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config
from nonebot import require

from ...consts import alc_header_cn

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna import Alconna, Args, MultiVar, on_alconna, CommandResult

from nonebot import on_command
from nonebot.adapters import Bot, Event
from nonebot.matcher import Matcher

from nonebot.adapters.onebot.v11 import MessageEvent

__plugin_meta__ = PluginMetadata(
    name="roll",
    description="功能丰富的随机数生成和随机选择工具，支持多种随机化算法和使用模式",
    usage="""roll 插件使用说明：

随机数生成：
• /roll - 生成0-100之间的随机数
• /roll <number> - 生成0到指定数字之间的随机数
• /roll <选项1> <选项2> ... - 从多个选项中随机选择

使用示例：
• /roll - 随机数0-100
• /roll 6 - 骰子模拟（0-6）
• /roll 苹果 香蕉 橙子 - 随机选择水果
• /roll 今天吃什么 明天再说 - 决策辅助""",
    type="application",
    config=Config,
    extra={
        "author": "ZRC Bot Team",
        "version": "1.0.0",
        "supported_adapters": ["OneBot V11"],
        "homepage": "https://github.com/ZRC-Bot/zrc-bot",
    },
)

config = get_plugin_config(Config)

alc = Alconna(
    "/roll",
    Args["options", MultiVar(AnyString, flag="*")],
    meta=CommandMeta(
        description="功能丰富的随机数生成和随机选择工具",
        usage="支持多种随机数生成模式和随机选择功能",
    ),
)

roll_cmd = on_alconna(alc, priority=5, use_cmd_start=False)


@roll_cmd.handle()
async def handle_roll(event: MessageEvent, arp: CommandResult):
    options = arp.result.main_args["options"]

    # 没有参数，默认是0-100的随机数
    if not options:
        result = random.randint(0, 100)

    # 如果只有一个参数且是数字
    elif len(options) == 1 and options[0].isdigit():
        upper_limit = int(options[0])
        result = random.randint(0, upper_limit)

    # 有多个参数，从中随机选择一个
    else:
        result = random.choice(options)

    await roll_cmd.finish(f"{result}")
