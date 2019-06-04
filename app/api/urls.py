# coding: utf-8 
# @Time : 2019/5/29 16:41 
# @Author : Jerryning 
# @Site :  
# @File : urls.py 
# @Software: PyCharm
# 公众号：Python编程与实战

from . import views
from ..api import application

application.add_url_rule("nba/team", view_func=views.GetTeam.as_view("getTeam"))
application.add_url_rule("nba/player", view_func=views.Player.as_view("player"))
application.add_url_rule("retire/player", view_func=views.RetirePlayer.as_view("retirePlayer"))
application.add_url_rule("lineChart", view_func=views.Line.as_view("line"))

if __name__ == "__main__":
    pass
