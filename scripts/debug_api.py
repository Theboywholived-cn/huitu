#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""调试后端 API 接口——打印各端点的响应状态与关键字段"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

ENDPOINTS = [
    ('GET', '/api/templates',          None),
    ('GET', '/api/templates?limit=5',  None),
    ('GET', '/api/chart-types',        None),
    ('GET', '/api/health',             None),
]

print(f'调试目标: {BASE_URL}')
print('=' * 60)

for method, path, payload in ENDPOINTS:
    url = BASE_URL + path
    try:
        if method == 'GET':
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, json=payload, timeout=5)

        try:
            data = resp.json()
            preview = json.dumps(data, ensure_ascii=False)[:120]
        except Exception:
            preview = resp.text[:120]

        status_mark = '✓' if resp.status_code < 400 else '✗'
        print(f'{status_mark} [{resp.status_code}] {method} {path}')
        print(f'   响应: {preview}')
    except requests.exceptions.ConnectionError:
        print(f'✗ [ERR] {method} {path}  →  无法连接，请确认后端已启动')
    except Exception as e:
        print(f'✗ [ERR] {method} {path}  →  {e}')
    print()

print('调试完毕')
