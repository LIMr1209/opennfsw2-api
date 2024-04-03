import os
import pathlib
import uuid
import shutil
import tarfile
import py7zr
import zipfile

import opennsfw2 as n2

weights_path = "../model/open_nsfw_weights.h5"


def extract_file(file_path, output_dir):
    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
    elif tarfile.is_tarfile(file_path):
        with tarfile.open(file_path, 'r') as tar_ref:
            tar_ref.extractall(output_dir)
    elif py7zr.is_7zfile(file_path):
        with py7zr.SevenZipFile(file_path, mode='r') as z:
            z.extractall(output_dir)


def load_model():
    pass


def infer_service(
        input_dir,
        data,
        suffix,
        kind,
):
    # 处理上传视频文件
    task_path = pathlib.Path(os.path.join(input_dir, str(uuid.uuid4())))
    if not task_path.exists():
        task_path.mkdir(parents=True, exist_ok=True)
    if kind == 1:
        video_path = pathlib.Path(task_path, f"src.{suffix}")
        with open(video_path, "wb") as f:
            f.write(data)
        elapsed_seconds, nsfw_probabilities = n2.predict_video_frames(str(video_path), weights_path=weights_path)
        nsfw_probability = max(nsfw_probabilities)
    elif kind == 2:
        image_path = pathlib.Path(task_path, f"src.{suffix}")
        with open(image_path, "wb") as f:
            f.write(data)
        nsfw_probability = n2.predict_image(str(image_path), weights_path=weights_path)
    else:
        zip_path = pathlib.Path(task_path, f"src.{suffix}")
        with open(zip_path, "wb") as f:
            f.write(data)
        images_path = pathlib.Path(task_path, "input")
        images_path.mkdir(parents=True, exist_ok=True)
        extract_file(zip_path, images_path)
        nsfw_probabilities = []
        for image_path in images_path.glob('*'):
            if image_path.is_file():
                nsfw_probabilities.append(n2.predict_image(str(image_path), weights_path=weights_path))
        nsfw_probability = max(nsfw_probabilities)
    shutil.rmtree(task_path)
    return 200, {"probability": nsfw_probability}
