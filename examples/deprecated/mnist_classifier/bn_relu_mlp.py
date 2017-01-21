from collections import OrderedDict
import numpy as np
import theano
from theano import tensor

from dagbldr.datasets import fetch_mnist, minibatch_iterator
from dagbldr.optimizers import sgd_nesterov
from dagbldr.utils import add_datasets_to_graph, get_params_and_grads
from dagbldr.utils import get_weights_from_graph
from dagbldr.utils import convert_to_one_hot
from dagbldr.utils import create_checkpoint_dict
from dagbldr.utils import TrainingLoop
from dagbldr.nodes import relu_layer, softmax_zeros_layer
from dagbldr.nodes import categorical_crossentropy


mnist = fetch_mnist()
train_indices = mnist["train_indices"]
valid_indices = mnist["valid_indices"]
X = mnist["data"]
y = mnist["target"]
n_targets = 10
y = convert_to_one_hot(y, n_targets)

# graph holds information necessary to build layers from parents
graph = OrderedDict()
X_sym, y_sym = add_datasets_to_graph([X, y], ["X", "y"], graph,
                                     list_of_test_values=[X[:10], y[:10]])
# random state so script is deterministic
random_state = np.random.RandomState(1999)

minibatch_size = 128
n_hid = 1000

on_off = tensor.iscalar()
on_off.tag.test_value = 0
l1 = relu_layer([X_sym], graph, 'l1', proj_dim=n_hid,
                batch_normalize=True, mode_switch=on_off,
                random_state=random_state)
y_pred = softmax_zeros_layer([l1], graph, 'y_pred',  proj_dim=n_targets)
nll = categorical_crossentropy(y_pred, y_sym).mean()
weights = get_weights_from_graph(graph)
L2 = sum([(w ** 2).sum() for w in weights])
cost = nll + .0001 * L2


params, grads = get_params_and_grads(graph, cost)

learning_rate = 0.1
momentum = 0.9
opt = sgd_nesterov(params, learning_rate, momentum)
updates = opt.updates(params, grads)

fit_function = theano.function([X_sym, y_sym, on_off], [cost], updates=updates)
cost_function = theano.function([X_sym, y_sym, on_off], [cost])
predict_function = theano.function([X_sym, on_off], [y_pred])

checkpoint_dict = create_checkpoint_dict(locals())


def error(*args):
    xargs = args[:-1]
    y = args[-1]
    final_args = xargs + (1,)
    y_pred = predict_function(*final_args)[0]
    return 1 - np.mean((np.argmax(
        y_pred, axis=1).ravel()) == (np.argmax(y, axis=1).ravel()))


def bn_fit_function(X, y):
    return fit_function(X, y, 0)


def bn_cost_function(X, y):
    return cost_function(X, y, 0)


train_itr = minibatch_iterator([X, y], minibatch_size, axis=0, stop_index=60000)
valid_itr = minibatch_iterator([X, y], minibatch_size, axis=0,
                               start_index=60000)

TL = TrainingLoop(bn_fit_function, bn_cost_function,
                  train_itr, valid_itr,
                  checkpoint_dict=checkpoint_dict,
                  list_of_train_output_names=["train_cost"],
                  valid_output_name="valid_cost",
                  n_epochs=1000,
                  optimizer_object=opt)
epoch_results = TL.run()
