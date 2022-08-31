import os
from functools import partial
from PyQt5.QtCore import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QGraphicsPixmapItem, QGraphicsScene, QMessageBox
import sys
from UI.MainWindow import Ui_MainWindow
from UI.labelimg import Ui_LabelImg
from libs.Common import Common
from utils.ustr import ustr
from utils.utils import new_action


class Main_Window(QMainWindow, Ui_LabelImg):
    def __init__(self):
        super(Main_Window, self).__init__()
        styleFile = "./qrc/style.qss"
        style = Common.readQss(styleFile)
        # self.setStyleSheet(style)
        self.setupUi(self)

        # For loading all image under a directory

        self.label_hist = []
        self.last_open_dir = None

        # self.img_count = len(self.m_img_list)
        self.dir_path = None  # 当前打开图片路径
        self.default_save_dir = None  # 默认的标注文件夹
        self.change_save_dir = None
        self.cur_img_idx = 0  # 当前文件索引
        self.framelist = []  # frame文件列表
        self.total_frame_number = len(self.framelist)  # frame总数

        self.model_type = None
        self.select_class = None
        self.save_as_format = None  # 存放的数据集格式
        
        self.loadedImage = False # 用于判断showImage是用来展示图片还是实现放大缩小的功能
        self.resizedWidth = 0
        self.resizedHeight = 0
        self.magOrMin = 0 # 用于判断图片是放大还是缩小，被用在showImage函数中，若此变量为0则为放大，否则缩小

        self.OpenDirButton.clicked.connect(self.open_dir)
        self.ImageListWidget.itemDoubleClicked.connect(self.pic_name_double_clicked)
        self.NextButton.clicked.connect(self.open_next_image)
        self.PrevButton.clicked.connect(self.open_prev_image)
        self.ResetButton.clicked.connect(self.file_reset)
        self.SaveDirButton.clicked.connect(self.change_save_dir_dialog)
        self.zoomIn.clicked.connect(self.zoomInImage)
        self.zoomOut.clicked.connect(self.zoomOutImage)

        action = partial(new_action, self)

    ########################
    ####打开存放frame的文件夹
    #######################
    def open_dir(self):
        pic_dir = QFileDialog.getExistingDirectory(self, "getExistingDirectory", "./")
        if pic_dir is None or len(pic_dir) < 1:
            QMessageBox.warning(self, "Error", "the directory is invalid",
                                QMessageBox.Ok)
            return
        FileList = sorted(os.listdir(pic_dir))
        for i, FileName in enumerate(FileList):
            if (FileName.split(".")[-1]) in ['png', 'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG']:
                PicName = pic_dir + '/' + FileName
                self.ImageListWidget.addItem(PicName)
                self.framelist.append(PicName)
        # print(self.framelist)
        self.showImage(self.framelist[0])
        self.dir_name = pic_dir
        self.default_save_dir = pic_dir
        self.SaveDir.setText(self.default_save_dir)
        self.total_frame_number = len(self.framelist)
        self.loadedImage = False

    ########################
    ####双击文件名打开图片
    #######################
    def pic_name_double_clicked(self, item=None):
        print('item.text()' + item.text())
        print(type(item.text()))
        self.cur_img_idx = self.framelist.index(item.text())
        filename = self.framelist[self.cur_img_idx]
        print(filename + "\n")
        if filename:
            self.showImage(filename)

    ########################
    ####打开下一张图片
    #######################
    def open_next_image(self):
        if self.cur_img_idx + 1 > self.total_frame_number:
            QMessageBox.information(self, 'Error', 'This is the last frame!')
            return
        self.cur_img_idx = self.cur_img_idx + 1
        filename = self.framelist[self.cur_img_idx]
        self.loadedImage = False
        if filename:
            self.showImage(filename)

    ########################
    ####打开上一张图片
    #######################
    def open_prev_image(self):
        if self.cur_img_idx - 1 < 0:
            QMessageBox.warning(self, 'Error', 'This is the first frame!',
                                QMessageBox.Yes)  # 2
            return
        self.cur_img_idx = self.cur_img_idx - 1
        filename = self.framelist[self.cur_img_idx]
        self.loadedImage = False
        if filename:
            self.showImage(filename)

    ########################
    ####打开图片
    #######################
    def showImage(self, filename):
        frame = QImage(filename)
        pix = QPixmap.fromImage(frame)

        # 当为false的时候，图片会被按一定比例缩小，并且能够被完整地呈现在应用窗口
        if self.loadedImage == False:
            pix = self.resizeImage(pix)
            # print(f"width:{pix.width()}---height:{pix.height()}\n")
            self.resizedWidth = pix.width()
            self.resizedHeight = pix.height()

        # 当为true的时候，此函数将被用于实现放大和缩小功能
        else:
            if self.magOrMin == 0:
                pix = self.magnifyImage(pix)
            else:
                pix = self.minimizeImage(pix)

        item = QGraphicsPixmapItem(pix)
        scene = QGraphicsScene()
        scene.addItem(item)
        self.graphicsView.setScene(scene)
        # self.graphicsView.fitInView(item)
        self.label_15.setText(f"{self.cur_img_idx}/{self.total_frame_number}\n")
        self.graphicsView.setDragMode(self.graphicsView.ScrollHandDrag)


    ########################
    ####修改图片大小
    #######################
    def resizeImage(self, pix):
        resizePix = QPixmap()
        if pix.width() <= 1025 and pix.height() <= 769:
            resizePix = pix
        else:
            if pix.width() == pix.height():
                resizePix = pix.scaled(750, 750, Qt.IgnoreAspectRatio, Qt.FastTransformation)
            else:
                resizePix = pix.scaled(pix.width() / 1.25, pix.height() / 1.25, Qt.IgnoreAspectRatio,
                                       Qt.FastTransformation)
                resizePix = self.resizeImage(resizePix)
        return resizePix


    ########################
    ####zoom-in slot function
    #######################
    def zoomInImage(self):
        self.loadedImage = True
        self.magOrMin = 0
        self.showImage(self.framelist[self.cur_img_idx])

    ########################
    ####放大图片
    #######################
    def magnifyImage(self, pix):
        magPix = QPixmap()
        magPix = pix.scaled(self.resizedWidth*1.25, self.resizedHeight*1.25, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        self.resizedWidth *= 1.25
        self.resizedHeight *= 1.25
        return magPix

    ########################
    ####zoom-out slot function
    #######################
    def zoomOutImage(self):
        self.loadedImage = True
        self.magOrMin = 1
        self.showImage(self.framelist[self.cur_img_idx])

    ########################
    ####缩小图片
    #######################
    def minimizeImage(self, pix):
        magPix = QPixmap()
        magPix = pix.scaled(self.resizedWidth/1.25, self.resizedHeight/1.25, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        self.resizedWidth /= 1.25
        self.resizedHeight /= 1.25
        return magPix


    ########################
    ####文件夹重置
    #######################
    def file_reset(self):
        self.framelist.clear()
        self.ImageListWidget.clear()
        self.label_15.setText("frame:")
        self.default_save_dir = None

    ########################
    ####更改标注文件存放的位置
    #######################
    def change_save_dir_dialog(self):
        if self.default_save_dir is not None:
            path = self.default_save_dir
        else:
            path = '.'
        changed_dir = QFileDialog.getExistingDirectory(self,
                                                       '-Save annotations to the directory', './')
        if changed_dir is not None and len(changed_dir) > 1:
            self.default_save_dir = changed_dir
            QMessageBox.information(self, "Success", "the annotation save directory has been changed!",
                                    QMessageBox.Ok)
        else:
            QMessageBox.warning(self, "Error", "the changed save directory is not existing!",
                                QMessageBox.Ok)
            return

    ########################
    ####利用目标检测算法自动标注
    #######################
    def autolabel(self, model, class_name):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWidget = Main_Window()
    mainWidget.show()
    sys.exit(app.exec_())
