# nbaPlayer

用 Python 自动生成 NBA 球员生涯数据曲线：将数据接口和 pyecharts 集成到 Flask 中，生成球员逐赛季得分 / 篮板 / 助攻 / 抢断 / 失误曲线，并给出赛季数、生涯场均与得分巅峰赛季等概要数据。主数据源已升级为 NBA 官方 stats.nba.com（经开源库 nba_api），并新增趋势、巅峰窗口、稳定性与双人对比等分析功能。

## 功能

1. 现役球员：30 支球队的球员名单查询，以及任意现役球员常规赛 / 季后赛生涯曲线
2. 历史巨星：14 位退役球星（乔丹、科比、姚明等）的常规赛 / 季后赛生涯曲线
3. 生涯概要：赛季数、场均得分 / 篮板 / 助攻、得分巅峰赛季，曲线下方附逐赛季数据表
4. 图表支持缩放（dataZoom）、图例、十字线提示，可通过 `color` 参数设置背景色
5. 发现接口：`/api/teams` 与 `/api/players/retired` 返回全部支持的球队与退役球星
6. 官方数据源：按英文全名查询任意现役 / 历史球员（`/nba/player2`），数据来自 stats.nba.com，不依赖网页结构；带 1 小时进程内缓存
7. 数据分析：得分趋势（斜率）、连续 3 季巅峰窗口、最大单季涨 / 跌幅、稳定性（变异系数）、五项指标生涯最高；双人对比页与接口（`/compare`、`/api/analysis/compare`）含按生涯年份对齐的得分折线与五维雷达图

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
| `GET /nba/player2?name=LeBron James&game=0` | 官方数据源球员曲线页（英文全名） | 覆盖现役与历史球员，页面含数据分析 |
| `GET /api/analysis/player?name=LeBron James&game=0` | 单人数据 + 概要 + 分析（JSON） | 分析含趋势/巅峰窗口/稳定性/生涯最高 |
| `GET /compare?player1=LeBron James&player2=Stephen Curry&game=0` | 双人对比页 | 得分折线（按生涯年份对齐）+ 五维雷达 + 对比表 |
| `GET /api/analysis/compare?player1=..&player2=..&game=0` | 双人对比（JSON） | 五项场均、差值、领先者与双方分析 |
| `GET /api/sources` | 数据源清单（JSON） | 各源的角色、覆盖范围与注意事项 |

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
│   ├── data/            # 数据源 provider 层（nba_api 官方数据源、缓存、字段映射）
│   ├── analysis.py      # 趋势/巅峰窗口/稳定性分析与双人对比、对比图
│   ├── forms/           # 参数校验（WTForms）
│   ├── spider/          # 虎扑 / stat-nba 抓取（legacy）、球队与球星映射、曲线与概要计算
│   └── templates/       # 首页、球员曲线页与双人对比页
└── requirements.txt
```

数据来源：现役球员来自虎扑 NBA，退役球星来自 stat-nba；上游页面结构变化时抓取可能失效。

## 数据源说明

选型调研（2026-11）结论：候选源逐一核查后，主数据源选 stats.nba.com + 开源库
[nba_api](https://github.com/swar/nba_api)（MIT、无需密钥、持续维护）——一次调用
即返回某球员常规赛与季后赛的逐赛季场均。其他候选未选原因：balldontlie 现已要求
注册密钥且逐赛季场均仅付费最高档提供；data.nba.net 已下线；Basketball Reference
限流 20 次/分钟且季后赛逐赛季需自行聚合（可作后续备选）；ESPN 非官方 JSON 无稳定性
承诺（可作兜底）。完整清单见 `GET /api/sources`。

使用注意：

- stats.nba.com **对部分机房 IP 段（云服务器）不响应**且有限流。在这类网络环境
  部署时，请把超时调大或配置代理，并善用缓存：
  - `NBA_API_TIMEOUT`：单次请求超时秒数（默认 30）
  - `NBA_API_PROXY`：代理地址（如 `http://127.0.0.1:7890`，默认不用）
  - `NBA_API_CACHE_TTL`：进程内缓存秒数（默认 3600）
- 上游不可用时新接口返回 502（与参数错误 400 区分）；球员英文名查不到返回 400。
- 中途换队的赛季，上游会返回多行（含 TOT 合计行），provider 已按赛季去重保留 TOT。
