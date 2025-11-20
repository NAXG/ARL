import os
import json
from xing.core import PluginType, PluginRunner
from xing.utils import load_plugins
from xing.conf import Conf as npoc_conf
from app import utils
from app.modules import PoCCategory
from app.config import Config

logger = utils.get_logger()


class NPoC:
    """docstring for ClassName"""

    def __init__(self, concurrency=6, tmp_dir="./"):
        super().__init__()
        self._plugins = None
        self._poc_info_list = None
        self.concurrency = concurrency
        self._plugin_name_list = None
        self.plugin_name_set = set()
        self._db_plugin_name_list = None
        self.tmp_dir = tmp_dir
        self.runner = None
        self.result = []
        self.brute_plugin_name_set = set()
        self.poc_plugin_name_set = set()
        self.sniffer_plugin_name_set = set()

    @property
    def plugin_name_list(self) -> list:
        """ xing 中插件名称列表 """

        if self._plugin_name_list is None:
            # 触发下调用
            self.poc_info_list
            self._plugin_name_list = list(self.plugin_name_set)

        return self._plugin_name_list

    @property
    def db_plugin_name_list(self) -> list:
        """ 数据库中插件名称列表 """
        if self._db_plugin_name_list is None:
            self._db_plugin_name_list = [
                item["plugin_name"] for item in utils.conn_db('poc').find({})
            ]

        return self._db_plugin_name_list

    @property
    def plugins(self) -> list:
        """ xing 中插件实例列表 """
        if self._plugins is None:
            self._plugins = self.load_all_poc()

        return self._plugins

    @property
    def poc_info_list(self) -> list:
        """ xing 中插件信息列表 """
        if self._poc_info_list is None:
            self._poc_info_list = self.gen_poc_info()

        return self._poc_info_list

    def load_all_poc(self):
        plugins = load_plugins(os.path.join(npoc_conf.PROJECT_DIRECTORY, "plugins"))
        return [
            plugin
            for plugin in plugins
            if plugin.plugin_type
            in {PluginType.POC, PluginType.BRUTE, PluginType.SNIFFER}
        ]

    def gen_poc_info(self):
        info_list = []
        for p in self.plugins:
            info = dict()
            info["plugin_name"] = getattr(p, "_plugin_name", "")
            if p.plugin_type == PluginType.SNIFFER:
                self.sniffer_plugin_name_set.add(info["plugin_name"])
                continue

            info["app_name"] = p.app_name
            info["scheme"] = ",".join(p.scheme)
            info["vul_name"] = p.vul_name
            info["plugin_type"] = p.plugin_type

            if p.plugin_type == PluginType.POC:
                info["category"] = PoCCategory.POC
                self.poc_plugin_name_set.add(info["plugin_name"])

            if p.plugin_type == PluginType.BRUTE:
                self.brute_plugin_name_set.add(info["plugin_name"])
                if "http" in info["scheme"]:
                    info["category"] = PoCCategory.WEBB_RUTE
                else:
                    info["category"] = PoCCategory.SYSTEM_BRUTE

            if info["plugin_name"] in self.plugin_name_set:
                logger.warning("plugin {} already exists".format(info["plugin_name"]))
                continue
            self.plugin_name_set.add(info["plugin_name"])
            info_list.append(info)

        return info_list

    def sync_to_db(self):
        for old in self.poc_info_list:
            new = old.copy()
            plugin_name = old["plugin_name"]
            new["update_date"] = utils.curr_date()

            try:
                # 使用upsert操作 - 存在则更新，不存在则插入
                utils.conn_db('poc').update_one(
                    {"plugin_name": plugin_name},
                    {"$set": new},
                    upsert=True
                )
                logger.info(f"sync {plugin_name} info to db (upsert)")
            except Exception as e:
                logger.error(f"sync plugin {plugin_name} failed: {e}")

        return True

    def delete_db(self):
        for name in self.db_plugin_name_list:
            if name not in self.plugin_name_list:
                query = {"plugin_name": name}
                utils.conn_db('poc').delete_one(query)

        return True

    def run_poc(self, plugin_name_list, targets):
        self.result = []
        npoc_conf.SAVE_TEXT_RESULT_FILENAME = ""
        random_file = os.path.join(self.tmp_dir, f"npoc_result_{utils.random_choices()}.txt")
        npoc_conf.SAVE_JSON_RESULT_FILENAME = random_file
        plugins = self.filter_plugin_by_name(plugin_name_list)

        runner = PluginRunner.PluginRunner(plugins=plugins, targets=targets, concurrency=self.concurrency)
        self.runner = runner
        runner.run()

        if not os.path.exists(random_file):
            return self.result

        self.result = [json.loads(item) for item in utils.load_file(random_file)]

        os.unlink(random_file)

        return self.result

    def run_all_poc(self, targets):
        return self.run_poc(self.plugin_name_list, targets)

    def filter_plugin_by_name(self, plugin_name_list):
        return [
            plugin
            for plugin in self.plugins
            if (curr_name := getattr(plugin, "_plugin_name", ""))
            and curr_name in plugin_name_list
        ]


def sync_to_db(del_flag=False):
    n = NPoC()
    n.sync_to_db()
    if del_flag:
        n.delete_db()
    return True


def run_risk_cruising(plugins, targets):
    n = NPoC(tmp_dir=Config.TMP_PATH, concurrency=8)
    return n.run_poc(plugins, targets)


def run_sniffer(targets):
    n = NPoC(concurrency=15, tmp_dir=Config.TMP_PATH)
    n.plugin_name_list
    #  跳过80 和 443 的识别
    new_targets = [
        stripped
        for t in targets
        for stripped in (t.strip(),)
        if not stripped.endswith(":80")
        and not stripped.endswith(":443")
    ]

    items = n.run_poc(n.sniffer_plugin_name_set, new_targets)

    def _parse_target(target):
        scheme, rest = target.split("://", 1)
        host, port = rest.split(":", 1)
        return scheme, host, port

    return [
        {
            "scheme": scheme,
            "host": host,
            "port": port,
            "target": target,
        }
        for result in items
        if (target := result["verify_data"]) and "://" in target
        for scheme, host, port in (_parse_target(target),)
    ]
