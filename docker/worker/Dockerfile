FROM rockylinux:9

WORKDIR /code

RUN dnf install epel-release python3.12  fontconfig wqy-microhei-fonts -y

RUN python3.12 -m ensurepip --default-pip

RUN dnf install nmap -y

RUN pip3.12 install --upgrade pip
RUN pip3.12 install playwright
RUN playwright install-deps
# Install Chromium via Playwright (for screenshots)
RUN playwright install chromium
# Install Firefox via dnf (for wappalyzer full mode)
RUN dnf install firefox -y

RUN dnf install python3.12-devel gcc-c++ -y

RUN dnf install nginx unzip wget -y

COPY app/ app/

COPY test/ test/

COPY docker/frontend/ frontend/

COPY docker/nginx.conf  /etc/nginx/nginx.conf

## 复制生成ssl证书文件
COPY docker/worker/gen_crt.sh /usr/bin/gen_crt.sh
## 复制 wait-for-it
COPY docker/worker/wait-for-it.sh /usr/bin/wait-for-it.sh

## 复制 ncrack依赖
COPY docker/ncrack /usr/local/bin/ncrack
COPY docker/ncrack-services /usr/local/share/ncrack/ncrack-services
## 复制npoc 并安装
COPY docker/ARL-NPoC/ /opt/ARL-NPoC/
WORKDIR /opt/ARL-NPoC/
ENV LANG en_US.UTF-8
RUN pip3.12 install -e .

WORKDIR /code

RUN curl https://ssl-config.mozilla.org/ffdhe2048.txt -o /etc/ssl/certs/dhparam.pem

COPY requirements.txt requirements.txt


COPY docker/GeoLite2/ /data/GeoLite2/

RUN pip3.12 install -r requirements.txt


## 安装 NPoC 的依赖
WORKDIR /opt/ARL-NPoC/
RUN pip3.12 install -r requirements.txt


# 定义nuclei版本
ARG NUCLEI_VERSION=3.2.4

# 安装nuclei
RUN wget -c "https://github.com/adysec/ARL/raw/master/tools/nuclei.zip" \
    && unzip "nuclei.zip" nuclei \
    && mv nuclei /usr/bin/ \
    && rm -f "nuclei.zip"

# 运行nuclei
RUN nuclei -ut

## 安装 WIH
RUN wget -c https://github.com/adysec/ARL/raw/master/tools/wih/wih_linux_amd64 -O /usr/bin/wih && chmod +x /usr/bin/wih
RUN wih --version

## 切换工作目录
WORKDIR /code

## 自测一下
RUN cp app/config.yaml.example app/config.yaml
RUN env FLASK_APP=app.main:arl_app python3.12 -m flask routes
RUN python3.12 -m app.celerytask
