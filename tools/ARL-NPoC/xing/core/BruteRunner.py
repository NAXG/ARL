from xing.core.BaseThread import BaseThread
from xing.utils import get_logger
from xing.utils.save_result import save_result
logger = get_logger()

MAX_PLG_BRUTE_ERROR_CNT = 30


class BruteRunner(BaseThread):
    def __init__(self, plg,  target, username_list, password_list, concurrency=6):
        auth_list = list(zip(username_list, password_list))
        super().__init__(targets=auth_list, concurrency=concurrency)
        self.plg = plg
        self.target = target
        self.result_map = {}
        self.shuffle_targets = getattr(self.plg, "shuffle_auth_list", False)

    def work(self, auth_pair):
        from xing.core.BasePlugin import BasePlugin
        user, pwd = auth_pair
        if not isinstance(self.plg, BasePlugin):
            return

        if self.result_map.get(user):
            logger.debug(f"password is founded , skip {user}")
            return

        plg_error_cnt = getattr(self.plg, "_error_cnt", 0)
        if plg_error_cnt >= MAX_PLG_BRUTE_ERROR_CNT:
            logger.debug(f"plg_error_cnt >= {MAX_PLG_BRUTE_ERROR_CNT}, skip {self.target}")
            return

        try:
            result = self.plg.login(self.target, user=user, passwd=pwd)
            if result:
                logger.success(f"found weak pass {user}:{pwd} {self.target}")
                msg = f"{self.target}----{user}:{pwd}"
                save_result(self.plg, msg)
                self.result_map[user] = pwd
        except Exception as e:
            # 这里应该加个锁
            plg_error_cnt = getattr(self.plg, "_error_cnt", 0)
            plg_error_cnt += 1
            setattr(self.plg, "_error_cnt", plg_error_cnt)
            logger.warning(f"error on {self.target} {user}:{pwd}")
            raise e

    def run(self):
        self._run()
        return self.result_map


def brute_runner(plg,  target, username_list, password_list, concurrency=6):
    runner = BruteRunner(plg=plg, target=target,
                         username_list=username_list, password_list=password_list, concurrency=concurrency)

    return runner.run()