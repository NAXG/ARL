import json
import os.path
import subprocess
import re

from app.config import Config
from app import utils

# 预编译正则表达式模式
DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
IP_PORT_PATTERN = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?::\d+)?$')


logger = utils.get_logger()


class NucleiScan:
    __slots__ = ('targets', 'nuclei_target_path', 'nuclei_result_path', 'nuclei_bin_path', 'nuclei_json_flag')

    def __init__(self, targets: list):
        self.targets = targets

        tmp_path = Config.TMP_PATH
        rand_str = utils.random_choices()

        self.nuclei_target_path = os.path.join(tmp_path,
                                               f"nuclei_target_{rand_str}.txt")

        self.nuclei_result_path = os.path.join(tmp_path,
                                               f"nuclei_result_{rand_str}.json")

        self.nuclei_bin_path = "nuclei"

        # 在nuclei 2.9.1 中 将-json 参数改成了 -jsonl 参数。
        self.nuclei_json_flag = None

    def _check_json_flag(self):
        json_flag = ["-json", "-jsonl"]
        for x in json_flag:
            command = [self.nuclei_bin_path, "-duc", x, "-version"]
            pro = subprocess.run(command, capture_output=True)
            if pro.returncode == 0:
                self.nuclei_json_flag = x
                return

        assert self.nuclei_json_flag

    def _delete_file(self):
        try:
            os.unlink(self.nuclei_target_path)
            # 删除结果临时文件
            if os.path.exists(self.nuclei_result_path):
                os.unlink(self.nuclei_result_path)
        except Exception as e:
            logger.warning(e)

    def check_have_nuclei(self) -> bool:
        command = [self.nuclei_bin_path, "-version"]
        try:
            pro = subprocess.run(command, capture_output=True)
            if pro.returncode == 0:
                return True
        except Exception as e:
            logger.debug(f"{str(e)}")

        return False

    def _gen_target_file(self):
        """使用推导式和类型一致的文件写入"""
        # 使用局部变量优化
        strip_func = str.strip
        domain_pattern = DOMAIN_PATTERN
        ip_port_pattern = IP_PORT_PATTERN

        # 使用推导式过滤有效目标，保持类型一致（始终为 str）
        valid_targets = [
            str(domain).strip()  # 保持类型一致：始终为 str
            for domain in self.targets
            if domain and isinstance(domain, (str, int))  # 确保基本有效性
        ]

        # 进一步验证格式
        valid_targets = [
            target for target in valid_targets
            if domain_pattern.match(target) or ip_port_pattern.match(target)
        ]

        # 批量写入文件
        with open(self.nuclei_target_path, "w") as f:
            f.write('\n'.join(valid_targets))
            if valid_targets:  # 确保文件以换行符结尾
                f.write('\n')

    def dump_result(self) -> list:
        """使用推导式替代循环构建结果列表（PEP 709 优化）"""
        # 使用局部变量优化频繁调用的函数
        logger_warning = logger.warning

        try:
            with open(self.nuclei_result_path) as f:
                # 使用推导式替代 while 循环，提升性能
                results = [
                    {
                        "template_url": str(data.get("template-url", "")),      # 保持类型一致：始终为 str
                        "template_id": str(data.get("template-id", "")),        # 保持类型一致：始终为 str
                        "vuln_name": str(data.get("info", {}).get("name", "")), # 保持类型一致：始终为 str
                        "vuln_severity": str(data.get("info", {}).get("severity", "")), # 保持类型一致：始终为 str
                        "vuln_url": str(data.get("matched-at", "")),            # 保持类型一致：始终为 str
                        "curl_command": str(data.get("curl-command", "")),      # 保持类型一致：始终为 str
                        "target": str(data.get("host", ""))                     # 保持类型一致：始终为 str
                    }
                    for line in f
                    if line.strip()  # 跳过空行
                    for data in [self._safe_load_json(line)]  # 安全的 JSON 加载
                    if data  # 确保数据有效
                ]

                return results

        except FileNotFoundError:
            logger_warning(f"Result file not found: {self.nuclei_result_path}")
            return []
        except Exception as e:
            logger_warning(f"Error reading results: {e}")
            return []

    def _safe_load_json(self, line):
        """安全的 JSON 加载，避免异常中断"""
        try:
            return json.loads(line.strip())
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to parse JSON line: {e}")
            return None

    def exec_nuclei(self):
        self._gen_target_file()

        command = [self.nuclei_bin_path, "-duc",
                   "-tags cve",
                   "-severity low,medium,high,critical",
                   "-type http",
                   f"-l {self.nuclei_target_path}",
                   self.nuclei_json_flag,  # 在nuclei 2.9.1 中 将 -json 参数改成了 -jsonl 参数
                   "-stats",
                   "-stats-interval 60",
                   f"-o {self.nuclei_result_path}",
                   ]

        logger.info(" ".join(command))
        utils.exec_system(command, timeout=96*60*60)

    def run(self):
        if not self.check_have_nuclei():
            logger.warning("not found nuclei")
            return []

        self._check_json_flag()

        self.exec_nuclei()

        results = self.dump_result()

        # 删除临时文件
        self._delete_file()

        return results


def nuclei_scan(targets: list):
    if not targets:
        return []

    n = NucleiScan(targets=targets)
    return n.run()

