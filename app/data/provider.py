# coding: utf-8
"""数据源 provider 层：把外部数据源统一成项目内部的数据结构。

内部结构与爬虫版保持一致，视图与模板无需区分数据来自哪里：
    {"data_list": [{赛季, 球队, 出场, 得分, ...}], "name": ..., "game": ...,
     "color": ..., "summary": {...}, "source": "nba_api"}

当前实现官方数据源 stats.nba.com（通过开源库 nba_api 访问，无需密钥）；
虎扑 / stat-nba 爬虫保留在 app/spider 中作为 legacy 数据源。

注意（选型调研结论，详见 README「数据源说明」）：
- stats.nba.com 对部分机房 IP 段不响应且有限流，因此这里带进程内缓存
  （默认 1 小时），并支持用环境变量走代理：
    NBA_API_TIMEOUT  单次请求超时秒数，默认 30
    NBA_API_PROXY    代理地址，如 http://127.0.0.1:7890，默认不走代理
    NBA_API_CACHE_TTL 缓存秒数，默认 3600
- 球员 ID 查找走 nba_api 的静态名单（本地数据，不发网络请求）。
"""
__author__ = 'Jerry'

import os
import threading
import time

from app.spider.nba import summarize_career


class DataSourceError(Exception):
    """数据源不可用（超时、上游无响应等），视图层据此返回 502。"""


class PlayerNotFoundError(DataSourceError):
    """静态名单里查不到该球员，视图层据此返回 400。"""


# stats.nba.com 字段 -> 项目内部中文字段
FIELD_MAP = [
    ("SEASON_ID", "赛季"),
    ("TEAM_ABBREVIATION", "球队"),
    ("GP", "出场"),
    ("GS", "首发"),
    ("MIN", "时间"),
    ("PTS", "得分"),
    ("REB", "篮板"),
    ("AST", "助攻"),
    ("STL", "抢断"),
    ("BLK", "盖帽"),
    ("TOV", "失误"),
    ("FG_PCT", "投篮命中率"),
    ("FG3_PCT", "三分命中率"),
    ("FT_PCT", "罚球命中率"),
    ("PF", "犯规"),
]

_PCT_FIELDS = {"FG_PCT", "FG3_PCT", "FT_PCT"}

_cache = {}
_cache_lock = threading.Lock()


def _env_int(name, default):
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _clean(value):
    """把 pandas/numpy 的标量转成原生 Python 类型，便于 JSON 序列化。"""
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            return value
    return value


def _format(en_key, value):
    value = _clean(value)
    if value is None:
        return ""
    if en_key in _PCT_FIELDS:
        try:
            return round(float(value), 3)
        except (TypeError, ValueError):
            return value
    if isinstance(value, float):
        return round(value, 1)
    return value


def _find_player(name):
    """在 nba_api 静态名单里按英文全名找球员（本地查找，不发请求）。"""
    from nba_api.stats.static import players as static_players

    matches = static_players.find_players_by_full_name(name)
    if not matches:
        raise PlayerNotFoundError(f"未找到球员：{name}（请使用英文全名，如 LeBron James）")
    lowered = name.strip().lower()
    for match in matches:
        if match["full_name"].lower() == lowered:
            return match
    return matches[0]


def _request_frames(player_id):
    """实际请求 stats.nba.com（无缓存），返回常规赛/季后赛两个表。"""
    from nba_api.stats.endpoints import PlayerCareerStats

    timeout = _env_int("NBA_API_TIMEOUT", 30)
    proxy = os.environ.get("NBA_API_PROXY") or None
    try:
        career = PlayerCareerStats(player_id=player_id, per_mode36="PerGame",
                                   timeout=timeout, proxy=proxy)
        return {
            "regular": career.season_totals_regular_season.get_data_frame(),
            "postseason": career.season_totals_post_season.get_data_frame(),
        }
    except Exception as exc:  # nba_api 对网络错误抛的异常类型不统一
        raise DataSourceError(f"官方数据源请求失败：{type(exc).__name__}: {exc}") from exc


def _fetch_frames(player_id):
    """带进程内缓存地拉逐赛季表：一次请求同时拿到常规赛与季后赛两个表，

    所以按球员 ID 缓存整包，默认 1 小时（NBA_API_CACHE_TTL 可调）。
    """
    ttl = _env_int("NBA_API_CACHE_TTL", 3600)
    now = time.time()
    with _cache_lock:
        hit = _cache.get(player_id)
        if hit and now - hit[0] < ttl:
            return hit[1]
    frames = _request_frames(player_id)
    with _cache_lock:
        _cache[player_id] = (now, frames)
    return frames


def _convert(frame):
    """把 stats.nba.com 的逐赛季表转成内部 data_list。

    同一赛季中途换队时上游会给多行（含一行 TEAM_ABBREVIATION=TOT 的
    合计行），这里按赛季去重、优先保留 TOT 行，和虎扑「汇总」行的
    处理口径一致。
    """
    if frame is None or len(frame) == 0:
        return []
    by_season = {}
    for row in frame.to_dict("records"):
        season = _clean(row.get("SEASON_ID"))
        data = {zh: _format(en, row.get(en)) for en, zh in FIELD_MAP if en in row}
        if season not in by_season or row.get("TEAM_ABBREVIATION") == "TOT":
            by_season[season] = data
    return [by_season[season] for season in sorted(by_season)]


def get_career_by_name(name, game="0", color=""):
    """按英文全名查球员逐赛季场均数据（官方数据源）。

    game: "0" 常规赛 / "1" 季后赛。查不到球员抛 PlayerNotFoundError，
    上游不可用抛 DataSourceError，该类别无数据时同样抛 DataSourceError。
    """
    player = _find_player(name)
    frames = _fetch_frames(player["id"])
    data_list = _convert(frames["postseason" if game == "1" else "regular"])
    game_label = "季后赛" if game == "1" else "常规赛"
    if not data_list:
        raise DataSourceError(f"{player['full_name']} 暂无{game_label}数据")
    return {
        "data_list": data_list,
        "name": player["full_name"],
        "game": game_label,
        "color": color,
        "summary": summarize_career(data_list),
        "source": "nba_api",
        "player_id": player["id"],
    }
