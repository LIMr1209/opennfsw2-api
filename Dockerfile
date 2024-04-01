# 使用官方nvidia的cuda11.3.1-ubuntu20.04-cudd8镜像作为基础镜像
FROM harbor.cheerytech.ai/components/ubuntu:22.04

# 设置基础环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 替换Ubuntu的源为清华大学源，以加速包的下载速度，并安装必要的包
RUN echo "deb http://nexus.cheerytech.ai/repository/tsinghua-ubuntu/ jammy main restricted universe multiverse" > /etc/apt/sources.list && \
    echo "deb http://nexus.cheerytech.ai/repository/tsinghua-ubuntu/ jammy-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://nexus.cheerytech.ai/repository/tsinghua-ubuntu/ jammy-backports main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb http://nexus.cheerytech.ai/repository/tsinghua-ubuntu/ jammy-security main restricted universe multiverse" >> /etc/apt/sources.list && \
    apt-get update && apt-get upgrade -y && \
    apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/*


# 下载并安装Anaconda
RUN wget https://minio.cheerytech.ai/public/Miniconda3-latest-Linux-x86_64.sh -O ~/anaconda.sh && \
    /bin/bash ~/anaconda.sh -b -p /opt/conda && \
    rm ~/anaconda.sh

# 添加conda环境
ENV PATH=/opt/conda/bin:$PATH
ENV PIP_INDEX_URL=https://nexus.cheerytech.ai/repository/pypi/simple
# root用户初始化conda到bash
RUN conda init bash

# 复制环境配置文件到容器中
COPY environment.yml /app/opennfsw2-api/environment.yml

# 设置工作目录
WORKDIR /app/opennfsw2-api

# 配置Conda，设置超时时间，并创建Conda环境
RUN echo  "channels:" > ~/.condarc && \
    echo  "  - https://nexus.cheerytech.ai/repository/conda-pytorch/" >> ~/.condarc && \
    echo  "  - https://nexus.cheerytech.ai/repository/conda-nvidia/" >> ~/.condarc && \
    echo  "  - https://nexus.cheerytech.ai/repository/anaconda/" >> ~/.condarc && \
    echo  "  - https://nexus.cheerytech.ai/repository/conda-forge/" >> ~/.condarc && \
    echo  "  - https://nexus.cheerytech.ai/repository/conda-pyg/" >> ~/.condarc && \
    conda config --set remote_read_timeout_secs 300 && \
    conda env create -f environment.yml --verbose && \
    conda clean -afy

# 复制后续所需环境文件
COPY code /app/opennfsw2-api/code/

WORKDIR /app/opennfsw2-api/code/
# 给予初始化脚本执行权限
RUN chmod +x /app/opennfsw2-api/code/entrypoint.sh

# 复制项目文件到容器中
ENTRYPOINT ["/bin/bash","/app/opennfsw2-api/code/entrypoint.sh"]
