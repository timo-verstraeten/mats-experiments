# REQUIREMENTS Python 3.7
# Numpy

import numpy as np
import pandas as pd

def variable_elimination(group_means):
    """
    Variable elimination for multi-agent multi-armed bandits.
    
    Parameters
    ----------
    group_means : list of pd.DataFrame
        For every group, a data frame where the first columns are the agents' names and the last column is the mean reward (named 'mu').
    Return
    ------
    pd.Series
        Joint arm with the agent's name annotated for each entry.
    """
    
    # Create coordination graph from group_means
    agents = {}  # Mapping from name to object
    reward_functions = []
    for table in group_means:
        reward_name = table.columns[-1]

        group_agents = set()
        for agent_name in list(filter(lambda x: x[:2] != 'mu', table.columns)):
            if agent_name not in agents:
                agents[agent_name] = Agent(agent_name)
            group_agents.add(agents[agent_name])

        reward_function = RewardFunction(reward_name, table, group_agents)
        reward_functions.append(reward_function)

    # Choose the agents to eliminate
    #TODO how to pick agent
    agents_ordered = list(agents.values())
    for agent in agents_ordered:
        agent.resolve()  # Eliminate agent from the graph

    # Find maximum joint arm that maximizes the sum of rewards
    joint_arm = pd.DataFrame()
    for agent in reversed(agents_ordered):
        joint_arm = agent.condition(joint_arm)

    return joint_arm.iloc[0]

class RewardFunction():
    def __init__(self, name, table, agents):
        self.name = name
        self.table = table
        self.agents = set(agents)
        
        # Add the reward function to each of the agents
        for agent in self.agents:
            agent.add_reward_function(self)

    def __str__(self):
        return self.name
    
    def __call__(self, joint_arm):
        # Create boolean mask to filter out the correct arm in the reward table.
        agents = self.table.columns.drop(self.name)
        mask = (self.table[agents] == joint_arm[agents].iloc[0]).all(axis=1)

        return self.table[self.name].loc[mask].iloc[0]  # Return reward as a float

    def __add__(self, other):
        common_agents = list(map(str, self.agents & other.agents))
        if len(common_agents) == 0:
            raise NotImplementedError("Addition of two non-overlapping reward tables is not implemented")
        
        # Merge two reward functions into a single new one
        name = f'{self.name}+{other.name}'
        agents = self.agents | other.agents
        table = self.table.merge(other.table, on=common_agents, how='outer')  # Merge both reward tables on the common agents
        table[name] = table[[self.name, other.name]].sum(axis=1)  # Sum both reward functions into a single one
        table.drop(columns=[self.name, other.name], inplace=True)  # Remote old reward functions

        return RewardFunction(name, table, agents)

    def replace_in_agents(self, new_reward):
        for agent in self.agents:
            agent.rewards.remove(self)  # Remove the current reward function
            if new_reward not in agent.rewards:
                # Only add new reward function if it doesn't exist in the list of the agent yet.
                agent.rewards.append(new_reward)  # Add the new reward function

    def eliminate_agent(self, agent):
        # Update table
        max_operator = lambda x: x.loc[x[self.name] == x[self.name].max()]
        neighbor_names = [str(neighbor) for neighbor in self.agents if neighbor != agent]
        if len(neighbor_names) == 0:
            # If there are no neighbors, compute max action
            cond_table = max_operator(self.table)
        else:
            # Compute maximal action per joint action of the neighbors
            cond_table = self.table.groupby(neighbor_names, as_index=False).apply(max_operator).reset_index(drop=True)
        
        # Update reward function
        self.agents -= set([agent])
        self.table = cond_table.drop(columns=str(agent))
        
        # Return conditional policy for eliminated agent
        return cond_table.drop(columns=self.name)

class Agent():
    def __init__(self, name):
        self.name = name
        self.rewards = []
        self.cond_policy = None
    
    def __str__(self):
        return self.name
    
    def resolve(self):
        # Create new reward function
        new_reward = sum(self.rewards[1:], self.rewards[0])
        
        # Create conditional policy
        self.cond_policy = new_reward.eliminate_agent(self)
    
        # Update neighbors
        for reward in self.rewards:
            reward.replace_in_agents(new_reward)

    def condition(self, partial_policy):
        common_agents = list(set(self.cond_policy.columns) & set(partial_policy.columns))
        if len(common_agents) == 0:
            # If there are no common agents, just concatenate both policies
            return pd.concat([self.cond_policy, partial_policy], axis=1, sort=False)
        else:
            # If there are common agents, merge both policies.
            return pd.merge(self.cond_policy, partial_policy, on=common_agents, how="right").dropna(0, 'any')

    def add_reward_function(self, reward):
        self.rewards.append(reward)
