import threading
import collections
import time
import requests.exceptions
from lxml import etree
from app import utils

logger = utils.get_logger()


class BaseThread:
    def __init__(self, targets, concurrency=6):
        self.concurrency = concurrency
        self.semaphore = threading.Semaphore(concurrency)
        self.targets = targets

    def work(self, target):
        raise NotImplementedError()

    def _work(self, url):
        try:
            self.work(url)
        except requests.exceptions.RequestException:
            pass

        except etree.Error:
            pass

        except Exception as e:
            logger.warning(f"error on {url}")
            logger.exception(e)

        except BaseException as e:
            logger.warning(f"BaseException on {url}")
            raise e
        finally:
            self.semaphore.release()

    def _run(self):
        deque = collections.deque(maxlen=5000)
        cnt = 0

        for target in self.targets:
            if isinstance(target, str):
                target = target.strip()

            cnt += 1
            logger.debug(f"[{cnt}/{len(self.targets)}] work on {target}")

            if not target:
                continue

            self.semaphore.acquire()
            t1 = threading.Thread(target=self._work, args=(target,))
            # 可以快速结束程序
            t1.daemon = True
            t1.start()

            deque.append(t1)

        for t in list(deque):
            while t.is_alive():
                time.sleep(0.2)


class ThreadMap(BaseThread):
    def __init__(self, fun, items, arg=None, concurrency=6):
        super().__init__(targets=items, concurrency=concurrency)
        if not callable(fun):
            raise TypeError("fun must be callable.")

        self._arg = arg
        self._fun = fun
        self._result_map = {}

    def work(self, target):
        if self._arg:
            result = self._fun(target, self._arg)
        else:
            result = self._fun(target)

        if result:
            self._result_map[str(target)] = result

    def run(self):
        self._run()
        return self._result_map


def thread_map(fun, items, arg=None, concurrency=6):
    t = ThreadMap(fun=fun, items=items, arg=arg, concurrency=concurrency)
    return t.run()
