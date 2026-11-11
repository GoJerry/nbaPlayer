# coding: utf-8
"""NBA 球员数据抓取与生涯曲线生成。

现役球员数据来自虎扑球员页，退役球星数据来自 stat-nba。
所有外发请求统一带超时，避免上游站点无响应时把请求挂死。
"""
__author__ = 'Jerry'

import requests
from scrapy import Selector

from pyecharts import options as opts
from pyecharts.charts import Line

from .mapping import verification, retire_verify

# 所有外发请求的统一超时（秒）
REQUEST_TIMEOUT = 10

# 曲线包含的五项场均指标
METRICS = ["得分", "篮板", "助攻", "抢断", "失误"]


def _to_number(value):
    """把表格里的字符串数字转成 float，转不了返回 None（图表留空）。"""
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def summarize_career(data_list):
    """根据逐赛季数据计算生涯概要。

    返回赛季数，以及得分/篮板/助攻的赛季场均平均值与得分巅峰赛季。
    数据缺失的字段自动跳过，不抛异常。
    """
    summary = {"seasons": len(data_list)}
    for key, prefix in (("得分", "points"), ("篮板", "rebounds"), ("助攻", "assists")):
        values = [_to_number(row.get(key)) for row in data_list]
        values = [v for v in values if v is not None]
        if not values:
            continue
        summary[f"{prefix}_avg"] = round(sum(values) / len(values), 1)
        if key == "得分":
            peak_idx = max(range(len(data_list)),
                           key=lambda i: _to_number(data_list[i].get(key)) or float("-inf"))
            summary["points_peak"] = _to_number(data_list[peak_idx].get(key))
            summary["points_peak_season"] = data_list[peak_idx].get("赛季", "")
    return summary


class Nba(object):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
    }

    @staticmethod
    def get_player(name):
        team = verification(name)

        if not team:
            return {"error": "请输入正确的球队"}

        url = f"https://nba.hupu.com/players/{team}"
        try:
            response = requests.get(url, headers=Nba.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException:
            return {"error": "球队数据获取失败，请稍后重试"}

        selector = Selector(text=response.text)

        player_list = selector.css(".players_table tr")[1:]
        player_dict = {}

        for player in player_list:
            player_dict[player.css("td")[1].css("b ::text").extract_first()] = player.css("td")[1].css(
                "b ::attr(href)").extract_first().split("/")[-1]

        return player_dict

    @staticmethod
    def spider(**kwargs):
        url = kwargs.get("player")
        game = kwargs.get("game")
        color = kwargs.get("color", "")

        name = url.split("-")[0].capitalize()
        url = "https://nba.hupu.com/players/" + url
        try:
            response = requests.get(url, headers=Nba.headers, timeout=REQUEST_TIMEOUT)
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

            return {"data_list": data_list, "name": name, "game": "季后赛" if game == "1" else "常规赛",
                    "color": color, "summary": summarize_career(data_list)}

        except Exception:
            return {"error": "请输入正确的地址"}

    @staticmethod
    def line_base(l, name, game, color) -> Line:
        c = (
            Line(init_opts=opts.InitOpts(bg_color=color, width="1000px", height="600px"))
                .add_xaxis([y.get("赛季", "") for y in l])
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=name, subtitle=game,
                                              subtitle_textstyle_opts={"color": "red"}),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    legend_opts=opts.LegendOpts(pos_top="8%"),
                    toolbox_opts=opts.ToolboxOpts(),
                    datazoom_opts=[opts.DataZoomOpts()],
                )
        )
        # 五项指标共用同一套画法，数值先转 float，缺失值留空而不是画成 0
        for metric in METRICS:
            c.add_yaxis(metric, [_to_number(y.get(metric)) for y in l], is_smooth=True,
                        markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]))
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
        if not number:
            return {"error": f"暂不支持退役球星{name}的查询，请联系公众号: Python编程与实战"}

        season = "playoff" if game == "1" else "season"
        url = f"http://www.stat-nba.com/player/stat_box/{number}_{season}.html"
        response = None
        for _ in range(5):
            try:
                response = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            except requests.RequestException:
                continue
            if response.status_code == 200:
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
            for i in range(len(th) - 1):
                result = career.css("td")[i + 1].css("::text").extract_first("")
                data[th[i + 1].css("::text").extract_first()] = \
                    career.css("td")[i + 1].css("a ::attr(href)").re_first(r"\d+") if i == 0 else result

            data_list.append(data)

        return {"data_list": data_list, "name": name, "game": "季后赛" if game == "1" else "常规赛",
                "color": color, "summary": summarize_career(data_list)}


if __name__ == '__main__':
    pass
