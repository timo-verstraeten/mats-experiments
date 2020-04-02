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
    total_rewards = []
    for i in range(n_iter):
        joint_arm = mats.pull()
        local_rewards = env.execute(joint_arm)
        total_rewards.append(sum(local_rewards))
        mats.update(joint_arm, local_rewards)
        print(i, sum(local_rewards), '\t', joint_arm.values)

    plt.plot(total_rewards)
    plt.savefig('test.pdf')

bernoulli_chain_experiment(n_iter=100)
