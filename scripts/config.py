# scripts/config.py
#
# 국가 목록의 유일한 원본은 config/countries.json 입니다.
# 이 파일은 더 이상 국가 목록을 직접 들고 있지 않고, json을 읽어서 제공만 합니다.

import json
import os

_CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_COUNTRIES_PATH = os.path.join(_CONFIG_DIR, "config", "countries.json")

with open(_COUNTRIES_PATH, encoding="utf-8") as f:
    COUNTRIES = json.load(f)
