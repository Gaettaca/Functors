#pragma once

#include <iostream>
#include <stdexcept>

template <class Iterator, class T>
Iterator FindLast(Iterator first, Iterator last, const T& val) {
    Iterator last_entrance = last;
    for (; first != last; ++first){
        if (*first == val) { last_entrance = first; }
    }
    return last_entrance;
}
