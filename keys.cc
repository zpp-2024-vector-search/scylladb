/*
 * Copyright (C) 2015 Cloudius Systems, Ltd.
 */

/*
 * This file is part of Scylla.
 *
 * Scylla is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Scylla is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Scylla.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <iostream>

#include "keys.hh"
#include "dht/i_partitioner.hh"

std::ostream& operator<<(std::ostream& out, const partition_key& pk) {
    return out << "pk{" << to_hex(pk) << "}";
}

std::ostream& operator<<(std::ostream& out, const clustering_key_prefix& ckp) {
    return out << "ckp{" << to_hex(ckp) << "}";
}

const legacy_compound_view<partition_key_view::c_type>
partition_key_view::legacy_form(const schema& s) const {
    return { *get_compound_type(s), _bytes };
}

int
partition_key_view::legacy_tri_compare(const schema& s, partition_key_view o) const {
    auto cmp = legacy_compound_view<c_type>::tri_comparator(*get_compound_type(s));
    return cmp(this->representation(), o.representation());
}

int
partition_key_view::ring_order_tri_compare(const schema& s, partition_key_view k2) const {
    auto t1 = dht::global_partitioner().get_token(s, *this);
    auto t2 = dht::global_partitioner().get_token(s, k2);
    if (t1 != t2) {
        return t1 < t2 ? -1 : 1;
    }
    return legacy_tri_compare(s, k2);
}

template class db::serializer<partition_key_view>;
template class db::serializer<clustering_key_prefix_view>;

template<>
db::serializer<partition_key_view>::serializer(const partition_key_view& key)
        : _item(key), _size(sizeof(uint16_t) /* size */ + key.representation().size()) {
}

template<>
void db::serializer<partition_key_view>::write(output& out, const partition_key_view& key) {
    bytes_view v = key.representation();
    out.write<uint16_t>(v.size());
    out.write(v.begin(), v.end());
}

template<>
void db::serializer<partition_key_view>::read(partition_key_view& b, input& in) {
    auto len = in.read<uint16_t>();
    b = partition_key_view::from_bytes(in.read_view(len));
}

template<>
partition_key_view db::serializer<partition_key_view>::read(input& in) {
    auto len = in.read<uint16_t>();
    return partition_key_view::from_bytes(in.read_view(len));
}

template<>
void db::serializer<partition_key_view>::skip(input& in) {
    auto len = in.read<uint16_t>();
    in.skip(len);
}

template<>
db::serializer<clustering_key_prefix_view>::serializer(const clustering_key_prefix_view& key)
        : _item(key), _size(sizeof(uint16_t) /* size */ + key.representation().size()) {
}

template<>
void db::serializer<clustering_key_prefix_view>::write(output& out, const clustering_key_prefix_view& key) {
    bytes_view v = key.representation();
    out.write<uint16_t>(v.size());
    out.write(v.begin(), v.end());
}

template<>
void db::serializer<clustering_key_prefix_view>::read(clustering_key_prefix_view& b, input& in) {
    auto len = in.read<uint16_t>();
    b = clustering_key_prefix_view::from_bytes(in.read_view(len));
}

template<>
clustering_key_prefix_view db::serializer<clustering_key_prefix_view>::read(input& in) {
    auto len = in.read<uint16_t>();
    return clustering_key_prefix_view::from_bytes(in.read_view(len));
}
