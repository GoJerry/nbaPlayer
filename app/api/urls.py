# coding: utf-8
"""路由注册。URL 规则统一以 / 开头（Werkzeug 的要求）。"""
from . import views
from ..api import application

application.add_url_rule("/nba/team", view_func=views.GetTeam.as_view("getTeam"))
application.add_url_rule("/nba/player", view_func=views.Player.as_view("player"))
application.add_url_rule("/retire/player", view_func=views.RetirePlayer.as_view("retirePlayer"))
application.add_url_rule("/lineChart", view_func=views.Line.as_view("line"))
application.add_url_rule("/api/teams", view_func=views.Teams.as_view("teams"))
application.add_url_rule("/api/players/retired", view_func=views.RetiredPlayers.as_view("retiredPlayers"))
application.add_url_rule("/nba/player2", view_func=views.StatsPlayer.as_view("statsPlayer"))
application.add_url_rule("/api/analysis/player", view_func=views.PlayerAnalysis.as_view("playerAnalysis"))
application.add_url_rule("/api/analysis/compare", view_func=views.CompareApi.as_view("compareApi"))
application.add_url_rule("/compare", view_func=views.ComparePage.as_view("comparePage"))
application.add_url_rule("/api/sources", view_func=views.Sources.as_view("sources"))

if __name__ == "__main__":
    pass
