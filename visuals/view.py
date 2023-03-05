import math

from PyQt5.QtCore import Qt, QPointF, QLine, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QFont, QPixmap
from PyQt5.QtWidgets import QGraphicsView, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem, QGraphicsScene, \
    QInputDialog


class GraphicView(QGraphicsView):
    new_Bbox = pyqtSignal(str)

    def __init__(self, scene=None, parent=None):
        super().__init__(parent)

        self.gr_scene = scene if scene is not None else GraphicScene()
        self.parent = parent
        self.pixmapItem = self.gr_scene.pixmapItem
        self.pixmap = self.gr_scene.pixmap

        self.edge_enable = False

        self.x1 = 0  # 记录左上角点位置
        self.y1 = 0
        self.x2 = 0  # 记录右下角点位置
        self.y2 = 0
        self.x1_view = 0  # 记录view坐标系下左上角位置
        self.y1_view = 0
        self.x2_view = 0
        self.y2_view = 0
        self.mousePressItem = False  # 当前是否点击了某个item, 如果点了，把item本身附上去
        self.drawLabelFlag = -1  # 是否加了一个框，因为可以点取消而不画Bbox
        self.bboxPointList = []  # 用来存放bbox左上和右下坐标及label，每个元素以[x1,y1,x2,y2,text]的形式储存
        self.labelList = []  # 存放label，会展示在旁边的listview中。单独放为了保证不重名
        self.defaultLabelId = 0

        self.bboxList = []  # 存放图元对象和对应的label，方便删除管理, 每个对象都是[item1, item2, edge_item]

        # for scroll
        self.ratio = 1  # 缩放初始比例
        self.zoom_step = 0.1  # 缩放步长
        self.zoom_max = 3  # 缩放最大值
        self.zoom_min = 0.2  # 缩放最小值

        self.init_ui()

    def init_ui(self):
        self.setScene(self.gr_scene)
        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.HighQualityAntialiasing |
                            QPainter.TextAntialiasing |
                            QPainter.SmoothPixmapTransform |
                            QPainter.LosslessImageRendering)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(self.AnchorUnderMouse)
        self.setDragMode(self.RubberBandDrag)

    def mousePressEvent(self, event):
        # 转换坐标系

        pt = self.mapToScene(event.pos())
        self.x1 = pt.x()
        self.y1 = pt.y()
        self.x1_view = event.x()
        self.y1_view = event.y()
        # print('上层graphic： view-', event.pos(), '  scene-', pt)

        item = self.get_item_at_click(event)
        if item:
            self.mousePressItem = item
        self.edge_enable = False
        if event.button() == Qt.MidButton:
            self.edge_enable = True
            self.preMousePosition = event.pos()

        else:
            super().mousePressEvent(event)  # 如果写到最开头，则线条拖拽功能会不起作用
        event.ignore()

    def get_item_at_click(self, event):
        """ Return the object that clicked on. """
        pos = event.pos()
        item = self.itemAt(pos)
        return item

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if event.buttons() == Qt.MidButton:
            self.MouseMove = event.pos() - self.preMousePosition  # 鼠标当前位置-先前位置=单次偏移量
            self.preMousePosition = event.pos()  # 更新当前鼠标在窗口上的位置，下次移动用
            for item in self.items():
                if isinstance(item, GraphicEdge):
                    continue
                item.setPos(item.pos() + self.MouseMove)  # 更新图元位置
            # 对边刷新，进行同步
            for gr_edge in self.gr_scene.edges:
                gr_edge.edge_wrap.update_positions()

    def mouseReleaseEvent(self, event):
        self.mousePressItem = False
        pt = self.mapToScene(event.pos())
        self.x2 = pt.x()
        self.y2 = pt.y()
        self.x2_view = event.x()
        self.y2_view = event.y()

        if self.edge_enable:
            pass
        else:
            super().mouseReleaseEvent(event)
            item = self.get_item_at_click(event)  # 获得当前点击的item对象
            if not isinstance(item, GraphicItem):  # 如果不是点击item，则生成一个新的Bbox
                # TODO: 自定义弹窗风格
                text, ok = QInputDialog.getText(self, 'Label', '输入label:')
                if ok and text:
                    text = self.getSpecialLabel(text)
                    # 实际上存进去的是view坐标系下的坐标
                    self.savebbox(self.x1_view, self.y1_view, self.x2_view, self.y2_view, text)
                    self.labelList.append(text)
                    self.drawBbox(text)
                    self.drawLabelFlag *= -1  # 将标记变为正，表示画了
                elif ok:
                    self.defaultLabelId += 1
                    defaultLabel = 'label' + str(self.defaultLabelId)
                    self.savebbox(self.x1_view, self.y1_view, self.x2_view, self.y2_view, defaultLabel)
                    self.labelList.append(defaultLabel)
                    self.drawBbox(defaultLabel)
                    self.drawLabelFlag *= -1
            else:  # 如果点击了item，说明想拖动item
                # print('点击item拖动，更新BboxPointList')
                # print('更新前bboxPointList：', self.bboxPointList)
                index, position = self.findBboxItemIndexFromItem(item)
                label_text = self.bboxList[index][2].gr_edge.information['class']
                index_in_bboxPointList = self.findBboxFromLabel(label_text)
                if position == 1:
                    self.bboxPointList[index_in_bboxPointList][0] = self.x2_view
                    self.bboxPointList[index_in_bboxPointList][1] = self.y2_view
                else:
                    self.bboxPointList[index_in_bboxPointList][2] = self.x2_view
                    self.bboxPointList[index_in_bboxPointList][3] = self.y2_view
                # print('更新后bboxPointList：', self.bboxPointList)
            event.ignore()  # 将信号同时发给父部件

    def drawBbox(self, label_text):
        item1 = GraphicItem()
        item1.setPos(self.x1, self.y1)
        self.gr_scene.add_node(item1)

        item2 = GraphicItem()
        item2.setPos(self.x2, self.y2)
        self.gr_scene.add_node(item2)

        edge_item = Edge(self.gr_scene, item1, item2, label_text)  # 这里原来是self.drag_edge，我给删了

        self.bboxList.append([item1, item2, edge_item])
        #
        # print(self.bboxPointList)

    def savebbox(self, x1, y1, x2, y2, text):
        bbox = [x1, y1, x2, y2, text]  # 两个点的坐标以一个元组的形式储存，最后一个元素是label
        self.bboxPointList.append(bbox)
        self.new_Bbox.emit(text)

    def getSpecialLabel(self, text):
        # 获得不重名的label
        index = 0
        text_new = text
        for label in self.labelList:
            if text == label.split(' ')[0]:
                index += 1
                text_new = text + '$' + str(index)
        return text_new

    def findBboxFromLabel(self, label):
        '''
        根据label的内容找到self.bboxPointList的index
        '''
        for i, b in enumerate(self.bboxPointList):
            if b[4] == label:
                return i

    def findBboxItemIndexFromLabel(self, label_text):
        '''
        根据label的内容找到self.bboxList的index
        '''
        for i, b in enumerate(self.bboxList):
            edge_item = b[2]
            text = edge_item.labelText
            if text == label_text:
                return i

    def findBboxItemIndexFromItem(self, item):
        # 根据左上角或右下角的item找到此Bbox在数组中的位置
        for i, b in enumerate(self.bboxList):
            if b[0] == item:
                return i, 1  # 第二个参数1代表点击的是左上点
            elif b[1] == item:
                return i, 2  # 第二个参数2代表点击的是右下点
            else:
                return -1, -1  # 表示没找着

    def removeBbox(self, index):
        item1, item2, edge_item = self.bboxList[index]
        self.gr_scene.remove_node(item1)
        self.gr_scene.remove_node(item2)
        # self.gr_scene.remove_edge(edge_item)
        del self.bboxList[index]

    # 定义滚轮方法，以鼠标悬停位置为缩放中心
    def wheelEvent(self, event):
        angle = event.angleDelta() / 8  # 返回QPoint对象，为滚轮转过的数值，单位为1/8度
        if angle.y() > 0:
            # print("滚轮上滚")
            self.ratio += self.zoom_step  # 缩放比例自加
            if self.ratio > self.zoom_max:
                self.ratio = self.zoom_max
            else:
                for item in self.items():
                    if isinstance(item, GraphicEdge):
                        continue
                    # 标注的小圆圈(GraphicItem)不参与缩放
                    if not isinstance(item, GraphicItem):
                        item.setScale(self.ratio)  # 缩放
                    a1 = event.pos() - item.pos()  # 鼠标与图元左上角的差值
                    a2 = self.ratio / (self.ratio - self.zoom_step) - 1  # 对应比例
                    delta = a1 * a2
                    item.setPos(item.pos() - delta)
                # 对边刷新，进行同步
                for gr_edge in self.gr_scene.edges:
                    gr_edge.edge_wrap.update_positions()
        else:
            # print("滚轮下滚")
            self.ratio -= self.zoom_step
            if self.ratio < self.zoom_min:
                self.ratio = self.zoom_min
            else:
                for item in self.items():
                    if isinstance(item, GraphicEdge):
                        continue
                    # 标注的小圆圈(GraphicItem)不参与缩放
                    if not isinstance(item, GraphicItem):
                        item.setScale(self.ratio)  # 缩放
                    a1 = event.pos() - item.pos()  # 鼠标与图元左上角的差值
                    a2 = self.ratio / (self.ratio + self.zoom_step) - 1  # 对应比例
                    delta = a1 * a2
                    item.setPos(item.pos() - delta)
                # 对边刷新，进行同步
                for gr_edge in self.gr_scene.edges:
                    gr_edge.edge_wrap.update_positions()


class GraphicScene(QGraphicsScene):

    def __init__(self, Qitem=None, parent=None):
        super().__init__(parent)
        # for scroll
        self.pixmapItem = None
        self.pixmap = None
        if Qitem is not None:
            if isinstance(Qitem, QPixmap):
                self.pixmap = Qitem
                self.pixmapItem = self.addPixmap(Qitem)
            else:
                self.addItem(Qitem)

        # background settings
        self.grid_size = 20
        self.grid_squares = 5

        self._color_background = Qt.transparent
        self._color_light = QColor('#2f2f2f')
        self._color_dark = QColor('#292929')

        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)

        self.setBackgroundBrush(self._color_background)
        self.setSceneRect(0, 0, 500, 500)

        self.nodes = []  # 储存图元
        self.edges = []  # 储存连线

        self.real_x = 50

    def add_node(self, node):  # 这个函数可以改成传两个参数node1node2，弄成一组加进self.nodes里
        self.nodes.append(node)
        self.addItem(node)

    def remove_node(self, node):
        self.nodes.remove(node)
        for edge in self.edges:
            if edge.edge_wrap.start_item is node or edge.edge_wrap.end_item is node:
                self.remove_edge(edge)
        self.removeItem(node)

    def add_edge(self, edge):
        self.edges.append(edge)
        self.addItem(edge)

    def remove_edge(self, edge):
        self.edges.remove(edge)
        self.removeItem(edge)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        # 获取背景矩形的上下左右的长度，分别向上或向下取整数
        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        # 从左边和上边开始
        first_left = left - (left % self.grid_size)  # 减去余数，保证可以被网格大小整除
        first_top = top - (top % self.grid_size)

        # 分别收集明、暗线
        lines_light, lines_dark = [], []
        for x in range(first_left, right, self.grid_size):
            if x % (self.grid_size * self.grid_squares) != 0:
                lines_light.append(QLine(x, top, x, bottom))
            else:
                lines_dark.append(QLine(x, top, x, bottom))

        for y in range(first_top, bottom, self.grid_size):
            if y % (self.grid_size * self.grid_squares) != 0:
                lines_light.append(QLine(left, y, right, y))
            else:
                lines_dark.append(QLine(left, y, right, y))

        # 最后把收集的明、暗线分别画出来
        painter.setPen(self._pen_light)
        if lines_light:
            painter.drawLines(*lines_light)

        painter.setPen(self._pen_dark)
        if lines_dark:
            painter.drawLines(*lines_dark)


class GraphicItem(QGraphicsEllipseItem):

    def __init__(self, parent=None):
        super().__init__(parent)
        pen = QPen()
        pen.setColor(Qt.red)
        pen.setWidth(2.0)
        self.setPen(pen)
        self.pix = self.setRect(0, 0, 10, 10)
        self.width = 10
        self.height = 10
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        # update selected node and its edge
        # 如果图元被选中，就更新连线，这里更新的是所有。可以优化，只更新连接在图元上的。
        if self.isSelected():
            for gr_edge in self.scene().edges:
                gr_edge.edge_wrap.update_positions()


class Edge:
    '''
    线条的包装类
    '''

    def __init__(self, scene, start_item, end_item, labelText=''):
        super().__init__()
        # 参数分别为场景、开始图元、结束图元
        self.scene = scene
        self.start_item = start_item
        self.end_item = end_item
        self.labelText = labelText

        # 线条图形在此创建
        self.gr_edge = GraphicEdge(self)
        # add edge on graphic scene  一旦创建就添加进scene
        self.scene.add_edge(self.gr_edge)

        if self.start_item is not None:
            self.update_positions()

    def update_positions(self):
        patch = self.start_item.width / 2  # 想让线条从图元的中心位置开始，让他们都加上偏移
        src_pos = self.start_item.pos()
        self.gr_edge.set_src(src_pos.x() + patch, src_pos.y() + patch)
        if self.end_item is not None:
            end_pos = self.end_item.pos()
            self.gr_edge.set_dst(end_pos.x() + patch, end_pos.y() + patch)
        else:
            self.gr_edge.set_dst(src_pos.x() + patch, src_pos.y() + patch)
        self.gr_edge.update()

    def remove_from_current_items(self):
        self.end_item = None
        self.start_item = None

    def remove(self):
        self.remove_from_current_items()
        self.scene.remove_edge(self.gr_edge)
        self.gr_edge = None


class GraphicEdge(QGraphicsPathItem):

    def __init__(self, edge_wrap, parent=None):
        super().__init__(parent)
        self.edge_wrap = edge_wrap
        # print(self.edge_wrap)
        self.width = 2.0
        self.pos_src = [0, 0]  # 线条起始坐标
        self.pos_dst = [0, 0]  # 线条结束坐标

        self._pen = QPen(QColor(255, 0, 0, 255))  # 画线条的笔
        self._pen.setWidthF(self.width)

        self._pen_dragging = QPen(QColor("#000"))  # 画拖拽线条的笔
        self._pen_dragging.setStyle(Qt.DashDotLine)
        self._pen_dragging.setWidthF(self.width)

        # 标注信息
        self.information = {'coordinates': '', 'class': '', 'name': '', 'scale': '', 'owner': '', 'saliency': ''}

    def set_src(self, x, y):
        self.pos_src = [x, y]

    def set_dst(self, x, y):
        self.pos_dst = [x, y]

    def calc_path(self):  # 计算线条的路径
        path = QPainterPath(QPointF(self.pos_src[0], self.pos_src[1]))  # 起点
        path.lineTo(self.pos_dst[0], self.pos_src[1])
        path.lineTo(self.pos_dst[0], self.pos_dst[1])
        path.moveTo(self.pos_src[0], self.pos_src[1])
        path.lineTo(self.pos_src[0], self.pos_dst[1])
        path.lineTo(self.pos_dst[0], self.pos_dst[1])

        font = QFont("Helvetica [Cronyx]", 18)
        font.setWeight(25)  # Light
        path.addText(self.pos_src[0], self.pos_src[1], font, self.edge_wrap.labelText)
        self.information['coordinates'] = str([self.pos_src[0], self.pos_src[1], self.pos_dst[0], self.pos_dst[1]])
        self.information['class'] = self.edge_wrap.labelText
        return path

    def boundingRect(self):
        return self.shape().boundingRect()

    def shape(self):
        return self.calc_path()

    def paint(self, painter, graphics_item, widget=None):
        self.setPath(self.calc_path())
        path = self.path()
        if self.edge_wrap.end_item is None:
            # 包装类中存储了线条开始和结束位置的图元
            # 刚开始拖拽线条时，并没有结束位置的图元，所以是None
            # 这个线条画的是拖拽路径，点线
            painter.setPen(self._pen_dragging)
            painter.drawPath(path)
        else:
            painter.setPen(self._pen)
            painter.drawPath(path)
