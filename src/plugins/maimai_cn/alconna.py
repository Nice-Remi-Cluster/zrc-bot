from arclet.alconna import Alconna, Args, Subcommand, CommandMeta
from nonebot_plugin_alconna import on_alconna

from src.consts import alc_header_cn, alias_divingfish, alias_luoxue

maimai_cn_alc = Alconna(
    "/maimai_cn",
    Subcommand(
        "bind",
        Args["sgwcmaid", str],
        Args["bind_name?", str],
        help_text="绑定国区舞萌账号",
    ),
    Subcommand(
        "list",
        help_text="查看所有已绑定的账号",
    ),
    Subcommand(
        "bind_diving_fish",
        Args["diving_fish_username", str],
        Args["diving_fish_password", str],
        help_text="绑定水鱼查分器",
    ),
    Subcommand(
        "bind_luoxue",
        Args["luoxue_friend_code", str],
        help_text="绑定落雪查分器",
    ),
    Subcommand(
        "set_primary",
        Args["bind_id", str],
        help_text="设置当前首选账号",
    ),
    Subcommand(
        "update",
        Args["source?", alias_divingfish + alias_luoxue],
        help_text="更新查分器",
    ),
    Subcommand(
        "b50",
        Args["source?", alias_divingfish + alias_luoxue],
        help_text="输出自己的b50成绩",
    ),
    meta=CommandMeta(
        description="舞萌DX国区玩家账号管理和成绩查询插件",
        usage="支持多查分器平台集成和B50成绩查询",
    ),
)

maimai_cn_matcher = on_alconna(maimai_cn_alc, use_cmd_start=False, priority=5)


maimai_cn_alc.shortcut(
    rf"{alc_header_cn}绑定舞萌 (\S+)(?: (\S+))?", {"command": "/maimai_cn bind {0} {1}"}
)
maimai_cn_alc.shortcut(f"{alc_header_cn}我都绑了什么", {"command": "/maimai_cn list"})
maimai_cn_alc.shortcut(f"{alc_header_cn}查绑定", {"command": "/maimai_cn list"})
maimai_cn_alc.shortcut(f"{alc_header_cn}更新b50", {"command": "/maimai_cn update"})
maimai_cn_alc.shortcut(f"{alc_header_cn}更新查分器", {"command": "/maimai_cn update"})
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}更新b50 (\S+)", {"command": "/maimai_cn update {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}更新(\S+)b50", {"command": "/maimai_cn update {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}更新查分器 (\S+)", {"command": "/maimai_cn update {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}更新(\S+)查分器", {"command": "/maimai_cn update {0}"}
)
maimai_cn_alc.shortcut(rf"{alc_header_cn}查(\S+)b50", {"command": "/maimai_cn b50 {0}"})
maimai_cn_alc.shortcut(rf"{alc_header_cn}看(\S+)b50", {"command": "/maimai_cn b50 {0}"})
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}查b50 (\S+)", {"command": "/maimai_cn b50 {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}看b50 (\S+)", {"command": "/maimai_cn b50 {0}"}
)
maimai_cn_alc.shortcut("b50", {"command": "/maimai_cn b50 水鱼"})
maimai_cn_alc.shortcut(rf"{alc_header_cn}查b50", {"command": "/maimai_cn b50 水鱼"})

# 水鱼查分器相关快捷方式
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}绑定水鱼 (\S+) (\S+)",
    {"command": "/maimai_cn bind_diving_fish {0} {1}"},
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}帮我绑水鱼 (\S+) (\S+)",
    {"command": "/maimai_cn bind_diving_fish {0} {1}"},
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}帮我绑定水鱼 (\S+) (\S+)",
    {"command": "/maimai_cn bind_diving_fish {0} {1}"},
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}绑定divingfish (\S+) (\S+)",
    {"command": "/maimai_cn bind_diving_fish {0} {1}"},
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}帮我绑divingfish (\S+) (\S+)",
    {"command": "/maimai_cn bind_diving_fish {0} {1}"},
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}帮我绑定divingfish (\S+) (\S+)",
    {"command": "/maimai_cn bind_diving_fish {0} {1}"},
)

# 落雪查分器相关快捷方式
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}绑定落雪 (\S+)", {"command": "/maimai_cn bind_luoxue {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}帮我绑落雪 (\S+)", {"command": "/maimai_cn bind_luoxue {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}帮我绑定落雪 (\S+)", {"command": "/maimai_cn bind_luoxue {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}绑定lxns (\S+)", {"command": "/maimai_cn bind_luoxue {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}帮我绑lxns (\S+)", {"command": "/maimai_cn bind_luoxue {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}帮我绑定lxns (\S+)", {"command": "/maimai_cn bind_luoxue {0}"}
)

# set_primary 相关快捷方式
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}设置首选 (\S+)", {"command": "/maimai_cn set_primary {0}"}
)
maimai_cn_alc.shortcut(
    rf"{alc_header_cn}切换首选 (\S+)", {"command": "/maimai_cn set_primary {0}"}
)
