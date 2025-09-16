from nonebot import require
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, BigInteger

require("nonebot_plugin_orm")
from nonebot_plugin_orm import Model


class WordBankQA(Model):
    """词库问答数据模型"""
    
    __tablename__ = "word_bank_qa"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="群聊ID")
    question: Mapped[str] = mapped_column(String(500), nullable=False, comment="问题")
    answer: Mapped[str] = mapped_column(Text, nullable=False, comment="答案")
    
    class Meta:
        table_description = "词库问答表"