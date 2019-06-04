# coding: utf-8
__author__ = 'Jerry'
"公众号：Python编程与实战,欢迎关注点赞"

import requests
from scrapy import Selector

from pyecharts import options as opts
from pyecharts.charts import Line

from .mapping import verification, retire_verify


class Nba(object):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
    }

    @staticmethod
    def get_player(name):
        team = verification(name)

        if team:
            url = f"https://nba.hupu.com/players/{team}"
            response = requests.get(url)

            selector = Selector(text=response.text)

            player_list = selector.css(".players_table tr")[1:]
            player_dict = {}

            for player in player_list:
                player_dict[player.css("td")[1].css("b ::text").extract_first()] = player.css("td")[1].css(
                    "b ::attr(href)").extract_first().split("/")[-1]

            return player_dict
        else:
            return {"error": "请输入正确的球队"}

    @staticmethod
    def spider(**kwargs):
        url = kwargs.get("player")
        game = kwargs.get("game")
        color = kwargs.get("color", "")

        name = url.split("-")[0].capitalize()
        url = "https://nba.hupu.com/players/" + url
        try:
            response = requests.get(url)
            selector = Selector(text=response.text)

            career_data = selector.css("#in_box .all_tables_check .list_table_box.J_p_l")[1].css("table")[1].css(
                "tr") if game == "1" else selector.css("#in_box .all_tables_check .list_table_box.J_p_l").css("table")[
                1].css("tr")

            data_list = []

            for career in career_data[1:]:
                data = dict()
                for _ in range(18):
                    data[career_data[0].xpath(".//td/text()").extract()[_]] = career.xpath(".//td/text()").extract()[_]

                if data["球队"] == "汇总":  # 网站bug
                    continue

                del data["命中率"]

                data_list.append(data)

            return {"data_list": data_list, "name": name, "game": "季后赛" if game == "1" else "常规赛", "color": color}

        except Exception:
            return {"error": f"请输入正确的地址"}

    @staticmethod
    def line_base(l, name, game, color) -> Line:
        c = (
            Line(init_opts=opts.InitOpts(bg_color=color))
                .add_xaxis([y["赛季"] for y in l])
                .add_yaxis("得分", [y["得分"] for y in l], is_smooth=True,
                           markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]))
                .add_yaxis("篮板", [y["篮板"] for y in l], is_smooth=True,
                           markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]))
                .add_yaxis("助攻", [y["助攻"] for y in l], is_smooth=True,
                           markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]))
                .add_yaxis("抢断", [y["抢断"] for y in l], is_smooth=True,
                           markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]))
                # .add_yaxis("罚球", [y["罚球"].split('-')[1] for y in l], is_smooth=True,
                #            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]))
                .add_yaxis("失误", [y["失误"] for y in l], is_smooth=True,
                           markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]))
                .set_global_opts(title_opts=opts.TitleOpts(title=name, subtitle_textstyle_opts={"color": "red"},
                                                           subtitle=game), toolbox_opts=opts.ToolboxOpts())
        )
        return c

    def history_player(self, **kwargs):
        """
        已退役的球星
        :return:
        """
        name = kwargs.get("retire")
        game = kwargs.get("game")
        color = kwargs.get("color", "")

        number = retire_verify(name)
        if number:
            season = "playoff" if game == "1" else "season"
            url = f"http://www.stat-nba.com/player/stat_box/{number}_{season}.html"
            for _ in range(5):

                response = requests.get(url, headers=self.headers)
                if response.status_code != 200:
                    continue
                else:
                    break
            else:
                return {"error": "请联系公众号: Python编程与实战"}

            content = response.content
            selector = Selector(text=content.decode("utf-8"))

            data_list = []

            career_data = selector.css("#stat_box_avg tr.sort")
            for career in reversed(career_data):
                data = dict()
                th = selector.css("#stat_box_avg thead tr th")
                for i in range(len(th)-1):
                    result = career.css("td")[i + 1].css("::text").extract_first("")
                    data[th[i+1].css("::text").extract_first()] = \
                        career.css("td")[i + 1].css("a ::attr(href)").re_first("\d+") if i == 0 else result

                data_list.append(data)

            return {"data_list": data_list, "name": name, "game": "季后赛" if game == "1" else "常规赛", "color": color}

        else:
            return {"error": f"暂不支持退役球星{name}的查询，请联系公众号: Python编程与实战"}


if __name__ == '__main__':
    # n = Nba()
    # n.history_player()
    pass
