#pragma once

#include <vector>

template<class Functor>
class ReverseBinaryFunctor {
private:
    Functor _f;
public:
    ReverseBinaryFunctor(Functor &f) : _f(f) {};

    template<class T>
    auto operator()(const T &a, const T &b) {
        return !this->_f(a, b);
    }
};

template<class Functor>
class ReverseUnaryFunctor {
private:
    Functor _f;
public:
    ReverseUnaryFunctor(Functor &f) : _f(f) {};

    template<class T>
    auto operator()(const T &a) {
        return !this->_f(a);
    }
};

template<class Functor>
ReverseUnaryFunctor<Functor> MakeReverseUnaryFunctor(Functor functor) {
    return ReverseUnaryFunctor<Functor>(functor);
}

template<class Functor>
ReverseBinaryFunctor<Functor> MakeReverseBinaryFunctor(Functor functor) {
    return ReverseBinaryFunctor<Functor>(functor);
}

class SimpleComparator {
private:
    int *_count;
public:
    SimpleComparator(int *count) : _count(count) {};
    template<typename T>
    auto operator()(const T &a, const T &b) {
        ++(*_count);
        return a != b;
    }
};

template<class Iterator>
int ComparisonsCount(Iterator first, Iterator last) {
    int count{};
    sort(first, last, SimpleComparator(&count));
    return count;
}
