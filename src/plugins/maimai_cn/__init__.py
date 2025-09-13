from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

from .cmd_base import *  # noqa: F403
from .cmd_score import *  # noqa: F403

from .models import *  # noqa: F403

__plugin_meta__ = PluginMetadata(
    name="maimai_cn",
    description="舞萌DX国区玩家账号管理和成绩查询插件，支持多查分器平台集成和B50成绩查询",
    usage="""maimai_cn 插件使用说明：

账号绑定：
• 绑定舞萌 <sgwcmaid> [bind_name] - 绑定国区舞萌账号
• 绑定水鱼 <username> <password> - 绑定水鱼查分器
• 绑定落雪 <username> <password> - 绑定落雪查分器

账号管理：
• 查看已绑定账号 - 显示所有已绑定的账号信息
• 设置首选账号 <bind_name> - 设置默认使用的账号

成绩查询：
• 更新查分器数据 - 同步最新成绩数据
• 查询B50成绩 [bind_name] - 查看Best 50成绩

支持多查分器平台（水鱼查分器、落雪查分器）和智能快捷指令系统。""",
    type="application",
    config=Config,
    extra={
        "author": "ZRC Bot Team",
        "version": "1.0.0",
        "supported_adapters": ["OneBot V11"],
        "homepage": "https://github.com/ZRC-Bot/zrc-bot"
    },
)

config = get_plugin_config(Config)
