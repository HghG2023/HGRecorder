import torch
from config import get_abs_path

class YOLOv5:
    def __init__(self, model_path=get_abs_path("YOLO_MODEL_PATH"), source='local'):
        """
        :param model_path: 模型文件的路径
        :param source: 模型来源，yolov5 仓库或本地
        """
        self.model = torch.hub.load(get_abs_path("YOLOV5_PATH"), 'custom', path=model_path, source=source)
 
    def predict(self, img_path):
        """
        :param img_path: 图像的路径
        :return: Detection 类型的对象
        """
        return self.model(img_path)

    def print_results(self, results):
        """
        :param results: Detection 类型的对象
        """
        results.print()

    def show_results(self, results):
        """
        :param results: Detection 类型的对象
        """
        results.show()

    def get_results_df(self, results):
        """
        :param results: Detection 类型的对象
        :return: 包含检测框信息的 pandas.DataFrame
        """
        return results.pandas().xyxy[0]

    def get_boxes_info(self, results_df):
        """
        :param results_df: 包含检测框信息的 pandas.DataFrame
        :return: 包含框的位置与类别等信息的 pandas.DataFrame
        """
        return results_df[['name', 'confidence', 'xmin', 'ymin', 'xmax', 'ymax']]
