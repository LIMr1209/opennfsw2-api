import os
import pathlib
import uuid
import shutil

import opennsfw2 as n2

weights_path = "../model/open_nsfw_weights.h5"

def load_model():
    pass


def infer_service(
        input_dir,
        data,
        suffix,
        kind,
):
    threshold = 0.5
    # 处理上传视频文件
    task_path = pathlib.Path(os.path.join(input_dir, str(uuid.uuid4())))
    if not task_path.exists():
        task_path.mkdir(parents=True, exist_ok=True)
    if kind == 1:
        video_path = pathlib.Path(task_path, f"src.{suffix}")
        with open(video_path, "wb") as f:
            f.write(data)
        elapsed_seconds, nsfw_probabilities = n2.predict_video_frames(str(video_path),weights_path=weights_path)
        nsfw_probability = max(nsfw_probabilities)
    else:
        image_path = pathlib.Path(task_path, f"src.{suffix}")
        with open(image_path, "wb") as f:
            f.write(data)
        nsfw_probability = n2.predict_image(str(image_path),weights_path=weights_path)
    shutil.rmtree(task_path)
    return 200, {"probability": nsfw_probability}
