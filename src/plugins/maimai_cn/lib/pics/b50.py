from maimai_py.models import ScoreExtend, Song, SongDifficulty


import asyncio
from pathlib import Path
import os
from loguru import logger
import cloudscraper
from nonebot.matcher import Matcher
from .lib import env
from maimai_py import MaimaiScores
from nonebot import require

require("nonebot_plugin_htmlrender")

from nonebot_plugin_htmlrender import template_to_pic

t = env.get_template("b50.html")


async def gen_b50(username: str, scores: MaimaiScores, matcher: Matcher) -> bytes:
    async def download_jacket(jacket_id: int):
        try:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(
                f"https://assets2.lxns.net/maimai/jacket/{jacket_id}.png"
            )
            response.raise_for_status()

            with open(f"resources/mai/mai/cover/{jacket_id}.png", "wb") as f:
                f.write(response.content)
        except Exception as e:
            logger.warning(f"封面下载失败 | 歌曲: {jacket_id} | 错误: {e}")

    async def check_resources():
        jacket_list = os.listdir("resources/mai/mai/cover")

        lost_jacket = []

        for i in score_mapping:
            if f"{i[0].id}.png" not in jacket_list:
                lost_jacket.append(i[0].id)

        if lost_jacket:
            await matcher.send(
                f"封面资源缺失，正在下载中，本次加载可能会慢一些...\n缺失的歌曲封面有{len(lost_jacket)}首"
            )

        tasks = []
        for i in lost_jacket:
            tasks.append(download_jacket(i))

        await asyncio.gather(*tasks)

    score_mapping: list[
        tuple[Song, SongDifficulty, ScoreExtend]
    ] = await scores.get_mapping()

    await check_resources()

    data = {
        "plateAsset": r"mai\pic\UI_Plate_300501.png",
        "iconAsset": r"mai\pic\UI_Icon_309503.png",
        "nickname": username,
        "rating": scores.rating,
        "standard_total": scores.rating_b35,
        "dx_total": scores.rating_b15,
        "standard": [
            {
                "song_id": i[0].id,
                "level": i[1].level_value,
                "jacket_url": f"mai/cover/{i[0].id}.png",
                "song_name": i[0].title,
                "dx_score": i[2].dx_score,
                "dx_rating": int(i[2].dx_rating),
                "fc": True if i[2].fc else False,
                "fc_icon": "mai/pic/UI_CHR_PlayBonus_FC.png",
                "fs": True if i[2].fs else False,
                "fs_icon": "mai/pic/UI_CHR_PlayBonus_FS.png",
                "rate_icon": f"mai/pic/UI_TTR_Rank_{i[2].rate.name}.png",
                "rate": i[2].rate.name,
                "achievements": i[2].achievements,
            }
            for i in score_mapping[:len(scores.scores_b35)]  # song songdiff ScoreExtend
        ],
        "dx": [
            {
                "song_id": i[0].id,
                "level": i[1].level_value,
                "jacket_url": f"mai/cover/{i[0].id}.png",
                "song_name": i[0].title,
                "dx_score": i[2].dx_score,
                "dx_rating": int(i[2].dx_rating),
                "fc": True if i[2].fc else False,
                "fc_icon": "mai/pic/UI_CHR_PlayBonus_FC.png",
                "fs": True if i[2].fs else False,
                "fs_icon": "mai/pic/UI_CHR_PlayBonus_FS.png",
                "rate_icon": f"mai/pic/UI_TTR_Rank_{i[2].rate.name}.png",
                "rate": i[2].rate.name,
                "achievements": i[2].achievements,
            }
            for i in score_mapping[len(scores.scores_b35):]  # song songdiff ScoreExtend
        ],
    }

    return await template_to_pic(
        template_path=str(Path(os.getcwd()) / "resources" / "mai"),
        template_name="b50.html",
        templates=data,
    )
