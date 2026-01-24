#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""查看模板列表"""
import requests
response = requests.get('http://127.0.0.1:8000/api/templates')
data = response.json()
for t in data:
    if '误差柱' in t.get('name', ''):
        print(f"ID: {t.get('id')}")
        print(f"Name: {t.get('name')}")
        print(f"RelDir: {t.get('rel_dir')}")
        print("---")
