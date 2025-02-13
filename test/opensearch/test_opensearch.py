#
# Copyright (C) 2025-present ScyllaDB
#
# SPDX-License-Identifier: LicenseRef-ScyllaDB-Source-Available-1.0
#
from opensearchpy import OpenSearch
import pytest

@pytest.mark.asyncio
async def test_opensearch_basic():
    host = 'localhost'
    port = 9200

    # Create the client with SSL/TLS and hostname verification disabled.
    client = OpenSearch(
        hosts = [{'host': host, 'port': port}],
        http_compress = True, # enables gzip compression for request bodies
        use_ssl = False,
        verify_certs = False,
        ssl_assert_hostname = False,
        ssl_show_warn = False
    )

    # Cluster should be in clean stare here so we can create index (without error that index already exists)
    
    index_name = 'python-test-index'
    index_body = {
    'settings': {
        'index': {
        'number_of_shards': 4
        }
    }
    }

    response = client.indices.create(index_name, body=index_body)
    print(f"Index creation response: {response}")

    response = client.cat.indices(format='json')
    for index in response:
        print(index['index'])
