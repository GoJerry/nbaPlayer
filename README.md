# nbaPlayer
用 Python 自动生成 NBA 球员生涯数据曲线

将爬虫和 pyecharts 集成到 flask 中，主要功能如下：

1.支持现役所有NBA球员常规赛和季后赛生涯曲线，根据不同 game 的值生成对应比赛类型数据曲线

2.支持历史巨星常规赛和季后赛生涯曲线

3.根据 color 值设置不同的背景色

使用教程：以湖人詹姆斯为例
- 获取某球队数据，url路径为/nba/team，参数为name
- 以湖人詹姆斯为例,在浏览器输入
http://127.0.0.1:5800/nba/team?name=湖人，想获取某球队改下球队名称即可

- 获取球员的生涯数据
在获取球队数据后，将球员数据加到 /nba/player?player= 中，同时加上game 0为常规赛，1为季后赛
http://127.0.0.1:5800/nba/player?player=lebronjames-650.html&game=0

- 获取退役球员数据
和球员数据类似，只要将 player 改成 retire 即可,比如乔丹：
http://127.0.0.1:5800/retire/player?retire=乔丹&game=1
