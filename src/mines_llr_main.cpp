#include <iostream>
#include <fstream>
#include <vector>

#include <AIToolbox/Utils/Core.hpp>
#include <AIToolbox/Factored/Bandit/Algorithms/LLR.hpp>
#include <AIToolbox/Factored/Utils/Core.hpp>
#include <AIToolbox/Tools/Statistics.hpp>

#include <CommandLineParsing.hpp>
#include <MiningProblem.hpp>

namespace f = AIToolbox::Factored;
namespace fb = f::Bandit;

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

    auto [A, getRew, getReg, deps, ranges, rules2] = makeMiningProblem(seed);
    (void)ranges;
    (void)rules2;

    size_t factorsNum = deps.size();

    AIToolbox::Statistics regrets(timesteps);
    f::Rewards rews(factorsNum);

    for (unsigned e = 0; e < experiments; ++e) {
        std::cout << "Experiment " << e+1 << '\n';
        f::Action action(A.size());

        fb::LLR x(A, deps);

        for (unsigned t = 0; t < timesteps; ++t) {
            std::cout << "Timestep " << t + 1 << '\n';
            rews = getRew(action);

            if (t > 28000) {
                printAction(action);
                std::cout << " ==> " << rews.transpose() << '\n';
            }

            regrets.record(getReg(action), t);

            action = x.stepUpdateQ(action, rews);
        }
        // x.setTimestep(0);
    }

    std::ofstream file(filename);
    file << regrets;
}
