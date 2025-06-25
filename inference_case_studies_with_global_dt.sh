#!/bin/bash
#
# Run inference on pre-trained model using global DT as input
#

# working directory
wd=$(pwd)
data=/leonardo_scratch/large/userexternal/hschulz0/data/
# git root directory
git_root_dir=/leonardo/home/userexternal/hschulz0/repos/

PYTHON="uv run python"

# Step 1:
#=========
# 1.1 Get the model weights from the training
CHECKPOINT=$data/saved_model/train-hi_lam-2x300-02_27_15-4034/last.ckpt

# 1.2 Get statistics from training data so this can be used to standardize the inference data

# 1.4 Get the neural-lam config file used for training
neural_lam_config=$data/config.yaml

# 1.3 Get the command (line arguemnts) used for training the model and for evaluation
graph_name=rect_hi3
neural_lam_command_line_args=(
    --num_workers 6
    --precision bf16-mixed
    --batch_size 1
    --hidden_dim 300
    --hidden_dim_grid 150
    --time_delta_enc_dim 32
    --config_path ${neural_lam_config}
    --model hi_lam
    --processor_layers 2
    --graph_name ${graph_name}
    --dynamic_time_deltas
    --num_nodes 1
    --epochs 30
    --ar_steps_train 1
    --lr 0.001
    --min_lr 0.001
    --val_interval 5
    --ar_steps_eval 8
    --val_steps_to_log 1 2 4 8 \
    --load ${CHECKPOINT}
    --eval val \
    --plot_vars pres_seasurface t2m u10m v10m pres0m lwavr0m swavr0m z700 t700 r700 u700 v700 tw700 r200 r1000 u1000
    --save_eval_to_zarr_path $data/state_predictions.zarr
)

# Step 2:
#=========
# Inference data, data preparation, graph creation and neural-lam: Clone git repositories and install environments 
# 2.1 Get you data to do inference from. If the data is in grib format, convert it to zarr

# Step 3:
#=========
# 3.1 Get you data to do inference from
# 3.2 If the data is in grib format, convert it to zarr
#cd ${git_root_dir}/mars_to_zarr
#uv run python -m mars_to_zarr --config $data/globalDT_MARS_20241214.yaml -v
#cd ${wd}

# Step 4:
#=========
# 4.1 Create mllam-data-prep datastore
mdp_config=$data/globalDT.20241214.yaml
${PYTHON} -m mllam_data_prep ${mdp_config}
# 4.2 Create mllam-data-prep boundary datastore
mdp_config=$data/globalDT_boundary.20241214.yaml
#${PYTHON} -m mllam_data_prep ${mdp_config}

# Step 5:
#=========
# 5.1 Create graph - Hierarchical 3-level
lev=3
#MND=12500 m
MND=0.2 #  degrees (corresponds roughly to 12.5 km at latitude 55.5)
#${PYTHON} -m neural_lam.build_rectangular_graph \
#  --config_path ${neural_lam_config} \
#  --archetype hierarchical \
#  --max_num_levels ${lev} \
#  --mesh_node_distance ${MND} \
#  --graph_name ${graph_name}
#cd ${wd}

# Step 6:
#=========
# 6.1 Run inference
${PYTHON} -m neural_lam.train_model "${neural_lam_command_line_args[@]}"

# Open questions:
# - Need to use the training statistics when doing inference - how?
# - Correct swavr and lwavr for interior data
# - Correct boundary data (e.g. q instead of r)
