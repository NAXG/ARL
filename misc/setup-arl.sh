set -e

cd /opt/

tee /etc/resolv.conf <<"EOF"
nameserver 1.1.1.1
nameserver 8.8.8.8
nameserver 223.5.5.5
nameserver 119.29.29.29
EOF


tee /etc/yum.repos.d/mongodb-org-6.0.repo <<"EOF"
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/6.0/x86_64/
gpgcheck=0
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
EOF

tee /etc/yum.repos.d/rabbitmq.repo <<"EOF"
[rabbitmq_erlang]
name=rabbitmq_erlang
baseurl=https://packagecloud.io/rabbitmq/erlang/el/9/$basearch
repo_gpgcheck=0
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/erlang/gpgkey
       https://github.com/rabbitmq/signing-keys/releases/download/2.0/rabbitmq-release-signing-key.asc
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300

[rabbitmq_erlang-source]
name=rabbitmq_erlang-source
baseurl=https://packagecloud.io/rabbitmq/erlang/el/9/SRPMS
repo_gpgcheck=0
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/erlang/gpgkey
       https://github.com/rabbitmq/signing-keys/releases/download/2.0/rabbitmq-release-signing-key.asc
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300

[rabbitmq_server]
name=rabbitmq_server
baseurl=https://packagecloud.io/rabbitmq/rabbitmq-server/el/9/$basearch
repo_gpgcheck=0
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey
       https://github.com/rabbitmq/signing-keys/releases/download/2.0/rabbitmq-release-signing-key.asc
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300

[rabbitmq_server-source]
name=rabbitmq_server-source
baseurl=https://packagecloud.io/rabbitmq/rabbitmq-server/el/9/SRPMS
repo_gpgcheck=0
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300
EOF

echo "安装依赖 ..."
dnf makecache
dnf install epel-release systemd rabbitmq-server python3.12 mongodb-org-server mongodb-mongosh python3.12-devel gcc-c++ git nginx fontconfig unzip wget nss nspr atk at-spi2-atk cups-libs libdrm at-spi2-core libX11 libXcomposite libXdamage libXext libXfixes libXrandr libgbm libxcb libxkbcommon pango cairo alsa-lib firefox nmap -y


if [ ! -f /usr/local/bin/pip3.12 ]; then
  cd /opt/
  echo "安装 pip3.12"
  python3.12 -m venv /opt/venv
  source /opt/venv/bin/activate
  python3.12 -m ensurepip --default-pip
  python3.12 -m pip install --upgrade pip
  echo "检查 virtualenv pip 版本 ..."
  pip --version
fi

if ! command -v nuclei &> /dev/null
then
  echo "安装 nuclei (最新版本)..."
  # 获取最新版本号
  LATEST_TAG=$(curl -s https://api.github.com/repos/projectdiscovery/nuclei/releases/latest | grep '"tag_name":' | cut -d'"' -f4)
  # 去掉版本号中的 "v" 前缀
  LATEST_VERSION=${LATEST_TAG#v}
  echo "Nuclei 最新版本: $LATEST_TAG"

  # 下载最新版本
  wget -c "https://github.com/projectdiscovery/nuclei/releases/download/$LATEST_TAG/nuclei_${LATEST_VERSION}_linux_amd64.zip" -O nuclei.zip
  unzip -q nuclei.zip -d /opt/nuclei/
  mv /opt/nuclei/nuclei /usr/bin/
  rm -rf nuclei.zip /opt/nuclei/
  nuclei -ut
fi


if ! command -v wih &> /dev/null
then
  echo "安装 wih ..."
  ## 安装 WIH
  wget -c https://github.com/naxg/ARL/raw/main/tools/wih/wih_linux_amd64 -O /usr/bin/wih && chmod +x /usr/bin/wih
  wih --version
fi

# 验证 Firefox 安装
echo "验证 Firefox 安装 ..."
firefox --version

if ! command -v geckodriver &> /dev/null
then
  echo "安装 geckodriver ..."
  wget -c https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz -O geckodriver.tar.gz
  tar -xzf geckodriver.tar.gz
  mv geckodriver /usr/local/bin/
  chmod +x /usr/local/bin/geckodriver
  rm geckodriver.tar.gz

  # 验证 geckodriver 安装
  echo "验证 geckodriver 安装 ..."
  geckodriver -V
fi


echo "启动服务 ..."
mkdir -p /etc/rabbitmq
# 幂等追加 RabbitMQ 配置：内存水位与消费者超时
grep -q '^vm_memory_high_watermark\.relative' /etc/rabbitmq/rabbitmq.conf 2>/dev/null || echo 'vm_memory_high_watermark.relative = 0.6' >> /etc/rabbitmq/rabbitmq.conf
grep -q '^consumer_timeout' /etc/rabbitmq/rabbitmq.conf 2>/dev/null || echo 'consumer_timeout = 14400000' >> /etc/rabbitmq/rabbitmq.conf

systemctl enable mongod
systemctl restart mongod
systemctl enable rabbitmq-server
systemctl restart rabbitmq-server

if [ ! -d ARL ]; then
  echo "克隆 ARL 项目 ..."
  git clone -b main --depth 1 https://github.com/naxg/ARL
fi

if [ ! -d "ARL-NPoC" ]; then
  echo "移动 ARL-NPoC 项目 ..."
  mv ARL/tools/ARL-NPoC ARL-NPoC
fi

cd /opt/ARL-NPoC
echo "安装 PoC 依赖 ..."
pip install -r requirements.txt
pip install -e .
cd ../

if [ ! -f /usr/local/bin/ncrack ]; then
  echo "下载 ncrack ..."
  if wget -c https://github.com/naxg/ARL/raw/main/tools/ncrack -O /usr/local/bin/ncrack; then
    chmod +x /usr/local/bin/ncrack
    echo "ncrack 下载成功"
  else
    echo "ncrack 下载失败"
  fi
fi

mkdir -p /usr/local/share/ncrack
if [ ! -f /usr/local/share/ncrack/ncrack-services ]; then
  echo "下载 ncrack-services ..."
  if wget -c https://github.com/naxg/ARL/raw/main/tools/ncrack-services -O /usr/local/share/ncrack/ncrack-services; then
    echo "ncrack-services 下载成功"
  else
    echo "ncrack-services 下载失败"
  fi
fi

mkdir -p /data/GeoLite2

# 获取最新版本号
echo "获取最新 GeoLite2 版本 ..."
LATEST_TAG=$(curl -s https://api.github.com/repos/P3TERX/GeoLite.mmdb/releases/latest | grep '"tag_name":' | cut -d'"' -f4)

if [ -z "$LATEST_TAG" ]; then
  echo "⚠️  无法获取最新版本，使用本地版本"
  LATEST_TAG="2024.01.01"  # fallback
else
  echo "📅 最新版本: $LATEST_TAG"
fi

# 下载 GeoLite2-ASN.mmdb
if [ ! -f /data/GeoLite2/GeoLite2-ASN.mmdb ]; then
  echo "下载 GeoLite2-ASN.mmdb (v$LATEST_TAG) ..."
  if wget -c "https://github.com/P3TERX/GeoLite.mmdb/releases/download/$LATEST_TAG/GeoLite2-ASN.mmdb" \
    -O /data/GeoLite2/GeoLite2-ASN.mmdb; then
    echo "✅ GeoLite2-ASN.mmdb 下载成功"
  else
    echo "❌ GeoLite2-ASN.mmdb 下载失败"
  fi
fi

# 下载 GeoLite2-City.mmdb
if [ ! -f /data/GeoLite2/GeoLite2-City.mmdb ]; then
  echo "下载 GeoLite2-City.mmdb (v$LATEST_TAG) ..."
  if wget -c "https://github.com/P3TERX/GeoLite.mmdb/releases/download/$LATEST_TAG/GeoLite2-City.mmdb" \
    -O /data/GeoLite2/GeoLite2-City.mmdb; then
    echo "✅ GeoLite2-City.mmdb 下载成功"
  else
    echo "❌ GeoLite2-City.mmdb 下载失败"
  fi
fi

cd /opt/ARL

if [ ! -f rabbitmq_user ]; then
  echo "添加 rabbitmq 用户"
  rabbitmqctl add_user arl arlpassword
  rabbitmqctl add_vhost arlv2host
  rabbitmqctl set_user_tags arl arltag
  rabbitmqctl set_permissions -p arlv2host arl ".*" ".*" ".*"
  echo "初始化 arl 用户"
  mongosh 127.0.0.1:27017/arl docker/mongo-init.js
fi

echo "安装 arl 依赖 ..."
pip install -r requirements.txt

# 检查 playwright 是否安装成功
if python3 -m playwright --version &> /dev/null; then
  echo "安装 playwright 浏览器 ..."
  playwright install chromium
else
  echo "⚠️ playwright not found, skipping browser installation"
fi

if [ ! -f app/config.yaml ]; then
  echo "创建 config.yaml"
  cp app/config.yaml.example  app/config.yaml
fi

if [ ! -f /etc/nginx/conf.d/arl.conf ]; then
  echo "复制 arl.conf"
  cp misc/arl.conf /etc/nginx/conf.d
fi



if [ ! -f /etc/ssl/certs/dhparam.pem ]; then
  echo "下载 dhparam.pem"
  curl https://ssl-config.mozilla.org/ffdhe2048.txt > /etc/ssl/certs/dhparam.pem
fi




cd /opt/ARL/

echo "生成证书 ..."
chmod +x docker/worker/gen_crt.sh
./docker/worker/gen_crt.sh


if [ ! -f /etc/systemd/system/arl-web.service ]; then
  echo  "复制 arl-web.service"
  cp misc/arl-web.service /etc/systemd/system/
fi

if [ ! -f /etc/systemd/system/arl-worker.service ]; then
  echo  "复制 arl-worker.service"
  cp misc/arl-worker.service /etc/systemd/system/
fi


if [ ! -f /etc/systemd/system/arl-worker-github.service ]; then
  echo  "复制 arl-worker-github.service"
  cp misc/arl-worker-github.service /etc/systemd/system/
fi

if [ ! -f /etc/systemd/system/arl-scheduler.service ]; then
  echo  "复制 arl-scheduler.service"
  cp misc/arl-scheduler.service /etc/systemd/system/
fi

chmod +x /opt/ARL/app/tools/*

echo "启动 arl 服务 ..."

systemctl enable arl-web
systemctl restart arl-web
systemctl enable arl-worker
systemctl restart arl-worker
systemctl enable arl-worker-github
systemctl restart arl-worker-github
systemctl enable arl-scheduler
systemctl restart arl-scheduler
systemctl enable nginx
systemctl restart nginx

#python tools/add_finger.py
#python tools/add_finger_ehole.py

echo "安装完成"
