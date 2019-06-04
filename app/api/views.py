# -*- coding: utf-8 -*-
# @Time : 2019/5/29 16:33 
# @Author : Jerryning 
# @Site :  
# @File : nba.py 
# @Software: PyCharm
# 公众号：Python编程与实战

from flask.views import MethodView
from flask import jsonify
from flask import request
from werkzeug.datastructures import ImmutableMultiDict
from flask import render_template

from app.forms import GetTeamForm, GetPlayerForm, RetirePlayerForm
from app.spider.nba import Nba


class GetTeam(MethodView):

    @staticmethod
    def get():
        args = request.args.to_dict()
        f = GetTeamForm(ImmutableMultiDict(args))
        if f.validate():
            team = args["name"]
            spider = Nba()
            result = spider.get_player(team)
            return jsonify(code=200, data=result, message="成功")
        else:
            return jsonify(code=400, data={}, message="参数错误")


class Player(MethodView):

    @staticmethod
    def get():
        kwargs = request.args.to_dict()
        f = GetPlayerForm(ImmutableMultiDict(kwargs))
        if f.validate():

            spider = Nba()
            data = spider.spider(**kwargs)
            if data.get("error"):
                return jsonify(code=400, data=data, message="失败")
            return render_template("player.html", result_json=data)
        else:
            return jsonify(code=400, data={}, message="参数错误")


class Line(MethodView):

    @staticmethod
    def get():
        args = request.args.to_dict()
        result = eval(args.get("result"))
        data_list = result.get("data_list")
        name = result.get("name")
        game = result.get("game")
        color = result.get("color", "")
        spider = Nba()
        line = spider.line_base(data_list, name, game, color)
        return line.dump_options()


class RetirePlayer(MethodView):
    @staticmethod
    def get():
        kwargs = request.args.to_dict()
        f = RetirePlayerForm(ImmutableMultiDict(kwargs))
        if f.validate():
            spider = Nba()
            data = spider.history_player(**kwargs)
            if data.get("error"):
                return jsonify(code=400, data=data, message="失败")

            return render_template("player.html", result_json=data)
        else:
            return jsonify(code=400, data={}, message="参数错误")


if __name__ == "__main__":
    pass
