import cgitb
import os
import sys

import cv2
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication, QMessageBox

from designer.Label_APP import Ui_MainWindow
from visuals.view import GraphicView, GraphicScene, GraphicItem
from util.qt_tools import clip_Qpos, Qpixmap2arr

from QCandyUi.CandyWindow import colorful

cgitb.enable(format("text"))


class LabelWindow(QMainWindow, Ui_MainWindow):
    numb_str_signal = pyqtSignal(str)

    def __init__(self, myQPixmap=None):
        super().__init__()
        if myQPixmap is not None:
            self.scene = GraphicScene(myQPixmap)
        else:
            self.scene = GraphicScene()

        self.view = GraphicView(self.scene)
        self.setupUi(self)

        self.setMinimumHeight(500)
        self.setMinimumWidth(500)
        self.setCentralWidget(self.view)
        self.setWindowTitle("CT图像标注系统")

        # 用于弹出窗口
        self.msg_win = QMessageBox()
        # 图像保存路径
        self.save_path = None

        self.label_list = []

        self.view.new_Bbox.connect(self.append_list)
        self.numb_str_signal.connect(self.del_list)
        self.actionpath_choose.triggered.connect(self.save_dir)
        self.actionpath_choose.triggered.connect(self.save_Image)

        # 使用帮助
        self.actionhelp.triggered.connect(self.help)
        # 关于我们
        self.actionabout_us.triggered.connect(self.about_us)

    def help(self):
        self.msg_win.information(self, '使用帮助',
                                 '本窗口为CT图像显示系统唤起的子窗口，用于对选取的截面图像进行细处理\n\n'
                                 '长按鼠标中键可以拖动图片进行移动，鼠标滚轮用以对图片进行缩放观察\n\n'
                                 '点击鼠标左键，长按进行框选后松开可以画出标注框并进行命名，支持对已经画好的框进行调节（左键长按框的顶点即可拖动）；'
                                 '若要删除某个标注框，在菜单栏中的标注管理选项下拉菜单（将显示目前所有标注框的名字），鼠标左键单击其即可\n\n'
                                 '若想要保存当前图像（含标注框），单击菜单栏中的标注图像保存选项，选择路径即可')

    def about_us(self):
        self.msg_win.information(self, '关于我们',
                                 '本软件为Opencv课程期末大作业\n'
                                 '项目开源于https://github.com/careless-lu/CT-image-annotation\n')

    def show_list(self):
        print(self.view.labelList)

    def append_list(self, Bbox_name):
        cur_label = QtWidgets.QAction(self)
        cur_label.setObjectName(Bbox_name)

        cur_label.triggered.connect(lambda: self.numb_str_signal.emit(Bbox_name))
        self.label_list.append((cur_label, Bbox_name))
        self.Labelmenu.addAction(cur_label)
        _translate = QtCore.QCoreApplication.translate
        cur_label.setText(_translate("LabelWindow", Bbox_name))

    def del_list(self, Bbox_name):
        for label_bag in self.label_list:
            if Bbox_name == label_bag[1]:
                # 删除Qaction
                label_bag[0].deleteLater()
                Bbox_index = self.view.findBboxItemIndexFromLabel(Bbox_name)
                # 删除图中标注
                self.view.removeBbox(Bbox_index)
                # 删除列表元素
                self.label_list.remove(label_bag)

    def save_dir(self):
        directory, fileType = QtWidgets.QFileDialog.getSaveFileName(self, "设置保存路径", "./",
                                                                    "PNG Files (*.png);;TIF Files (*.tif)"
                                                                    ";;All Files (*)")
        suffix = os.path.splitext(directory)[1]
        if suffix not in ['.png', '.tif']:
            self.msg_win.critical(self, '严重错误', '所选路径无效，请查看帮助')
            self.save_path = None
        else:
            self.save_path = directory

    # TODO: Super-resolution
    def save_Image(self):
        if self.save_path is not None:
            # 获取底层图片尺寸，并将其转为熟悉的array用于进一步处理(包括int16->uint8，标注矩形框的绘制)
            pixmapQsize = self.scene.pixmap.size()
            pic = Qpixmap2arr(self.scene.pixmap).copy()
            # cv2的shape: (h,w,c)
            # print(pic.shape, pic.dtype)
            # 一对两个点存储进Bboxes，用于进一步图像保存显示
            count = 0
            Bboxes = []
            # 记录”奇数次“的Bbox，用于凑一对
            pre_item_pos = None
            for item in self.scene.items():
                if isinstance(item, GraphicItem):
                    # 关于图像的相对坐标，注意越界需要截断
                    item_rel_Qpos = (item.pos() - self.scene.pixmapItem.pos()) / self.scene.pixmapItem.scale()
                    item_pos = clip_Qpos(pixmapQsize, item_rel_Qpos)
                    count += 1
                    if count % 2 == 0:
                        Bboxes.append((pre_item_pos, item_pos))
                    else:
                        pre_item_pos = item_pos
            for (pt1, pt2) in Bboxes:
                cv2.rectangle(pic, pt1, pt2, (0, 0, 255), 2)
            cv2.imwrite(self.save_path, pic)
            self.msg_win.information(self, '保存成功', '图像已保存至:\n{}'.format(self.save_path))


def demo_run():
    app = QApplication(sys.argv)
    demo = LabelWindow(QPixmap("blue.jpg"))
    # compatible with Mac Retina screen.
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    # show up
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    demo_run()
