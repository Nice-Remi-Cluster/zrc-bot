from arclet.alconna import Alconna, Subcommand, Args, MultiVar, Option, CommandMeta
from nepattern import AnyString
from src.consts import alc_header_cn

alc = Alconna(
    "/word_qa",
    Subcommand(
        "q",
        Args["question", str],
        help_text="查询词库问答",
    ),
    Subcommand(
        "add",
        Args["question", str],
        Args["answer", MultiVar(AnyString, flag="*")],
        help_text="添加词库问答",
    ),
    Subcommand(
        "remove?",
        Args["question", str],
        Option("--all|-A", help_text="删除所有匹配的记录"),
        help_text="删除词库问答",
    ),
    Subcommand(
        "list",
        help_text="列出所有词库问答",
    ),
    meta=CommandMeta(
        description="固定词库问答工具",
        usage="支持分群聊存储的词库问答功能",
    ),
)

# 添加快捷方式
# 查询相关
alc.shortcut(rf"{alc_header_cn}问 (.+)", {"command": "/word_qa q {0}"})
alc.shortcut(rf"{alc_header_cn}查问题 (.+)", {"command": "/word_qa q {0}"})
alc.shortcut(rf"问(.+)", {"command": "/word_qa q {0}"})

# 添加相关
alc.shortcut(rf"{alc_header_cn}添加问答 (.+?) (.+)", {"command": "/word_qa add {0} {1}"})
alc.shortcut(rf"{alc_header_cn}加问答 (.+?) (.+)", {"command": "/word_qa add {0} {1}"})
alc.shortcut(rf"{alc_header_cn}学习 (.+?) (.+)", {"command": "/word_qa add {0} {1}"})

# 删除相关
alc.shortcut(rf"{alc_header_cn}删除问答 (.+)", {"command": "/word_qa remove {0}"})
alc.shortcut(rf"{alc_header_cn}删问答 (.+)", {"command": "/word_qa remove {0}"})
alc.shortcut(rf"{alc_header_cn}忘记 (.+)", {"command": "/word_qa remove {0}"})
alc.shortcut(rf"{alc_header_cn}删除全部问答 (.+)", {"command": "/word_qa remove {0} --all"})

# 列表相关
alc.shortcut(f"{alc_header_cn}问答列表", {"command": "/word_qa list"})
alc.shortcut(f"{alc_header_cn}词库列表", {"command": "/word_qa list"})
alc.shortcut(f"{alc_header_cn}查看问答", {"command": "/word_qa list"})