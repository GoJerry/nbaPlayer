# coding: utf-8
"""生涯数据分析：趋势、巅峰窗口、最大涨跌、稳定性、双人对比与对比图。

全部基于内部 data_list（逐赛季场均）做本地计算，不访问网络，
因此 nba_api 官方数据源与虎扑 / stat-nba 两种 legacy 数据都能共用。
"""
__author__ = 'Jerry'

import json
import math
import statistics

from pyecharts import options as opts
from pyecharts.charts import Line, Radar

from .spider.nba import METRICS, _to_number, summarize_career


def _series(data_list, metric):
    """取出某指标的 (赛季, 数值) 序列，缺失值跳过。"""
    pairs = []
    for row in data_list:
        value = _to_number(row.get(metric))
        if value is not None:
            pairs.append((row.get("赛季", ""), value))
    return pairs


def _average(data_list, metric):
    values = [v for _, v in _series(data_list, metric)]
    return round(sum(values) / len(values), 1) if values else None


def _slope(values):
    """最小二乘斜率：平均每个赛季该指标变化多少。"""
    n = len(values)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    numerator = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
    denominator = sum((i - mean_x) ** 2 for i in range(n))
    return numerator / denominator if denominator else 0.0


def analyze_career(data_list, metric="得分"):
    """单人深度分析。返回字典，数据不足的字段自动省略。

    - trend / points_slope：得分趋势标签与每季斜率（>=0.3 上升，<=-0.3 下滑）
    - prime_window：连续 3 个赛季（不足 3 季取全部）场均得分最高的窗口
    - biggest_jump / biggest_drop：得分单季最大涨幅与跌幅（含起止赛季）
    - stability / points_std / points_cv：得分变异系数与稳定性标签
    - career_highs：五项指标各自的单季最高值及所在赛季
    """
    analysis = {}
    pairs = _series(data_list, metric)
    values = [v for _, v in pairs]

    if len(values) >= 2:
        slope = _slope(values)
        analysis["points_slope"] = round(slope, 2)
        analysis["trend"] = "上升" if slope >= 0.3 else "下滑" if slope <= -0.3 else "平稳"

        window = min(3, len(values))
        best_start = max(range(len(values) - window + 1),
                         key=lambda i: sum(values[i:i + window]))
        analysis["prime_window"] = {
            "seasons": f"{pairs[best_start][0]} ~ {pairs[best_start + window - 1][0]}",
            "points_avg": round(sum(values[best_start:best_start + window]) / window, 1),
            "size": window,
        }

        diffs = [(pairs[i + 1][1] - pairs[i][1], pairs[i][0], pairs[i + 1][0])
                 for i in range(len(values) - 1)]
        jump = max(diffs)
        drop = min(diffs)
        analysis["biggest_jump"] = {"from_season": jump[1], "to_season": jump[2],
                                    "delta": round(jump[0], 1)}
        analysis["biggest_drop"] = {"from_season": drop[1], "to_season": drop[2],
                                    "delta": round(drop[0], 1)}

    if len(values) >= 3:
        mean = sum(values) / len(values)
        std = statistics.pstdev(values)
        cv = std / mean if mean else 0.0
        analysis["points_std"] = round(std, 1)
        analysis["points_cv"] = round(cv, 2)
        analysis["stability"] = "稳定" if cv < 0.15 else "一般" if cv < 0.3 else "波动大"

    highs = {}
    for m in METRICS:
        m_pairs = _series(data_list, m)
        if m_pairs:
            season, value = max(m_pairs, key=lambda p: p[1])
            highs[m] = {"value": value, "season": season}
    if highs:
        analysis["career_highs"] = highs
    return analysis


def compare_careers(name_a, data_a, name_b, data_b):
    """双人对比：五项指标的生涯赛季场均、差值与领先者，外加双方概要。"""
    rows = []
    for metric in METRICS:
        avg_a, avg_b = _average(data_a, metric), _average(data_b, metric)
        if avg_a is None or avg_b is None:
            leader, diff = "", None
        elif avg_a == avg_b:
            leader, diff = "持平", 0.0
        else:
            leader = name_a if avg_a > avg_b else name_b
            diff = round(avg_a - avg_b, 1)
        rows.append({"metric": metric, "player1_avg": avg_a, "player2_avg": avg_b,
                     "diff": diff, "leader": leader})
    return {
        "player1": name_a,
        "player2": name_b,
        "metrics": rows,
        "summary1": summarize_career(data_a),
        "summary2": summarize_career(data_b),
    }


def build_compare_charts(name_a, data_a, name_b, data_b):
    """生成对比图的 pyecharts 配置（JSON 字符串），供对比页直接渲染。

    折线图按「生涯第 N 年」对齐两人得分（生涯长度不同时短的留空），
    避免直接按赛季年份比对年龄差异；雷达图为五项指标生涯场均。
    """
    points_a = [v for _, v in _series(data_a, "得分")]
    points_b = [v for _, v in _series(data_b, "得分")]
    years = max(len(points_a), len(points_b))
    pad = lambda seq: seq + [None] * (years - len(seq))
    line = (
        Line(init_opts=opts.InitOpts(width="1000px", height="500px"))
        .add_xaxis([f"第{i + 1}年" for i in range(years)])
        .add_yaxis(name_a, pad(points_a), is_smooth=True)
        .add_yaxis(name_b, pad(points_b), is_smooth=True)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=f"{name_a} vs {name_b}", subtitle="逐年场均得分（按生涯年份对齐）"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            legend_opts=opts.LegendOpts(pos_top="8%"),
            datazoom_opts=[opts.DataZoomOpts()],
        )
    )

    avg_a = [_average(data_a, m) or 0 for m in METRICS]
    avg_b = [_average(data_b, m) or 0 for m in METRICS]
    schema = [opts.RadarIndicatorItem(name=m, max_=max(1, math.ceil(max(a, b) * 1.3)))
              for m, a, b in zip(METRICS, avg_a, avg_b)]
    radar = (
        Radar(init_opts=opts.InitOpts(width="700px", height="500px"))
        .add_schema(schema=schema)
        .add(name_a, [avg_a], label_opts=opts.LabelOpts(is_show=False))
        .add(name_b, [avg_b], label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(title_opts=opts.TitleOpts(title="生涯场均五维对比"),
                         legend_opts=opts.LegendOpts(pos_bottom="0%"))
    )
    return json.loads(line.dump_options()), json.loads(radar.dump_options())
