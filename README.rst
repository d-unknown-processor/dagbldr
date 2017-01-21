dagbldr
-------
A small helper library for building directed acyclic graphs in Theano


What
----
Easy prototyping of out-of-core recurrent models with conditional structures,
simple monitoring via html plots, many wrapped examples and tests,
and a focus on node/function based code instead
of an object-oriented approach. 

One other goal is to make sharing experiment code easy - the entire
library is serialized during training, and tries to
have absolute minimal dependencies besides numpy, scipy, and Theano.
Eventually I would like to save a single file which has all the codepaths
used in an experiment.

Philosophically, there is similarity to Lasagne (another great neural network library)
but written with my own research goals in mind.


WARNING
-------
If you use this library, I will likely break your code. Someday I hope to have enough examples, tests,
and experiments to have the API solid, but for now consider this "bleeding edge" type development.


Install
-------
The typical install involves setting up a scientific Python environment using
your preferred approach (I like Continuum Analytics Anaconda personally), plus
the latest version of Theano.

Once this is done, clone this repo and run


``python setup.py develop``


Try running tests and examples to be sure install worked correctly.
