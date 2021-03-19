#pragma once

#include <vector>

struct Sum {
    template<class T>
    T operator()(const T &a, const T &b) {
        return a + b;
    }
};

struct Prod {
    template<class T>
    T operator()(T &a, const T &b) {
        return a * b;
    }
};

struct Concat {
    template<class T>
    auto operator()(std::vector<T> &a, const std::vector<T> &b) {
        a.insert(a.end(), b.begin(), b.end());
        return a;
    }
};

template<class Iterator, class T, class BinaryOp>
T Fold(Iterator first, Iterator last, T init, BinaryOp func) {
    for (auto iter = first; iter != last; ++iter) {
        init = func(init, *iter);
    }
    return init;
}

class Length {
private:
    int *_cnt;
public:
    Length(int *cnt) : _cnt(cnt) {};

    template<class T>
    auto operator()(const T &a, const T &b) {
        ++(*_cnt);
        return a;
    }
};
