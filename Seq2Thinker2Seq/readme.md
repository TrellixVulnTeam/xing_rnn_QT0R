Data Format:

# File Structure

```
raw_data/
	train
	dev
	test

model_{version}/
	data_cache/
		train.ids
		dev.ids
		test.ids
		vocab
	saved_model/
		summary
	log.train.txt
	log.beam_decode.txt
	log.force_decode.txt
```

# Bucket sizes

`max_source_length` = max source length

`max_target_length` = max target length + 1 (due to _GO and _EOS)

	

# Using Tensorboard:

```bash
# on HPC
$ source init_tensorflow.sh
$ tensorboard --logdir=model/model_ptb --port=8080
# anther terminal (port foward)
$ ssh -L 6006:127.0.0.1:8080 xingshi@hpc-login2.usc.edu
```
Then open browser: localhost:6006

# Thinker

Only works for basic_seq2seq now, not for attention_seq2seq


# TODO:
1. batch normalization