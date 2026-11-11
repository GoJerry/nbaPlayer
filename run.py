# coding: utf-8
"""启动入口。HOST / PORT 可用环境变量覆盖，默认 0.0.0.0:5800。"""
import os

from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run(host=os.environ.get("HOST", "0.0.0.0"),
                    port=int(os.environ.get("PORT", "5800")))
