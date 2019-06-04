# coding: utf-8
from flask import Blueprint
from flask import render_template
from flask import jsonify

application = Blueprint("application", __name__)

from . import urls


@application.route("/")
def index():

    return render_template("index.html", result_json=[{"data_list": "a"}])


if __name__ == '__main__':
    pass
