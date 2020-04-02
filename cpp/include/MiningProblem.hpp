#include <random>
#include <iostream>

#include <AIToolbox/Utils/Core.hpp>
#include <AIToolbox/Factored/Bandit/Algorithms/MAUCE.hpp>
#include <AIToolbox/Factored/Bandit/Algorithms/Utils/VariableElimination.hpp>
#include <AIToolbox/Factored/Utils/Core.hpp>

namespace f = AIToolbox::Factored;
namespace fb = f::Bandit;

inline void printPartialAction(const f::PartialAction & pa) {
    for (size_t i = 0; i < pa.first.size(); ++i) {
        std::cout << "(" << pa.first[i] << ", " << pa.second[i] << ")";
    }
}

inline void printAction(const f::Action & y){
    std::cout << "[";
    for (auto yy : y) std::cout << yy << ", ";
    std::cout << "]";
};

double rewFun(double p, size_t workers) {
    if (!workers)
        return 0.0;
    return p * std::pow(1.03, workers);
};

inline auto makeMiningProblem(unsigned seed) {
    std::cout << "Using seed " << seed << '\n';

    std::default_random_engine rand(seed);
    std::uniform_int_distribution<size_t> villages(5, 15);
    std::uniform_int_distribution<size_t> workersPerVillage(1, 5);
    std::uniform_int_distribution<size_t> minesPerVillage(2, 4);
    std::uniform_real_distribution<double> mineP(0, 0.5);

    // Generate villages and attached mines
    auto villagesNum = villages(rand);
    f::Action A(villagesNum);
    f::Action workers(villagesNum);
    for (size_t n = 0; n < villagesNum; ++n) {
        A[n] = minesPerVillage(rand);
        // Last village has 4 mines
        if (n == villagesNum - 1)
            A[n] = 4;

        workers[n] = workersPerVillage(rand);

        std::cout << "Village " << n << " has " << workers[n]
                  << " workers and " << A[n] << " mines.\n";
    }
    // Find out which villages are attached to each mine
    const auto minesNum = villagesNum + 3;
    auto mines = std::vector<std::vector<size_t>>(minesNum);
    for (size_t n = 0; n < villagesNum; ++n)
        for (size_t i = n; i < n + A[n]; ++i)
            mines[i].push_back(n);
    for (size_t i = 0; i < mines.size(); ++i) {
        std::cout << "Mine " << i << " is connected to villages: ";
        for (size_t j = 0; j < mines[i].size(); ++j)
            std::cout << mines[i][j] << ", ";
        std::cout << "\n";
    }

    // Compute probabilities for each mine
    auto minePs = std::vector<double>(minesNum);
    for (size_t m = 0; m < minesNum; ++m) {
        minePs[m] = mineP(rand);
        std::cout << "Mine " << m << " has p: " << minePs[m] << '\n';
    }

    // Here we build the rules for the problem as now specified.
    std::vector<fb::QFunctionRule> rules;
    for (size_t m = 0; m < minesNum; ++m) {
        f::PartialFactorsEnumerator enumerator(A, mines[m]);
        while (enumerator.isValid()) {
            const auto & pAction = *enumerator;
            unsigned totalMiners = 0;
            for (size_t i = 0; i < pAction.first.size(); ++i) {
                if (pAction.first[i] + pAction.second[i] == m)
                    totalMiners += workers[pAction.first[i]];
            }
            const double v = rewFun(minePs[m], totalMiners);
            rules.emplace_back(fb::QFunctionRule{pAction, v});

            enumerator.advance();
        }
    }
    // And we solve it in order to find out which action is the best.
    fb::VariableElimination ve;
    auto result = ve(A, rules);

    std::cout << "Best action: "; printAction(std::get<0>(result));
    std::cout << " ==> " << std::get<1>(result) << '\n';
    auto norm = std::get<1>(result);

    // BUILDING STRUCTURES TO RUN THE EXPERIMENTS:

    // Here we build the function we will use to sample reward.
    // The reward obtained is normalized so that the average regret will be 1.
    auto getRew = [rand, workers, minePs, norm](const f::Action & a) mutable {
        f::Rewards rews(minePs.size());
        rews.fill(0.0);
        for (size_t m = 0; m < minePs.size(); ++m) {
            unsigned totalMiners = 0;
            for (size_t i = 0; i < a.size(); ++i) {
                if (i + a[i] == m)
                    totalMiners += workers[i];
            }
            const double p = rewFun(minePs[m], totalMiners);
            std::bernoulli_distribution roll(p / norm);
            rews[m] = static_cast<double>(roll(rand));
        }
        return rews;
    };
    // Compute true regret of an action without randomness.
    auto getReg = [workers, minePs, norm](const f::Action & a) mutable {
        double regret = 1.0;
        for (size_t m = 0; m < minePs.size(); ++m) {
            unsigned totalMiners = 0;
            for (size_t i = 0; i < a.size(); ++i) {
                if (i + a[i] == m)
                    totalMiners += workers[i];
            }
            const double p = rewFun(minePs[m], totalMiners);
            regret -= p / norm;
        }
        return regret;
    };

    // We build the factor dependencies for XXXAlgorithm
    std::vector<f::PartialKeys> deps;
    std::vector<double> ranges;
    for (size_t m = 0; m < minesNum; ++m) {
        deps.emplace_back(mines[m]);
        ranges.emplace_back(1.0);
        std::cout << "Adding vector: " << ranges.back() << " -- ";
        for (auto v : mines[m])
            std::cout << v << ", ";
        std::cout << "\n";
    }

    // Building rules for SparseCooperativeQLearning
    std::vector<fb::QFunctionRule> rules2;
    size_t counter = 0;
    for (size_t m = 0; m < minesNum; ++m) {
        // Only create rules here once, skip duplicates.
        if (m > 0 && mines[m] == mines[m-1])
            continue;
        f::PartialFactorsEnumerator enumerator(A, mines[m]);
        while (enumerator.isValid()) {
            const auto & pAction = *enumerator;
            rules2.emplace_back(fb::QFunctionRule{pAction, 10.0});
            std::cout << "Rule number " << counter++ << ": ";
            printPartialAction(pAction);
            std::cout << " ==> 10.0\n";

            enumerator.advance();
        }
        std::cout << "------\n";
    }

    return std::make_tuple(A, getRew, getReg, deps, ranges, rules2);
}
