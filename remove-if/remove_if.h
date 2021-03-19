#pragma once

#include <stdexcept>

template <class Iterator, class Predicate>
Iterator RemoveIf(Iterator first, Iterator last, Predicate pred) {
    for (; first != last; ++first) {
        if (pred(*first)) { break;}
    }
    if (first != last) {
        for (Iterator i = first; ++i != last;) {
            if (!pred(*i)) { *first++ = std::move(*i); }
        }
    }
    return first;
}
