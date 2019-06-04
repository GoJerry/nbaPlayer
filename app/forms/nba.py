# coding: utf-8 
# @Time : 2019/5/29 16:37 
# @Author : Jerryning 
# @Site :  
# @File : nba.py 
# @Software: PyCharm
# 公众号：Python编程与实战

from wtforms import Form
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class GetTeamForm(Form):
    name = StringField("球队名称", validators=[InputRequired()])


class GetPlayerForm(Form):
    player = StringField("球员url", validators=[InputRequired()])
    game = StringField("比赛类型,0常规赛 1季后赛", validators=[InputRequired()])
    color = StringField("背景色")


class RetirePlayerForm(Form):
    retire = StringField("球员名称", validators=[InputRequired()])
    game = StringField("比赛类型,0常规赛 1季后赛", validators=[InputRequired()])
    color = StringField("背景色")


if __name__ == "__main__":
    pass
