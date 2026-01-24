#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新组织模板文件夹结构
根据 Python 代码推断图表类型，按类型分类重组
"""

import os
import shutil
import re
from datetime import datetime
from pathlib import Path

TEMPLATES_ROOT = r"D:\文件夹\绘图\图像代码数据汇总"
BACKUP_ROOT = os.path.join(
    os.path.dirname(TEMPLATES_ROOT),
    f"图像代码数据汇总_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
)

def get_chart_type(filename, dirname, code):
    """根据文件名、目录名和代码推断图表类型"""
    search = (filename + dirname + code).lower()
    
    if 'taylor' in search:
        return 'taylor'
    if 'violin' in search:
        return 'violin'
    if 'boxplot' in search:
        return 'boxplot'
    if any(k in search for k in ['heatmap', 'imshow', 'contour']):
        return 'heatmap'
    if 'bar(' in search:
        return 'bar'
    if 'scatter' in search and any(k in search for k in ['cmap', 'colorbar']):
        return 'scatter_cmap'
    if 'scatter' in search and 'subplot' in search:
        return 'scatter_multi'
    if 'scatter' in search:
        return 'scatter'
    if 'plot(' in search and 'subplot' in search:
        return 'line_multi'
    if 'plot(' in search:
        return 'line'
    if 'hist' in search:
        return 'hist'
    
    return 'other'

def get_normalized_name(pyfile):
    """从Python文件提取规范化名称"""
    try:
        with open(pyfile, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 提取 TITLE 常量
        m = re.search(r'TITLE\s*=\s*["\'](.+?)["\']', content)
        if m:
            return m.group(1).strip()
        
        # 提取 plt.title/suptitle
        m = re.search(r'plt\.(suptitle|title)\(\s*["\'](.+?)["\']', content)
        if m:
            title = m.group(2).strip()
            if title and title.lower() not in ['title', 'figure']:
                return title
        
        # 用文件名
        return Path(pyfile).stem
    except:
        return Path(pyfile).stem

def main():
    print("🔄 开始备份原文件夹...")
    if os.path.exists(TEMPLATES_ROOT):
        shutil.copytree(TEMPLATES_ROOT, BACKUP_ROOT)
        print(f"✓ 备份完成: {BACKUP_ROOT}")
    else:
        print(f"✗ 模板根目录不存在: {TEMPLATES_ROOT}")
        return
    
    # 从备份中扫描（因为可能已经清空了原目录）
    scan_root = BACKUP_ROOT
    migrations = {}
    
    print(f"\n🔍 扫描文件结构 (from {scan_root})...")
    count = 0
    
    if not os.path.exists(scan_root):
        print(f"✗ 扫描目录不存在: {scan_root}")
        return
    
    # 遍历所有子目录
    for category in os.listdir(scan_root):
        category_path = os.path.join(scan_root, category)
        if not os.path.isdir(category_path):
            continue
        
    # 遍历所有子目录
    for category in os.listdir(scan_root):
        category_path = os.path.join(scan_root, category)
        if not os.path.isdir(category_path):
            continue
        
        # 同时检查该分类目录下的直接Python文件 和 子目录中的Python文件
        all_roots = [category_path]  # 先加分类目录本身
        all_roots.extend([os.path.join(category_path, d) for d in os.listdir(category_path) 
                         if os.path.isdir(os.path.join(category_path, d))])
        
        for root in all_roots:
            # 不用 os.walk，只检查当前目录的 .py 文件
            try:
                files = os.listdir(root)
            except:
                continue
                
            py_files = [f for f in files if f.endswith('.py') and not f.startswith('__')]
            if not py_files:
                # 如果当前目录没有 .py，继续 walk 查找子目录
                for sub_root, dirs, sub_files in os.walk(root):
                    py_files = [f for f in sub_files if f.endswith('.py') and not f.startswith('__')]
                    if py_files:
                        root = sub_root
                        files = sub_files
                        break
                else:
                    continue
            
            # 选择主要 Python 文件
            main_py = py_files[0]
            for pf in py_files:
                if Path(pf).stem == Path(root).name:
                    main_py = pf
                    break
            else:
                # 选择文件大小最大的（通常是主脚本）
                main_py = max(py_files, key=lambda f: os.path.getsize(os.path.join(root, f)))
            
            main_py_path = os.path.join(root, main_py)
            
            # 读取代码推断类型
            try:
                with open(main_py_path, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
            except:
                code = ""
            
            chart_type = get_chart_type(main_py, Path(root).name, code)
            
            # 获取规范化名称
            norm_name = get_normalized_name(main_py_path)
            # 清理名称（移除特殊字符，保留中文）
            norm_name = norm_name[:50] if norm_name else Path(root).name
            
            # 构建新路径（在原TEMPLATES_ROOT中）
            new_chart_dir = os.path.join(TEMPLATES_ROOT, chart_type)
            new_template_dir = os.path.join(new_chart_dir, norm_name)
            
            migrations[root] = {
                'old_path': root,
                'new_path': new_template_dir,
                'chart_type': chart_type,
                'template_name': norm_name,
                'main_py': main_py_path
            }
            count += 1
    
    print(f"✓ 找到 {count} 个模板目录")
    
    # 执行迁移（清空前）
    print("\n📦 执行文件迁移...")
    success = 0
    errors = []
    
    for old_path, info in migrations.items():
        new_path = info['new_path']
        try:
            os.makedirs(new_path, exist_ok=True)
            
            # 复制所有文件
            for item in os.listdir(old_path):
                if item == '.idea':
                    continue
                src = os.path.join(old_path, item)
                dst = os.path.join(new_path, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            # 重命名主Python文件
            main_py_name = os.path.basename(info['main_py'])
            if main_py_name != 'main.py':
                old_main = os.path.join(new_path, main_py_name)
                if os.path.exists(old_main):
                    os.rename(old_main, os.path.join(new_path, 'main.py'))
            
            print(f"✓ {info['chart_type']:20} / {info['template_name']}")
            success += 1
        except Exception as e:
            errors.append(f"✗ {old_path}: {e}")
    
    # 迁移后清空原作者/日期分类目录
    print("\n🧹 清空原作者/日期分类目录...")
    preserved = {
        '.idea',
        # 英文目录（旧结构/兼容）
        'taylor', 'bar', 'heatmap', 'scatter', 'scatter_cmap', 'scatter_multi',
        'violin', 'boxplot', 'line_multi', 'line', 'hist', 'other',
        # 中文目录（新结构）
        '泰勒图', '柱状图', '热力图', '散点图', '色标散点图', '散点对比图',
        '小提琴图', '箱线图', '多曲线', '折线图', '直方图', '其他'
    }
    for item in os.listdir(TEMPLATES_ROOT):
        item_path = os.path.join(TEMPLATES_ROOT, item)
        # 保留：隐藏目录、脚本、新的分类目录
        if item.startswith('.') or item.endswith('.ps1') or item.endswith('.py') or item in preserved:
            continue
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"  deleted: {item}")
        except Exception as e:
            print(f"  failed to delete {item}: {e}")
    
    print(f"\n✓ 迁移完成: {success}/{count} 成功")
    if errors:
        print("\n❌ 错误:")
        for err in errors:
            print(f"  {err}")
    
    print(f"\n💾 备份已保存: {BACKUP_ROOT}")
    print("如需恢复，执行: shutil.copytree(...)")

if __name__ == '__main__':
    main()
