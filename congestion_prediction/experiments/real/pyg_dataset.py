import torch
import torch.nn
from torch_geometric.data import Dataset
from torch_geometric.data import Data

import numpy as np
import pickle

class pyg_dataset(Dataset):
    def __init__(self, data_dir, fold_index, split, target, load_pe = False, num_eigen = 5, load_global_info = True, load_pd = False, total_samples = 32):
        super().__init__()
        self.data_dir = data_dir
        self.fold_index = fold_index
        self.split = split
        self.target = target
        assert target == 'demand' or target == 'capacity' or target == 'congestion'
        print('Learning target:', self.target)

        # Position encoding
        self.load_pe = load_pe
        self.num_eigen = num_eigen
        self.load_global_info = load_global_info
        self.load_pd = load_pd

        # Read cross-validation
        file_name = data_dir + '/6_fold_cross_validation.pkl'
        f = open(file_name, 'rb')
        dictionary = pickle.load(f)
        f.close()
        folds = dictionary['folds']

        # Take the sample indices
        test_indices = folds[self.fold_index]
        train_indices = [idx for idx in range(total_samples) if idx not in test_indices]

        if self.split == 'train':
            self.sample_indices = train_indices
        else:
            self.sample_indices = test_indices
        
        self.num_samples = len(self.sample_indices)
        print('Number of samples:', self.num_samples)

        # Read data
        self.data = []

        for sample in self.sample_indices:
            # Read node features
            file_name = data_dir + '/' + str(sample) + '.node_features.pkl'
            f = open(file_name, 'rb')
            dictionary = pickle.load(f)
            f.close()

            num_instances = dictionary['num_instances']
            num_nets = dictionary['num_nets']
            instance_features = torch.Tensor(dictionary['instance_features'])
            net_features = torch.zeros(num_nets, instance_features.size(1))
            x = torch.cat([instance_features, net_features], dim = 0)

            # Read learning targets
            file_name = data_dir + '/' + str(sample) + '.targets.pkl'
            f = open(file_name, 'rb')
            dictionary = pickle.load(f)
            f.close()

            demand = torch.Tensor(dictionary['demand'])
            capacity = torch.Tensor(dictionary['capacity'])

            if self.target == 'demand':
                y = torch.sum(demand, dim = 1).unsqueeze(dim = 1)
            elif self.target == 'capacity':
                y = torch.sum(capacity, dim = 1).unsqueeze(dim = 1)
            elif self.target == 'congestion':
                congestion = demand - capacity
                y = torch.sum(congestion, dim = 1).unsqueeze(dim = 1)
            else:
                print('Unknown learning target')
                assert False

            # Read connection
            file_name = data_dir + '/' + str(sample) + '.bipartite.pkl'
            f = open(file_name, 'rb')
            dictionary = pickle.load(f)
            f.close()

            instance_idx = torch.Tensor(dictionary['instance_idx']).unsqueeze(dim = 1).long()
            net_idx = torch.Tensor(dictionary['net_idx']) + num_instances
            net_idx = net_idx.unsqueeze(dim = 1).long()

            edge_attr = torch.Tensor(dictionary['edge_attr']).unsqueeze(dim = 1).float()
            edge_index = torch.cat((instance_idx, net_idx), dim = 1)
            
            '''
            edge_dir = dictionary['edge_dir']
            print('Edge dir:', edge_dir.shape)
            print('Min:', np.min(edge_dir))
            print('Max:', np.max(edge_dir))
            '''

            # PyG data
            example = Data()
            example.__num_nodes__ = x.size(0)
            example.x = x
            example.y = y
            example.edge_index = torch.transpose(edge_index, 0, 1)
            example.edge_attr = edge_attr

            # Load capacity
            capacity = torch.sum(capacity, dim = 1).unsqueeze(dim = 1)
            norm_cap = (capacity - torch.min(capacity)) / (torch.max(capacity) - torch.min(capacity))
            capacity_features = torch.cat([capacity, torch.sqrt(capacity), norm_cap, torch.sqrt(norm_cap), torch.square(norm_cap), torch.sin(norm_cap), torch.cos(norm_cap)], dim = 1)

            capacity_features = torch.cat([capacity_features, torch.zeros(num_nets, capacity_features.size(1))], dim = 0)
            example.x = torch.cat([example.x, capacity_features], dim = 1)

            # Load positional encoding
            if self.load_pe == True:
                file_name = data_dir + '/' + str(sample) + '.eigen.' + str(self.num_eigen) + '.pkl'
                f = open(file_name, 'rb')
                dictionary = pickle.load(f)
                f.close()

                example.evects = torch.Tensor(dictionary['evects'])
                example.evals = torch.Tensor(dictionary['evals'])

            # Load global information
            if self.load_global_info == True:
                file_name = data_dir + '/' + str(sample) + '.global_information.pkl'
                f = open(file_name, 'rb')
                dictionary = pickle.load(f)
                f.close()

                core_util = dictionary['core_utilization']
                global_info = torch.Tensor(np.array([core_util, np.sqrt(core_util), core_util ** 2, np.cos(core_util), np.sin(core_util)]))
                num_nodes = example.x.size(0)
                global_info = torch.cat([global_info.unsqueeze(dim = 0) for i in range(num_nodes)], dim = 0)

                example.x = torch.cat([example.x, global_info], dim = 1)

            # Load persistence diagram and neighbor list
            if self.load_pd == True:
                file_name = data_dir + '/' + str(sample) + '.node_neighbor_features.pkl'
                f = open(file_name, 'rb')
                dictionary = pickle.load(f)
                f.close()

                pd = torch.Tensor(dictionary['pd'])
                neighbor_list = torch.Tensor(dictionary['neighbor'])

                assert pd.size(0) == num_instances
                assert neighbor_list.size(0) == num_instances

                pd = torch.cat([pd, torch.zeros(num_nets, pd.size(1))], dim = 0)
                neighbor_list = torch.cat([neighbor_list, torch.zeros(num_nets, neighbor_list.size(1))], dim = 0)

                example.x = torch.cat([example.x, pd, neighbor_list], dim = 1)

            self.data.append(example)

        print('Done reading data')

    def len(self):
        return self.num_samples

    def get(self, idx):
        return self.data[idx]

