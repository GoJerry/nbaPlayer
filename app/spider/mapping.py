# coding: utf-8
__author__ = 'Jerry'
# 公众号：Python编程与实战,欢迎关注点赞

term_mapping = {
    "火箭": "rockets",
    "湖人": "lakers",
    "勇士": "warriors",
    "马刺": "spurs",
    "灰熊": "grizzlies",
    "鹈鹕": "pelicans",
    "独行侠": "mavericks",
    "快船": "clippers",
    "国王": "kings",
    "太阳": "suns",
    "掘金": "nuggets",
    "爵士": "jazz",
    "雷霆": "thunder",
    "猛龙": "raptors",
    "76人": "76ers",
    "凯尔特人": "celtics",
    "篮网": "nets",
    "尼克斯": "knicks",
    "魔术": "magic",
    "黄蜂": "hornets",
    "热火": "heat",
    "奇才": "wizards",
    "老鹰": "hawks",
    "雄鹿": "bucks",
    "步行者": "pacers",
    "活塞": "pistons",
    "公牛": "bulls",
    "骑士": "cavaliers",
    "开拓者": "blazers",
    "森林狼": "timberwolves",
}

retire_mapping = {
    "乔丹": "1717",
    "科比": "195",
    "马龙": "2545",
    "魔术师": "1786",
    "大鸟": "379",
    "天勾": "136",
    "奥拉朱旺": "2701",
    "奥尼尔": "2716",
    "邓肯": "785",
    "拉塞尔": "2921",
    "艾弗森": "1687",
    "姚明": "2315",
    "麦迪": "2421",
    "张伯伦": "693",
}


def verification(team):
    team = term_mapping.get(team)  # 球队名称
    return team


def retire_verify(name):
    url = retire_mapping.get(name)
    return url


if __name__ == '__main__':
    pass
