# -*- coding: utf-8 -*-
"""HTTP 接口层。

约定：JSON 接口统一返回 {"code", "data", "message"}，且 HTTP 状态码
与 body 里的 code 保持一致（参数错误/处理失败为 400）。
"""
import json

from flask import jsonify, render_template, request
from flask.views import MethodView
from werkzeug.datastructures import ImmutableMultiDict

from app.forms import GetPlayerForm, GetTeamForm, RetirePlayerForm
from app.spider.mapping import all_retired_players, all_teams
from app.spider.nba import Nba


def _error(message="参数错误", data=None):
    return jsonify(code=400, data=data or {}, message=message), 400


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


if __name__ == "__main__":
    pass
