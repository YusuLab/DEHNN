#!/bin/bash

program=train_gnn_hetero_net

#target=demand
#target=capacity
#target=congestion
target=hpwl
# Index of graph
graph_index=$1

mkdir $program
cd $program
mkdir $target
cd ..
dir=./$program/$target/

data_dir=../../data/2023-03-06_data/

num_epoch=1000
batch_size=1
learning_rate=0.001
seed=123456789
n_layers=2
hidden_dim=32

# Device
device=cuda
device_idx=1

# Position encoding
pe=none
pos_dim=0

# Global information
load_global_info=0

# Persistence diagram & Neighbor list
load_pd=1

# Test mode
test_mode=0

# GNN type
gnn_type=gcn

# Virtual node
virtual_node=0

# Execution
name=${program}.${target}.num_epoch.${num_epoch}.batch_size.${batch_size}.learning_rate.${learning_rate}.seed.${seed}.n_layers.${n_layers}.hidden_dim.${hidden_dim}.pe.${pe}.pos_dim.${pos_dim}.virtual_node.${virtual_node}.gnn_type.${gnn_type}.load_global_info.${load_global_info}.load_pd.${load_pd}.graph_index.${graph_index}
CUDA_VISIBLE_DEVICES=$device_idx python3 $program.py --target=$target --dir=$dir --name=$name --num_epoch=$num_epoch --batch_size=$batch_size --learning_rate=$learning_rate --seed=$seed --n_layers=$n_layers --hidden_dim=$hidden_dim --pe=$pe --pos_dim=$pos_dim --virtual_node=$virtual_node --gnn_type=$gnn_type --load_global_info=$load_global_info --load_pd=$load_pd --test_mode=$test_mode --device=$device --data_dir=$data_dir --graph_index=$graph_index

