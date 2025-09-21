set -e

cd /opt/

tee /etc/resolv.conf <<"EOF"
nameserver 180.76.76.76
nameserver 4.2.2.1
nameserver 1.1.1.1
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

echo "install dependencies ..."
cd /opt/
dnf update -y
dnf install epel-release -y
dnf install systemd -y
dnf install rabbitmq-server -y
dnf install python3.12 mongodb-org-server mongodb-mongosh python3.12-devel gcc-c++ git nginx fontconfig unzip wget -y


if [ ! -f /usr/local/bin/pip3.12 ]; then
  echo "install  pip3.12"
  python3.12 -m venv /opt/venv
  source /opt/venv/bin/activate
  python3.12 -m ensurepip --default-pip
  python3.12 -m pip install --upgrade pip
fi

echo "check virtualenv pip version ..."
pip --version


if ! command -v nmap &> /dev/null
then
    echo "install nmap ..."
    dnf install nmap -y
fi


if ! command -v nuclei &> /dev/null
then
  echo "install nuclei"
  wget -c https://github.com/naxg/ARL/raw/2.6.7/tools/nuclei.zip -O nuclei.zip
  unzip nuclei.zip && mv nuclei /usr/bin/ && rm -f nuclei.zip
  nuclei -ut
  rm -rf /opt/*
fi


if ! command -v wih &> /dev/null
then
  echo "install wih ..."
  ## 安装 WIH
  wget -c https://github.com/naxg/ARL/raw/main/tools/wih/wih_linux_amd64 -O /usr/bin/wih && chmod +x /usr/bin/wih
  wih --version
fi


echo "start services ..."
mkdir -p /etc/rabbitmq && \
echo 'vm_memory_high_watermark.relative = 0.6' >> /etc/rabbitmq/rabbitmq.conf

systemctl enable mongod
systemctl restart mongod
systemctl enable rabbitmq-server
systemctl restart rabbitmq-server

cd /opt
if [ ! -d ARL ]; then
  echo "git clone ARL proj"
  git clone -b 2.6.7 https://github.com/naxg/ARL
fi

if [ ! -d "ARL-NPoC" ]; then
  echo "mv ARL-NPoC proj"
 mv ARL/tools/ARL-NPoC ARL-NPoC
fi

cd /opt/ARL-NPoC
echo "install poc requirements ..."
pip install -r requirements.txt
pip install -e .
cd ../

if [ ! -f /usr/local/bin/ncrack ]; then
  echo "Download ncrack ..."
  wget -c https://github.com/naxg/ARL/raw/main/tools/ncrack -O /usr/local/bin/ncrack
  chmod +x /usr/local/bin/ncrack
fi

mkdir -p /usr/local/share/ncrack
if [ ! -f /usr/local/share/ncrack/ncrack-services ]; then
  echo "Download ncrack-services ..."
  wget -c https://github.com/naxg/ARL/raw/main/tools/ncrack-services -O /usr/local/share/ncrack/ncrack-services
fi

mkdir -p /data/GeoLite2
if [ ! -f /data/GeoLite2/GeoLite2-ASN.mmdb ]; then
  echo "download GeoLite2-ASN.mmdb ..."
  wget -c https://github.com/naxg/ARL/raw/main/tools/GeoLite2-ASN.mmdb -O /data/GeoLite2/GeoLite2-ASN.mmdb
fi

if [ ! -f /data/GeoLite2/GeoLite2-City.mmdb ]; then
  echo "download GeoLite2-City.mmdb ..."
  wget -c https://github.com/naxg/ARL/raw/main/tools/GeoLite2-City.mmdb -O /data/GeoLite2/GeoLite2-City.mmdb
fi

cd /opt/ARL

if [ ! -f rabbitmq_user ]; then
  touch rabbitmq_user
  echo "add rabbitmq user"
  rabbitmqctl add_user arl arlpassword
  rabbitmqctl add_vhost arlv2host
  rabbitmqctl set_user_tags arl arltag
  rabbitmqctl set_permissions -p arlv2host arl ".*" ".*" ".*"
  echo "init arl user"
  mongosh 127.0.0.1:27017/arl docker/mongo-init.js
fi

echo "install arl requirements ..."
pip install -r requirements.txt

if [ ! -f app/config.yaml ]; then
  echo "create config.yaml"
  cp app/config.yaml.example  app/config.yaml
fi

if [ ! -f /usr/bin/phantomjs ]; then
  echo "install phantomjs"
  ln -s `pwd`/app/tools/phantomjs  /usr/bin/phantomjs
fi

if [ ! -f /etc/nginx/conf.d/arl.conf ]; then
  echo "copy arl.conf"
  cp misc/arl.conf /etc/nginx/conf.d
fi



if [ ! -f /etc/ssl/certs/dhparam.pem ]; then
  echo "download dhparam.pem"
  curl https://ssl-config.mozilla.org/ffdhe2048.txt > /etc/ssl/certs/dhparam.pem
fi




echo "gen cert ..."
chmod +x docker/worker/gen_crt.sh
./docker/worker/gen_crt.sh


cd /opt/ARL/


if [ ! -f /etc/systemd/system/arl-web.service ]; then
  echo  "copy arl-web.service"
  cp misc/arl-web.service /etc/systemd/system/
fi

if [ ! -f /etc/systemd/system/arl-worker.service ]; then
  echo  "copy arl-worker.service"
  cp misc/arl-worker.service /etc/systemd/system/
fi


if [ ! -f /etc/systemd/system/arl-worker-github.service ]; then
  echo  "copy arl-worker-github.service"
  cp misc/arl-worker-github.service /etc/systemd/system/
fi

if [ ! -f /etc/systemd/system/arl-scheduler.service ]; then
  echo  "copy arl-scheduler.service"
  cp misc/arl-scheduler.service /etc/systemd/system/
fi

chmod +x /opt/ARL/app/tools/*

echo "start arl services ..."

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

python tools/add_finger.py
python tools/add_finger_ehole.py

echo "install done"