#include <catch.hpp>
#include <util.h>
#include <strict_iterator.h>
#include <remove_if.h>

#include <string>
#include <vector>

bool IsEmpty(const std::string& s) {
    return s.empty();
}

TEST_CASE("Simple") {
    std::vector<std::string> data{"aba", "", "caba", "", ""};
    auto first = MakeStrict(data.begin(), data.begin(), data.end());
    auto last = MakeStrict(data.begin(), data.end(), data.end());
    auto it = RemoveIf(first, last, IsEmpty);

    auto expected = MakeStrict(data.begin(), data.begin() + 2, data.end());
    REQUIRE(expected == it);
    REQUIRE("aba" == data[0]);
    REQUIRE("caba" == data[1]);
}

TEST_CASE("Empty") {
    std::vector<std::string> data;
    auto first = MakeStrict(data.begin(), data.begin(), data.end());
    auto last = MakeStrict(data.begin(), data.end(), data.end());
    REQUIRE(first == RemoveIf(first, last, IsEmpty));
}

TEST_CASE("Long") {
    RandomGenerator rnd(85475);
    const int kCount = 1e5;
    const int kVal = 1e9;
    std::vector<int> elems(kCount);
    for (int& x : elems) {
        x = rnd.GenInt(-kVal, kVal);
    }
    auto first = MakeStrict(elems.begin(), elems.begin(), elems.end());
    auto last = MakeStrict(elems.begin(), elems.end(), elems.end());
    auto old_elems = elems;

    auto new_end = RemoveIf(first, last, [](int x) { return x % 2 == 0; });

    auto cur_it = old_elems.begin();
    for (auto it = first; it != new_end; ++it) {
        while (*cur_it % 2 == 0) {
            ++cur_it;
        }
        REQUIRE(*cur_it == *it);
        ++cur_it;
    }
}
