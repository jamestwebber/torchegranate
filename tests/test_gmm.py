# test_bayes_classifier.py
# Contact: Jacob Schreiber <jmschreiber91@gmail.com>

import numpy
import torch
import pytest

from torchegranate.gmm import GeneralMixtureModel
from torchegranate.distributions import Exponential

from .distributions._utils import _test_initialization_raises_one_parameter
from .distributions._utils import _test_initialization
from .distributions._utils import _test_predictions
from .distributions._utils import _test_efd_from_summaries
from .distributions._utils import _test_raises

from nose.tools import assert_raises
from numpy.testing import assert_array_almost_equal


MIN_VALUE = 0
MAX_VALUE = None
VALID_VALUE = 1.2


@pytest.fixture
def X():
	return [[1, 2, 0],
	     [0, 0, 1],
	     [1, 1, 2],
	     [2, 2, 2],
	     [3, 1, 0],
	     [5, 1, 4],
	     [2, 1, 0],
	     [1, 0, 2],
	     [1, 1, 0],
	     [0, 2, 1],
	     [0, 0, 0]]


@pytest.fixture
def w():
	return [[1], [2], [0], [0], [5], [1], [2], [1], [1], [2], [0]]


@pytest.fixture
def model():
	d = [Exponential([2.1, 0.3, 0.1]), Exponential([1.5, 3.1, 2.2])]
	return GeneralMixtureModel(d, priors=[0.7, 0.3])


###


def test_initialization():
	d = [Exponential(), Exponential()]
	model = GeneralMixtureModel(d)

	_test_initialization(model, None, "priors", 0.0, False, None)
	assert_raises(AttributeError, getattr, model, "_w_sum")
	assert_raises(AttributeError, getattr, model, "_log_priors")


def test_initialization_raises():
	d = [Exponential(), Exponential()]

	assert_raises(TypeError, GeneralMixtureModel)
	assert_raises(ValueError, GeneralMixtureModel, d, [0.2, 0.2, 0.6])
	assert_raises(ValueError, GeneralMixtureModel, d, [0.2, 1.0])
	assert_raises(ValueError, GeneralMixtureModel, d, [-0.2, 1.2])

	assert_raises(ValueError, GeneralMixtureModel, Exponential)
	assert_raises(ValueError, GeneralMixtureModel, d, inertia=-0.4)
	assert_raises(ValueError, GeneralMixtureModel, d, inertia=1.2)
	assert_raises(ValueError, GeneralMixtureModel, d, inertia=1.2, frozen="true")
	assert_raises(ValueError, GeneralMixtureModel, d, inertia=1.2, frozen=3)
	

def test_reset_cache(model, X):
	model.summarize(X)
	
	assert_array_almost_equal(model._w_sum, [4.443249, 6.556751])
	assert_array_almost_equal(model._log_priors, [-0.356675, -1.203973])

	model._reset_cache()
	assert_array_almost_equal(model._w_sum, [0.0, 0.0])
	assert_array_almost_equal(model._log_priors, [-0.356675, -1.203973])	


def test_initialize(X):
	d = [Exponential(), Exponential()]
	model = GeneralMixtureModel(d)

	assert model.d is None
	assert model.m == 2
	assert model._initialized == False
	assert_raises(AttributeError, getattr, model, "_w_sum")
	assert_raises(AttributeError, getattr, model, "_log_priors")

	model._initialize(3)
	assert model._initialized == True
	assert model.priors.shape[0] == 2
	assert model.d == 3
	assert model.m == 2
	assert_array_almost_equal(model.priors, [0.5, 0.5])
	assert_array_almost_equal(model._w_sum, [0.0, 0.0])

	model._initialize(2)
	assert model._initialized == True
	assert model.priors.shape[0] == 2
	assert model.d == 2
	assert model.m == 2
	assert_array_almost_equal(model.priors, [0.5, 0.5])
	assert_array_almost_equal(model._w_sum, [0.0, 0.0])

	d = [Exponential([0.4, 2.1]), Exponential([3, 1]), Exponential([0.2, 1])]
	model = GeneralMixtureModel(d)
	assert model._initialized == True
	assert model.d == 2
	assert model.m == 3

	model._initialize(3)
	assert model._initialized == True
	assert model.priors.shape[0] == 3
	assert model.d == 3
	assert model.m == 3
	assert_array_almost_equal(model.priors, [1./3, 1./3, 1./3])
	assert_array_almost_equal(model._w_sum, [0.0, 0.0, 0.0])



###


def test_emission_matrix(model, X):
	e = model._emission_matrix(X)

	assert_array_almost_equal(e, 
		[[ -4.7349,  -4.8411],
         [ -7.5921,  -3.9838],
         [-21.4016,  -5.4276],
         [-25.2111,  -6.4169],
         [ -2.3540,  -5.8519],
         [-43.3063,  -9.0034],
         [ -1.8778,  -5.1852],
         [-18.0682,  -5.1051],
         [ -1.4016,  -4.5185],
         [-14.2587,  -4.6290],
         [  2.4079,  -3.5293]], 4)
	assert_array_almost_equal(e[:, 0], model.distributions[0].log_probability(X) 
		- 0.3567, 4)
	assert_array_almost_equal(e[:, 1], model.distributions[1].log_probability(X) 
		- 1.2040, 4)


def test_emission_matrix_raises(model, X):
	_test_raises(model, "_emission_matrix", X, min_value=MIN_VALUE)

	d = [Exponential(), Exponential()]
	model = GeneralMixtureModel(d)
	_test_raises(model, "_emission_matrix", X, min_value=MIN_VALUE)


def test_log_probability(model, X):
	logp = model.log_probability(X)
	assert_array_almost_equal(logp, [-4.0935, -3.9571, -5.4276, -6.4169, 
		-2.3241, -9.0034, -1.8418, -5.1051, -1.3582, -4.6289,  2.4106], 4)


def test_log_probability_raises(model, X):
	_test_raises(model, "log_probability", X, min_value=MIN_VALUE)

	d = [Exponential(), Exponential()]
	model = GeneralMixtureModel(d)
	_test_raises(model, "log_probability", X, min_value=MIN_VALUE)


def test_predict(model, X):
	y_hat = model.predict(X)
	assert_array_almost_equal(y_hat, [0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0], 4)


def test_predict_raises(model, X):
	_test_raises(model, "predict", X, min_value=MIN_VALUE)

	d = [Exponential(), Exponential()]
	model = GeneralMixtureModel(d)
	_test_raises(model, "predict", X, min_value=MIN_VALUE)


def test_predict_proba(model, X):
	y_hat = model.predict_proba(X)
	assert_array_almost_equal(y_hat,
		[[5.2653e-01, 4.7347e-01],
         [2.6385e-02, 9.7361e-01],
         [1.1551e-07, 1.0000e+00],
         [6.8830e-09, 1.0000e+00],
         [9.7063e-01, 2.9372e-02],
         [1.2660e-15, 1.0000e+00],
         [9.6468e-01, 3.5317e-02],
         [2.3451e-06, 1.0000e+00],
         [9.5759e-01, 4.2413e-02],
         [6.5741e-05, 9.9993e-01],
         [9.9737e-01, 2.6323e-03]], 4)

	model2 = GeneralMixtureModel(model.distributions)
	y_hat2 = model2.predict_proba(X)
	assert_array_almost_equal(y_hat2,
		[[3.2277e-01, 6.7723e-01],
         [1.1481e-02, 9.8852e-01],
         [4.9503e-08, 1.0000e+00],
         [2.9498e-09, 1.0000e+00],
         [9.3405e-01, 6.5951e-02],
         [5.4255e-16, 1.0000e+00],
         [9.2130e-01, 7.8700e-02],
         [1.0050e-06, 1.0000e+00],
         [9.0633e-01, 9.3666e-02],
         [2.8176e-05, 9.9997e-01],
         [9.9388e-01, 6.1207e-03]], 4)	


def test_predict_proba_raises(model, X):
	_test_raises(model, "predict_proba", X, min_value=MIN_VALUE)

	d = [Exponential(), Exponential()]
	model = GeneralMixtureModel(d)
	_test_raises(model, "predict_proba", X, min_value=MIN_VALUE)


def test_predict_log_proba(model, X):
	y_hat = model.predict_log_proba(X)
	assert_array_almost_equal(y_hat,
		[[-6.4145e-01, -7.4766e-01],
         [-3.6350e+00, -2.6740e-02],
         [-1.5974e+01,  0.0000e+00],
         [-1.8794e+01,  0.0000e+00],
         [-2.9812e-02, -3.5277e+00],
         [-3.4303e+01,  0.0000e+00],
         [-3.5955e-02, -3.3434e+00],
         [-1.2963e+01, -2.3842e-06],
         [-4.3338e-02, -3.1603e+00],
         [-9.6298e+00, -6.5804e-05],
         [-2.6357e-03, -5.9399e+00]], 3)

	model2 = GeneralMixtureModel(model.distributions)
	y_hat2 = model2.predict_log_proba(X)
	assert_array_almost_equal(y_hat2,
		[[-1.1308e+00, -3.8974e-01],
         [-4.4671e+00, -1.1548e-02],
         [-1.6821e+01,  0.0000e+00],
         [-1.9642e+01,  0.0000e+00],
         [-6.8226e-02, -2.7188e+00],
         [-3.5150e+01,  0.0000e+00],
         [-8.1969e-02, -2.5421e+00],
         [-1.3810e+01, -9.5367e-07],
         [-9.8348e-02, -2.3680e+00],
         [-1.0477e+01, -2.8133e-05],
         [-6.1395e-03, -5.0961e+00]], 3)	


def test_predict_log_proba_raises(model, X):
	_test_raises(model, "predict_log_proba", X, min_value=MIN_VALUE)

	d = [Exponential(), Exponential()]
	model = GeneralMixtureModel(d)
	_test_raises(model, "predict_log_proba", X, min_value=MIN_VALUE)

###


def test_partial_summarize(model, X):
	model.summarize(X[:4])
	assert_array_almost_equal(model._w_sum, [0.552914, 3.447086])

	model.summarize(X[4:])
	assert_array_almost_equal(model._w_sum, [4.443249, 6.556751])


def test_full_summarize(model, X):
	model.summarize(X)
	assert_array_almost_equal(model._w_sum, [4.443249, 6.556751])


def test_summarize_weighted(model, X, w):
	model.summarize(X, sample_weight=w)
	assert_array_almost_equal(model._w_sum, [8.319529, 6.68047])


def test_summarize_weighted_flat(model, X, w):
	w = numpy.array(w)[:,0] 

	model.summarize(X, sample_weight=w)
	assert_array_almost_equal(model._w_sum, [8.319529, 6.68047])


def test_summarize_weighted_2d(model, X):
	model.summarize(X, sample_weight=X)
	assert_array_almost_equal(model._w_sum, [3.432638, 9.567362])


def test_summarize_raises(model, X, w):
	assert_raises(ValueError, model.summarize, [X])
	assert_raises(ValueError, model.summarize, X[0])
	assert_raises((ValueError, TypeError), model.summarize, X[0][0])
	assert_raises(ValueError, model.summarize, [x[:-1] for x in X])
	assert_raises(ValueError, model.summarize, 
		[[-0.1 for i in range(3)] for x in X])

	assert_raises(ValueError, model.summarize, [X], w)
	assert_raises(ValueError, model.summarize, X, [w])
	assert_raises(ValueError, model.summarize, [X], [w])
	assert_raises(ValueError, model.summarize, X[:len(X)-1], w)
	assert_raises(ValueError, model.summarize, X, w[:len(w)-1])


def test_from_summaries(model, X):
	model.summarize(X)
	model.from_summaries()

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.403932, 0.596068])
	assert_array_almost_equal(model._log_priors, 
		numpy.log([0.403932, 0.596068]))


def test_from_summaries_weighted(model, X, w):
	model.summarize(X, sample_weight=w)
	model.from_summaries()

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.554635, 0.445365])
	assert_array_almost_equal(model._log_priors, 
		numpy.log([0.554635, 0.445365]))


def test_from_summaries_null(model):
	model.from_summaries()

	assert model.distributions[0].scales[0] != 2.1 
	assert model.distributions[1].scales[0] != 1.5

	assert_array_almost_equal(model._w_sum, [0., 0.])


def test_from_summaries_inertia(X):
	d = [Exponential([2.1, 0.3, 0.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, priors=[0.2, 0.8], inertia=0.3)
	model.summarize(X)
	model.from_summaries()

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.271142, 0.728858])
	assert_array_almost_equal(model._log_priors, 
		numpy.log([0.271142, 0.728858]))


	d = [Exponential([2.1, 0.3, 0.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, priors=[0.2, 0.8], inertia=1.0)
	model.summarize(X)
	model.from_summaries()

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.2, 0.8])
	assert_array_almost_equal(model._log_priors, numpy.log([0.2, 0.8]))


	s1, s2 = [2.1, 0.3, 0.1], [1.5, 3.1, 2.2] 
	d = [Exponential(s1, inertia=1.0), Exponential(s2, inertia=1.0)]
	model = GeneralMixtureModel(d, priors=[0.2, 0.8])
	model.summarize(X)
	model.from_summaries()

	assert_array_almost_equal(model.distributions[0].scales, s1)
	assert_array_almost_equal(model.distributions[1].scales, s2)

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.301631, 0.698369])
	assert_array_almost_equal(model._log_priors, 
		numpy.log([0.301631, 0.698369]))


	d = [Exponential(s1, inertia=1.0), Exponential(s2)]
	model = GeneralMixtureModel(d, priors=[0.2, 0.8], inertia=1.0)
	model.summarize(X)
	model.from_summaries()

	assert_array_almost_equal(model.distributions[0].scales, s1)
	assert_array_almost_equal(model.distributions[1].scales, 
		[1.478256, 1.113561, 1.561704])

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.2, 0.8])
	assert_array_almost_equal(model._log_priors, numpy.log([0.2, 0.8]))


def test_from_summaries_weighted_inertia(X, w):
	d = [Exponential([2.1, 0.3, 0.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, priors=[0.2, 0.8], inertia=0.3)
	model.summarize(X, sample_weight=w)
	model.from_summaries()

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.349767, 0.650233])
	assert_array_almost_equal(model._log_priors, 
		numpy.log([0.349767, 0.650233]))


	d = [Exponential([2.1, 0.3, 0.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, priors=[0.2, 0.8], inertia=1.0)
	model.summarize(X, sample_weight=w)
	model.from_summaries()

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.2, 0.8])
	assert_array_almost_equal(model._log_priors, numpy.log([0.2, 0.8]))


def test_from_summaries_frozen(model, X):
	d = [Exponential([2.1, 0.3, 0.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, priors=[0.2, 0.8], frozen=True)
	model.summarize(X)
	model.from_summaries()

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.2, 0.8])
	assert_array_almost_equal(model._log_priors, numpy.log([0.2, 0.8]))


	s1, s2 = [2.1, 0.3, 0.1], [1.5, 3.1, 2.2] 
	d = [Exponential(s1, frozen=True), Exponential(s2, frozen=True)]
	model = GeneralMixtureModel(d, priors=[0.2, 0.8])
	model.summarize(X)
	model.from_summaries()

	assert_array_almost_equal(model.distributions[0].scales, s1)
	assert_array_almost_equal(model.distributions[1].scales, s2)

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.301631, 0.698369])
	assert_array_almost_equal(model._log_priors, 
		numpy.log([0.301631, 0.698369]))


	d = [Exponential(s1, frozen=True), Exponential(s2)]
	model = GeneralMixtureModel(d, priors=[0.2, 0.8], frozen=True)
	model.summarize(X)
	model.from_summaries()

	assert_array_almost_equal(model.distributions[0].scales, s1)
	assert_array_almost_equal(model.distributions[1].scales, 
		[1.478256, 1.113561, 1.561704])

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.2, 0.8])
	assert_array_almost_equal(model._log_priors, numpy.log([0.2, 0.8]))


def test_fit(X):
	d = [Exponential([2.1, 0.3, 1.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, max_iter=1)
	model.fit(X)

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.44044, 0.55956])
	assert_array_almost_equal(model._log_priors, numpy.log([0.44044, 0.55956]))


	d = [Exponential([2.1, 0.3, 1.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, max_iter=5)
	model.fit(X)

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.378347, 0.621653])
	assert_array_almost_equal(model._log_priors, 
		numpy.log([0.378347, 0.621653]))


def test_fit_weighted(X, w):
	d = [Exponential([2.1, 0.3, 1.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, max_iter=1)
	model.fit(X, sample_weight=w)

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.487912, 0.512088])
	assert_array_almost_equal(model._log_priors, 
		numpy.log([0.487912, 0.512088]))


	d = [Exponential([2.1, 0.3, 1.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, max_iter=5)
	model.fit(X, sample_weight=w)

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.511616, 0.488384])
	assert_array_almost_equal(model._log_priors, 
		numpy.log([0.511616, 0.488384]))


def test_fit_chain(X):
	d = [Exponential([2.1, 0.3, 1.1]), Exponential([1.5, 3.1, 2.2])]
	model = GeneralMixtureModel(d, max_iter=1).fit(X)

	assert_array_almost_equal(model._w_sum, [0., 0.])
	assert_array_almost_equal(model.priors, [0.44044, 0.55956])
	assert_array_almost_equal(model._log_priors, numpy.log([0.44044, 0.55956]))


def test_fit_raises(model, X, w):
	assert_raises(ValueError, model.fit, [X])
	assert_raises(ValueError, model.fit, X[0])
	assert_raises((ValueError, TypeError), model.fit, X[0][0])
	assert_raises(ValueError, model.fit, [x[:-1] for x in X])
	assert_raises(ValueError, model.fit, 
		[[-0.1 for i in range(3)] for x in X])

	assert_raises(ValueError, model.fit, [X], w)
	assert_raises(ValueError, model.fit, X, [w])
	assert_raises(ValueError, model.fit, [X], [w])
	assert_raises(ValueError, model.fit, X[:len(X)-1], w)
	assert_raises(ValueError, model.fit, X, w[:len(w)-1])
