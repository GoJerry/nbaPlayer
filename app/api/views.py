# -*- coding: utf-8 -*-
"""HTTP 接口层。

约定：JSON 接口统一返回 {"code", "data", "message"}，且 HTTP 状态码
与 body 里的 code 保持一致（参数错误/处理失败为 400）。
"""
import json

from flask import jsonify, render_template, request
from flask.views import MethodView
from werkzeug.datastructures import ImmutableMultiDict

from app.analysis import analyze_career, build_compare_charts, compare_careers
from app.data.provider import DataSourceError, PlayerNotFoundError, get_career_by_name
from app.forms import (CompareForm, GetPlayerForm, GetTeamForm,
                       RetirePlayerForm, StatsPlayerForm)
from app.spider.mapping import all_retired_players, all_teams
from app.spider.nba import Nba


def _error(message="参数错误", data=None):
    return jsonify(code=400, data=data or {}, message=message), 400


def _upstream_error(message):
    """上游数据源不可用（网络被封/超时等），与参数错误区分开。"""
    return jsonify(code=502, data={}, message=message), 502


def _fetch_stats_player(name, game, color=""):
    """查官方数据源并附带分析。返回 (result, error_response)，二者取一。"""
    try:
        result = get_career_by_name(name, game, color)
    except PlayerNotFoundError as exc:
        return None, _error(message=str(exc))
    except DataSourceError as exc:
        return None, _upstream_error(str(exc))
    result["analysis"] = analyze_career(result["data_list"])
    return result, None


class GetTeam(MethodView):
    """GET /nba/team?name=湖人 -> 球队现役球员名单"""

    @staticmethod
    def get():
        args = request.args.to_dict()
        form = GetTeamForm(ImmutableMultiDict(args))
        if not form.validate():
            return _error()
        spider = Nba()
        result = spider.get_player(args["name"])
        if isinstance(result, dict) and result.get("error"):
            return _error(message="失败", data=result)
        return jsonify(code=200, data=result, message="成功")


class Player(MethodView):
    """GET /nba/player?player=lebronjames-650.html&game=0 -> 球员生涯曲线页"""

    @staticmethod
    def get():
        kwargs = request.args.to_dict()
        form = GetPlayerForm(ImmutableMultiDict(kwargs))
        if not form.validate():
            return _error()
        spider = Nba()
        data = spider.spider(**kwargs)
        if data.get("error"):
            return _error(message="失败", data=data)
        data["analysis"] = analyze_career(data["data_list"])
        return render_template("player.html", result_json=data)


class RetirePlayer(MethodView):
    """GET /retire/player?retire=乔丹&game=1 -> 退役球星生涯曲线页"""

    @staticmethod
    def get():
        kwargs = request.args.to_dict()
        form = RetirePlayerForm(ImmutableMultiDict(kwargs))
        if not form.validate():
            return _error()
        spider = Nba()
        data = spider.history_player(**kwargs)
        if data.get("error"):
            return _error(message="失败", data=data)
        data["analysis"] = analyze_career(data["data_list"])
        return render_template("player.html", result_json=data)


class Line(MethodView):
    """GET /lineChart?result=<JSON> -> pyecharts 曲线配置。

    result 由 player.html 把 result_json 原样回传。历史上这里用 eval()
    解析，等于对任意访客开放远程代码执行；现改为 json.loads，
    解析失败或结构不对直接 400。
    """

    @staticmethod
    def get():
        raw = request.args.get("result", "")
        try:
            result = json.loads(raw)
        except (TypeError, ValueError):
            return _error(message="result 不是合法的 JSON")
        if not isinstance(result, dict) or not isinstance(result.get("data_list"), list):
            return _error(message="result 缺少 data_list")
        spider = Nba()
        line = spider.line_base(result["data_list"], result.get("name", ""),
                                result.get("game", ""), result.get("color", ""))
        return line.dump_options()


class Teams(MethodView):
    """GET /api/teams -> 全部支持的球队（中文名 -> 虎扑 slug）"""

    @staticmethod
    def get():
        return jsonify(code=200, data=all_teams(), message="成功")


class RetiredPlayers(MethodView):
    """GET /api/players/retired -> 全部支持查询的退役球星"""

    @staticmethod
    def get():
        return jsonify(code=200, data=all_retired_players(), message="成功")


class StatsPlayer(MethodView):
    """GET /nba/player2?name=LeBron James&game=0 -> 官方数据源生涯曲线页。

    与 /nba/player 的区别：按英文全名查询，数据来自 stats.nba.com
    （经 nba_api），覆盖现役与历史球员，不依赖虎扑页面结构。
    """

    @staticmethod
    def get():
        kwargs = request.args.to_dict()
        form = StatsPlayerForm(ImmutableMultiDict(kwargs))
        if not form.validate():
            return _error()
        result, error = _fetch_stats_player(kwargs["name"], kwargs["game"],
                                            kwargs.get("color", ""))
        if error:
            return error
        return render_template("player.html", result_json=result)


class PlayerAnalysis(MethodView):
    """GET /api/analysis/player?name=LeBron James&game=0 -> 数据 + 概要 + 分析（JSON）"""

    @staticmethod
    def get():
        kwargs = request.args.to_dict()
        form = StatsPlayerForm(ImmutableMultiDict(kwargs))
        if not form.validate():
            return _error()
        result, error = _fetch_stats_player(kwargs["name"], kwargs["game"])
        if error:
            return error
        return jsonify(code=200, data=result, message="成功")


class CompareApi(MethodView):
    """GET /api/analysis/compare?player1=&player2=&game=0 -> 双人对比（JSON）"""

    @staticmethod
    def get():
        kwargs = request.args.to_dict()
        form = CompareForm(ImmutableMultiDict(kwargs))
        if not form.validate():
            return _error()
        first, error = _fetch_stats_player(kwargs["player1"], kwargs["game"])
        if error:
            return error
        second, error = _fetch_stats_player(kwargs["player2"], kwargs["game"])
        if error:
            return error
        data = compare_careers(first["name"], first["data_list"],
                               second["name"], second["data_list"])
        data["game"] = first["game"]
        data["source"] = "nba_api"
        data["analysis1"] = first["analysis"]
        data["analysis2"] = second["analysis"]
        return jsonify(code=200, data=data, message="成功")


class ComparePage(MethodView):
    """GET /compare?player1=LeBron James&player2=Stephen Curry&game=0 -> 双人对比页"""

    @staticmethod
    def get():
        kwargs = request.args.to_dict()
        form = CompareForm(ImmutableMultiDict(kwargs))
        if not form.validate():
            return _error()
        first, error = _fetch_stats_player(kwargs["player1"], kwargs["game"])
        if error:
            return error
        second, error = _fetch_stats_player(kwargs["player2"], kwargs["game"])
        if error:
            return error
        comparison = compare_careers(first["name"], first["data_list"],
                                     second["name"], second["data_list"])
        line_options, radar_options = build_compare_charts(
            first["name"], first["data_list"], second["name"], second["data_list"])
        return render_template("compare.html", comparison=comparison,
                               line_options=line_options, radar_options=radar_options,
                               analysis1=first["analysis"], analysis2=second["analysis"],
                               game=first["game"])


class Sources(MethodView):
    """GET /api/sources -> 当前接入的数据源清单与各自的角色"""

    @staticmethod
    def get():
        sources = [
            {
                "id": "nba_api",
                "name": "stats.nba.com（经开源库 nba_api）",
                "role": "主数据源",
                "auth": "无需密钥",
                "coverage": "现役与历史球员逐赛季常规赛/季后赛场均",
                "endpoints": ["/nba/player2", "/api/analysis/player",
                              "/api/analysis/compare", "/compare"],
                "notes": "stats.nba.com 对部分机房 IP 不响应且有限流；provider 内置 "
                         "1 小时进程内缓存，可用 NBA_API_PROXY 走代理、NBA_API_TIMEOUT 调超时",
            },
            {
                "id": "hupu",
                "name": "虎扑 NBA",
                "role": "legacy（现役球员名单与曲线）",
                "auth": "无需密钥",
                "coverage": "现役球员逐赛季数据",
                "endpoints": ["/nba/team", "/nba/player"],
                "notes": "页面结构变化时可能失效",
            },
            {
                "id": "stat-nba",
                "name": "stat-nba",
                "role": "legacy（退役球星）",
                "auth": "无需密钥",
                "coverage": "14 位退役球星逐赛季数据",
                "endpoints": ["/retire/player"],
                "notes": "页面结构变化时可能失效",
            },
        ]
        return jsonify(code=200, data=sources, message="成功")


if __name__ == "__main__":
    pass
