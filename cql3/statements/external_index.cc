

#include "seastar/core/coroutine.hh"
#include "seastar/core/future.hh"
#include "seastar/core/sstring.hh"
#include "seastar/http/client.hh"
#include "seastar/http/request.hh"
#include "seastar/net/api.hh"
#include "seastar/net/inet_address.hh"
#include "seastar/net/socket_defs.hh"
#include "seastarx.hh"
#include <string_view>
#include "external_index.hh"


const uint16_t OPENSEARCH_PORT = 21137;


future<> opensearch_index::send_req(const sstring& request) {
    auto http_req = http::request::make("GET", "127.0.0.1:2137", "https://admin:admin@127.0.0.1:2137/nazwa-indeksu/_search");
    http_req.write_body("json", "{\"query\": {\"match_all\": {}}}");
    auto inet_addr = net::inet_address("127.0.0.1::2137");
    auto sock_addr = socket_address(inet_addr);
    auto client = http::experimental::client(sock_addr);
    
}


