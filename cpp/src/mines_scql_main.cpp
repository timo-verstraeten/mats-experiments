#include <iostream>
#include <fstream>
#include <vector>

#include <AIToolbox/Utils/Core.hpp>
#include <AIToolbox/Factored/MDP/Algorithms/SparseCooperativeQLearning.hpp>
#include <AIToolbox/Factored/Utils/Core.hpp>
#include <AIToolbox/Factored/Bandit/Policies/SingleActionPolicy.hpp>
#include <AIToolbox/Factored/Bandit/Policies/EpsilonPolicy.hpp>
#include <AIToolbox/Tools/Statistics.hpp>

#include <CommandLineParsing.hpp>
#include <MiningProblem.hpp>

namespace f = AIToolbox::Factored;
namespace fm = f::MDP;

int main(int argc, char** argv) {
    int seed;
    unsigned experiments;
    unsigned timesteps;
    std::string filename;
    Options options;
    options.push_back(makeRequiredOption("seed,s", &seed, "set the experiment's seed"));
    options.push_back(makeDefaultedOption("experiments,e", &experiments, "set the number of experiments", 1u));
    options.push_back(makeDefaultedOption("timesteps,t", &timesteps, "set the timesteps per experiment", 40000u));
    options.push_back(makeRequiredOption("output,o", &filename, "set the final output file"));

    if (!parseCommandLine(argc, argv, options))
        return 1;

    auto [A, getRew, getReg, deps, ranges, rules] = makeMiningProblem(seed);
    (void)ranges;
    size_t factorsNum = deps.size();

    AIToolbox::Statistics regrets(timesteps);
    f::Rewards rews(A.size());

    fb::SingleActionPolicy p(A);
    fb::EpsilonPolicy ep(p);

    for (unsigned e = 0; e < experiments; ++e) {
        std::cout << "Experiment " << e+1 << std::endl;
        f::Action action(A.size());

        fm::SparseCooperativeQLearning solver({}, A, 0.9, 0.3);

        for (const auto & rule : rules)
            solver.insertRule(fm::QFunctionRule{{}, rule.action, rule.value});

        constexpr double init = 0.05;
        for (unsigned t = 0; t < timesteps; ++t) {
            ep.setEpsilon(init - std::min(init, 0.00001 * t));
            // std::cout << t << " " << ep.getEpsilon() << "\n";

            auto factorRews = getRew(action);
            rews.fill(0.0);
            for (size_t f = 0; f < factorsNum; ++f) {
                double rew = factorRews[f];
                for (auto a : deps[f])
                    rews[a] += rew/deps[f].size();
            }
            // if (t < 100) {
            //     printAction(action);
            //     std::cout << " ==> " << rews.transpose() << '\n';
            // }

            regrets.record(getReg(action), t);

            p.updateAction(solver.stepUpdateQ({}, action, {}, rews));
            action = ep.sampleAction();
        }
        // solver.getDiscount();
    }

    std::ofstream file(filename);
    file << regrets;
}
