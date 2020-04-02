#include <ThompsonSamplingPoissonPolicy.hpp>

#include <AIToolbox/Factored/Bandit/Algorithms/Utils/VariableElimination.hpp>
#include <random>

ThompsonSamplingPoissonPolicy::ThompsonSamplingPoissonPolicy(const AIToolbox::Factored::Action & A, const AIToolbox::Factored::Bandit::QFunction & q, const std::vector<std::vector<unsigned>> & counts) :
        Base(A), q_(q), counts_(counts) {}

AIToolbox::Factored::Action ThompsonSamplingPoissonPolicy::sampleAction() const {
    using VE = AIToolbox::Factored::Bandit::VariableElimination;
    VE::GVE::Graph graph(A.size());

    for (size_t i = 0; i < q_.bases.size(); ++i) {
        const auto & basis = q_.bases[i];
        const auto & counts = counts_[i];
        auto & factorNode = graph.getFactor(basis.tag)->getData();
        const bool isFilled = factorNode.size() > 0;

        if (!isFilled) factorNode.reserve(basis.values.size());

        for (size_t y = 0; y < static_cast<size_t>(basis.values.size()); ++y) {
            // Jeoffrey's prior
            std::gamma_distribution<double> dist(basis.values[y] * counts[y] + 0.5, 1.0/(counts[y] + 0.0));
            const auto val = dist(rand_);

            if (isFilled)
                factorNode[y].second.first += val;
            else
                factorNode.emplace_back(y, VE::Factor{val, {}});
        }
    }
    VE ve;
    return std::get<0>(ve(A, graph));
}

double ThompsonSamplingPoissonPolicy::getActionProbability(const AIToolbox::Factored::Action & a) const {
    // The true formula here is hard, so we don't compute this exactly.
    //
    // Instead we sample, which is easier and possibly faster if we just
    // want a rough approximation.
    constexpr unsigned trials = 1000;
    unsigned selected = 0;

    for (size_t i = 0; i < trials; ++i)
        if (sampleAction() == a)
            ++selected;

    return static_cast<double>(selected) / trials;
}
