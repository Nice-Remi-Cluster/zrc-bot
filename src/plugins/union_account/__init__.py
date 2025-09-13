from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from .config import Config
from .models import *  # noqa: F403
from .depends import get_or_create_union_uuid

__plugin_meta__ = PluginMetadata(
    name="union_account",
    description="统一账户管理系统，为机器人提供用户唯一标识和多平台账号绑定功能",
    usage="""union_account 插件说明：

核心功能：
• 统一用户标识 - 为每个用户分配唯一的UUID
• QQ账号绑定 - 支持一个用户绑定多个QQ账号
• 跨插件用户管理 - 为其他插件提供统一的用户识别服务

技术特性：
• 自动用户创建和绑定
• 数据库持久化存储
• 依赖注入支持
• 异步数据库操作

适用场景：
• 多插件用户数据关联
• 用户身份统一管理
• 跨平台账号绑定""",
    type="library",
    config=Config,
    extra={
        "author": "ZRC Bot Team",
        "version": "1.0.0",
        "supported_adapters": ["OneBot V11"],
        "homepage": "https://github.com/ZRC-Bot/zrc-bot",
    },
)

config = get_plugin_config(Config)
