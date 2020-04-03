import pandas as pd
import scipy as sp

class Bernoulli0101Chain():
    
    def __init__(self, n_agents):
        self.agents = [f'A{i}' for i in range(n_agents)]
        
        self.groups = []
        self.true_means = []
        for i in range(n_agents-1):
            # Create group
            group = [[0, 0],
                     [0, 1],
                     [1, 0],
                     [1, 1]]
            group = pd.DataFrame(group, columns=self.agents[i:i+2])
            self.groups.append(group)
                 
            # Create mean table
            if i % 2 == 0:
                means = [[0.75],
                         [1.00],
                         [0.25],
                         [0.90]]
            else:
                means = [[0.75],
                         [0.25],
                         [1.00],
                         [0.90]]
            means = pd.DataFrame(means, columns=[f'mu{i}'])
            means = pd.concat([group, means], axis=1, sort=False)
            self.true_means.append(means)

    def regret(self, joint_arm):
        # Compute optimal arm
        optimal_arm = pd.Series([i % 2 for i in range(len(self.agents))], index=self.agents)

        # Get true means
        return sum(self._get_means(optimal_arm)) - sum(self._get_means(joint_arm))

    def execute(self, joint_arm):
        local_rewards = []
        for mean in self._get_means(joint_arm):
            # Sample random reward
            local_rewards.append(sp.stats.bernoulli(p=mean).rvs(1)[0])
        return local_rewards

    def _get_means(self, joint_arm):
        means = []
        for local_means, group in zip(self.true_means, self.groups):
            # Get local mean associated with joint arm
            agents = group.columns
            index = (local_means[agents] == joint_arm[agents]).all(axis=1)
            mean = local_means.loc[index].drop(columns=agents).values[0,0]
        
            means.append(mean)
        return means

def test_bernoulli_chain():
    from coordination_graph import variable_elimination
    
    n_agents = 10
    env = Bernoulli0101Chain(n_agents)

    # TEST: variable elimination returns the correct optimal joint arm and associated reward
    true_optimal_arm = pd.DataFrame([i % 2 for i in range(n_agents)], index=env.agents).T
    joint_arm = variable_elimination(env.true_means)
    is_optimal = (joint_arm == true_optimal_arm).all(axis=1).iloc[0]
    assert(is_optimal and sum(env.get_means(joint_arm)) == n_agents-1 and "The optimal joint action and reward returned by VE are not correct")
