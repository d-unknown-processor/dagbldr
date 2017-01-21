'''
import numpy as np
import theano

from theano.compat.python2x import OrderedDict
from dagbldr.datasets import load_mountains, minibatch_iterator
from dagbldr.optimizers import sgd
from dagbldr.utils import TrainingLoop
from dagbldr.utils import add_datasets_to_graph, get_params_and_grads
from dagbldr.utils import make_character_level_from_text
from dagbldr.utils import gen_make_list_one_hot_minibatch
from dagbldr.nodes import masked_cost, categorical_crossentropy
from dagbldr.nodes import softmax_layer, shift_layer
from dagbldr.nodes import gru_recurrent_layer, conditional_gru_recurrent_layer
from dagbldr.nodes import bidirectional_gru_recurrent_layer
from dagbldr.nodes import content_attention_gru_recurrent_layer


# minibatch size
minibatch_size = 10

# Get data for lovecraft experiments
mountains = load_mountains()
text = mountains["data"]
# Get a tiny subset
text = text[:10]
cleaned, mfunc, inv_mfunc, mapper = make_character_level_from_text(text)
n_chars = len(mapper.keys())

# Necessary setup since text is done on per minibatch basis
text_minibatch_func = gen_make_list_one_hot_minibatch(n_chars)
X = [l[:3] for l in cleaned]
y = [l[3:5] for l in cleaned]
X_mb, X_mb_mask = text_minibatch_func(X, slice(0, minibatch_size))
y_mb, y_mb_mask = text_minibatch_func(y, slice(0, minibatch_size))


def test_conditional_gru_recurrent():
    random_state = np.random.RandomState(1999)
    graph = OrderedDict()
    n_hid = 5
    n_out = n_chars

    # input (where first dimension is time)
    datasets_list = [X_mb, X_mb_mask, y_mb, y_mb_mask]
    names_list = ["X", "X_mask", "y", "y_mask"]
    X_sym, X_mask_sym, y_sym, y_mask_sym = add_datasets_to_graph(
        datasets_list, names_list, graph)

    h = gru_recurrent_layer([X_sym], X_mask_sym, n_hid, graph, 'l1_end',
                            random_state)

    shifted_y_sym = shift_layer([y_sym], graph, 'shift')

    h_dec, context = conditional_gru_recurrent_layer([y_sym], [h], y_mask_sym,
                                                     n_hid, graph, 'l2_dec',
                                                     random_state)

    # linear output activation
    y_hat = softmax_layer([h_dec, context, shifted_y_sym], graph, 'l2_proj',
                          n_out, random_state=random_state)

    # error between output and target
    cost = categorical_crossentropy(y_hat, y_sym)
    cost = masked_cost(cost, y_mask_sym).mean()
    # Parameters of the model
    """
    params, grads = get_params_and_grads(graph, cost)

    # Use stochastic gradient descent to optimize
    opt = sgd(params)
    learning_rate = 0.00000
    updates = opt.updates(params, grads, learning_rate)


    fit_function = theano.function([X_sym, X_mask_sym, y_sym, y_mask_sym],
                                   [cost], updates=updates,
                                   mode="FAST_COMPILE")
    """

    cost_function = theano.function([X_sym, X_mask_sym, y_sym, y_mask_sym],
                                    [cost], mode="FAST_COMPILE")

    checkpoint_dict = {}
    train_itr = minibatch_iterator([X_mb, X_mb_mask, y_mb, y_mb_mask],
                                   minibatch_size, axis=1)
    valid_itr = minibatch_iterator([X_mb, X_mb_mask, y_mb, y_mb_mask],
                                   minibatch_size, axis=1)
    TL = TrainingLoop(cost_function, cost_function,
                      train_itr, valid_itr,
                      checkpoint_dict=checkpoint_dict,
                      list_of_train_output_names=["cost"],
                      valid_output_name="valid_cost",
                      n_epochs=1)
    TL.run()


def test_conditional_attention_gru_recurrent():
    random_state = np.random.RandomState(1999)
    graph = OrderedDict()
    n_hid = 5
    n_out = n_chars

    # input (where first dimension is time)
    datasets_list = [X_mb, X_mb_mask, y_mb, y_mb_mask]
    names_list = ["X", "X_mask", "y", "y_mask"]
    X_sym, X_mask_sym, y_sym, y_mask_sym = add_datasets_to_graph(
        datasets_list, names_list, graph)

    h = bidirectional_gru_recurrent_layer([X_sym], X_mask_sym, n_hid, graph,
                                          'l1_end', random_state)

    shifted_y_sym = shift_layer([y_sym], graph, 'shift')

    h_dec, context, attention = content_attention_gru_recurrent_layer(
        [y_sym], [h], y_mask_sym, X_mask_sym, n_hid, graph, 'l2_dec',
        random_state)

    # linear output activation
    y_hat = softmax_layer([h_dec, context, shifted_y_sym], graph, 'l2_proj',
                          n_out, random_state=random_state)

    # error between output and target
    cost = categorical_crossentropy(y_hat, y_sym)
    cost = masked_cost(cost, y_mask_sym).mean()
    # Parameters of the model
    """
    params, grads = get_params_and_grads(graph, cost)

    # Use stochastic gradient descent to optimize
    opt = sgd(params)
    learning_rate = 0.00000
    updates = opt.updates(params, grads, learning_rate)

    fit_function = theano.function([X_sym, X_mask_sym, y_sym, y_mask_sym],
                                   [cost], updates=updates,
                                   mode="FAST_COMPILE")
    """

    cost_function = theano.function([X_sym, X_mask_sym, y_sym, y_mask_sym],
                                    [cost], mode="FAST_COMPILE")

    checkpoint_dict = {}
    train_itr = minibatch_iterator([X_mb, X_mb_mask, y_mb, y_mb_mask],
                                   minibatch_size, axis=1)
    valid_itr = minibatch_iterator([X_mb, X_mb_mask, y_mb, y_mb_mask],
                                   minibatch_size, axis=1)
    TL = TrainingLoop(cost_function, cost_function,
                      train_itr, valid_itr,
                      checkpoint_dict=checkpoint_dict,
                      list_of_train_output_names=["cost"],
                      valid_output_name="valid_cost",
                      n_epochs=1)
    TL.run()
'''
