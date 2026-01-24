#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Batch-standardize legacy matplotlib templates.

目标：递归扫描 `图像代码数据汇总/**/main.py`，对脚本做“尽量小改动”的自动修复：
- 强制无头运行：matplotlib.use('Agg')
- 注入中文字体自适配（SimHei / Microsoft YaHei 等），避免乱码
- 将常见的硬编码数据读取替换为基于 glob 的动态查找
- 将 plt.show() 替换为 plt.savefig('output.png')

该脚本会：
- 默认就地修改，并为每个文件创建 .bak 备份（可关闭）
- 支持 --dry-run 只输出将要修改的文件

注意：这是基于启发式的“批量修复器”，不会保证 100% 覆盖所有非典型写法。
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


INJECT_BLOCK = r"""# --- standardized by scripts/standardize_templates.py ---
import matplotlib
matplotlib.use('Agg')  # headless


def _configure_cn_fonts() -> None:
    """Best-effort Chinese font config (SimHei / Microsoft YaHei / etc.)."""
    try:
        from matplotlib import font_manager

        preferred = [
            'Microsoft YaHei',
            'SimHei',
            'PingFang SC',
            'Hiragino Sans GB',
            'Noto Sans CJK SC',
            'Source Han Sans SC',
            'WenQuanYi Micro Hei',
        ]
        available = {f.name for f in font_manager.fontManager.ttflist}
        chosen = [name for name in preferred if name in available]
        if chosen:
            import matplotlib.pyplot as plt

            plt.rcParams['font.sans-serif'] = chosen
            plt.rcParams['axes.unicode_minus'] = False
    except Exception:
        # Keep templates runnable even if font discovery fails.
        pass


def _find_data_file(patterns=None) -> str:
    """Find first data file in current working directory.

    Templates are executed in an isolated temp folder where the uploaded file
    is placed, so searching the CWD is intentional.
    """
    import glob

    patterns = patterns or ['*.csv', '*.xlsx', '*.xls']
    for pat in patterns:
        matches = sorted(glob.glob(pat))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"No data file found. Tried patterns: {patterns}")


_configure_cn_fonts()


# --- end standardized block ---
"""


@dataclass
class PatchResult:
    changed: bool
    reasons: List[str]


def _split_leading_preamble(text: str) -> Tuple[str, str]:
    """Keep shebang/encoding/comment header intact."""
    lines = text.splitlines(True)
    preamble: List[str] = []
    i = 0

    # shebang
    if i < len(lines) and lines[i].startswith('#!'):
        preamble.append(lines[i])
        i += 1

    # encoding
    if i < len(lines) and re.search(r'coding[:=]\s*[-\w.]+', lines[i]):
        preamble.append(lines[i])
        i += 1

    # module docstring (single or triple quotes) - keep as-is
    # We avoid parsing; just keep consecutive comment/docstring lines at top.
    # Stop once we hit a non-empty, non-comment line that is not a docstring start.
    while i < len(lines):
        line = lines[i]
        if line.strip() == '':
            preamble.append(line)
            i += 1
            continue
        if line.lstrip().startswith('#'):
            preamble.append(line)
            i += 1
            continue
        if line.lstrip().startswith(('"""', "'''")):
            # include docstring block
            quote = '"""' if '"""' in line else "'''"
            preamble.append(line)
            i += 1
            # consume until closing quote
            while i < len(lines) and quote not in lines[i]:
                preamble.append(lines[i])
                i += 1
            if i < len(lines):
                preamble.append(lines[i])
                i += 1
            # allow trailing blank line
            continue
        break

    return ''.join(preamble), ''.join(lines[i:])


def _ensure_inject_block(text: str) -> Tuple[str, bool]:
    if 'standardized by scripts/standardize_templates.py' in text:
        return text, False

    preamble, rest = _split_leading_preamble(text)
    if preamble and not preamble.endswith('\n'):
        preamble += '\n'

    # Ensure one blank line between preamble and injected block
    if preamble and not preamble.endswith('\n\n'):
        if not preamble.endswith('\n'):
            preamble += '\n'
        preamble += '\n'

    new_text = preamble + INJECT_BLOCK + rest
    return new_text, True


def _patch_show_to_savefig(text: str) -> Tuple[str, bool]:
    # Replace common `plt.show(...)` (including spaces/args) with savefig.
    if 'plt.show' not in text:
        return text, False

    pattern = re.compile(r"(^|\n)(?P<indent>[ \t]*)plt\.show\(.*?\)\s*", re.MULTILINE)

    def repl(m: re.Match) -> str:
        indent = m.group('indent')
        return (
            f"{m.group(1)}{indent}plt.savefig('output.png', dpi=300, bbox_inches='tight')\n"
            f"{indent}plt.close()\n"
        )

    new_text, n = pattern.subn(repl, text)
    return new_text, n > 0


def _patch_data_loading(text: str) -> Tuple[str, bool]:
    changed = False

    # pandas read_csv('xxx.csv') / read_excel('xxx.xlsx') -> find via glob in CWD
    # Only patch when first argument is a simple string literal.

    def _sub_call(func_name: str, exts: List[str]) -> None:
        nonlocal text, changed
        # matches: pd.read_csv('a.csv', ...) OR pandas.read_csv("a.csv")
        # capture prefix (pd or pandas or just read_csv) and keep rest args.
        # We only replace the first string-literal argument.
        exts_re = '|'.join(re.escape(e) for e in exts)
        pat = re.compile(
            rf"(?P<prefix>\b(?:pd|pandas)\.){re.escape(func_name)}\(\s*(?P<q>['\"])(?P<path>[^'\"]+?\.(?:{exts_re}))(?P=q)\s*(?P<rest>,[^\)]*)?\)",
            flags=re.IGNORECASE,
        )

        def repl(m: re.Match) -> str:
            nonlocal changed
            rest = m.group('rest') or ''
            patterns = []
            for e in exts:
                patterns.append(f"*.{e}")
                patterns.append(f"*.{e.upper()}")
            changed = True
            prefix = m.group('prefix')
            return f"{prefix}{func_name}(_find_data_file({patterns!r}){rest})"

        text, n = pat.subn(repl, text)
        if n > 0:
            changed = True

    _sub_call('read_csv', ['csv', 'txt'])
    _sub_call('read_excel', ['xlsx', 'xls'])

    # Also patch open('xxx.csv') -> open(_find_data_file([...])) if file ext matches.
    open_pat = re.compile(
        r"\bopen\(\s*(?P<q>['\"])(?P<path>[^'\"]+?\.(?:csv|CSV|xlsx|XLSX|xls|XLS))(?P=q)\s*(?P<rest>,[^\)]*)?\)",
    )

    def open_repl(m: re.Match) -> str:
        nonlocal changed
        path = m.group('path').lower()
        rest = m.group('rest') or ''
        if path.endswith('.csv'):
            patterns = ['*.csv', '*.CSV', '*.txt', '*.TXT']
        else:
            patterns = ['*.xlsx', '*.XLSX', '*.xls', '*.XLS']
        changed = True
        return f"open(_find_data_file({patterns!r}){rest})"

    text, n = open_pat.subn(open_repl, text)
    if n > 0:
        changed = True

    return text, changed


def standardize_file(path: Path) -> Tuple[PatchResult, str]:
    raw = path.read_text(encoding='utf-8', errors='ignore')
    reasons: List[str] = []

    new, did = _ensure_inject_block(raw)
    if did:
        reasons.append('inject_agg_and_fonts_and_finder')

    new2, did2 = _patch_data_loading(new)
    if did2:
        reasons.append('patch_data_loading')

    new3, did3 = _patch_show_to_savefig(new2)
    if did3:
        reasons.append('replace_show_with_savefig')

    return PatchResult(changed=(new3 != raw), reasons=reasons), new3


def iter_main_py(root: Path) -> Iterable[Path]:
    for p in root.rglob('main.py'):
        if p.is_file():
            yield p


def main() -> int:
    parser = argparse.ArgumentParser(description='Standardize legacy matplotlib templates in bulk')
    parser.add_argument('--root', default='图像代码数据汇总', help='templates root directory (default: 图像代码数据汇总)')
    parser.add_argument('--dry-run', action='store_true', help='only print what would change')
    parser.add_argument('--no-backup', action='store_true', help='do not create .bak backup files')
    parser.add_argument('--yes', action='store_true', help='skip confirmation prompt')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    root = (project_root / args.root).resolve()

    if not root.exists():
        print(f"[ERROR] root not found: {root}")
        return 2

    targets = list(iter_main_py(root))
    if not targets:
        print(f"[WARN] no main.py found under: {root}")
        return 0

    print(f"Found {len(targets)} files.")

    if not args.yes and not args.dry_run:
        resp = input('Proceed to modify files in-place? (y/N): ').strip().lower()
        if resp not in {'y', 'yes'}:
            print('Aborted.')
            return 1

    changed_count = 0
    for p in targets:
        result, new_text = standardize_file(p)
        if not result.changed:
            continue

        changed_count += 1
        rel = p.relative_to(project_root)
        print(f"[CHANGED] {rel}  ({', '.join(result.reasons)})")

        if args.dry_run:
            continue

        if not args.no_backup:
            bak = p.with_suffix(p.suffix + '.bak')
            if not bak.exists():
                bak.write_text(p.read_text(encoding='utf-8', errors='ignore'), encoding='utf-8')

        p.write_text(new_text, encoding='utf-8')

    print(f"Done. Changed {changed_count}/{len(targets)} files.")
    if args.dry_run:
        print('Dry-run mode: no files were modified.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
