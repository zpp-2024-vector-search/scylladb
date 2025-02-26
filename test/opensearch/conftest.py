#
# Copyright (C) 2024-present ScyllaDB
#
# SPDX-License-Identifier: LicenseRef-ScyllaDB-Source-Available-1.0
#
# This file configures pytest for all tests in this directory, and also
# defines common test fixtures for all of them to use.
from opensearchpy import OpenSearch
import pytest
import os

@pytest.fixture(scope="function")
async def opensearch():
    host = os.environ.get('OPENSEARCH_ADDRESS')
    port = os.environ.get('OPENSEARCH_PORT')

    client = OpenSearch(
        hosts = [{'host': host, 'port': port}],
        http_compress = True,
        use_ssl = False,
        verify_certs = False,
        ssl_assert_hostname = False,
        ssl_show_warn = False
    )

    yield client

    client.close()
