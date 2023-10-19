import json
import os
import sys

import openpyxl
from contextlib import contextmanager
import time
from loguru import logger
from functools import wraps
from dataclasses import dataclass, field
from typing import Literal, List
import traceback
from DownloadKit import DownloadKit
from pathlib import Path


d = DownloadKit()
PROGRESS_FILE = "progress_cache.json"


logger.remove()  # 删除默认的控制台处理器
logger.add(
    sys.stderr,
    level="INFO"
)
logger.add("mylog.log", rotation="5 MB", level="DEBUG")


@dataclass
class Image:
    id: int = 0
    author: str = ""
    platform: Literal["unsplash", "pixabay"] = ""
    tags: List[str] = field(default_factory=list)
    title: str = ""
    description: str = ""
    preview_link: str = ""


@contextmanager
def rate_limit(max_per_minute=100):
    min_interval = 60.0 / max_per_minute
    start_time = time.perf_counter()

    yield

    elapsed = time.perf_counter() - start_time
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
# for _ in range(10):
#     with rate_limit(5):  # 每分钟5次，作为示例
#         print("Executing some code...")


def read_column(filename,column='A'):
    workbook = openpyxl.load_workbook(filename)
    sheet = workbook.active
    column_data = [cell.value for cell in sheet[column] if cell.value is not None]
    workbook.close()
    return column_data


def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}


def cache_progress(func):
    def wrapper(*args, **kwargs):
        data = load_progress()
        list_to_process = args[0]
        starting_index = data.get("last_completed", -1) + 1
        for i in range(starting_index, len(list_to_process)):
            try:
                func(list_to_process[i], **kwargs)
                data["last_completed"] = i
                save_progress(data)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                line_number = exc_traceback.tb_lineno
                traceback.print_tb(exc_traceback)
                logger.error(
                    f"Failed on index {i} due to {exc_type} {exc_value} at line {line_number}")
                save_progress(data)
                d.wait()
                break
            except KeyboardInterrupt:
                data["last_completed"] = i
                save_progress(data)
                # d.wait()
                raise
                # sys.exit(1)

    return wrapper


def count_files_in_subdirs(directory: Path) -> dict:
    """
    遍历指定目录下的子目录，并统计每个子目录中的文件数量。

    :param directory: 要遍历的目录的路径
    :return: 一个字典，键是子目录名称，值是文件数量
    """
    counts = {}

    for subdir in directory.iterdir():
        if subdir.is_dir():
            counts[subdir.name] = sum(
                1 for _ in subdir.iterdir() if _.is_file())

    return counts
