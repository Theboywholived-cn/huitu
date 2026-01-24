#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the scan_templates() function works with new directory structure.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Mock settings
class MockSettings:
    TEMPLATES_PATH = r"D:\文件夹\绘图\图像代码数据汇总"

# Temporarily replace settings
import app.core.config as config_module
original_settings = config_module.settings
config_module.settings = MockSettings()

# Now import the function
from app.api.routes_templates import scan_templates

# Run scan
print("🔍 Scanning templates...")
templates = scan_templates()

print(f"\n✓ Found {len(templates)} templates:\n")

# Group by category
by_category = {}
for t in templates:
    if t.category not in by_category:
        by_category[t.category] = []
    by_category[t.category].append(t)

# Display results
for category in sorted(by_category.keys()):
    print(f"\n📊 {category} ({len(by_category[category])} templates)")
    for t in by_category[category]:
        has_data = "✓ data" if t.has_data_file else "  -"
        has_thumb = "✓ thumb" if t.thumbnail else "  -"
        print(f"  • {t.name:30} [{has_data}] [{has_thumb}]")

# Restore settings
config_module.settings = original_settings
