#!/usr/bin/python3
#
# Copyright (C) 2025-present ScyllaDB
#
# SPDX-License-Identifier: LicenseRef-ScyllaDB-Source-Available-1.0
#
"""OpenSearch cluster for testing.
   Provides helpers to setup and manage OpenSearch cluster for testing.
"""
from opensearchpy import OpenSearch
import asyncio
import os

class OpenSearchCluster:

    OPEN_SEARCH_DIR = '/opt/scylladb/dependencies/'

    async def start(self):
        os.environ['OPENSEARCH_JAVA_HOME'] = f'{self.OPEN_SEARCH_DIR}/opensearch-2.19.0/jdk'

        process = await asyncio.create_subprocess_exec(
            f'{self.OPEN_SEARCH_DIR}/opensearch-2.19.0/bin/opensearch',
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True
        )
        await asyncio.sleep(10)  # Give it some time to start
        if process.returncode is not None:
            print("OpenSearch failed to start")
        else:
            print("OpenSearch started successfully")

    async def stop(self):
        process = await asyncio.create_subprocess_exec(
            'pkill', '-f', 'opensearch-2.19.0'
        )
        await process.communicate()
        if process.returncode != 0:
            print("Failed to stop OpenSearch")
        else:
            print("OpenSearch stopped successfully")

    async def clear(self):
        pass

    async def execute(self, query):
        pass


async def main():
    pass

if __name__ == '__main__':
    asyncio.run(main())
