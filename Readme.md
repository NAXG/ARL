## ARL(Asset Reconnaissance Lighthouse)资产侦察灯塔系统
<a href="https://github.com/adysec/ARL/stargazers"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/adysec/ARL?color=yellow&logo=riseup&logoColor=yellow&style=flat-square"></a>
<a href="https://github.com/adysec/ARL/network/members"><img alt="GitHub forks" src="https://img.shields.io/github/forks/adysec/ARL?color=orange&style=flat-square"></a>
<a href="https://github.com/adysec/ARL/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/adysec/ARL?color=red&style=flat-square"></a>

ARL资产侦察灯塔系统备份项目，**已跑通**

本项目基于 [https://github.com/adysec/ARL](https://github.com/adysec/ARL) 的二次修改

### 二次修改说明

本次修改采用 [subfinder](https://github.com/projectdiscovery/subfinder) 替代原来的 API 查询请求进行子域名收集，提升子域名发现的效率和准确性。

**subfinder 文件路径：** `/opt/ARL/app/services/dns_query_plugin/subfinder`

**subfinder 配置文件路径：** `/opt/ARL/app/services/dns_query_plugin/provider-config.yaml`

**API 配置说明：** 详细的 API 配置方法请参考 [subfinder 官方文档](https://docs.projectdiscovery.io/opensource/subfinder/install#post-install-configuration)

### 简介
旨在快速侦察与目标关联的互联网资产，构建基础资产信息库。
协助甲方安全团队或者渗透测试人员有效侦察和检索资产，发现存在的薄弱点和攻击面。

### 系统要求

建议采用**Docker内源码安装**或**Docker内源码安装**方式运行。系统配置建议：CPU:4线程 内存:8G 带宽:10M。
由于自动资产发现过程中会有大量的的发包，建议采用云服务器可以带来更好的体验。

如遇mongod服务问题导致`timeout of 12000ms exceeded`，请尝试在docker启动中加入路径`-v /sys/fs/cgroup:/sys/fs/cgroup`

### Docker 内源码安装（最新版，需要为境外网络环境，且网络稳定）

```bass
sudo docker run --privileged -it -d -p 5003:5003 --name=arl --restart=always centos /usr/sbin/init
docker exec -it arl bash
# docker内运行，通过源码安装ARL
curl https://raw.githubusercontent.com/naxg/ARL/master/misc/setup-arl.sh >install.sh
bash install.sh
exit
```

docker内执行后直接exit退出即可

Ubuntu 下可以直接执行 `apt-get install docker.io docker-compose -y` 安装相关依赖

### 源码安装

原版ARL仅适配centos 7，我更新至仅支持centos8（centos:latest）
如果在其他目录可以创建软连接，且安装了四个服务分别为`arl-web`, `arl-worker`, `arl-worker-github`, `arl-scheduler`

```
wget https://raw.githubusercontent.com/naxg/ARL/master/misc/setup-arl.sh
chmod +x setup-arl.sh
./setup-arl.sh
```
### 查看服务状态

```
systemctl status arl-web
systemctl status arl-worker
systemctl status arl-worker-github
systemctl status arl-scheduler
```
### ARL修改

```
# 一键删站
docker stop arl && docker rm arl

# 删除镜像
docker rmi arl

# 改poc，poc位置/opt/ARL-NPoC
docker exec -it arl bash
systemctl restart arl*

# 改指纹，/opt/ARL/tools/指纹数据.json
docker exec -it arl bash
cd /opt/ARL && python3.6 tools/add_finger.py
```
### 特性

1. 域名资产发现和整理
2. IP/IP 段资产整理
3. 端口扫描和服务识别
4. WEB 站点指纹识别
5. 资产分组管理和搜索
6. 任务策略配置
7. 计划任务和周期任务
8. Github 关键字监控
9. 域名/IP 资产监控
10. 站点变化监控
11. 文件泄漏等风险检测
12. nuclei PoC 调用
13. [WebInfoHunter](https://tophanttechnology.github.io/ARL-doc/function_desc/web_info_hunter/) 调用和监控

### 配置
   默认端口5003 (https), 默认用户名密码admin/arlpass  