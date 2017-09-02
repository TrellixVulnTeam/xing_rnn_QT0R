
#!/bin/bash
#PBS -q isi
#PBS -l walltime=1:00:00
#PBS -l nodes=1:ppn=8

ROOT_DIR=../
PY=$ROOT_DIR/py/run.py
BLEU=$ROOT_DIR/py/util/multi-bleu.perl
MODEL_DIR=$ROOT_DIR/model/smallh100d07l01n2attadagrad
DATA_DIR=$ROOT_DIR/data/small/
TRAIN_PATH_FROM=$DATA_DIR/train.src
TRAIN_PATH_TO=$DATA_DIR/train.tgt
DEV_PATH_FROM=$DATA_DIR/valid.src
DEV_PATH_TO=$DATA_DIR/valid.tgt
TEST_PATH_FROM=$DATA_DIR/test.src
TEST_PATH_TO=$DATA_DIR/test.tgt
DECODE_OUTPUT=$MODEL_DIR/decode_output/__decode_id__.output
BLEU_OUTPUT=$MODEL_DIR/decode_output/__decode_id__.bleu

source /home/nlg-05/xingshi/sh/init_tensorflow.sh

python $PY --mode TRAIN --model_dir $MODEL_DIR --train_path_from $TRAIN_PATH_FROM --dev_path_from $DEV_PATH_FROM --train_path_to $TRAIN_PATH_TO --dev_path_to $DEV_PATH_TO --saveCheckpoint True --allow_growth True  --batch_size 4 --size 100 --keep_prob 0.7 --learning_rate 0.1 --n_epoch 100 --num_layers 2 --attention True --from_vocab_size 100 --to_vocab_size 100 --min_source_length 0 --max_source_length 22 --min_target_length 0 --max_target_length 22 --n_bucket 2 --optimizer adagrad --N 00000 --attention_style additive --attention_scale True