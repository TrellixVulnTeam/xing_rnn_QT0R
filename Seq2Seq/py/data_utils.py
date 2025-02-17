# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Utilities for downloading data from WMT, tokenizing, vocabularies."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gzip
import os
import re
import tarfile

from six.moves import urllib

from tensorflow.python.platform import gfile
import tensorflow as tf
import numpy as np

# Special vocabulary symbols - we always put them at the start.
_PAD = b"_PAD"
_GO = b"_GO"
_EOS = b"_EOS"
_UNK = b"_UNK"
_START_VOCAB = [_PAD, _GO, _EOS, _UNK]

PAD_ID = 0
GO_ID = 1
EOS_ID = 2
UNK_ID = 3

# Regular expressions used to tokenize.
_WORD_SPLIT = re.compile(b"([.,!?\"':;)(])")
_DIGIT_RE = re.compile(br"\d")

# URLs for WMT data.
_WMT_ENFR_TRAIN_URL = "http://www.statmt.org/wmt10/training-giga-fren.tar"
_WMT_ENFR_DEV_URL = "http://www.statmt.org/wmt15/dev-v2.tgz"


def maybe_download(directory, filename, url):
  """Download filename from url unless it's already in directory."""
  if not os.path.exists(directory):
    print("Creating directory %s" % directory)
    os.mkdir(directory)
  filepath = os.path.join(directory, filename)
  if not os.path.exists(filepath):
    print("Downloading %s to %s" % (url, filepath))
    filepath, _ = urllib.request.urlretrieve(url, filepath)
    statinfo = os.stat(filepath)
    print("Successfully downloaded", filename, statinfo.st_size, "bytes")
  return filepath


def gunzip_file(gz_path, new_path):
  """Unzips from gz_path into new_path."""
  print("Unpacking %s to %s" % (gz_path, new_path))
  with gzip.open(gz_path, "rb") as gz_file:
    with open(new_path, "wb") as new_file:
      for line in gz_file:
        new_file.write(line)


def get_wmt_enfr_train_set(directory):
  """Download the WMT en-fr training corpus to directory unless it's there."""
  train_path = os.path.join(directory, "giga-fren.release2.fixed")
  if not (gfile.Exists(train_path +".fr") and gfile.Exists(train_path +".en")):
    corpus_file = maybe_download(directory, "training-giga-fren.tar",
                                 _WMT_ENFR_TRAIN_URL)
    print("Extracting tar file %s" % corpus_file)
    with tarfile.open(corpus_file, "r") as corpus_tar:
      def is_within_directory(directory, target):
          
          abs_directory = os.path.abspath(directory)
          abs_target = os.path.abspath(target)
      
          prefix = os.path.commonprefix([abs_directory, abs_target])
          
          return prefix == abs_directory
      
      def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
      
          for member in tar.getmembers():
              member_path = os.path.join(path, member.name)
              if not is_within_directory(path, member_path):
                  raise Exception("Attempted Path Traversal in Tar File")
      
          tar.extractall(path, members, numeric_owner=numeric_owner) 
          
      
      safe_extract(corpus_tar, directory)
    gunzip_file(train_path + ".fr.gz", train_path + ".fr")
    gunzip_file(train_path + ".en.gz", train_path + ".en")
  return train_path


def get_wmt_enfr_dev_set(directory):
  """Download the WMT en-fr training corpus to directory unless it's there."""
  dev_name = "newstest2013"
  dev_path = os.path.join(directory, dev_name)
  if not (gfile.Exists(dev_path + ".fr") and gfile.Exists(dev_path + ".en")):
    dev_file = maybe_download(directory, "dev-v2.tgz", _WMT_ENFR_DEV_URL)
    print("Extracting tgz file %s" % dev_file)
    with tarfile.open(dev_file, "r:gz") as dev_tar:
      fr_dev_file = dev_tar.getmember("dev/" + dev_name + ".fr")
      en_dev_file = dev_tar.getmember("dev/" + dev_name + ".en")
      fr_dev_file.name = dev_name + ".fr"  # Extract without "dev/" prefix.
      en_dev_file.name = dev_name + ".en"
      dev_tar.extract(fr_dev_file, directory)
      dev_tar.extract(en_dev_file, directory)
  return dev_path


def basic_tokenizer(sentence):
  """Very basic tokenizer: split the sentence into a list of tokens."""
  return sentence.strip().split()

  #words = []
  #for space_separated_fragment in sentence.strip().split():
  #  words.extend(_WORD_SPLIT.split(space_separated_fragment))
  #return [w for w in words if w]


def create_vocabulary(vocabulary_path, data_path, max_vocabulary_size,
                      tokenizer=None, normalize_digits=False):
  """Create vocabulary file (if it does not exist yet) from data file.
  Data file is assumed to contain one sentence per line. Each sentence is
  tokenized and digits are normalized (if normalize_digits is set).
  Vocabulary contains the most-frequent tokens up to max_vocabulary_size.
  We write it to vocabulary_path in a one-token-per-line format, so that later
  token in the first line gets id=0, second line gets id=1, and so on.
  Args:
    vocabulary_path: path where the vocabulary will be created.
    data_path: data file that will be used to create vocabulary.
    max_vocabulary_size: limit on the size of the created vocabulary.
    tokenizer: a function to use to tokenize each data sentence;
      if None, basic_tokenizer will be used.
    normalize_digits: Boolean; if true, all digits are replaced by 0s.
  """
  if True: # always create from scratch
    print("Creating vocabulary %s from data %s" % (vocabulary_path, data_path))
    vocab = {}
    with gfile.GFile(data_path, mode="rb") as f:
      counter = 0
      for line in f:
        counter += 1
        if counter % 100000 == 0:
          print("  processing line %d" % counter)
        line = tf.compat.as_bytes(line)
        tokens = tokenizer(line) if tokenizer else basic_tokenizer(line)
        for w in tokens:
          word = _DIGIT_RE.sub(b"0", w) if normalize_digits else w
          if word in vocab:
            vocab[word] += 1
          else:
            vocab[word] = 1
      vocab_list = _START_VOCAB + sorted(vocab, key=vocab.get, reverse=True)
      if len(vocab_list) > max_vocabulary_size:
        vocab_list = vocab_list[:max_vocabulary_size]
      with gfile.GFile(vocabulary_path, mode="wb") as vocab_file:
        for w in vocab_list:
          vocab_file.write(w + b"\n")


def initialize_vocabulary(vocabulary_path):
  """Initialize vocabulary from file.
  We assume the vocabulary is stored one-item-per-line, so a file:
    dog
    cat
  will result in a vocabulary {"dog": 0, "cat": 1}, and this function will
  also return the reversed-vocabulary ["dog", "cat"].
  Args:
    vocabulary_path: path to the file containing the vocabulary.
  Returns:
    a pair: the vocabulary (a dictionary mapping string to integers), and
    the reversed vocabulary (a list, which reverses the vocabulary mapping).
  Raises:
    ValueError: if the provided vocabulary_path does not exist.
  """
  if gfile.Exists(vocabulary_path):
    rev_vocab = []
    with gfile.GFile(vocabulary_path, mode="rb") as f:
      rev_vocab.extend(f.readlines())
    rev_vocab = [tf.compat.as_bytes(line.strip()) for line in rev_vocab]
    vocab = dict([(x, y) for (y, x) in enumerate(rev_vocab)])
    return vocab, rev_vocab
  else:
    raise ValueError("Vocabulary file %s not found.", vocabulary_path)


def sentence_to_token_ids(sentence, vocabulary,
                          tokenizer=None, normalize_digits=False):
  """Convert a string to list of integers representing token-ids.
  For example, a sentence "I have a dog" may become tokenized into
  ["I", "have", "a", "dog"] and with vocabulary {"I": 1, "have": 2,
  "a": 4, "dog": 7"} this function will return [1, 2, 4, 7].
  Args:
    sentence: the sentence in bytes format to convert to token-ids.
    vocabulary: a dictionary mapping tokens to integers.
    tokenizer: a function to use to tokenize each sentence;
      if None, basic_tokenizer will be used.
    normalize_digits: Boolean; if true, all digits are replaced by 0s.
  Returns:
    a list of integers, the token-ids for the sentence.
  """

  if tokenizer:
    words = tokenizer(sentence)
  else:
    words = basic_tokenizer(sentence)
  if not normalize_digits:
    return [vocabulary.get(w, UNK_ID) for w in words]
  # Normalize digits by 0 before looking words up in the vocabulary.
  return [vocabulary.get(_DIGIT_RE.sub(b"0", w), UNK_ID) for w in words]


def data_to_token_ids(data_path, target_path, vocabulary_path,
                      tokenizer=None, normalize_digits=False):
  """Tokenize data file and turn into token-ids using given vocabulary file.
  This function loads data line-by-line from data_path, calls the above
  sentence_to_token_ids, and saves the result to target_path. See comment
  for sentence_to_token_ids on the details of token-ids format.
  Args:
    data_path: path to the data file in one-sentence-per-line format.
    target_path: path where the file with token-ids will be created.
    vocabulary_path: path to the vocabulary file.
    tokenizer: a function to use to tokenize each sentence;
      if None, basic_tokenizer will be used.
    normalize_digits: Boolean; if true, all digits are replaced by 0s.
  """
  if True:
    print("Tokenizing data in %s" % data_path)
    vocab, _ = initialize_vocabulary(vocabulary_path)
    with gfile.GFile(data_path, mode="rb") as data_file:
      with gfile.GFile(target_path, mode="w") as tokens_file:
        counter = 0
        for line in data_file:
          counter += 1
          if counter % 100000 == 0:
            print("  tokenizing line %d" % counter)
          token_ids = sentence_to_token_ids(tf.compat.as_bytes(line), vocab,
                                            tokenizer, normalize_digits)
          tokens_file.write(" ".join([str(tok) for tok in token_ids]) + "\n")


def prepare_wmt_data(data_dir, en_vocabulary_size, fr_vocabulary_size, tokenizer=None):
  """Get WMT data into data_dir, create vocabularies and tokenize data.
  Args:
    data_dir: directory in which the data sets will be stored.
    en_vocabulary_size: size of the English vocabulary to create and use.
    fr_vocabulary_size: size of the French vocabulary to create and use.
    tokenizer: a function to use to tokenize each data sentence;
      if None, basic_tokenizer will be used.
  Returns:
    A tuple of 6 elements:
      (1) path to the token-ids for English training data-set,
      (2) path to the token-ids for French training data-set,
      (3) path to the token-ids for English development data-set,
      (4) path to the token-ids for French development data-set,
      (5) path to the English vocabulary file,
      (6) path to the French vocabulary file.
  """
  # Get wmt data to the specified directory.
  train_path = get_wmt_enfr_train_set(data_dir)
  dev_path = get_wmt_enfr_dev_set(data_dir)

  from_train_path = train_path + ".en"
  to_train_path = train_path + ".fr"
  from_dev_path = dev_path + ".en"
  to_dev_path = dev_path + ".fr"
  return prepare_data(data_dir, from_train_path, to_train_path, from_dev_path, to_dev_path, en_vocabulary_size,
                      fr_vocabulary_size, tokenizer)


def prepare_data(data_dir, from_train_path, to_train_path, from_dev_path, to_dev_path, from_vocabulary_size,
                 to_vocabulary_size, tokenizer=None, preprocess_data = True):
  """Preapre all necessary files that are required for the training.
    Args:
      data_dir: the folder to store the processed file
      from_train_path: path to the file that includes "from" training samples.
      to_train_path: path to the file that includes "to" training samples.
      from_dev_path: path to the file that includes "from" dev samples.
      to_dev_path: path to the file that includes "to" dev samples.
      from_vocabulary_size: size of the "from language" vocabulary to create and use.
      to_vocabulary_size: size of the "to language" vocabulary to create and use.
      tokenizer: a function to use to tokenize each data sentence;
        if None, basic_tokenizer will be used.
      preprocess_data: if False, only return the address. 
    Returns:
      A tuple of 6 elements:
        (1) path to the token-ids for "from language" training data-set,
        (2) path to the token-ids for "to language" training data-set,
        (3) path to the token-ids for "from language" development data-set,
        (4) path to the token-ids for "to language" development data-set,
        (5) path to the "from language" vocabulary file,
        (6) path to the "to language" vocabulary file.
    """
  # Create vocabularies of the appropriate sizes.

  to_vocab_path = os.path.join(data_dir, "vocab.to")
  from_vocab_path =  os.path.join(data_dir,"vocab.from")
  if preprocess_data:
    create_vocabulary(to_vocab_path, to_train_path , to_vocabulary_size, tokenizer)
    create_vocabulary(from_vocab_path, from_train_path , from_vocabulary_size, tokenizer)

  # Create token ids for the training data.
  to_train_ids_path = os.path.join(data_dir,"train.tgt.ids")
  from_train_ids_path = os.path.join(data_dir,"train.src.ids")
  if preprocess_data:
    data_to_token_ids(to_train_path, to_train_ids_path, to_vocab_path, tokenizer)
    data_to_token_ids(from_train_path, from_train_ids_path, from_vocab_path, tokenizer)

  # Create token ids for the development data.
  to_dev_ids_path = os.path.join(data_dir,"dev.tgt.ids")
  from_dev_ids_path = os.path.join(data_dir,"dev.src.ids")
  if preprocess_data:
    data_to_token_ids(to_dev_path, to_dev_ids_path, to_vocab_path, tokenizer)
    data_to_token_ids(from_dev_path, from_dev_ids_path, from_vocab_path, tokenizer)

  return (from_train_ids_path, to_train_ids_path,
          from_dev_ids_path, to_dev_ids_path,
          from_vocab_path, to_vocab_path)

def prepare_test_data(data_dir, from_test_path, from_vocab_path, tokenizer=None):
  
  from_test_ids_path = os.path.join(data_dir,"test.src.ids")
  data_to_token_ids(from_test_path, from_test_ids_path, from_vocab_path, tokenizer)

  return from_test_ids_path

def prepare_test_target_data(data_dir, to_test_path, to_vocab_path, tokenizer=None):
  to_test_ids_path = os.path.join(data_dir,"test.tgt.ids")
  data_to_token_ids(to_test_path, to_test_ids_path, to_vocab_path, tokenizer)
  return to_test_ids_path

def get_vocab_info(cache_dir):
    from_vocab_path = os.path.join(cache_dir, "vocab.from")
    to_vocab_path = os.path.join(cache_dir, "vocab.to")
    from_vocab_size = get_real_vocab_size(from_vocab_path)
    to_vocab_size = get_real_vocab_size(to_vocab_path)
    return from_vocab_path,to_vocab_path,from_vocab_size,to_vocab_size

def get_real_vocab_size(vocab_path):
    n = 0
    f = open(vocab_path)
    for line in f:
        n+=1
    f.close()
    return n

  
def load_index2word(vocab_path):
    f = open(vocab_path)
    d = {}
    i = 0
    for line in f:
        line = line.strip()
        d[i] = line
        i += 1
    f.close()
    return d

  
def load_word2index(vocab_path):
    f = open(vocab_path)
    d = {}
    i = 0
    for line in f:
        line = line.strip()
        d[line] = i
        i += 1
    f.close()
    return d


def id_to_tokens(line, to_vocab):
    # to_vocab: a list
    sent = " ".join(to_vocab[x] for x in line[:-1])
    return sent
  
  
def ids_to_tokens(lines, to_vocab_path, dest_path, ttable = None, test_source_orig_tok = None):
    # lines : [(sentences, score, attention_history)]

    unk_replace = False
    if ttable != None:
        unk_replace = True

  
    # load vocab 
    d = []
    f = open(to_vocab_path)
    for line in f:
        line = line.strip()
        d.append(line)
    f.close()

    f = open(dest_path,'w')
    sent_idx = 0
    
    for line in lines:
        if line == None: # empty sentence
            f.write("\n")
            continue

        words = []
        word_idxs, score, attention_history = line
        for i, word_idx in enumerate(word_idxs):
            if word_idx == 2: # _EOS
                continue
            
            if word_idx == 3: # _UNK
                target_word = "_UNK"
                if unk_replace:
                    attention_dist = attention_history[i]
                    attention_dist = attention_dist.reshape((-1))
                    attent_pos = np.argmax(attention_dist)
                    # NOTE: test_source_orig_tok is reversed
                    attent_source_word = test_source_orig_tok[sent_idx][attent_pos]

                    #print(i, word_idx)
                    #print(attention_dist)
                    #print(attent_pos)
                    #print(" ".join(test_source_orig_tok[sent_idx]))
                    #print(attent_source_word)
                    #if attent_source_word in ttable:
                    #    print("TTable:", ttable[attent_source_word])
                        
                    if attent_source_word in ttable:
                        target_word = ttable[attent_source_word][0]
                    else:
                        target_word = attent_source_word
                words.append(target_word)
                continue

            target_word = d[word_idx]
            words.append(target_word)
        
        sent = " ".join(words)
        f.write(sent+"\n")
        
        sent_idx += 1
        
    f.close()
    
# rare weights

def frequency(train_file):
    d = {}
    d[2] = 0 # for EOS
    f = open(train_file)
    for line in f:
        words = [int(x) for x in line.strip().split()]
        d[2] += 1
        for word in words:
            if word not in d:
                d[word] = 0
            d[word] += 1
    f.close()
    return d

def output_weight(train_file, weight_file):

    freq = frequency(train_file)
  
    f = open(weight_file,'w')

    s = sum(freq.values())
    indexs = sorted(freq)
    for i in indexs:
        weight = s*1.0 / freq[i] 
        f.write("{} {}\n".format(i,weight))

    f.close()


def check_rare_weights(target_outputs, vocab_weights, alpha, np_dtype = np.float32, log_weight = False, alpha_decay = 1.0, n_decay = 0):
    alpha = np.power(alpha_decay,n_decay) * alpha
    new_weights = np.zeros_like(target_outputs, dtype = np_dtype)
    #print(target_outputs)
    m,n = new_weights.shape
    for i in xrange(m):
        s = 0.0
        ns = 0
        for j in xrange(n):
            w = target_outputs[i][j]
            if w in vocab_weights:
                if log_weight: 
                    s+= np.power(np.log(vocab_weights[w]),alpha)
                else:
                    s+= np.power(vocab_weights[w],alpha)
                ns += 1
        for j in xrange(n):
            w = target_outputs[i][j]
            if w in vocab_weights:
                if log_weight:
                    new_weights[i,j] = np.power(np.log(vocab_weights[w]),alpha) / s * ns
                else:
                    new_weights[i,j] = np.power(vocab_weights[w],alpha) / s * ns
                
    new_weights = new_weights.tolist()
    #print(new_weights)
    return new_weights
                
def load_vocab_weights(weight_file):
    f = open(weight_file)
    d = {}
    for line in f:
        ll = line.split()
        index = int(ll[0])
        weight = float(ll[1])
        d[index] = weight
    f.close()
    return d

def load_data_orig_reverse(path):
    # load the original data, don't convert to ids
    d = []
    f = open(path)
    for line in f:
        words = line.split()[::-1]
        d.append(words)
    f.close()
    return d
