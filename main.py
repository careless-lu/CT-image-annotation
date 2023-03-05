# encoding: utf-8
"""
@author: Ljz
@file: main.py
@time: 2022/11/29 12:12
"""
import os
import sys

import PySide2
import albumentations as albu
import cv2
import numpy as np
import torch as th
from PyQt5 import QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtWidgets import QDesktopWidget, QMainWindow
from PySide2 import QtCore
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from qt_material import apply_stylesheet

from LabelWin import LabelWindow
from final_CT_APP import Ui_APP_Window
from util.qt_tools import _open_dir, show_Slider_name, ini_Slider, show_Win, _show_CUB

plt.rcParams['font.sans-serif'] = 'SimHei'

dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path


# @colorful('blueGreen')
class UI_APP(Ui_APP_Window, QMainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.center()
        # CT序列数据(array格式) shape:[c,h,w]
        self.data_cube = None
        # 以文件打开
        self.file_path.triggered.connect(self.open_file)
        # 以文件夹打开
        self.dir_path.triggered.connect(self.open_dir)
        # 图像保存路径
        self.save_path = None
        # 用于弹出窗口
        self.msg_win = QMessageBox()
        self.textBrowser.setText('\n\n       \.欢迎使用本CT图像显示系统软件./\n'
                                 '\t 建议您在使用前查看帮助')
        # 防止未打开文件就调用标注，导致崩溃
        self.is_load = False
        # 标注窗口
        self.LabelPlaneA.triggered.connect(self.Label_A)
        self.LabelPlaneB.triggered.connect(self.Label_B)
        self.LabelPlaneC.triggered.connect(self.Label_C)
        # 使用帮助
        self.actionhelp.triggered.connect(self.help)
        # 关于我们
        self.actionabout_us.triggered.connect(self.about_us)

    def help(self):
        self.msg_win.information(self, '使用帮助',
                                 '欢迎使用该CT图像显示系统\n\n'
                                 '菜单栏中的打开选项用于读取CT扫描数据，'
                                 '支持pt类型压缩文件，DICOM以及多种常见图片格式(PNG,TIF)等文件夹的序列读取\n\n'
                                 '读取的图片文件中DICOM将以int16处理，其余格式图片将均转为uint16处理\n\n'
                                 '滑动条可以分别调节对应显示窗口的窗宽窗位，以及序列图像的选取(右下角为三截面示意图)\n\n'
                                 '菜单栏中的图像保存选项可以将当前窗口的显示图像进行保存，并支持多窗口拼接保存\n\n'
                                 '菜单栏中的图像标注选项将唤起另外的窗口，支持对某一截面图像进行缩放观察、标注、保存等功能')

    def about_us(self):
        self.msg_win.information(self, '关于我们',
                                 '本软件为Opencv课程期末大作业\n'
                                 '项目开源于https://github.com/careless-lu/CT-image-annotation\n')

    # 加载全局图像及各类初始化设置
    def load(self):
        self.is_load = True
        self.cube_shape = self.data_cube.shape
        # 分别对应三视图: 横断面(c可变),冠状面(h可变),矢状面(w可变)
        self.imgA = self.data_cube[0, :, :]
        self.imgB = self.data_cube[:, 0, :]
        self.imgC = self.data_cube[:, :, 0]
        # 分别对应编辑修改后的三视图
        self.newImgA = self.data_cube[0, :, :]
        self.newImgB = self.data_cube[:, 0, :]
        self.newImgC = self.data_cube[:, :, 0]

        # PlaneA显示横截面,务必记得-1，否则越界
        ini_Slider(self.PlaneA, start=0, end=self.cube_shape[0] - 1, pos=0)
        self.ini_Win_A()
        self.PlaneA.valueChanged.connect(self.ini_Win_A)
        # PlaneB显示面B
        ini_Slider(self.PlaneB, start=0, end=self.cube_shape[1] - 1, pos=0)
        self.ini_Win_B()
        self.PlaneB.valueChanged.connect(self.ini_Win_B)
        # PlaneC显示面C
        ini_Slider(self.PlaneC, start=0, end=self.cube_shape[2] - 1, pos=0)
        self.ini_Win_C()
        self.PlaneC.valueChanged.connect(self.ini_Win_C)

        self.figure = plt.figure(dpi=64, figsize=(6, 6))
        self.ViewCUB = FigureCanvas(self.figure)
        self.gridLayout.addWidget(self.ViewCUB, 1, 3, 1, 1)

        self.show_CUB()
        self.PlaneA.valueChanged.connect(self.show_CUB)
        self.PlaneB.valueChanged.connect(self.show_CUB)
        self.PlaneC.valueChanged.connect(self.show_CUB)

        # 图像保存
        self.saveA.triggered.connect(self.save_dir)
        self.saveA.triggered.connect(self.save_Win_A)
        self.saveB.triggered.connect(self.save_dir)
        self.saveB.triggered.connect(self.save_Win_B)
        self.saveC.triggered.connect(self.save_dir)
        self.saveC.triggered.connect(self.save_Win_C)
        self.saveCUB.triggered.connect(self.save_dir)
        self.saveCUB.triggered.connect(self.save_Win_CUB)
        self.saveAll.triggered.connect(self.save_dir)
        self.saveAll.triggered.connect(self.save_Win_ALL)

        # 图像标注
        self.LabelPlaneA.triggered.connect(self.Label_A)

        # 显示滑动条名称
        show_Slider_name(self.A_L, self.A_W, self.B_L, self.B_W, self.C_L, self.C_W,
                         self.PlaneA, self.PlaneB, self.PlaneC)

    def open_file(self):
        fileName, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                   "Tensor File(*.pt)")
        if fileName == '':
            pass  # 防止关闭或取消导入关闭所有页面
        else:
            self.data_cube = th.load(fileName).numpy()
            self.textBrowser.setText('数据读取完毕\nshape:{}\ndtype:{}'.format(self.data_cube.shape, self.data_cube.dtype))
            self.load()

    def open_dir(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(None, "选取文件夹", os.getcwd())

        self.data_cube = _open_dir(directory, self.msg_win, self.textBrowser, self)
        if self.data_cube is not None:
            self.load()

    def save_dir(self):
        directory, fileType = QtWidgets.QFileDialog.getSaveFileName(self, "设置保存路径", "./",
                                                                    "PNG Files (*.png);;TIF Files (*.tif)"
                                                                    ";;All Files (*)")
        suffix = os.path.splitext(directory)[1]
        if suffix not in ['.png', '.tif']:
            self.msg_win.critical(self, '严重错误', '所选路径无效，请查看帮助')
            self.textBrowser.setText('所选路径无效，请查看帮助')
            self.save_path = None
        else:
            self.textBrowser.setText('图像已保存至:\n{}'.format(directory))
            self.save_path = directory

    def ini_Win_A(self):
        plane = self.PlaneA.value()
        self.imgA = self.data_cube[plane, :, :]
        min_val, max_Val, _, _ = cv2.minMaxLoc(self.imgA)
        # 窗位
        ini_Slider(self.A_L, start=min_val, end=max_Val, pos=int((max_Val + min_val) / 2))
        # 窗宽
        ini_Slider(self.A_W, start=1, end=int(max_Val - min_val), pos=int(max_Val - min_val))
        self.show_Win_A()
        self.A_L.valueChanged.connect(self.show_Win_A)
        self.A_W.valueChanged.connect(self.show_Win_A)

    def ini_Win_B(self):
        plane = self.PlaneB.value()
        self.imgB = self.data_cube[:, plane, :]
        min_val, max_Val, _, _ = cv2.minMaxLoc(self.imgB)
        # 窗位
        ini_Slider(self.B_L, start=min_val, end=max_Val, pos=int((max_Val + min_val) / 2))
        # 窗宽
        ini_Slider(self.B_W, start=1, end=int(max_Val - min_val), pos=int(max_Val - min_val))
        self.show_Win_B()
        self.B_L.valueChanged.connect(self.show_Win_B)
        self.B_W.valueChanged.connect(self.show_Win_B)

    def ini_Win_C(self):
        plane = self.PlaneC.value()
        self.imgC = self.data_cube[:, :, plane]
        min_val, max_Val, _, _ = cv2.minMaxLoc(self.imgC)
        # 窗位
        ini_Slider(self.C_L, start=min_val, end=max_Val, pos=int((max_Val + min_val) / 2))
        # 窗宽
        ini_Slider(self.C_W, start=1, end=int(max_Val - min_val), pos=int(max_Val - min_val))
        self.show_Win_C()
        self.C_L.valueChanged.connect(self.show_Win_C)
        self.C_W.valueChanged.connect(self.show_Win_C)

    def show_Win_A(self):
        self.newImgA = show_Win(self.A_L.value(), self.A_W.value(), self.imgA, self.ViewA)

    def show_Win_B(self):
        self.newImgB = show_Win(self.B_L.value(), self.B_W.value(), self.imgB, self.ViewB)

    def show_Win_C(self):
        self.newImgC = show_Win(self.C_L.value(), self.C_W.value(), self.imgC, self.ViewC)

    def show_CUB(self):
        x = self.PlaneA.value()
        y = self.PlaneB.value()
        z = self.PlaneC.value()
        _show_CUB(x, y, z, self.figure, self.cube_shape)
        self.ViewCUB.draw()

    def save_Win_A(self):
        if self.save_path is not None:
            cv2.imwrite(self.save_path, self.newImgA)

    def save_Win_B(self):
        if self.save_path is not None:
            cv2.imwrite(self.save_path, self.newImgB)

    def save_Win_C(self):
        if self.save_path is not None:
            cv2.imwrite(self.save_path, self.newImgC)

    def save_Win_CUB(self):
        if self.save_path is not None:
            self.figure.savefig(self.save_path)

    # 四张图片拼接保存
    def save_Win_ALL(self):
        if self.save_path is not None:
            # 解码ViewCUB.renderer 得到三维示意图的rgb图像
            CUBImg = np.asarray(self.ViewCUB.renderer.buffer_rgba()).take([0, 1, 2], axis=2)
            transform = albu.PadIfNeeded(min_height=512, min_width=512, position='center',
                                         border_mode=0, value=[0, 0, 0])
            syn_imgs = []
            for _ in [self.newImgA, self.newImgB, self.newImgC]:
                _ = cv2.cvtColor(_, cv2.COLOR_GRAY2RGB)
                syn_imgs.append(transform(image=_)['image'])
            syn_imgs.append(albu.Resize(height=512, width=512)(image=CUBImg)['image'])

            stack_w1 = np.concatenate([syn_imgs[0], syn_imgs[1]], axis=0)
            stack_w2 = np.concatenate([syn_imgs[2], syn_imgs[3]], axis=0)
            all_img = np.concatenate([stack_w1, stack_w2], axis=1)

            cv2.imwrite(self.save_path, all_img)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(round((screen.width() - size.width()) / 2), round((screen.height() - size.height()) / 2))

    def Label_A(self):
        if self.is_load:
            x = self.newImgA.shape[1]  # 获取图像大小
            y = self.newImgA.shape[0]
            frame = QImage(self.newImgA, x, y, QImage.Format_Grayscale8)
            pix = QPixmap.fromImage(frame)
            self.label_Win = LabelWindow(pix)  # 创建场景
            self.label_Win.show()

    def Label_B(self):
        if self.is_load:
            x = self.newImgB.shape[1]  # 获取图像大小
            y = self.newImgB.shape[0]
            frame = QImage(self.newImgB, x, y, QImage.Format_Grayscale8)
            pix = QPixmap.fromImage(frame)
            self.label_Win = LabelWindow(pix)  # 创建场景
            self.label_Win.show()

    def Label_C(self):
        if self.is_load:
            x = self.newImgC.shape[1]  # 获取图像大小
            y = self.newImgC.shape[0]
            frame = QImage(self.newImgC, x, y, QImage.Format_Grayscale8)
            pix = QPixmap.fromImage(frame)
            self.label_Win = LabelWindow(pix)  # 创建场景
            self.label_Win.show()


if __name__ == "__main__":
    # colorful
    extra_setting = {
        # Button colors
        'danger': '#dc3545',
        'warning': '#ffc107',
        'success': '#17a2b8',

        # Font
        'font_family': 'monoespace',
        'font_size': '16px',
        'line_height': '16px',

        # Density Scale
        'density_scale': '-1',
    }

    # CT_data = th.load('CT_data.pt').numpy()
    # print('数据读取完毕, shape:{}'.format(CT_data.shape))
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    win = UI_APP()
    apply_stylesheet(app, theme='dark_teal.xml', extra=extra_setting)
    win.show()
    sys.exit(app.exec_())
