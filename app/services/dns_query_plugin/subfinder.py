import subprocess
import uuid
from app.services.dns_query import DNSQueryBase
from app.config import Config
import os

class Query(DNSQueryBase):
    def __init__(self):
        super(Query, self).__init__()
        self.source_name = "subfinder"
        self.subfinder_path = Config.SUBFINDER_BIN
        self.config_path = Config.SUBFINDER_CONFIG

    def sub_domains(self, target):
        if not os.path.exists(self.subfinder_path):
            self.logger.warning("Subfinder binary not found at: {}".format(self.subfinder_path))
            return []


        safe_target = target.replace('.', '_')
        temp_filename = f"subfinder_{safe_target}_{uuid.uuid4().hex[:8]}.txt"
        temp_path = os.path.join(Config.TMP_PATH, temp_filename)

        command = [
            self.subfinder_path,
            "-d", target,
            "-pc", self.config_path,
            "-silent",
            "-o", temp_path
        ]

        self.logger.debug("Running subfinder command: {}".format(" ".join(command)))

        try:
            process = subprocess.Popen(
                command,
                stdout=None,
                stderr=None
            )
            process.wait(timeout=300)

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command)

            with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                output = f.read().strip()

            subdomains = output.split('\n')
            # Filter out empty strings that may result from empty output
            results = [sub for sub in subdomains if sub]

            # Clean up temp file
            os.unlink(temp_path)
            
            self.logger.info(f"Subfinder found {len(results)} subdomains for {target}")
            return results

        except subprocess.TimeoutExpired:
            self.logger.warning(f"Subfinder command timed out for target: {target}")
            try:
                process.kill()
            except:
                pass
            return []
        except FileNotFoundError:
            self.logger.error("Subfinder binary not found at path: {}".format(self.subfinder_path))
            return []
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Subfinder execution failed for target {target}")
            return []
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while running Subfinder for {target}: {e}")
            return []
