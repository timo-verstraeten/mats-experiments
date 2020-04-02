from coordination_graph import variable_elimination

import numpy as np
import pandas as pd
import scipy as sp

class ThompsonSampling():
    def __init__(self, arms, priors):
        self._arms = arms
        self._mean_dists = priors

    def sample(self):
        theta = self._arms.copy()
        theta['mu'] = [dist.sample() for dist in self._mean_dists]
        return theta
    
    def pull(self):
        # Sample
        means = self.sample()
        
        # Maximize
        max_operator = lambda x: x.loc[x[self.name] == x[self.name].max()]
        a_max = means.loc[means['mu'] == means['mu'].max()]
        a_max.drop(columns='mu', inplace=True)

        return a_max

    def update(self, arm, reward):
        index = np.where((self._arms == arm).all(axis=1))[0][0]
        self._mean_dists[index].update(reward)

class MultiAgentThompsonSampling():
    def __init__(self, groups, priors):
        # Create local Thompson sampler per group
        self._groups = groups
        self._groups_samplers = [ThompsonSampling(local_arms, local_priors) for local_arms, local_priors in zip(groups, priors)]

    def sample(self):
        theta = []
        
        # Sample per group
        for e, sampler in enumerate(self._groups_samplers):
            theta_e = sampler.sample()
            theta_e.rename(columns={'mu': f'mu{e}'}, inplace=True)
            theta.append(theta_e)
        return theta

    def pull(self):
        # Sample
        group_means = self.sample()
        
        # Maximize
        a_max = variable_elimination(group_means)

        return a_max

    def update(self, joint_arm, local_rewards):
        for local_arms, local_sampler, local_reward in zip(self._groups, self._groups_samplers, local_rewards):
            local_sampler.update(joint_arm[local_arms.columns], local_reward)
            

