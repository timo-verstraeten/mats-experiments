from environments import Bernoulli0101Chain
from posteriors import BetaPosterior
from thompson_sampling import MultiAgentThompsonSampling

import matplotlib.pyplot as plt
import pandas as pd
import scipy as sp


def bernoulli_chain_experiment(n_iter):
    # Create environment
    n_agents = 10
    env = Bernoulli0101Chain(n_agents)

    # Create priors
    priors = [[BetaPosterior(0.5, 0.5) for _ in range(arms.shape[0])] for arms in env.groups]
    
    # Run MATS
    mats = MultiAgentThompsonSampling(env.groups, priors)
    regrets = []
    for i in range(n_iter):
        # Do step with MATS
        joint_arm = mats.pull()
        local_rewards = env.execute(joint_arm)
        mats.update(joint_arm, local_rewards)

        # Logging
        regret = env.regret(joint_arm)
        regrets.append(regret)
        print(i, regret, '\t', joint_arm.values)

    plt.plot(regrets)
    plt.xlabel('Iteration')
    plt.ylabel('Regret')
    plt.savefig(f'test_bernoulli_chain_experiment_{n_iter}.pdf')

bernoulli_chain_experiment(n_iter=100)
