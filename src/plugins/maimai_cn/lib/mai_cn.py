from nonebot import logger
import httpx
from maimai_py import (
    DivingFishProvider,
    FCType,
    FSType,
    LevelIndex,
    LXNSProvider,
    MaimaiClient,
    RateType,
    SongType,
)
from maimai_py.models import Score as MaimaiPyScore
from maimai_py.utils import ScoreCoefficient
from nonebot import get_plugin_config
from wahlap_mai_ass_expander import MaiSimClient
from wahlap_mai_ass_expander.model import Score as MaiCNScore

from ..config import Config

config = get_plugin_config(Config)

maimai_py_client = MaimaiClient()
divingfish_provider = DivingFishProvider(
    developer_token=config.diving_fish_developer_token
)
lxns_provider = LXNSProvider(developer_token=config.lxns_developer_token)


async def mai_cn_score_to_maimaipy(
    maicn_scores: list[MaiCNScore],
) -> list[MaimaiPyScore]:
    """
    将maimaicn的成绩格式转换为maimai.py用格式
    """
    songs_info = await maimai_py_client.songs(provider=lxns_provider)
    scores = []

    for i in maicn_scores:
        music_id = i["musicId"]
        level = i["level"]
        achievement = i["achievement"]
        combo_status = i["comboStatus"]
        sync_status = i["syncStatus"]
        deluxscore_max = i["deluxscoreMax"]
        i["scoreRank"]
        play_count = i["playCount"]

        song_info = await songs_info.by_id(
            music_id % 10000 if music_id < 100000 else music_id
        )
        if song_info is None:
            continue
        song_type = (
            SongType.UTAGE
            if music_id > 100000
            else SongType.STANDARD
            if music_id < 10000
            else SongType.DX
        )
        # 添加边界检查，防止 IndexError
        level_index_list = list(LevelIndex)
        if level < 0 or level >= len(level_index_list):
            # 如果 level 超出范围，跳过这个成绩
            continue
        song_level_index = level_index_list[level]
        song_difficulty = song_info.get_difficulty(song_type, song_level_index)

        if not song_difficulty:
            logger.exception(f"未找到{song_type} {song_level_index}的难度")
            raise ValueError(f"转换出错, {song_info}")

        scores.append(
            MaimaiPyScore(
                id=music_id % 10000 if music_id < 100000 else music_id,
                level=song_difficulty.level,
                level_index=song_level_index,
                achievements=achievement / 10000,
                fc=[None, FCType.FC, FCType.FCP, FCType.AP, FCType.APP][combo_status],
                fs=[None, FSType.FS, FSType.FSP, FSType.FSD, FSType.FSDP, FSType.SYNC][
                    sync_status
                ],
                dx_score=deluxscore_max,
                dx_rating=ScoreCoefficient(achievement / 10000).ra(level),
                play_count=play_count,
                rate=RateType._from_achievement(achievement / 10000),
                type=song_type,
            )
        )
    return scores


def mai_client_constructor():
    httpx_client = None

    if config.maimai_arcade_proxy_host:
        httpx_client = httpx.AsyncClient(
            proxy=f"http://{config.maimai_arcade_proxy_username}:{config.maimai_arcade_proxy_password}@{config.maimai_arcade_proxy_host}:{config.maimai_arcade_proxy_port}",
        )

    return MaiSimClient(
        chip_id=config.maimai_arcade_chip_id,
        aes_key=config.maimai_arcade_aes_key,
        aes_iv=config.maimai_arcade_aes_iv,
        obfuscate_param=config.maimai_arcade_obfuscate_param,
        httpx_client=httpx_client,
    )


async def get_maimai_uid(qr_code: str):
    resp = await mai_client_constructor().qr_scan(qr_code)
    return resp["userID"]


async def get_maimai_user_all_score(user_id: int):
    resp = await mai_client_constructor().get_user_full_music_detail(user_id)
    return resp


async def get_maimai_user_preview_info(user_id: int):
    resp = await mai_client_constructor().get_user_preview_info(user_id)
    return resp
