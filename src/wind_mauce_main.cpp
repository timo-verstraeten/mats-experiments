#include <iostream>
#include <iomanip>
#include <fstream>
#include <vector>

#include <AIToolbox/Utils/Core.hpp>
#include <AIToolbox/Factored/Bandit/Algorithms/MAUCE.hpp>
#include <AIToolbox/Factored/Utils/Core.hpp>
#include <AIToolbox/Tools/Statistics.hpp>

#include <CommandLineParsing.hpp>
#include <TurbinesProblem.hpp>

#define PRINTD(x)
//#define PRINTD(x) std::cout << x

namespace f = AIToolbox::Factored;
namespace fb = f::Bandit;
// namespace fm = f::MDP;

int main(int argc, char** argv) {
    unsigned experiments;
    unsigned timesteps;
    double range;
    std::string filename;
    Options options;
    options.push_back(makeDefaultedOption("experiments,e", &experiments, "set the number of experiments", 1u));
    options.push_back(makeDefaultedOption("timesteps,t", &timesteps, "set the timesteps per experiment", 40000u));
    options.push_back(makeRequiredOption("output,o", &filename, "set the final output file"));
    options.push_back(makeRequiredOption("range,r", &range, "set the ranges for all local joint actions"));

    if (!parseCommandLine(argc, argv, options))
        return 1;

    auto [A, getRew, deps, rules2] = makeTurbinesProblem();
    (void)rules2;

    size_t factorsNum = deps.size();
    for (size_t i = 0; i < deps.size(); ++i) {
        std::cout << "Dep: ";
        for (size_t j = 0; j < deps[i].size(); ++j) {
            std::cout << deps[i][j] << ", ";
        }
        std::cout << "\n";
    }
    std::vector<double> ranges(deps.size(), range);

    f::Rewards rews(factorsNum);
    std::vector<bool> singles(A.size());

    std::cout << "Divs = ";
    for (size_t a = 0; a < A.size(); ++a) {
        bool single = false;
        for (size_t f = 0; f < deps.size(); ++f) {
            if (deps[f].size() == 1 &&
                deps[f][0] == a) {
                single = true;
                break;
            }
        }
        singles[a] = single;
        std::cout << singles[a] << ", ";
    }
    std::cout << '\n';
    // double minRew = 1.0, maxRew = 0.0;

    AIToolbox::Statistics regrets(timesteps);

    for (unsigned e = 0; e < experiments; ++e) {
        std::cout << "Experiment " << e+1 << std::endl;
        f::Action action(A.size(), 0);

        fb::MAUCE x(A, deps, ranges);

        for (unsigned t = 0; t < timesteps; ++t) {
            std::cout << "[" << e+1 << "] Timestep " << t + 1 << std::endl;
            const auto tmp = getRew(action);

            for (size_t f = 0; f < deps.size(); ++f) {
                rews[f] = 0.0;
                if (deps[f].size() == 1)
                    rews[f] += tmp[deps[f][0]];
                else
                    for (const auto a : deps[f])
                        if (!singles[a])
                            rews[f] += tmp[a];
            }
            //const auto min = tmp.minCoeff();
            //const auto max = tmp.maxCoeff();
            //if (min < minRew)
            //    minRew = min;
            //if (max > maxRew)
            //    maxRew = max;

            printAction(action);
            PRINTD(" ==> " << tmp.transpose() << " ( " << tmp.sum() << " ) ==== " << rews.transpose() << " ( " << rews.sum() << " )\n");

            const double regret = (1.0 - tmp.sum());
            regrets.record(regret, t);

            action = x.stepUpdateQ(action, rews);
            PRINTD("STEP UPDATE ENDED, NOW STARTING NEXT TIMESTEP ######\n\n");
        }
        // x.setTimestep(0);
    }

    PRINTD("MIN REW OBTAINED: " << minRew << "; MAX REW OBTAINED = " << maxRew << '\n');

    std::ofstream file(filename);
    file << regrets;
}
