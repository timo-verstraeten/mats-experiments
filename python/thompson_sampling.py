from coordination_graph import variable_elimination

import numpy as np
import pandas as pd
import scipy as sp

class ThompsonSampling():
    """
    Traditional Thompson sampling mechanism.
    
    Methods
    -------
    sample()
        Sample a single value for each the mean posteriors.
    pull()
        Pull an arm according to the probability matching mechanism of Thompson sampling.
    update(arm, reward)
        Update an arm's mean posterior with a given reward.
    """
    
    def __init__(self, arms, priors):
        """
        Parameters
        ----------
        arms : pd.DataFrame
            arms with entries labeled with the associated agent
        priors : list of objects with superclass 'posteriors.Posterior'
            prior for each arm (should be in the same order as arms)
        """
        self._arms = arms
        self._posteriors = priors  # Mean posteriors

    def sample(self):
        """
        Returns
        -------
        list of float
            A sample from every mean's posterior.
        """
        theta = self._arms.copy()
        theta['mu'] = [post.sample() for post in self._posteriors]
        return theta
    
    def pull(self):
        """
        Returns
        -------
        pd.Series
            A joint arm with the agents' names as columns
        """
        # Sample
        means = self.sample()
        
        # Maximize
        max_operator = lambda x: x.loc[x[self.name] == x[self.name].max()]
        a_max = means.loc[means['mu'] == means['mu'].max()]
        a_max.drop(columns='mu', inplace=True)

        return a_max

    def update(self, arm, reward):
        """
        Parameters
        ----------
        arm : pd.Series
            arm with entries labeled with the associated agent
        reward : float
            reward received for executing the arm
        """
        index = np.where((self._arms == arm).all(axis=1))[0][0]
        self._posteriors[index].update(reward)

class MultiAgentThompsonSampling():
    """
    Multi-agent Thompson sampling (MATS) mechanism.
        
    Methods
    -------
    sample()
        Sample  from the mean posteriors.
    pull()
        Pull a joint arm according to the probability matching mechanism of MATS.
    update(arm, reward)
        Update an arm's mean posterior with a given reward.
    """

    def __init__(self, groups, priors):
        """
        Parameters
        ----------
        groups : list of pd.DataFrame
            A data frame for each local group. The data frame consists of every possible local joint arm (rows) jointly over the agents (columns) within the group.
        priors : list of list of objects with superclass 'posteriors.Posterior'
            Each group has a list of priors, i.e., one for the mean of every local joint action.
        """
        # Create local Thompson sampler per group
        self._groups = groups
        self._groups_samplers = [ThompsonSampling(local_arms, local_priors) for local_arms, local_priors in zip(groups, priors)]

    def sample(self):
        """
        Returns
        -------
        list of list of float
            For every group, a sample from every mean's posterior.
        """
        theta = []
        
        # Sample per group
        for e, sampler in enumerate(self._groups_samplers):
            theta_e = sampler.sample()
            theta_e.rename(columns={'mu': f'mu{e}'}, inplace=True)
            theta.append(theta_e)
        return theta

    def pull(self):
        """
        Returns
        -------
        pd.Series
            A joint arm with the agents' names as columns
        """
        # Sample
        group_means = self.sample()
        
        # Maximize
        a_max = variable_elimination(group_means)

        return a_max

    def update(self, joint_arm, local_rewards):
        """
        Parameters
        ----------
        joint_arm : pd.Series
            arm with entries labeled with the associated agent
        local_rewards : list of float
            For each group, the reward received for executing the local arm
        ----------
        """
        for local_arms, local_sampler, local_reward in zip(self._groups, self._groups_samplers, local_rewards):
            local_sampler.update(joint_arm[local_arms.columns], local_reward)
            

