import threading
from app.helpers import asset_site, asset_domain
from app import utils
from app.helpers.scope import get_scope_by_scope_id
from app.helpers.message_notify import push_email, push_dingding
from app.helpers.asset_site_monitor import is_black_asset_site
from .baseThread import BaseThread
from .fetchSite import fetch_site


logger = utils.get_logger()


class AssetSiteCompare(BaseThread):
    def __init__(self, scope_id):
        self._scope_id = scope_id
        sites = asset_site.find_site_by_scope_id(scope_id)
        logger.info(f"load {len(sites)}  site from {self._scope_id}")
        super().__init__(targets=sites, concurrency=15)
        self.new_site_info_map = {}
        self.mutex = threading.Lock()
        self.site_change_map = {}

    def work(self, site):
        if is_black_asset_site(site):
            logger.debug(f"{site} in black asset site")
            return

        conn = utils.http_req(site)
        item = {
            "title": utils.get_title(conn.content),
            "status": conn.status_code
        }
        with self.mutex:
            self.new_site_info_map[site] = item

    def compare(self):
        site_info_list = asset_site.find_site_info_by_scope_id(scope_id=self._scope_id)
        for site_info in site_info_list:
            curr_site = site_info["site"]
            # 访问不了的站点和黑名单站点，跳过
            if curr_site not in self.new_site_info_map:
                continue

            new_site_info = self.new_site_info_map[curr_site]
            if new_site_info["status"] in [404, 502, 504]:
                continue

            if new_site_info["title"] != site_info["title"]:
                # 只关注标题不为空
                if new_site_info["title"]:
                    self.site_change_map[curr_site] = site_info

            elif new_site_info["status"] != site_info["status"]:
                # 只关注变成200的变化
                if new_site_info["status"] == 200:
                    self.site_change_map[curr_site] = site_info

    def run(self):
        self._run()
        self.compare()

        # 已经用完了省一点空间。
        self.new_site_info_map.clear()

        return self.site_change_map


class AssetSiteMonitor:
    def __init__(self, scope_id):
        self.scope_id = scope_id
        self.status_change_list = []
        self.title_change_list = []
        self.site_change_info_list = []  # 保存变化了的站点信息，用于保存到任务中
        scope_data = get_scope_by_scope_id(self.scope_id)
        if not scope_data:
            raise Exception(f"没有找到资产组 {self.scope_id}")

        self.scope_name = scope_data["name"]

    def compare_status(self, site_info, old_site_info):
        curr_status = site_info["status"]
        old_status = old_site_info["status"]
        curr_site = site_info["site"]

        asset_site_id = old_site_info["_id"]

        if curr_status != old_status:
            item = {
                "site": curr_site,
                "status": curr_status,
                "old_status": old_status
            }
            logger.info(f"{curr_site} status {old_status} => {curr_status}")

            self.update_asset_site(asset_site_id, site_info)
            self.status_change_list.append(item)
            return True

    def compare_title(self, site_info, old_site_info):
        curr_title = site_info["title"]
        old_title = old_site_info["title"]
        curr_site = site_info["site"]

        asset_site_id = old_site_info["_id"]

        if curr_title != old_title:
            item = {
                "site": curr_site,
                "title": curr_title,
                "old_title": old_title
            }

            logger.info(f"{curr_site} title {old_title} => {curr_title}")

            self.update_asset_site(asset_site_id, site_info)

            self.title_change_list.append(item)
            return True

    def build_change_list(self):
        compare = AssetSiteCompare(scope_id=self.scope_id)
        # 根据资产组中的站点去重新请求，并比对状态码和标题。
        site_change_map = compare.run()
        sites = list(site_change_map.keys())

        if not sites:
            logger.info(f"not found change ok site, scope_id: {self.scope_id}")
            return

        logger.info(f"found scope site {len(sites)}, scope_id: {self.scope_id}")

        site_info_list = fetch_site(sites)

        for site_info in site_info_list:
            curr_site = site_info["site"]
            if curr_site not in site_change_map:
                continue

            if "入口" not in site_info["tag"]:
                continue

            old_site_info = site_change_map[curr_site]

            if self.compare_title(site_info, old_site_info):
                self.site_change_info_list.append(site_info)
                continue

            if self.compare_status(site_info, old_site_info):
                self.site_change_info_list.append(site_info)
                continue

    # 对新发现的资产分组站点进行删除操作并添加一条新的数据
    def update_asset_site(self, asset_id, site_info):
        query = {
            "_id": asset_id
        }
        copy_site_info = site_info.copy()
        copy_site_info["scope_id"] = self.scope_id
        curr_date = utils.curr_date_obj()
        copy_site_info["save_date"] = curr_date
        copy_site_info["update_date"] = curr_date

        utils.conn_db("asset_site").delete_one(query)
        utils.conn_db("asset_site").insert_one(copy_site_info)

    def build_status_html_report(self):
        html = ""
        style = 'style="border: 0.5pt solid; font-size: 14px;"'

        table_start = '''<table style="border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="border: 0.5pt solid;">编号</th>
                            <th style="border: 0.5pt solid;">站点</th>
                            <th style="border: 0.5pt solid;">变化前状态码</th>
                            <th style="border: 0.5pt solid;">当前状态码</th>
                        </tr>
                    </thead>
                    <tbody>\n'''
        html += table_start

        tr_cnt = 0
        for item in self.status_change_list:
            tr_cnt += 1
            tr_tag = '<tr><td {}> {} </td><td {}> {} </td><td {}>' \
                     '{}</td> <td {}> {} </td></tr>\n'.format(
                style, tr_cnt, style, item["site"], style, item["old_status"], style, item["status"])

            html += tr_tag
            if tr_cnt > 10:
                break

        html += '</tbody></table>'
        return html

    def build_title_html_report(self):
        html = ""
        style = 'style="border: 0.5pt solid; font-size: 14px;"'

        table_start = '''<table style="border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="border: 0.5pt solid;">编号</th>
                            <th style="border: 0.5pt solid;">站点</th>
                            <th style="border: 0.5pt solid;">变化前标题</th>
                            <th style="border: 0.5pt solid;">当前标题</th>
                        </tr>
                    </thead>
                    <tbody>\n'''
        html += table_start

        tr_cnt = 0
        for item in self.title_change_list:
            tr_cnt += 1
            title = item["title"].replace('>', "&#x3e;").replace('<', "&#x3c;")
            old_title = item["old_title"].replace('>', "&#x3e;").replace('<', "&#x3c;")
            tr_tag = '<tr><td {}> {} </td><td {}> {} </td><td {}>' \
                     '{}</td> <td {}> {} </td></tr>\n'.format(
                style, tr_cnt, style, item["site"], style, old_title, style, title)

            html += tr_tag
            if tr_cnt > 10:
                break

        html += '</tbody></table>'
        return html

    def build_html_report(self):
        html = f" <br/><br/> 新发现标题变化 {len(self.title_change_list)}， 状态码变化 {len(self.status_change_list)}<br/><br/><br/>"

        if self.title_change_list:
            title_html = self.build_title_html_report()
            html += title_html

            html += "\n<br/><br/>\n"

        if self.status_change_list:
            status_html = self.build_status_html_report()
            html += status_html

        return html

    def build_status_markdown_report(self):
        tr_cnt = 0
        markdown = "状态码变化\n\n"

        for item in self.status_change_list:
            tr_cnt += 1
            markdown += "{}. [{}]({})  {} => {} \n".format(tr_cnt,
                                                           item["site"],
                                                           item["site"],
                                                           item["old_status"],
                                                           item["status"]
                                                           )
            if tr_cnt > 5:
                break

        return markdown

    def build_title_markdown_report(self):
        tr_cnt = 0
        markdown = "标题变化\n\n"

        for item in self.title_change_list:
            tr_cnt += 1
            markdown += "{}. [{}]({})  {} => {} \n".format(tr_cnt,
                                                           item["site"],
                                                           item["site"],
                                                           item["old_title"],
                                                           item["title"]
                                                           )
            if tr_cnt > 5:
                break

        return markdown

    def build_markdown_report(self):
        markdown = f"\n站点监控-{self.scope_name} 灯塔消息推送\n\n"

        markdown += f"\n 新发现标题变化 {len(self.title_change_list)}， 状态码变化 {len(self.status_change_list)} \n\n"

        if self.title_change_list:
            markdown += self.build_title_markdown_report()
            markdown += "\n"

        if self.status_change_list:
            markdown += self.build_status_markdown_report()

        return markdown

    def run(self):
        self.build_change_list()
        if not self.status_change_list and not self.title_change_list:
            logger.info(f"not found change by {self.scope_id}")
            return

        html_report = self.build_html_report()
        html_title = f"[站点监控-{self.scope_name}] 灯塔消息推送"
        push_email(title=html_title, html_report=html_report)

        markdown_report = self.build_markdown_report()
        push_dingding(markdown_report=markdown_report)


class Domain2SiteMonitor:
    def __init__(self, scope_id):
        self.scope_id = scope_id
        self.site_info_list = []
        self.html_report = ""
        self.dingding_markdown = ""

    def find_not_domain_site(self):
        sites = asset_site.find_site_by_scope_id(self.scope_id)
        domains = asset_domain.find_domain_by_scope_id(self.scope_id)
        ret = []
        if len(domains) == 0:
            return ret

        logger.info(f"load {len(domains)} domain, scope_id:{self.scope_id}")

        have_domain_site_list = [
            utils.get_hostname(site).split(":")[0]
            for site in sites
        ]

        no_domain_site_list = set(domains) - set(have_domain_site_list)
        ret = [f"https://{domain}" for domain in no_domain_site_list]

        logger.info(f"load {len(ret)} no_domain_site_list, scope_id:{self.scope_id}")

        return ret

    def run(self):
        sites = self.find_not_domain_site()
        if not sites:
            return []

        site_info_list = fetch_site(sites, concurrency=20, http_timeout=(5, 6))

        # 过滤 502, 504
        for site_info in site_info_list:
            if site_info["status"] in [502, 504, 501, 422, 410]:
                continue

            # 过滤400 状态码
            if site_info["status"] == 400 and "400" in site_info["title"]:
                continue

            self.site_info_list.append(site_info)

        self.build_report()

        if self.site_info_list:
            self.insert_asset_site()

        return self.site_info_list

    def insert_asset_site(self):
        for site_info in self.site_info_list:
            site_info = site_info.copy()
            site_info["scope_id"] = self.scope_id
            curr_date = utils.curr_date_obj()
            site_info["save_date"] = curr_date
            site_info["update_date"] = curr_date
            utils.conn_db('asset_site').insert_one(site_info)
        logger.info(f"save asset_site {len(self.site_info_list)} to {self.scope_id}")

    def build_report(self):
        from app.utils.push import dict2table, dict2dingding_mark
        info_list = []
        tr_cnt = 0
        for site_info in self.site_info_list:
            tr_cnt += 1
            if tr_cnt > 8:
                continue

            info = {
                "站点": site_info['site'],
                "标题": site_info['title'],
                "状态码": site_info['status'],
                "页面长度": site_info['body_length']
            }
            info_list.append(info)

        html = f" <br/> 新发现站点 {len(self.site_info_list)} <br/>"

        html += dict2table(info_list)

        mark = f"  新发现站点 {len(self.site_info_list)}  "

        mark += dict2dingding_mark(info_list)

        self.html_report = html
        self.dingding_markdown = mark


def asset_site_monitor(scope_id):
    monitor = AssetSiteMonitor(scope_id=scope_id)
    monitor.run()
