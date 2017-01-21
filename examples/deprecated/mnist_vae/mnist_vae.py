from collections import OrderedDict
import numpy as np
import theano

from dagbldr.datasets import fetch_binarized_mnist, minibatch_iterator
from dagbldr.optimizers import adam
from dagbldr.utils import add_datasets_to_graph, get_params_and_grads
from dagbldr.utils import TrainingLoop
from dagbldr.utils import create_or_continue_from_checkpoint_dict
from dagbldr.nodes import softplus_layer, linear_layer, sigmoid_layer
from dagbldr.nodes import gaussian_log_sample_layer, gaussian_log_kl
from dagbldr.nodes import binary_crossentropy


mnist = fetch_binarized_mnist()
train_indices = mnist["train_indices"]
train_end = len(train_indices)
valid_indices = mnist["valid_indices"]
X = mnist["data"]

# graph holds information necessary to build layers from parents
graph = OrderedDict()
X_sym = add_datasets_to_graph([X], ["X"], graph)
# random state so script is deterministic
random_state = np.random.RandomState(1999)

minibatch_size = 100
n_code = 100
n_enc_layer = [200, 200]
n_dec_layer = [200, 200]
width = 28
height = 28
n_input = width * height

# encode path aka q
l1_enc = softplus_layer([X_sym], graph, 'l1_enc', n_enc_layer[0], random_state=random_state)
l2_enc = softplus_layer([l1_enc], graph, 'l2_enc',  n_enc_layer[1],
                        random_state=random_state)
code_mu = linear_layer([l2_enc], graph, 'code_mu', n_code, random_state=random_state)
code_log_sigma = linear_layer([l2_enc], graph, 'code_log_sigma', n_code,
                              random_state=random_state)
kl = gaussian_log_kl([code_mu], [code_log_sigma], graph, 'kl').mean()
samp = gaussian_log_sample_layer([code_mu], [code_log_sigma], graph, 'samp',
                                 random_state)

# decode path aka p
l1_dec = softplus_layer([samp], graph, 'l1_dec',  n_dec_layer[0], random_state=random_state)
l2_dec = softplus_layer([l1_dec], graph, 'l2_dec', n_dec_layer[1], random_state=random_state)
out = sigmoid_layer([l2_dec], graph, 'out', n_input, random_state=random_state)

nll = binary_crossentropy(out, X_sym).mean()
# log p(x) = -nll so swap sign
# want to minimize cost in optimization so multiply by -1
cost = -1 * (-nll - kl)
params, grads = get_params_and_grads(graph, cost)

learning_rate = 0.0003
opt = adam(params, learning_rate)
updates = opt.updates(params, grads)

fit_function = theano.function([X_sym], [nll, kl, nll + kl], updates=updates)
cost_function = theano.function([X_sym], [nll + kl])
encode_function = theano.function([X_sym], [code_mu, code_log_sigma])
decode_function = theano.function([samp], [out])

checkpoint_dict = create_or_continue_from_checkpoint_dict(locals())

train_itr = minibatch_iterator([X], minibatch_size, stop_index=train_end, axis=0)
valid_itr = minibatch_iterator([X], minibatch_size, start_index=train_end, axis=0)

TL = TrainingLoop(
    fit_function, cost_function,
    train_itr, valid_itr,
    checkpoint_dict=checkpoint_dict,
    list_of_train_output_names=["nll", "kl", "lower_bound"],
    valid_output_name="valid_lower_bound",
    n_epochs=2000)
epoch_results = TL.run()
