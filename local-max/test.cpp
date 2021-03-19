#include <catch.hpp>
#include <util.h>
#include <strict_iterator.h>
#include <local_max.h>
#include <vector>

TEST_CASE("Simple") {
    std::vector<int> data = {3, 0, 1, 5, 7, 2};
    auto first = MakeStrict(data.begin(), data.begin(), data.end());
    auto last = MakeStrict(data.begin(), data.end(), data.end());

    auto it = LocalMax(first, last);
    REQUIRE(*it == data[4]);
}

TEST_CASE("NoLocalMaximum") {
    std::vector<int> data = {1, 2, 3, 4, 5, 6};
    auto first = MakeStrict(data.begin(), data.begin(), data.end());
    auto last = MakeStrict(data.begin(), data.end(), data.end());

    auto it = LocalMax(first, last);
    REQUIRE(it == last);
}

TEST_CASE("OneElement") {
    std::vector<int> data = {1};
    auto first = MakeStrict(data.begin(), data.begin(), data.end());
    auto last = MakeStrict(data.begin(), data.end(), data.end());

    auto it = LocalMax(first, last);
    REQUIRE(it == last);
}

TEST_CASE("TwoElements") {
    std::vector<int> data = {1, 2};
    auto first = MakeStrict(data.begin(), data.begin(), data.end());
    auto last = MakeStrict(data.begin(), data.end(), data.end());

    REQUIRE(last == LocalMax(first, last));
}

TEST_CASE("Empty") {
    std::vector<int> data;
    auto first = MakeStrict(data.begin(), data.begin(), data.end());
    auto last = MakeStrict(data.begin(), data.end(), data.end());

    REQUIRE(last == LocalMax(first, last));
}