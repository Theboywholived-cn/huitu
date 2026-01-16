"""
    pandas-1.4.4
    numpy-1.24.4
    seaborn-0.13.2
    matplotlib-3.4.3
"""
import pandas as pd
import numpy as np
# import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import ticker
import os
from pathlib import Path
import matplotlib as mpl

# 使用Matplotlib配置替代Proplot配置
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.labelsize"] = 15
# 正确设置刻度标签大小
mpl.rcParams["xtick.labelsize"] = 13
mpl.rcParams["ytick.labelsize"] = 13
mpl.rcParams["figure.titlesize"] = 15  # 替代suptitle.size
mpl.rcParams["axes.titlesize"] = 14    # 替代title.size
# 关闭次要刻度
mpl.rcParams["xtick.minor.visible"] = False
mpl.rcParams["ytick.minor.visible"] = False

current_dir = Path(os.path.dirname(os.path.abspath(__file__)))

def plot_percent_stacked_bar(labels, data_list, bar_colors, bar_labels, save_name_prefix):
    """
    绘制百分比堆积柱形图的函数
    :param labels: x 轴刻度标签，列表形式
    :param data_list: 数据列表，每个元素是一组数据，如 [type01, type02, type03]
    :param bar_colors: 柱子颜色列表
    :param bar_labels: 柱子标识标签列表
    :param save_name_prefix: 保存文件名称的前缀
    """
    all_data = data_list
    bottom_y = np.zeros(len(labels))
    sums = np.sum(all_data, axis=0)

    width = .6
    fig, ax = plt.subplots(figsize=(5, 4), dpi=100, facecolor="w")

    for data, color, label in zip(all_data, bar_colors, bar_labels):
        y = data / sums
        ax.bar(labels, y, width, bottom=bottom_y, color=color, label=label, ec='k')
        bottom_y = y + bottom_y

    ax.tick_params(which='major', direction='in', length=3, width=1., bottom=False)
    for spine in ["top", "left", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_linewidth(2)

    # 修复 FixedFormatter 警告问题：先设置刻度定位器，再设置刻度标签
    locator = ticker.FixedLocator(range(len(labels)))
    ax.xaxis.set_major_locator(locator)
    ax.set_xticklabels(labels, size=12)

    ax.set_ylim(ymin=0, ymax=1.05)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))
    ax.legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.08))

    # 添加标签
    for c in ax.containers:
        label_color = "k" if bar_colors[0] == "#d0d0d0" else "w"
        ax.bar_label(c, label_type='center', size=13,
                     labels=[str(round(i * 100, 1)) for i in c.datavalues],
                     color=label_color, fontweight="bold")

    # 保存文件
    # fig.savefig(current_dir / "图4-1-14 百分比堆积柱形图绘制示例_b.pdf", bbox_inches='tight')
    # fig.savefig(current_dir / "图4-1-14 百分比堆积柱形图绘制示例_b.png",
    #         bbox_inches='tight',dpi=300)
    plt.show()


if __name__ == "__main__":
    # 数据加载：优先读取外部文件，否则使用内置数据
    def load_stacked_data():
        for fname in ['示范数据.xlsx', '示范数据.csv']:
            if os.path.exists(fname):
                try:
                    if fname.endswith('.csv'):
                        df = pd.read_csv(fname)
                    else:
                        df = pd.read_excel(fname)
                    # 期望格式：类别,系列1,系列2,...
                    if '类别' in df.columns:
                        labels = df['类别'].tolist()
                        series_cols = [c for c in df.columns if c != '类别']
                        data_list = [df[c].values for c in series_cols]
                        return labels, data_list, series_cols
                except Exception:
                    pass
        # 内置示例数据
        labels = ['one', 'two', 'three', 'four', 'five']
        type01 = np.array([10, 8, 5, 10, 2])
        type02 = np.array([13, 10, 7, 4, 10])
        type03 = np.array([5, 7, 10, 6, 8])
        return labels, [type01, type02, type03], ["type01", "type02", "type03"]
    
    labels, data_list, series_names = load_stacked_data()

    """ # a）百分比堆积柱形图绘制示例（灰色系）
    bar_color_gray = ["#d0d0d0", "#a8a8a8", "#808080"]
    bar_label_gray = ["type01", "type02", "type03"]
    plot_percent_stacked_bar(labels, [type01, type02, type03], bar_color_gray, bar_label_gray,
                             "图4-1-14 百分比堆积柱形图绘制示例_a") """

    # b）百分比堆积柱形图绘制示例（NEJM色系）
    bar_color_nejm = ["#BC3C29FF", "#0072B5FF", "#E18727FF", "#20854EFF", "#7876B1FF"][:len(data_list)]
    plot_percent_stacked_bar(labels, data_list, bar_color_nejm, series_names,
                             "图4-1-14 百分比堆积柱形图绘制示例_b")