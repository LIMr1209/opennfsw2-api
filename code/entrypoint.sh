#!/bin/bash

# 确保脚本在遇到错误时终止
set -e

# 激活Conda环境
echo "Activating Conda environment..."
source /opt/conda/bin/activate opennfsw2-api

# 运行Python脚本
echo "Running Python script..."
exec python inference_service.py