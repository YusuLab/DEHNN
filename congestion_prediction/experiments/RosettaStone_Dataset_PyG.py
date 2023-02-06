import torch
import torch.nn
from torch_geometric.data import Dataset
from torch_geometric.data import Data

import numpy as np
import json

train_designs = [
    'adaptec1',
    'adaptec2',
    'adaptec3',
    'bigblue1',
    'bigblue2',
    'newblue1',
    'newblue2',
    'newblue3',
    'newblue4',
    'newblue5',
    'superblue1',
    'superblue2',
    'superblue3',
    'superblue4',
    'superblue5',
    'superblue6',
    'superblue7',
    'superblue9',
    'superblue10',
    'superblue11',
    'superblue12',
    'superblue14',
    'superblue15',
    'superblue16',
]

valid_designs = [
    'adaptec4',
    'bigblue3',
    'newblue6',
    'superblue18',
]

test_designs = [
    'adaptec5',
    'bigblue4',
    'newblue7',
    'superblue19'
]

class RosettaStone_Dataset_PyG(Dataset):
    def __init__(self, data_dir, split):
        super().__init__()

        self.data_dir = data_dir
        self.split = split

        if split == 'train':
            self.designs = train_designs
        elif split == 'valid':
            self.designs = valid_designs
        elif split == 'test':
            self.designs = test_designs
        else:
            print('Unsupported split!')
            self.designs = None

        print('Number of designs:', len(self.designs))

        for design in self.designs:
            conn_fn = self.data_dir + '/' + design + '/' + design + '_connectivity.npz'
            fson_fn = self.data_dir + '/' + design + '/' + design + '.json.gz'

            # Connectivity
            print('Reading', conn_fn)
            conn = np.load(conn_fn)
            row = conn['row']
            col = conn['col']
            data = conn['data']
            shape = conn['shape']

        print('Done data pre-processing for the', self.split, 'set')

    def len(self):
        return len(self.designs)

    def get(self, idx):
        return None


