#pragma once

#include <stdexcept>

template <class Iterator>
Iterator LocalMax(Iterator first, Iterator last) {
    if (first == last) { return last;}
    while (++first != last && std::next(first) != last) {
        if (*std::prev(first) < *first && *std::next(first) < *first) {
            return first;
        }
    }
    return last;
}

// last      ~~>  first == last
// 1 last    ~~>  ++first != last
// 1 2 last  ~~>  std::next(first) != last