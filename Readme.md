## ARL(Asset Reconnaissance Lighthouse)资产侦察灯塔系统
<a href="https://github.com/adysec/ARL/stargazers"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/adysec/ARL?color=yellow&logo=riseup&logoColor=yellow&style=flat-square"></a>
<a href="https://github.com/naxg/ARL/network/members"><img alt="GitHub forks" src="https://img.shields.io/github/forks/naxg/ARL?color=orange&style=flat-square"></a>
<a href="https://github.com/naxg/ARL/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/naxg/ARL?color=red&style=flat-square"></a>

ARL资产侦察灯塔系统备份项目，**已跑通**

本项目基于 [https://github.com/adysec/ARL](https://github.com/adysec/ARL) 的二次修改


### 简介
旨在快速侦察与目标关联的互联网资产，构建基础资产信息库。
协助甲方安全团队或者渗透测试人员有效侦察和检索资产，发现存在的薄弱点和攻击面。

### 系统要求

建议采用**Docker内源码安装**方式运行。系统配置建议：CPU:4线程 内存:8G 带宽:10M。
由于自动资产发现过程中会有大量的的发包，建议采用云服务器可以带来更好的体验。

### Docker 内源码安装（最新版，需要为境外网络环境，且网络稳定）

```bass
sudo docker run --privileged -it -d -p 5003:5003 --name=arl --restart=always rockylinux/rockylinux:9-ubi-init /usr/sbin/init
docker exec -it arl bash
# docker内运行，通过源码安装ARL
curl https://raw.githubusercontent.com/naxg/ARL/main/misc/setup-arl.sh >install.sh
bash install.sh
exit
```

docker内执行后直接exit退出即可


默认端口5003 (https), 默认用户名密码admin/arlpass 


### ARL修改

```
# 一键删站
docker stop arl && docker rm arl

# 删除镜像
docker rmi arl

# 改poc，poc位置/opt/ARL-NPoC
docker exec -it arl bash
systemctl restart arl*
```
 


### 二次修改说明

本次二次开发聚焦于以下改进：
- 升级运行时环境，将 Python 从 3.6 提升至 3.12.x，以获得最新的性能优化。
- 将 MongoDB 版本从 4.x 升级至 6.x，提升数据存储稳定性与可扩展性。
- 修复历史遗留问题，优化系统整体可用性。
- 使用 [subfinder](https://github.com/projectdiscovery/subfinder) 替代原 API 查询请求进行子域名收集，提升发现效率与准确性。

**subfinder 文件路径：** `/opt/ARL/app/services/dns_query_plugin/subfinder`

**subfinder 配置文件路径：** `/opt/ARL/app/services/dns_query_plugin/provider-config.yaml`

例子：
```yaml
binaryedge:
  - 0bf8919b-aab9-42e4-9574-d3b639324597
  - ac244e2f-b635-4581-878a-33f4e79a2c13
censys:
  - ac244e2f-b635-4581-878a-33f4e79a2c13:dd510d6e-1b6e-4655-83f6-f347b363def9
certspotter: []
passivetotal:
  - sample-email@user.com:sample_password
redhuntlabs:
  - ENDPOINT:API_TOKEN
  - https://reconapi.redhuntlabs.com/community/v1/domains/subdomains:joEPzJJp2AuOCw7teAj63HYrPGnsxuPQ
securitytrails: []
shodan:
  - AAAAClP1bJJSRMEYJazgwhJKrggRwKA
github:
  - ghp_lkyJGU3jv1xmwk4SDXavrLDJ4dl2pSJMzj4X
  - ghp_gkUuhkIYdQPj13ifH4KA3cXRn8JD2lqir2d4
zoomeyeapi:
  - zoomeye.hk:4f73021d-ff95-4f53-937f-83d6db719eec
quake:
  - 0cb9030c-0a40-48a3-b8c4-fca28e466ba3
facebook:
  - APP_ID:APP_SECRET
intelx:
  - HOST:API_KEY
  - 2.intelx.io:s4324-b98b-41b2-220e8-3320f6a1284d
```

**API 配置说明：** 详细的 API 配置方法请参考 [subfinder 官方文档](https://docs.projectdiscovery.io/opensource/subfinder/install#post-install-configuration)