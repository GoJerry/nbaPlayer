# coding: utf-8
import os

__all__ = ["Config"]


class Config(object):
    PROJECT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    JSON_AS_ASCII = False

    DEBUG = True  # debug


if __name__ == '__main__':
    pass
