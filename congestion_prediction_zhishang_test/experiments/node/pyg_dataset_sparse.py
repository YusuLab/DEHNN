import torch
import torch.nn
from torch_geometric.data import Dataset
from torch_geometric.data import Data

import numpy as np
import pickle

class pyg_dataset_sparse(Dataset):
    def __init__(self, data_dir, graph_index, target, load_pe = False, num_eigen = 5, load_global_info = True, load_pd = False, graph_rep = 'star', vn = True, debug = False):
        super().__init__()
        self.data_dir = data_dir
        self.graph_index = graph_index
        self.target = target
        assert target == 'demand' or target == 'capacity' or target == 'congestion'
        print('Learning target:', self.target)

        self.load_pe = load_pe
        self.num_eigen = num_eigen
        self.load_global_info = load_global_info
        self.load_pd = load_pd

        # Split
        if not debug:
            file_name = str(graph_index) + '.split_sparse.pkl'
            f = open(file_name, 'rb')
            dictionary = pickle.load(f)
            f.close()

            self.train_indices = dictionary['train_indices']
            self.valid_indices = dictionary['valid_indices_inst']
            self.test_indices = dictionary['test_indices_inst']

        # Read node features
        file_name = data_dir + '/' + str(graph_index) + '.node_features.pkl'
        f = open(file_name, 'rb')
        dictionary = pickle.load(f)
        f.close()

        self.design_name = dictionary['design']

        num_instances = dictionary['num_instances']
        num_nets = dictionary['num_nets']
        instance_features = torch.Tensor(dictionary['instance_features'])
        instance_features = instance_features[:, 2:]

        # Read learning targets
        file_name = data_dir + '/' + str(graph_index) + '.net_demand_capacity.pkl'
        f = open(file_name, 'rb')
        dictionary = pickle.load(f)
        f.close()

        demand = torch.Tensor(dictionary['demand'])
        capacity = torch.Tensor(dictionary['capacity'])

        if self.target == 'demand':
            y = demand.unsqueeze(dim = 1)
        elif self.target == 'capacity':
            y = capacity.unsqueeze(dim = 1)
        elif self.target == 'congestion':
            congestion = demand - capacity
            y = congestion.unsqueeze(dim = 1)
        else:
            print('Unknown learning target')
            assert False

        # Read connection
        file_name = data_dir + '/' + str(graph_index) + '.bipartite.pkl'
        f = open(file_name, 'rb')
        dictionary = pickle.load(f)
        f.close()
        
        # Read Filter Index file
#         file_name = data_dir + '/' + str(graph_index) + '.select.pkl'
#         f = open(file_name, 'rb')
#         select_indices = pickle.load(f)['select_indicess']
#         f.close()
        
        row = dictionary['instance_idx']#[select_indices]
        col = dictionary['net_idx']#[select_indices]
        edge_dir = dictionary['edge_dir']#[select_indices]
        
        data = torch.ones(len(row))
        
        i = np.array([row, col])
        
        net_inst_adj = torch.sparse_coo_tensor(i, data).t()
        
        v_drive_idx = [idx for idx in range(len(row)) if edge_dir[idx] == 1]
        v_sink_idx = [idx for idx in range(len(row)) if edge_dir[idx] == 0] 
        
        inst_net_adj_v_drive = torch.sparse_coo_tensor(i.T[v_drive_idx].T, data[v_drive_idx])
        
        inst_net_adj_v_sink = torch.sparse_coo_tensor(i.T[v_sink_idx].T, data[v_sink_idx])
        
        x = instance_features

        # PyG data
        
        example = Data()
        example.__num_nodes__ = x.size(0)
        example.x = x
        example.y = y
        example.net_inst_adj = net_inst_adj
        example.inst_net_adj_v_drive = inst_net_adj_v_drive
        example.inst_net_adj_v_sink = inst_net_adj_v_sink
      
        if vn:
            file_name = data_dir + '/' + str(graph_index) + '.single_star_part_dict.pkl'
            f = open(file_name, 'rb')

            part_dict = pickle.load(f)
            f.close()


            file_name = data_dir + '/' + str(graph_index) + '.star_top_part_dict.pkl'
            f = open(file_name, 'rb')

            part_id_to_top = pickle.load(f)
            f.close()

            edge_index_local_vn = []
            edge_index_vn_top = []
            part_id_lst = list(part_dict.values())

            for local_idx in range(len(example.x)):
                vn_idx = part_dict[local_idx]
                edge_index_local_vn.append([local_idx, vn_idx])
            

            top_part_id_lst = []
            for part_idx, top_idx in part_id_to_top.items():
                top_part_id_lst.append(top_idx)
                
                edge_index_vn_top.append([part_idx, top_idx])
            
            
            
            
            example.num_vn = len(np.unique(part_id_lst))
            example.num_top_vn = len(np.unique(top_part_id_lst))
            
            print(example.num_vn, example.num_top_vn)
            
            example.part_id = torch.Tensor(edge_index_local_vn).long().t()[1]
            #example.edge_index_local_vn = torch.Tensor(edge_index_local_vn).long().t()
            #example.edge_index_vn_top = torch.Tensor(edge_index_vn_top).long().t()
        
        
        #weights = torch.tensor([weight_dict[target.item()] for target in targets.view(-1)]).float()
        #example.weights = weights
        
        # Load capacity
        #file_name = data_dir + '/' + str(graph_index) + '.targets.pkl'
        #f = open(file_name, 'rb')
        #dictionary = pickle.load(f)
        #f.close()

        #demand = torch.Tensor(dictionary['demand'])
        #capacity = torch.Tensor(dictionary['capacity'])

        #capacity = torch.sum(capacity, dim = 1).unsqueeze(dim = 1)
        #norm_cap = (capacity - torch.min(capacity)) / (torch.max(capacity) - torch.min(capacity))
        #capacity_features = torch.cat([capacity, torch.sqrt(capacity), norm_cap, torch.sqrt(norm_cap), torch.square(norm_cap), torch.sin(norm_cap), torch.cos(norm_cap)], dim = 1)

        #example.x = torch.cat([example.x, capacity_features], dim = 1)
        
        capacity = capacity.unsqueeze(dim = 1)
        norm_cap = (capacity - torch.min(capacity)) / (torch.max(capacity) - torch.min(capacity))
        capacity_features = torch.cat([capacity, torch.sqrt(capacity), norm_cap, torch.sqrt(norm_cap), torch.square(norm_cap), torch.sin(norm_cap), torch.cos(norm_cap)], dim = 1)
        

        # Load positional encoding
        if self.load_pe == True:
            file_name = data_dir + '/' + str(graph_index) + '.eigen.' + str(self.num_eigen) + '.pkl'
            f = open(file_name, 'rb')
            dictionary = pickle.load(f)
            f.close()

            example.evects = torch.Tensor(dictionary['evects'])
            example.evals = torch.Tensor(dictionary['evals'])

        # Load global information
        if self.load_global_info == True:
            file_name = data_dir + '/' + str(graph_index) + '.global_information.pkl'
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
            file_name = data_dir + '/' + str(graph_index) + '.node_neighbor_features.pkl'
            f = open(file_name, 'rb')
            dictionary = pickle.load(f)
            f.close()

            pd = torch.Tensor(dictionary['pd'])
            neighbor_list = torch.Tensor(dictionary['neighbor'])

            assert pd.size(0) == num_instances
            assert neighbor_list.size(0) == num_instances

            example.x = torch.cat([example.x, pd, neighbor_list], dim = 1)            

        
        example.x_net = capacity_features
        
        self.example = example
        
        print(example, graph_index)

    def len(self):
        return 1

    def get(self, idx):
        return self.example

