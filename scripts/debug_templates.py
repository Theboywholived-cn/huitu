import os
import sys
sys.path.insert(0, 'backend')

from app.api.routes_templates import scan_templates
from app.core.config import settings

print(f"TEMPLATES_ROOT: {settings.TEMPLATES_ROOT}")
print(f"路径是否存在: {os.path.exists(settings.TEMPLATES_ROOT)}")

if os.path.exists(settings.TEMPLATES_ROOT):
    print(f"\n目录内容:")
    items = os.listdir(settings.TEMPLATES_ROOT)
    for item in items[:10]:
        item_path = os.path.join(settings.TEMPLATES_ROOT, item)
        is_dir = os.path.isdir(item_path)
        print(f"  {'[目录]' if is_dir else '[文件]'} {item}")
    print(f"... 共{len(items)}个项目")

print(f"\n扫描模板...")
templates = scan_templates()
print(f"找到模板数: {len(templates)}")
if templates:
    for t in templates[:3]:
        print(f"  - {t.name} ({t.category})")
else:
    print("  没有找到任何模板")
