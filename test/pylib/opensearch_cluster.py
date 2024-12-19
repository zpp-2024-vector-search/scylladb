from functools import wraps
import asyncio
import concurrent.futures
from asyncio.subprocess import Process
from contextlib import asynccontextmanager
from collections import ChainMap
import itertools
import logging
import os
import pathlib
import shutil
import tempfile
import time
import traceback
from typing import Any, Optional, Dict, List, Set, Tuple, Callable, AsyncIterator, NamedTuple, Union, NoReturn
import uuid
from io import BufferedWriter
from test.pylib.rest_client import ScyllaRESTAPIClient, HTTPError
from test.pylib.util import LogPrefixAdapter, read_last_line
from test.pylib.internal_types import ServerNum, IPAddress, HostID, ServerInfo, ServerUpState
from functools import partial
from opensearchpy import AsyncOpenSearch
import aiohttp
import aiohttp.web
import yaml
import signal
import glob
import errno
import re

import psutil

io_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)


async def async_rmtree(directory, *args, **kwargs):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(io_executor, partial(shutil.rmtree, directory, *args, **kwargs))


class OpenSearchServer:
    TOPOLOGY_TIMEOUT = 1000
    start_time: float
    sleep_interval: float
    log_file: BufferedWriter
    host_id: HostID                             # Host id (UUID)
    newid = itertools.count(start=1).__next__   # Sequential unique id

    def __init__(self, api, exe: str, vardir: str,
                 logger: Union[logging.Logger, logging.LoggerAdapter],
                 ) -> None:
        # pylint: disable=too-many-arguments
        self.server_id = ServerNum(OpenSearchServer.newid())
        # this variable needed to make a cleanup after server is not needed anymore
        self.exe = pathlib.Path(exe).resolve()
        self.vardir = pathlib.Path(vardir)
        self.logger = logger
        self.cmd: Optional[Process] = None
        shortname = f"opensearch-{self.server_id}"
        self.workdir = self.vardir / shortname
        self.log_filename = (self.vardir / shortname).with_suffix(".log")
        self.api = api

    async def install_and_start(self) -> None:
        """Setup and start this server."""

        await self.install()

        try:
            await self.start()
        except:
            await self.stop()
            raise

    def check_opensearch_executable(self) -> None:
        """Check if executable exists and can be run"""
        if not os.access(self.exe, os.X_OK):
            raise RuntimeError(f"{self.exe} is not executable")        

    async def install(self) -> None:
        """Create a working directory with all subdirectories, initialize
        a configuration file."""

        self.check_opensearch_executable()

        self.logger.info("installing Scylla server in %s...", self.workdir)

        # Cleanup any remains of the previously running server in this path
        await async_rmtree(self.workdir, ignore_errors=True)

        try:
            self.workdir.mkdir(parents=True, exist_ok=True)

            self.log_file = self.log_filename.open("wb")
        except:
            try:
                await async_rmtree(self.workdir)
            except FileNotFoundError:
                pass
            self.log_filename.unlink(missing_ok=True)
            raise
    
    async def is_alive(self):
        try:
            await self.api.info()
            return True
        except Exception:
            return False

    async def start(self,
    ):
        """Start an installed server. May be used for restarts."""

        env = os.environ.copy()

        self.cmd = await asyncio.create_subprocess_exec(
            self.exe,
            cwd=self.workdir,
            stderr=self.log_file,
            stdout=self.log_file,
            env=env,
            preexec_fn=os.setsid,
        )

        self.start_time = time.time()
        sleep_interval = 0.1

        def report_error(message: str) -> NoReturn:
            message += f", server_id {self.server_id}, workdir {self.workdir.name}"
            message += f", host_id {getattr(self, 'host_id', '<missing>')}"
            self.logger.error(message)
            self.logger.error("last line of %s:\n%s", self.log_filename, read_last_line(self.log_filename))
            log_handler = logging.getLogger().handlers[0]
            if hasattr(log_handler, 'baseFilename'):
                logpath = log_handler.baseFilename   # type: ignore
            else:
                logpath = "?"
            raise RuntimeError(message + "\nCheck the log files:\n"
                                         f"{logpath}\n"
                                         f"{self.log_filename}")

        while time.time() < self.start_time + self.TOPOLOGY_TIMEOUT:
            assert self.cmd is not None
            if self.cmd.returncode:
                self.cmd = None
                report_error("failed to start the node")

            if await self.is_alive():
                return

            # Sleep and retry
            await asyncio.sleep(sleep_interval)

        
        report_error(
                f"the node failed to start within the timeout"
            )
        
    async def stop(self):
        self.cmd.kill()
        await self.cmd.wait()
    


class OpenSearchCluster:
    def __init__(self, logger: Union[logging.Logger, logging.LoggerAdapter]) -> None:
        self.logger = logger
        self.name = str(uuid.uuid1())
        # Every ScyllaServer is in one of self.running, self.stopped.
        # These dicts are disjoint.
        # A server ID present in self.removed may be either in self.running or in self.stopped.
        self.running: Dict[ServerNum, OpenSearchServer] = {}        # started servers
        self.stopped: Dict[ServerNum, OpenSearchServer] = {}        # servers no longer running but present
        self.servers = ChainMap(self.running, self.stopped)
        # The first IP assigned to a server added to the cluster.
        # cluster is started (but it might not have running servers)
        self.is_running: bool = False
        # cluster was modified in a way it should not be used in subsequent tests
        self.is_dirty: bool = False
        self.api = AsyncOpenSearch(
            hosts= [{'host': 'localhost', 'port': 9200}],
            http_compress = True, # enables gzip compression for request bodies
            use_ssl = False,
            verify_certs = False,
            ssl_assert_hostname = False,
            ssl_show_warn = False
        )
        self.logger.info("Created new cluster %s", self.name)

    async def install_and_start(self) -> None:
        """Setup initial servers and start them.
           Catch and save any startup exception"""
        try:
            await self.add_server()
        except Exception as exc:
            # If start fails, swallow the error to throw later,
            # at test time.
            self.start_exception = exc
        self.is_running = True
        self.logger.info("Created cluster %s", self)
        self.is_dirty = False
    
    async def uninstall(self) -> None:
        for server in self.running.values():
            await server.stop()
    
    async def add_server(self) -> None:
        server = OpenSearchServer(self.api, "~/opensearch-2.18.0/bin/opensearch", "~/test", self.logger)
        await server.install_and_start()

    async def get_info(self): 
        await self.api.info()
