#include <random>
#include <tuple>

inline auto makeNodesProblem(size_t nodes) {
    auto getMeanRewards = [](size_t i, size_t a1, size_t a2) {
        // WARNING! IF YOU CHANGE THIS YOU NEED TO UPDATE THE GETREGRET
        // FUNCTION BELOW!!
        if (!a1 && !a2) {
            return 0.75;
        } else if (!a1 && a2) {
            return (i % 2 == 0) ? 1 : 0.25;
        } else if (a1 && !a2) {
            return (i % 2 == 0) ? 0.25 : 1;
        } else {
            return 0.9;
        }
    };
    auto getReward = [getMeanRewards](size_t i, size_t a1, size_t a2){
        static std::default_random_engine rand(0);
        std::bernoulli_distribution roll(getMeanRewards(i, a1, a2));
        return roll(rand);
    };
    auto getRegret = [getMeanRewards](size_t i, size_t a1, size_t a2){
        // 1.0 here represents the max value obtainable by agents i and i+1. In
        // this case they can always obtain reward 1.0, so that's what we use
        // to subtract.
        return 1.0 - getMeanRewards(i, a1, a2);
    };

    //                     getRew,    getRegret, norm
    return std::make_tuple(getReward, getRegret, nodes - 1);
}
