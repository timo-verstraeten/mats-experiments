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
#include <NodesProblem.hpp>

namespace f = AIToolbox::Factored;
namespace fb = f::Bandit;
namespace fm = f::MDP;


int main(int argc, char** argv) {
    size_t nodes;
    unsigned experiments;
    unsigned timesteps;
    std::string filename;
    Options options;
    options.push_back(makeRequiredOption("nodes,n", &nodes, "set the experiment's nodes number"));
    options.push_back(makeDefaultedOption("experiments,e", &experiments, "set the number of experiments", 1000u));
    options.push_back(makeDefaultedOption("timesteps,t", &timesteps, "set the timesteps per experiment", 500u));
    options.push_back(makeRequiredOption("output,o", &filename, "set the final output file"));

    if (!parseCommandLine(argc, argv, options))
        return 1;
    if (nodes < 3) {
        std::cout << "Nodes cannot be less than three!\n";
        return 1;
    }

    f::State S{}; // Bandit problem, no state
    f::Action A(nodes, 2);

    std::vector<fm::QFunctionRule> rules;

    for (size_t i = 0; i < nodes - 1; ++i) {
        rules.push_back({{}, {{i, i+1}, {0, 0}},  5.0});
        rules.push_back({{}, {{i, i+1}, {0, 1}},  5.0});
        rules.push_back({{}, {{i, i+1}, {1, 0}},  5.0});
        rules.push_back({{}, {{i, i+1}, {1, 1}},  5.0});
    }

   // const double factorsNum = A.size() - 1.0;

    auto [getReward, getRegret, norm] = makeNodesProblem(nodes);

    AIToolbox::Statistics regrets(timesteps);

    fb::SingleActionPolicy p(A);
    fb::EpsilonPolicy ep(p);

    for (unsigned e = 0; e < experiments; ++e) {
        std::cout << "Experiment " << e + 1 << std::endl;

        f::Action action(A.size());
        f::Rewards rew(nodes);
        constexpr double alpha = 0.3, gamma = 0.9;
        fm::SparseCooperativeQLearning solver(S, A, gamma, alpha);

        for (const auto & rule : rules)
            solver.insertRule(rule);

        constexpr double init = 0.05;
        for (unsigned t = 0; t < timesteps; ++t) {
            ep.setEpsilon(init - std::min(init, t / 500.0));

            double trueRegret = 0.0;
            rew.setZero();
            for (unsigned i = 0; i < nodes-1; ++i) {
                double irew = getReward(i, action[i], action[i+1]);
                trueRegret += getRegret(i, action[i], action[i+1]);

                rew[i]   += irew/2.0;
                rew[i+1] += irew/2.0;
            }
            // std::cout << " ==> " << rew[0];
            // for (size_t q = 1; q < nodes-1; ++q) std::cout << ", " << rew[q];
            // std::cout << "\n";

            // const double expRegret = 1.0 - rew.sum()/norm;
            regrets.record(trueRegret / norm, t);

            p.updateAction(solver.stepUpdateQ({}, action, {}, rew));
            action = ep.sampleAction();
        }
    }

    std::ofstream file(filename);
    file << regrets;
}
