# coding: utf-8
"""应用配置。

环境相关的开关走环境变量，不要再写死：DEBUG 默认关闭，
本地调试时设置环境变量 NBA_DEBUG=1 再开启。
"""
import os

__all__ = ["Config"]


class Config(object):
    PROJECT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    JSON_AS_ASCII = False

    # 仅在显式设置 NBA_DEBUG=1 时开启，避免以调试模式对外提供服务
    DEBUG = os.environ.get("NBA_DEBUG", "0") == "1"


if __name__ == '__main__':
    pass
