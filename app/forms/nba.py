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


if __name__ == "__main__":
    pass
