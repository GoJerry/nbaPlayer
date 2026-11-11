# nbaPlayer

用 Python 自动生成 NBA 球员生涯数据曲线：将爬虫和 pyecharts 集成到 Flask 中，生成球员逐赛季得分 / 篮板 / 助攻 / 抢断 / 失误曲线，并给出赛季数、生涯场均与得分巅峰赛季等概要数据。

## 功能

1. 现役球员：30 支球队的球员名单查询，以及任意现役球员常规赛 / 季后赛生涯曲线
2. 历史巨星：14 位退役球星（乔丹、科比、姚明等）的常规赛 / 季后赛生涯曲线
3. 生涯概要：赛季数、场均得分 / 篮板 / 助攻、得分巅峰赛季，曲线下方附逐赛季数据表
4. 图表支持缩放（dataZoom）、图例、十字线提示，可通过 `color` 参数设置背景色
5. 发现接口：`/api/teams` 与 `/api/players/retired` 返回全部支持的球队与退役球星

## 快速开始

```bash
pip install -r requirements.txt
python run.py            # 默认监听 0.0.0.0:5800，可用 HOST/PORT 覆盖
```

本地调试可设置 `NBA_DEBUG=1`（默认关闭 DEBUG）。

## 接口一览

| 接口 | 说明 | 示例 |
| --- | --- | --- |
| `GET /` | 首页（含快速开始链接） |  |
| `GET /nba/team?name=湖人` | 某球队现役球员名单（JSON） | 返回 球员名 -> 虎扑球员页 slug |
| `GET /nba/player?player=lebronjames-650.html&game=0` | 现役球员生涯曲线页 | `player` 取自球队名单接口的返回值 |
| `GET /retire/player?retire=乔丹&game=1` | 退役球星生涯曲线页 |  |
| `GET /api/teams` | 全部支持的球队（JSON） | 30 支 |
| `GET /api/players/retired` | 全部支持的退役球星（JSON） | 14 位 |
| `GET /lineChart?result=<JSON>` | pyecharts 曲线配置（由球员页前端调用） | `result` 必须是合法 JSON |

参数：`game` 0 = 常规赛、1 = 季后赛（其他值会返回 400）；`color` 可选，如 `color=%23f5f5f5`。

JSON 接口统一返回 `{"code", "data", "message"}`，HTTP 状态码与 `code` 一致。

以湖人詹姆斯为例：先打开 `http://127.0.0.1:5800/nba/team?name=湖人` 拿到球员 slug，
再访问 `http://127.0.0.1:5800/nba/player?player=lebronjames-650.html&game=0` 查看曲线。

## 项目结构

```
├── run.py               # 启动入口（HOST/PORT 环境变量）
├── config/              # 配置（NBA_DEBUG=1 开启调试）
├── app/
│   ├── api/             # 路由与视图
│   ├── forms/           # 参数校验（WTForms）
│   ├── spider/          # 虎扑 / stat-nba 抓取、球队与球星映射、曲线与概要计算
│   └── templates/       # 首页与球员曲线页
└── requirements.txt
```

数据来源：现役球员来自虎扑 NBA，退役球星来自 stat-nba；上游页面结构变化时抓取可能失效。
