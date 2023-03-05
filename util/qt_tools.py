# encoding: utf-8
"""
@author: Ljz
@file: qt_tools.py
@time: 2022/11/29 2:13
"""
from collections import Counter

import numpy as np
from PyQt5 import QtCore
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QSlider, QMessageBox
from mpl_toolkits.mplot3d import Axes3D

from util.data_trans import splitSuffix, dcm2arr, pic2arr


def _open_dir(directory, msgBox, textBoard, Widget):
    if directory == '':
        pass  # 防止关闭或取消导入
    else:
        img_names, suffixs = splitSuffix(directory)
        # 均为dcm图像
        if suffixs.count('.dcm') == len(suffixs):
            dataArray = dcm2arr(directory)
            textBoard.setText('数据读取完毕\nshape:{}\ndtype:{}'.format(dataArray.shape, dataArray.dtype))
            return dataArray
        else:
            supported_suffix = ['.png', '.jpg', '.jpeg', '.tif', '.bmp']
            suffix_count = Counter(suffixs)
            suffix_num = sum([suffix_count[x] for x in supported_suffix])
            # 序列至少有2张图像
            if suffix_num == len(suffixs) and suffix_num > 1:
                # 第一次确认判断（后缀确认）
                names = []
                if sum([suffix_count[x] > 0 for x in supported_suffix]) > 1:
                    for name in supported_suffix:
                        if suffix_count[name] > 0:
                            names.append(name)

                    choice = msgBox.warning(Widget, '警告',
                                            '请注意，您的图片文件路径中图片后缀名不唯一\n'
                                            '含有{}\n是否继续读取？'.format(names),
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

                    if choice == QMessageBox.Yes:
                        pass
                    else:
                        return None

                # 第二次确认判断（前缀名称确认）
                warn_flag = False
                for name in img_names:
                    if not name.isdigit():
                        warn_flag = True
                        break

                if warn_flag:
                    choice = msgBox.warning(Widget, '警告',
                                            '请注意，您的图片文件路径中图片名不是纯数字\n'
                                            '自动过滤非数字字符进行序列排序，可能会影响结果\n'
                                            '是否继续读取？'.format(names),
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if choice == QMessageBox.Yes:
                        pass
                    else:
                        return None

                dataArray = pic2arr(directory)
                textBoard.setText('数据读取完毕\nshape:{}\ndtype:{}'.format(dataArray.shape, dataArray.dtype))
                return dataArray
            else:
                msgBox.critical(Widget, '严重错误', '所选路径无效，请查看帮助')
                textBoard.setText('所选路径无效，请查看帮助')
                return None


def show_Slider_name(*kwargs):
    for slider in kwargs:
        slider.show_name()


def ini_Slider(Slider, start, end, pos, ticks=1):
    """
    initialize a slider conveniently
    :param Slider: Slider from QT5
    :param start: start of the Slider
    :param end: end of the Slider
    :param pos: initial position of the Slider
    :param ticks: ticks
    """
    Slider.setMinimum(round(start))
    Slider.setMaximum(round(end))
    Slider.setSingleStep(round(ticks))
    Slider.setTickPosition(QSlider.TicksBelow)
    Slider.setValue(round(pos))
    Slider.show_name()


# Change QMainWindow to QWidget!!!
def show_Win(L, W, img, View):
    img = ((img - int((L - W) / 2)) / W * 255).astype(np.uint8)
    img = np.clip(img, 0, 255)
    x = img.shape[1]  # 获取图像大小
    y = img.shape[0]
    frame = QImage(img, x, y, QImage.Format_Grayscale8)
    pix = QPixmap.fromImage(frame)
    scene = QGraphicsScene()  # 创建场景
    # 缩放图像大小
    pix = pix.scaled(384, 384, QtCore.Qt.KeepAspectRatio)
    scene.addPixmap(pix)
    View.setScene(scene)
    return img


def _show_CUB(x, y, z, fig, cube_shape):
    # 长方体外框起点(x0,y0,z0)
    color = 'red'
    x0 = y0 = z0 = 0
    dx, dy, dz = [x - 1 for x in cube_shape]
    # 交换顺序，使得squeeze维的x能作为z轴方向，用于观察显示
    x, y, z = y, z, x
    dx, dy, dz = dy, dz, dx

    ax = Axes3D(fig, auto_add_to_figure=False)
    fig.add_axes(ax)
    xx = [x0, x0, x0 + dx, x0 + dx, x0]
    yy = [y0, y0 + dy, y0 + dy, y0, y0]
    kwargs1 = {'alpha': 1, 'color': color}
    ax.plot3D(xx, yy, [z0] * 5, **kwargs1)
    ax.plot3D(xx, yy, [z0 + dz] * 5, **kwargs1)
    ax.plot3D([x0, x0], [y0, y0], [z0, z0 + dz], **kwargs1)
    ax.plot3D([x0, x0], [y0 + dy, y0 + dy], [z0, z0 + dz], **kwargs1)
    ax.plot3D([x0 + dx, x0 + dx], [y0 + dy, y0 + dy], [z0, 2 + dz], **kwargs1)
    ax.plot3D([x0 + dx, x0 + dx], [y0, y0], [z0, z0 + dz], **kwargs1)

    # 绘制三个截取平面
    xx = np.linspace(0, dx, 10)
    yy = np.linspace(0, dy, 10)
    zz = np.linspace(0, dz, 10)

    yy2, zz2 = np.meshgrid(yy, zz)
    ax.plot_surface(np.full_like(yy2, x), yy2, zz2, color='blue', alpha=0.5)
    ax.text(x, dy / 2, dz / 2, '冠状面', fontsize=15, color='white', bbox=dict(facecolor='blue', alpha=0.7))
    xx2, zz2 = np.meshgrid(xx, zz)
    ax.plot_surface(xx2, np.full_like(yy2, y), zz2, color='red', alpha=0.5)
    ax.text(dx / 2, y, dz / 2, '矢状面', fontsize=15, color='white', bbox=dict(facecolor='red', alpha=0.7))
    xx2, yy2 = np.meshgrid(xx, yy)
    ax.plot_surface(xx2, yy2, np.full_like(xx2, z), color='green', alpha=0.5)
    ax.text(dx / 2, dy / 2, z, '横断面', fontsize=15, color='white', bbox=dict(facecolor='green', alpha=0.7))


def clip_Qpos(ItemQsize, Qpos):
    x_max, y_max = ItemQsize.width(), ItemQsize.height()
    if Qpos.x() < 0:
        x = 0
    elif Qpos.x() > x_max:
        x = x_max
    else:
        x = Qpos.x()
    if Qpos.y() < 0:
        y = 0
    elif Qpos.y() > y_max:
        y = y_max
    else:
        y = Qpos.y()
    return round(x), round(y)


def Qpixmap2arr(qtpixmap):
    qimg = qtpixmap.toImage()
    temp_shape = (qimg.height(), qimg.bytesPerLine() * 8 // qimg.depth())
    temp_shape += (4,)
    ptr = qimg.bits()
    ptr.setsize(qimg.byteCount())
    # 为了保存带上颜色框，转为uint8
    result = np.array(ptr, dtype=np.uint8).reshape(temp_shape)
    result = result[..., :3]

    return result

