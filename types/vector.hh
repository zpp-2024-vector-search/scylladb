/*
 * Copyright (C) 2024-present ScyllaDB
 */

/*
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

#pragma once


#include "types/types.hh"
#include "exceptions/exceptions.hh"

class vector_type_impl : public concrete_type<std::vector<data_value>> {
    using intern = type_interning_helper<vector_type_impl, data_type, size_t>;
protected:
    data_type _elements_type;
    size_t _dimension;
public:
    vector_type_impl(data_type elements_type, size_t dimension);
    static shared_ptr<const vector_type_impl> get_instance(data_type type, size_t dimension);
    data_type get_elements_type() const {
        return _elements_type;
    }
    size_t get_dimension() const {
        return _dimension;
    }
    static std::strong_ordering compare_vectors(data_type elements_comparator, size_t dimension,
                        managed_bytes_view o1, managed_bytes_view o2);
                        
    std::vector<managed_bytes> split_fragmented(FragmentedView auto v) const {
        std::vector<managed_bytes> elements;
        for (size_t i = 0; i < _dimension; ++i) {
            auto element = read_vector_element(v, _elements_type->value_length_if_fixed());
            elements.push_back(managed_bytes(element));
        }
        return elements;
    }

    template <typename Range> // range of managed_bytes or managed_bytes_view
    requires requires (Range it) { {*std::begin(it)} -> std::convertible_to<managed_bytes_view>; }
    static managed_bytes build_value_fragmented(Range&& range, std::optional<size_t> value_length_if_fixed) {
        bool is_fixed_length = value_length_if_fixed.has_value();
        size_t size = 0;

        for (auto&& v : range) {
            size += v.size();
        }

        if (!is_fixed_length) {
            size += range.size() * sizeof(int32_t);
        }

        auto ret = managed_bytes(managed_bytes::initialized_later(), size);
        auto out = managed_bytes_mutable_view(ret);

        
        for (auto&& v : range) {
            if (!is_fixed_length) {
                write<int32_t>(out, v.size());
            }
            write_fragmented(out, managed_bytes_view(v));
        }
        return ret;
    }

    template <typename RangeOf_bytes>  // also accepts bytes_view
    requires requires (RangeOf_bytes it) { {*std::begin(it)} -> std::convertible_to<bytes_view>; }
    static bytes build_value(RangeOf_bytes&& range, std::optional<size_t> value_length_if_fixed) {
        bool is_fixed_length = value_length_if_fixed.has_value();
        size_t size = 0;

        for (auto&& v : range) {
            size += v.size();
        }

        if (!is_fixed_length) {
            size += range.size() * sizeof(int32_t);
        }

        auto ret = bytes(bytes::initialized_later(), size);

        auto out = ret.begin();

        for (auto&& v : range) {
            if (!is_fixed_length) {
                write<int32_t>(out, v.size());
            }
            out = std::copy_n(v.begin(), v.size(), out);
        }

        return ret;
    }
private:
    static sstring make_name(data_type type, size_t dimension);

};

template <FragmentedView View>
View read_vector_element(View& v, std::optional<size_t> value_length_if_fixed) {
    int32_t element_size = 0;
    if (value_length_if_fixed) {
        element_size = value_length_if_fixed.value();
    }
    else {
        element_size = read_simple<int32_t>(v);
    }
    
    if (element_size < 0) {
        throw exceptions::invalid_request_exception("null/unset is not supported inside vectors");
    }

    if ((size_t)element_size > v.size_bytes()) {
        throw exceptions::invalid_request_exception("Not enough bytes to read a vector element");
    }
    return read_simple_bytes(v, element_size);
}

data_value make_vector_value(data_type type, vector_type_impl::native_type value);