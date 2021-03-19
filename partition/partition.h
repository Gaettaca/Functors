#pragma once

#include <stdexcept>

template <class Iterator, class Predicate>
Iterator Partition(Iterator first, Iterator last, Predicate pred) {
    for (; first != last; ++first) {
        if (!pred(*first)) { break;}
    }
    if (first == last) { return last; }
    for (Iterator i = std::next(first); i != last; ++i) {
        if (pred(*i)) {
            std::iter_swap(i, first);
            ++first;
        }
    }
    return first;
}
