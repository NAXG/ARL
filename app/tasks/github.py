from bson import ObjectId
from app.services import github_search
from app.services.githubSearch import GithubResult
from app.modules import TaskStatus
from app import utils
from app.config import Config
from app.utils import push

logger = utils.get_logger()


class GithubTaskTask:
    def __init__(self, task_id, keyword):
        self.task_id = task_id
        self.keyword = keyword
        self.collection = "github_task"
        self.results = []

    def search_result(self):
        self.update_status("search")
        results = github_search(keyword=self.keyword)
        self.results.extend(results)

    def save_content(self):
        self.update_status(f"fetch content-{len(self.results)}")
        items_to_insert = []
        for result in self.results:
            if not isinstance(result, GithubResult):
                continue

            if self.filter_result(result):
                continue

            item = self.result_to_dict(result)
            items_to_insert.append(item)

        if items_to_insert:
            utils.conn_db("github_result").insert_many(items_to_insert)

    def result_to_dict(self, result):
        item = result.to_dict()
        item["human_content"] = result.human_content(self.keyword)
        item["keyword"] = self.keyword
        item["github_task_id"] = self.task_id
        return item

    def filter_result(self, result: GithubResult):
        path_keyword_list = ["open-app-filter/", "/adbyby",
                             "/adblock", "luci-app-dnsfilter/",
                             "Spider/", "/spider", "_files/",
                             "alexa_10k.json", "/WeWorkProviderTest.php"]
        for path in path_keyword_list:
            if path in result.path:
                return True

        content_keyword_list = ["DOMAIN-SUFFIX", "HOST-SUFFIX", "name:[proto;sport;dport;host",
                                '  "websites": [',
                                "import android.app.Application;",
                                "import android.app.Activity;"]
        for keyword in content_keyword_list:
            if keyword in result.content:
                return True

        return False

    def update_status(self, value):
        query = {"_id": ObjectId(self.task_id)}
        update = {"$set": {"status": value}}
        utils.conn_db(self.collection).update_one(query, update)

    def set_start_time(self):
        query = {"_id": ObjectId(self.task_id)}
        update = {"$set": {"start_time": utils.curr_date()}}
        utils.conn_db(self.collection).update_one(query, update)

    def set_end_time(self):
        query = {"_id": ObjectId(self.task_id)}
        update = {"$set": {"end_time": utils.curr_date()}}
        utils.conn_db(self.collection).update_one(query, update)

    def statistic(self):
        query = {"_id": ObjectId(self.task_id)}
        table_list = ['github_result']
        result = {}
        for table in table_list:
            cnt = utils.conn_db(table).count_documents({"github_task_id": self.task_id})
            stat_key = table + "_cnt"
            result[stat_key] = cnt

        logger.info("insert task stat")
        update = {"$set": {"statistic": result}}
        utils.conn_db(self.collection).update_one(query, update)

    def run(self):
        self.set_start_time()

        self.search_result()
        self.save_content()

        self.update_status(TaskStatus.DONE)
        self.statistic()
        self.set_end_time()


class GithubTaskMonitor(GithubTaskTask):
    def __init__(self, task_id, keyword, scheduler_id):
        super().__init__(task_id, keyword)
        self.scheduler_id = scheduler_id
        self.hash_md5_list = []
        self.new_results = []  # 保存过滤后的结果

    def init_md5_list(self):
        query = {"github_scheduler_id": self.scheduler_id}
        results = list(utils.conn_db("github_hash").find(query, {"hash_md5": 1}))
        for result in results:
            if result["hash_md5"] not in self.hash_md5_list:
                self.hash_md5_list.append(result["hash_md5"])

    def save_mongo(self):
        self.update_status("fetch content")
        hashes_to_insert = []
        items_to_insert = []
        for result in self.results:
            if not isinstance(result, GithubResult):
                continue

            if result.hash_md5 in self.hash_md5_list:
                continue

            # 保存md5, 直接在过滤前，避免重复过滤
            self.hash_md5_list.append(result.hash_md5)
            hash_data = {"hash_md5": result.hash_md5, "github_scheduler_id": self.scheduler_id}
            hashes_to_insert.append(hash_data)

            if self.filter_result(result):
                continue

            item = self.result_to_dict(result)
            item["github_scheduler_id"] = self.scheduler_id
            item["update_date"] = utils.curr_date_obj()
            self.new_results.append(result)
            items_to_insert.append(item)

        if hashes_to_insert:
            utils.conn_db("github_hash").insert_many(hashes_to_insert)

        if items_to_insert:
            utils.conn_db("github_monitor_result").insert_many(items_to_insert)

        logger.info(f"github_monitor save {self.keyword} {len(items_to_insert)}")

    def build_repo_map(self):
        repo_map = dict()
        for result in self.new_results:
            repo_name = result.repo_full_name
            if repo_map.get(repo_name) is None:
                repo_map[repo_name] = [result]
            else:
                repo_map[repo_name].append(result)

        return repo_map

    def build_html_report(self):
        repo_map = self.build_repo_map()
        repo_cnt = 0
        html = f"<br/><br/> <div> 搜索: {self.keyword}  仓库数：{len(repo_map.keys())}  结果数： {len(self.new_results)} </div>"
        for repo_name in repo_map:
            repo_cnt += 1
            # 为了较少长度，超过 5 个仓库就跳过
            if repo_cnt > 5:
                break

            start_div = f'<br/><br/><br/><div>#{repo_cnt} <a href="https://github.com/{repo_name}"> {repo_name} </a> 结果数：{len(repo_map[repo_name])}</div><br/>\n'
            table_start = '''<table style="border-collapse: collapse;">
            <thead>
                <tr>
                    <th style="border: 0.5pt solid; padding:14px;">编号</th>
                    <th style="border: 0.5pt solid; padding:14px;">文件名</th>
                    <th style="border: 0.5pt solid; padding:14px;">代码</th>
                    <th style="border: 0.5pt solid; padding:14px;">Commit 时间</th>
                </tr>
            </thead>
            <tbody>\n'''
            html += start_div
            html += table_start

            style = 'style="border: 0.5pt solid; font-size: 14px; padding:14px"'
            tr_cnt = 0
            for item in repo_map[repo_name]:
                tr_cnt += 1
                code_content = item.human_content(self.keyword).replace('>', "&#x3e;").replace('<', "&#x3c;")
                code_content = code_content[:2000]
                tr_tag = '<tr>' \
                         f'<td {style}> {tr_cnt} </td>' \
                         f'<td {style}> <div style="width: 300px"> <a href="{item.html_url}"> {item.path} </a> </div> </td>' \
                         f'<td {style}> <pre style="max-width: 600px; overflow: auto; max-height: 600px;">{code_content}</pre></td>' \
                         f'<td {style}> {item.commit_date} </td>' \
                         '</tr>\n'

                html += tr_tag
                if tr_cnt > 10:
                    break

            table_end = '</tbody></table>'
            end_div = "</div>"

            html += table_end
            html += end_div

        return html

    def build_markdown_report(self):
        repo_map = self.build_repo_map()

        markdown = f"[监控-Github-{self.keyword}] \n 仓库数:{len(repo_map.keys())}  结果数:{len(self.new_results)} \n --- \n"

        global_cnt = 0
        repo_cnt = 0
        for repo_name in repo_map:
            repo_cnt += 1
            # 为了较少长度，超过 5 个参考就跳过
            if repo_cnt > 5:
                break

            tr_cnt = 0
            for item in repo_map[repo_name]:
                tr_cnt += 1
                global_cnt += 1
                url_text = item.repo_full_name + " " + item.path
                markdown += f"{global_cnt}. [{url_text}]({item.html_url})  \n"
                if tr_cnt > 5:
                    break

        return markdown

    # 消息推送
    def push_msg(self):
        if not self.new_results:
            return

        logger.info(f"found new result {self.keyword} {len(self.new_results)}")

        self.push_dingding()
        self.push_email()

    def push_dingding(self):
        try:
            if Config.DINGDING_ACCESS_TOKEN and Config.DINGDING_SECRET:
                data = push.dingding_send(access_token=Config.DINGDING_ACCESS_TOKEN,
                                      secret=Config.DINGDING_SECRET, msgtype="markdown",
                                      msg=self.build_markdown_report())
                if data.get("errcode", -1) == 0:
                    logger.info("push dingding succ")
                return True

        except Exception as e:
            logger.warning(self.keyword, e)

    def push_email(self):
        try:
            if Config.EMAIL_HOST and Config.EMAIL_USERNAME and Config.EMAIL_PASSWORD:
                html_report = self.build_html_report()
                push.send_email(host=Config.EMAIL_HOST, port=Config.EMAIL_PORT, mail=Config.EMAIL_USERNAME,
                                password=Config.EMAIL_PASSWORD, to=Config.EMAIL_TO,
                                title=f"[Github--{self.keyword}] 灯塔消息推送", html=html_report)
                logger.info("send email succ")
                return True
        except Exception as e:
            logger.warning(self.keyword, e)

    def run(self):
        self.set_start_time()

        # 初始化MD5
        self.init_md5_list()

        # 根据关键字搜索出结果
        self.search_result()

        # 保存到监控结果
        self.save_mongo()

        # 保存到任务结果
        self.results = self.new_results
        self.save_content()

        self.push_msg()

        # 保存统计结果
        self.statistic()
        self.update_status(TaskStatus.DONE)
        self.set_end_time()


# Github 普通任务
def github_task_task(task_id, keyword):
    task = GithubTaskTask(task_id=task_id, keyword=keyword)
    try:
        if not Config.GITHUB_TOKEN:
            logger.error("GITHUB_TOKEN is empty")
            task.update_status(TaskStatus.ERROR)
            task.set_end_time()
            return

        task.run()
    except Exception as e:
        logger.exception(e)

        task.update_status(TaskStatus.ERROR)
        task.set_end_time()


# Github 监控任务
def github_task_monitor(task_id, keyword, scheduler_id):
    task = GithubTaskMonitor(task_id=task_id,
                             keyword=keyword, scheduler_id=scheduler_id)
    try:
        task.run()
    except Exception as e:
        logger.exception(e)

        task.update_status(TaskStatus.ERROR)
        task.set_end_time()
