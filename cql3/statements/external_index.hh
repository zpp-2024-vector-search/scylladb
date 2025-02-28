#pragma once

#include "cql3/cql_statement.hh"
#include <optional>
#include <seastar/core/shared_ptr.hh>
#include "seastar/core/future.hh"
#include "seastar/core/sstring.hh"
#include "seastar/net/api.hh"
#include "transport/messages/result_message.hh"

#include "cql3/statements/select_statement.hh"
#include "transport/messages/result_message.hh"
#include <seastar/core/shared_ptr.hh>
#include <seastar/core/execution_stage.hh>
#include <string_view>
#include "view_info.hh"

#include "seastarx.hh"

class query_processor;



template<typename T = void>
using coordinator_result = cql3::statements::select_statement::coordinator_result<T>;


class external_index {
    virtual future<coordinator_result<::shared_ptr<cql_transport::messages::result_message::rows>>> read_posting_list() = 0;
};


class opensearch_index: external_index {

    std::optional<connected_socket> conn_sock;

    future<connected_socket> connect();

    future<> send_req(const sstring&);

    future<coordinator_result<::shared_ptr<cql_transport::messages::result_message::rows>>> read_posting_list();
};
