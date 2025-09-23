import time
import json
from app import utils
from app.config import Config
from .baseThread import BaseThread
logger = utils.get_logger()


class WebAnalyze(BaseThread):
    def __init__(self, sites, concurrency=3):
        super().__init__(sites, concurrency = concurrency)
        self.analyze_map = {}

    def work(self, site):
        cmd_parameters = ['phantomjs',
                          '--ignore-ssl-errors true',
                          '--ssl-protocol any',
                          '--ssl-ciphers ALL',
                          Config.DRIVER_JS ,
                          site
                          ]
        logger.debug("WebAnalyze=> {}".format(" ".join(cmd_parameters)))

        output = utils.check_output(cmd_parameters, timeout=20)
        output = output.decode('utf-8', errors='ignore')

        try:
            result = self._extract_json(output)
            self.analyze_map[site] = result.get("applications", [])
        except ValueError as exc:
            logger.info(f"webAnalyze parse failed on {site}: {exc}")
            self.analyze_map[site] = []

    def run(self):
        t1 = time.time()
        logger.info(f"start WebAnalyze {len(self.targets)}")
        self._run()
        elapse = time.time() - t1
        logger.info(f"end WebAnalyze elapse {elapse}")
        return self.analyze_map

    def _extract_json(self, output):
        """Extract first JSON object from mixed PhantomJS stdout."""
        decoder = json.JSONDecoder()
        idx = output.find("{")

        while idx != -1:
            try:
                obj, _ = decoder.raw_decode(output[idx:])
                return obj
            except json.JSONDecodeError:
                idx = output.find("{", idx + 1)

        raise ValueError("no JSON object in output")


def web_analyze(sites, concurrency=3):
    s = WebAnalyze(sites, concurrency=concurrency)
    return s.run()




