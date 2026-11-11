# coding: utf-8
"""请求参数校验。game 只能是 0（常规赛）或 1（季后赛）。"""
from wtforms import Form
from wtforms.fields import StringField
from wtforms.validators import AnyOf, InputRequired

GAME_VALIDATORS = [InputRequired(),
                   AnyOf(["0", "1"], message="比赛类型只能是 0（常规赛）或 1（季后赛）")]


class GetTeamForm(Form):
    name = StringField("球队名称", validators=[InputRequired()])


class GetPlayerForm(Form):
    player = StringField("球员url", validators=[InputRequired()])
    game = StringField("比赛类型,0常规赛 1季后赛", validators=GAME_VALIDATORS)
    color = StringField("背景色")


class RetirePlayerForm(Form):
    retire = StringField("球员名称", validators=[InputRequired()])
    game = StringField("比赛类型,0常规赛 1季后赛", validators=GAME_VALIDATORS)
    color = StringField("背景色")


class StatsPlayerForm(Form):
    """官方数据源（nba_api）按英文全名查询。"""
    name = StringField("球员英文全名", validators=[InputRequired()])
    game = StringField("比赛类型,0常规赛 1季后赛", validators=GAME_VALIDATORS)
    color = StringField("背景色")


class CompareForm(Form):
    """双人对比：两位球员的英文全名。"""
    player1 = StringField("球员一英文全名", validators=[InputRequired()])
    player2 = StringField("球员二英文全名", validators=[InputRequired()])
    game = StringField("比赛类型,0常规赛 1季后赛", validators=GAME_VALIDATORS)


if __name__ == "__main__":
    pass
