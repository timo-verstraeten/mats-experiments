# REQUIREMENTS Python 3.7
# Numpy

import numpy as np
import pandas as pd

def variable_elimination(group_means):
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

    #TODO how to pick agent
    agents_ordered = list(agents.values())
    for agent in agents_ordered:
        agent.resolve()

    # Maximize
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
        # Compute local arm used in reward function
        local_arm = self.table.columns.drop(self.name)
        mask = (self.table[local_arm] == joint_arm[local_arm].iloc[0]).all(axis=1)

        return self.table[self.name].loc[mask].iloc[0]

    def __add__(self, other):
        common_agents = list(map(str, self.agents & other.agents))
        if len(common_agents) == 0:
            raise NotImplementedError("Addition of two non-overlapping reward tables is not implemented")
        
        # Merge two reward functions
        name = f'{self.name}+{other.name}'
        agents = self.agents | other.agents
        table = self.table.merge(other.table, on=common_agents, how='outer')
        table[name] = table[[self.name, other.name]].sum(axis=1)
        table.drop(columns=[self.name, other.name], inplace=True)

        return RewardFunction(name, table, agents)

    def replace_in_agents(self, new_reward_function):
        for agent in self.agents:
            agent.reward_functions.remove(self)
            if new_reward_function not in agent.reward_functions:
                agent.reward_functions.append(new_reward_function)

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
        self.reward_functions = []
        self.cond_policy = None
    
    def __str__(self):
        return self.name
    
    def resolve(self):
        # Create new reward function
        new_reward_function = sum(self.reward_functions[1:], self.reward_functions[0])
        
        # Create conditional policy
        self.cond_policy = new_reward_function.eliminate_agent(self)
    
        # Update neighbors
        for reward_function in self.reward_functions:
            reward_function.replace_in_agents(new_reward_function)

    def condition(self, partial_policy):
        common_agents = list(set(self.cond_policy.columns) & set(partial_policy.columns))
        if len(common_agents) == 0:
            return pd.concat([self.cond_policy, partial_policy], axis=1, sort=False)
        else:
            return pd.merge(self.cond_policy, partial_policy, on=common_agents, how="right").dropna(0, 'any')

    def add_reward_function(self, reward_func):
        self.reward_functions.append(reward_func)
