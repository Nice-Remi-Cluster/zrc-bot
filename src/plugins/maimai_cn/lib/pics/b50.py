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


# Rating等级映射函数
def _find_rating_level(rating: int) -> str:
    """根据Rating值返回对应的等级图标文件名"""
    if rating < 1000:
        return "mai/pic/UI_CMN_DXRating_01.png"
    elif rating < 2000:
        return "mai/pic/UI_CMN_DXRating_02.png"
    elif rating < 4000:
        return "mai/pic/UI_CMN_DXRating_03.png"
    elif rating < 7000:
        return "mai/pic/UI_CMN_DXRating_04.png"
    elif rating < 10000:
        return "mai/pic/UI_CMN_DXRating_05.png"
    elif rating < 12000:
        return "mai/pic/UI_CMN_DXRating_06.png"
    elif rating < 13000:
        return "mai/pic/UI_CMN_DXRating_07.png"
    elif rating < 14000:
        return "mai/pic/UI_CMN_DXRating_08.png"
    elif rating < 14500:
        return "mai/pic/UI_CMN_DXRating_09.png"
    elif rating < 15000:
        return "mai/pic/UI_CMN_DXRating_10.png"
    else:
        return "mai/pic/UI_CMN_DXRating_11.png"


# 段位等级映射函数
def _find_match_level(additional_rating: int) -> str:
    """根据段位等级数值返回对应的段位图标文件名"""
    if additional_rating <= 0:
        return "mai/pic/UI_DNM_DaniPlate_00.png"
    elif additional_rating <= 10:
        return f"mai/pic/UI_DNM_DaniPlate_{additional_rating:02d}.png"
    else:
        return f"mai/pic/UI_DNM_DaniPlate_{additional_rating + 1:02d}.png"


# DX Score星级评价函数
def _calc_dx_star(dx_score: int, total_notes: int) -> tuple[int, str]:
    """计算DX Score星级和对应图标"""
    if total_notes == 0:
        return 0, ""
    
    percentage = (dx_score / (total_notes * 3)) * 100
    
    if percentage >= 97:
        return 5, "mai/pic/UI_GAM_Gauge_DXScoreIcon_05.png"
    elif percentage >= 95:
        return 4, "mai/pic/UI_GAM_Gauge_DXScoreIcon_04.png"
    elif percentage >= 93:
        return 3, "mai/pic/UI_GAM_Gauge_DXScoreIcon_03.png"
    elif percentage >= 90:
        return 2, "mai/pic/UI_GAM_Gauge_DXScoreIcon_02.png"
    elif percentage >= 85:
        return 1, "mai/pic/UI_GAM_Gauge_DXScoreIcon_01.png"
    else:
        return 0, ""


# FC类型图标映射
def _get_fc_icon(fc_type: str) -> str:
    """根据FC类型返回对应图标路径"""
    fc_mapping = {
        "fc": "mai/pic/UI_MSS_MBase_Icon_FC.png",
        "fcp": "mai/pic/UI_MSS_MBase_Icon_FCp.png",
        "ap": "mai/pic/UI_MSS_MBase_Icon_AP.png",
        "app": "mai/pic/UI_MSS_MBase_Icon_APp.png"
    }
    return fc_mapping.get(fc_type.lower(), "")


# FS类型图标映射
def _get_fs_icon(fs_type: str) -> str:
    """根据FS类型返回对应图标路径"""
    fs_mapping = {
        "fs": "mai/pic/UI_MSS_MBase_Icon_FS.png",
        "fsp": "mai/pic/UI_MSS_MBase_Icon_FSp.png",
        "fsd": "mai/pic/UI_MSS_MBase_Icon_FSD.png",
        "fsdp": "mai/pic/UI_MSS_MBase_Icon_FSDp.png",
        "sync": "mai/pic/UI_MSS_MBase_Icon_Sync.png"
    }
    return fs_mapping.get(fs_type.lower(), "")


# 难度等级色彩映射
def _get_difficulty_colors(level_index: int) -> dict:
    """根据难度索引返回对应的色彩配置"""
    difficulty_colors = {
        0: {  # Basic
            "bg_color": "rgba(111, 212, 61, 1)",
            "text_color": "rgba(255, 255, 255, 1)",
            "id_color": "rgba(129, 217, 85, 1)",
            "bg_image": "mai/pic/b50_score_basic.png"
        },
        1: {  # Advanced
            "bg_color": "rgba(248, 183, 9, 1)",
            "text_color": "rgba(255, 255, 255, 1)",
            "id_color": "rgba(245, 189, 21, 1)",
            "bg_image": "mai/pic/b50_score_advanced.png"
        },
        2: {  # Expert
            "bg_color": "rgba(255, 129, 141, 1)",
            "text_color": "rgba(255, 255, 255, 1)",
            "id_color": "rgba(255, 129, 141, 1)",
            "bg_image": "mai/pic/b50_score_expert.png"
        },
        3: {  # Master
            "bg_color": "rgba(159, 81, 220, 1)",
            "text_color": "rgba(255, 255, 255, 1)",
            "id_color": "rgba(159, 81, 220, 1)",
            "bg_image": "mai/pic/b50_score_master.png"
        },
        4: {  # Re:Master
            "bg_color": "rgba(219, 170, 255, 1)",
            "text_color": "rgba(138, 0, 226, 1)",
            "id_color": "rgba(138, 0, 226, 1)",
            "bg_image": "mai/pic/b50_score_remaster.png"
        }
    }
    
    # 默认使用Master难度的配色
    return difficulty_colors.get(level_index, difficulty_colors[3])


# 获取notes数量的辅助函数
def _get_total_notes(difficulty: SongDifficulty) -> int:
    """
    根据SongDifficulty数据模型获取歌曲总note数
    根据maimai.py 1.3.5版本的实际数据结构
    """
    try:
        # 直接使用SongDifficulty的各种note数量属性
        total = (
            difficulty.tap_num +
            difficulty.hold_num +
            difficulty.slide_num +
            difficulty.touch_num +
            difficulty.break_num
        )
        
        if total > 0:
            return total
        
        # 如果各个属性都为0，使用level_dx_score属性（总DX分数除以3）
        return difficulty.level_dx_score // 3
        
    except Exception as e:
        logger.warning(f"获取notes数据时出错: {e}")
        return 800  # 安全默认值


# 版本图标映射
def _get_version_icon(song_type) -> str:
    """根据歌曲类型返回版本图标"""
    type_str = str(song_type) if song_type else "DX"
    return f"mai/pic/{type_str}.png" if type_str in ["DX", "SD"] else "mai/pic/DX.png"


# 自定义名牌检查函数
def _check_custom_plate(plate_name: str) -> str:
    """检查自定义名牌是否存在，如果存在返回路径，否则返回默认名牌"""
    if not plate_name:
        return ""
    
    custom_path = f"mai/plate/{plate_name}.png"
    full_path = f"resources/mai/{custom_path}"
    
    if os.path.exists(full_path):
        return custom_path
    return ""


# QQ头像获取函数
def _get_qq_avatar(qq_id: str) -> str:
    """根据QQ号获取头像路径，如果存在本地缓存则返回路径"""
    if not qq_id:
        return ""
    
    avatar_path = f"mai/avatar/{qq_id}.jpg"
    full_path = f"resources/mai/{avatar_path}"
    
    if os.path.exists(full_path):
        return avatar_path
    return ""


async def gen_b50(username: str, scores: MaimaiScores, matcher: Matcher, qq_id: str = "", custom_plate: str = "") -> bytes:
    """
    生成B50成绩单图片
    
    Args:
        username: 用户名
        scores: maimai.py的MaimaiScores对象
        matcher: NoneBot匹配器
        qq_id: QQ号（可选），用于获取头像
        custom_plate: 自定义名牌名称（可选）
    
    Returns:
        生成的图片字节流
    """
    try:
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
        
        # 计算用户信息相关数据
        rating_level = _find_rating_level(scores.rating)
        additional_rating = 0  # TODO: 从用户数据中获取段位等级
        match_level = _find_match_level(additional_rating)
        class_level = "mai/pic/UI_FBR_Class_00.png"  # TODO: 从用户数据中获取等级
        
        # 检查自定义图片
        custom_plate_path = _check_custom_plate(custom_plate)
        qq_avatar_path = _get_qq_avatar(qq_id)
        
        # 构建标准歌曲数据
        standard_songs = []
        for song, difficulty, score in score_mapping[:len(scores.scores_b35)]:

            total_notes = _get_total_notes(difficulty)
            dx_score = score.dx_score or 0
            dx_star_level, dx_star_icon = _calc_dx_star(dx_score, total_notes)
            dx_percentage = (dx_score / (total_notes * 3) * 100) if total_notes > 0 and dx_score else 0
            
            # 获取难度色彩配置
            # LevelIndex是枚举类型，需要获取其value
            level_idx = score.level_index.value if hasattr(score.level_index, 'value') else 0
            colors = _get_difficulty_colors(level_idx)
            
            # 获取FC/FS图标
            # FCType和FSType是枚举类型，需要获取其name属性
            fc_icon = _get_fc_icon(score.fc.name) if score.fc else ""
            fs_icon = _get_fs_icon(score.fs.name) if score.fs else ""
            
            # 获取版本图标
            version_icon = _get_version_icon(getattr(song, 'type', 'DX'))
            
            song_data = {
                "song_id": song.id,
                "level": score.level,
                "level_index": score.level_index.value if hasattr(score.level_index, 'value') else 0,
                "jacket_url": f"mai/cover/{song.id}.png",
                "song_name": song.title,
                "type": str(getattr(song, 'type', 'DX')),
                "version_icon": version_icon,
                "dx_score": dx_score,
                "total_notes": total_notes,
                "dx_percentage": dx_percentage,
                "dx_star_level": dx_star_level,
                "dx_star_icon": dx_star_icon,
                "dx_rating": int(score.dx_rating or 0),
                "fc": bool(score.fc),
                "fc_type": score.fc.name if score.fc else "",
                "fc_icon": fc_icon,
                "fs": bool(score.fs),
                "fs_type": score.fs.name if score.fs else "",
                "fs_icon": fs_icon,
                "rate_icon": f"mai/pic/UI_TTR_Rank_{score.rate.name}.png",
                "rate": score.rate.name,
                "achievements": f"{score.achievements:.4f}",
                "difficulty_bg": colors["bg_image"],
                "background_color": colors["bg_color"],
                "text_color": colors["text_color"],
                "id_color": colors["id_color"]
            }
            standard_songs.append(song_data)
        
        # 构建DX歌曲数据
        dx_songs = []
        for song, difficulty, score in score_mapping[len(scores.scores_b35):]:
            # 安全获取总notes数
            total_notes = _get_total_notes(difficulty)
            
            # 安全获取dx_score
            dx_score = score.dx_score if score.dx_score is not None else 0
            
            # 计算DX星级
            dx_star_level, dx_star_icon = _calc_dx_star(dx_score, total_notes)
            
            # 计算DX百分比
            dx_percentage = (dx_score / (total_notes * 3) * 100) if total_notes > 0 and dx_score > 0 else 0
            
            # 获取难度色彩配置
            level_idx = score.level_index.value if hasattr(score.level_index, 'value') else 0
            colors = _get_difficulty_colors(level_idx)
            
            # 获取FC/FS图标
            fc_icon = _get_fc_icon(score.fc.name) if score.fc else ""
            fs_icon = _get_fs_icon(score.fs.name) if score.fs else ""
            
            # 获取版本图标
            # Song对象可能没有type属性，使用默认值
            song_type = getattr(song, 'type', None)
            if song_type:
                song_type_str = song_type.name if hasattr(song_type, 'name') else str(song_type)
            else:
                song_type_str = "DX"  # 默认值
            version_icon = _get_version_icon(song_type_str)
            
            song_data = {
                "song_id": song.id,
                "level": score.level,
                "level_index": score.level_index.value if hasattr(score.level_index, 'value') else 0,
                "jacket_url": f"mai/cover/{song.id}.png",
                "song_name": song.title,
                "type": song_type_str,
                "version_icon": version_icon,
                "dx_score": dx_score,
                "total_notes": total_notes,
                "dx_percentage": dx_percentage,
                "dx_star_level": dx_star_level,
                "dx_star_icon": dx_star_icon,
                "dx_rating": int(score.dx_rating) if score.dx_rating is not None else 0,
                "fc": bool(score.fc),
                "fc_type": score.fc.name if score.fc else "",
                "fc_icon": fc_icon,
                "fs": bool(score.fs),
                "fs_type": score.fs.name if score.fs else "",
                "fs_icon": fs_icon,
                "rate_icon": f"mai/pic/UI_TTR_Rank_{score.rate.name}.png",
                "rate": score.rate.name,
                "achievements": f"{score.achievements:.4f}",
                "difficulty_bg": colors["bg_image"],
                "background_color": colors["bg_color"],
                "text_color": colors["text_color"],
                "id_color": colors["id_color"]
            }
            dx_songs.append(song_data)

        data = {
            # 用户基本信息
            "plateAsset": "mai/pic/UI_Plate_300501.png",
            "plateCustom": custom_plate_path,  # 支持自定义名牌
            "iconAsset": "mai/pic/UI_Icon_309503.png",
            "qqAvatar": qq_avatar_path,  # 支持QQ头像
            "nickname": username,
            "rating": scores.rating,
            "rating_level": rating_level,
            "match_level": match_level,
            "class_level": class_level,
            "standard_total": scores.rating_b35,
            "dx_total": scores.rating_b15,
            "additional_rating": additional_rating,
            
            # 背景和装饰元素
            "b50_bg": "mai/pic/b50_bg.png",
            "logo": "mai/pic/logo.png",
            "shougou_bg": "mai/pic/UI_CMN_Shougou_Rainbow.png",
            
            # 歌曲数据
            "standard": standard_songs,
            "dx": dx_songs,
        }

        return await template_to_pic(
            template_path=str(Path(os.getcwd()) / "resources" / "mai"),
            template_name="b50.html",
            templates=data,
        )
        
    except Exception as e:
        logger.error(f"B50生成失败: {e}")
     
        # 尝试使用简化数据生成错误报告
        error_data = {
            "plateAsset": "mai/pic/UI_Plate_300501.png",
            "plateCustom": "",
            "iconAsset": "mai/pic/UI_Icon_309503.png",
            "qqAvatar": "",
            "nickname": username,
            "rating": getattr(scores, 'rating', 0),
            "rating_level": "mai/pic/UI_CMN_DXRating_01.png",
            "match_level": "mai/pic/UI_DNM_DaniPlate_00.png",
            "class_level": "mai/pic/UI_FBR_Class_00.png",
            "standard_total": getattr(scores, 'rating_b35', 0),
            "dx_total": getattr(scores, 'rating_b15', 0),
            "additional_rating": 0,
            "b50_bg": "mai/pic/b50_bg.png",
            "logo": "mai/pic/logo.png",
            "shougou_bg": "mai/pic/UI_CMN_Shougou_Rainbow.png",
            "standard": [],
            "dx": [],
        }
        
        try:
            return await template_to_pic(
                template_path=str(Path(os.getcwd()) / "resources" / "mai"),
                template_name="b50.html",
                templates=error_data,
            )
        except Exception as final_error:
            logger.error(f"B50错误模板生成也失败: {final_error}")
            raise e  # 抛出原始错误
