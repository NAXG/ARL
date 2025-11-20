import nmap
import re

from app import utils
from app.config import Config
from app.utils import is_valid_exclude_ports

logger = utils.get_logger()

# 预编译正则表达式模式
IP_PATTERN = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
PORT_PATTERN = re.compile(r'^\d+$')


class PortScan:
    __slots__ = ('targets', 'ports', 'max_host_group', 'alive_port', 'nmap_arguments', 'max_retries',
                 'host_timeout', 'parallelism', 'min_rate', 'exclude_ports')

    def __init__(self, targets, ports=None, service_detect=False, os_detect=False,
                 port_parallelism=None, port_min_rate=None, custom_host_timeout=None,
                 exclude_ports=None,
                 ):
        self.targets = " ".join(targets)
        self.ports = ports
        self.max_host_group = 32
        self.alive_port = "22,80,443,843,3389,8007-8011,8443,9090,8080-8091,8093,8099,5000-5004,2222,3306,1433,21,25"
        self.nmap_arguments = "-sT -n --open"
        self.max_retries = 3
        self.host_timeout = 60*5
        self.parallelism = port_parallelism  # 默认 32
        self.min_rate = port_min_rate  # 默认64
        self.exclude_ports = exclude_ports

        if service_detect:
            self.host_timeout += 60 * 5
            self.nmap_arguments += " -sV"

        if os_detect:
            self.host_timeout += 60 * 4
            self.nmap_arguments += " -O"

        if len(self.ports.split(",")) > 60:
            self.nmap_arguments += f" -PE -PS{self.alive_port}"
            self.max_retries = 2
        else:
            if self.ports != "0-65535":
                self.nmap_arguments += " -Pn"

        if self.ports == "0-65535":
            self.max_host_group = 2
            self.min_rate = max(self.min_rate, 800)
            self.parallelism = max(self.parallelism, 128)

            self.nmap_arguments += f" -PE -PS{self.alive_port}"
            self.host_timeout += 60 * 5
            self.max_retries = 2

        self.nmap_arguments += " --max-rtt-timeout 800ms"
        self.nmap_arguments += f" --min-rate {self.min_rate}"
        self.nmap_arguments += " --script-timeout 6s"
        self.nmap_arguments += f" --max-hostgroup {self.max_host_group}"

        # 依据传过来的超时为准，保持类型一致（始终为 int）
        if custom_host_timeout is not None:
            try:
                timeout_value = int(custom_host_timeout)
                if timeout_value > 0:
                    self.host_timeout = timeout_value
            except (ValueError, TypeError):
                logger.warning(f"Invalid custom_host_timeout value: {custom_host_timeout}, using default: {self.host_timeout}")
        self.nmap_arguments += f" --host-timeout {self.host_timeout}s"
        self.nmap_arguments += f" --min-parallelism {self.parallelism}"
        self.nmap_arguments += f" --max-retries {self.max_retries}"

        if self.exclude_ports is not None:
            if self.exclude_ports != "" and\
                    is_valid_exclude_ports(self.exclude_ports):
                self.nmap_arguments += f" --exclude-ports {self.exclude_ports}"

    def run(self):
        logger.info(f"nmap target {self.targets[:20]}  ports {self.ports[:20]}  arguments {self.nmap_arguments}")
        nm = nmap.PortScanner()
        nm.scan(hosts=self.targets, ports=self.ports, arguments=self.nmap_arguments)

        # 使用局部变量优化频繁访问
        all_hosts = nm.all_hosts()
        logger_debug = logger.debug

        # 使用推导式替代循环构建列表（PEP 709 优化）
        ip_info_list = [
            {
                "ip": host,
                "port_info": self._build_port_info_list(nm, host),
                "os_info": self.os_match_by_accuracy(nm[host].get("osmatch", []))
            }
            for host in all_hosts
        ]

        logger_debug(f"Port scan completed for {len(ip_info_list)} hosts")
        return ip_info_list

    def _build_port_info_list(self, nm, host):
        """使用推导式构建端口信息列表，保持类型一致"""
        port_info_list = []

        for proto in nm[host].all_protocols():
            port_len = len(nm[host][proto])

            # 使用推导式替代循环，保持 port_id 始终为 int 类型
            proto_ports = [
                {
                    "port_id": int(port),  # 保持类型一致：始终为 int
                    "service_name": str(nm[host][proto][port]["name"]),     # 保持类型一致：始终为 str
                    "version": str(nm[host][proto][port]["version"]),       # 保持类型一致：始终为 str
                    "product": str(nm[host][proto][port]["product"]),       # 保持类型一致：始终为 str
                    "protocol": str(proto)                                  # 保持类型一致：始终为 str
                }
                for port in nm[host][proto]
                if not (port_len > 600 and port not in [80, 443])  # 过滤条件
            ]

            port_info_list.extend(proto_ports)

        return port_info_list

    def os_match_by_accuracy(self, os_match_list):
        """使用局部变量优化和类型一致性的 OS 匹配"""
        # 将 int 转换提前，保持类型一致
        for os_match in os_match_list:
            accuracy_str = os_match.get('accuracy', '0')
            try:
                accuracy = int(accuracy_str)
                if accuracy > 90:
                    return os_match
            except (ValueError, TypeError):
                continue

        return {}


def port_scan(targets, ports=Config.TOP_10, service_detect=False, os_detect=False,
              port_parallelism=32, port_min_rate=64, custom_host_timeout=None, exclude_ports=None):
    targets = list(set(targets))
    targets = list(filter(utils.not_in_black_ips, targets))
    ps = PortScan(targets=targets, ports=ports, service_detect=service_detect, os_detect=os_detect,
                  port_parallelism=port_parallelism, port_min_rate=port_min_rate,
                  custom_host_timeout=custom_host_timeout,
                  exclude_ports=exclude_ports,
                  )
    return ps.run()
