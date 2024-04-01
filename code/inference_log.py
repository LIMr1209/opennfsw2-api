import logging
import os
import pathlib

_srcfile = os.path.normcase(logging.addLevelName.__code__.co_filename)


# python默认的输出会将消息原样输出，如果有异常的话，会将异常堆栈多行形式返回。不方便进行日志的收集分析。所以需要将其输出为一行。
class WebServerLogFormatter(logging.Formatter):
    '''将换行转义'''

    def __init__(self, fmt=None, datefmt=None):
        super(WebServerLogFormatter, self).__init__(fmt, datefmt)

    def format(self, record):
        msg: str = super().format(record)
        return msg.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n')


file_fmt = WebServerLogFormatter(fmt="%(asctime)s # "
                                "%(levelname)s # "
                                "%(name)s # "
                                "%(filename)s # "
                                "%(funcName)s # "
                                "Line=%(lineno)s # "
                                "Msg=%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
streame_fmt = logging.Formatter(fmt="%(asctime)s # "
                                "%(levelname)s # "
                                "%(name)s # "
                                "%(filename)s # "
                                "%(funcName)s # "
                                "Line=%(lineno)s # "
                                "Msg=%(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# log_dir = pathlib.Path("inference_logs/")
# if not log_dir.exists():
#     log_dir.mkdir(parents=True, exist_ok=True)


# error_file_handler = logging.FileHandler(pathlib.Path(log_dir, 'error.log'), mode="a", encoding='utf-8')
# error_file_handler.setLevel(logging.ERROR)
# error_file_handler.setFormatter(file_fmt)
# info_file_handler = logging.FileHandler(pathlib.Path(log_dir, 'info.log'), mode="a", encoding='utf-8')
# info_file_handler.setFormatter(file_fmt)
info_handler = logging.StreamHandler()
info_handler.setFormatter(streame_fmt)

project_name = os.getcwd().rsplit("/", 1)[1]
logger = logging.Logger(project_name)
# logger.addHandler(error_file_handler)
# logger.addHandler(info_file_handler)
logger.addHandler(info_handler)
