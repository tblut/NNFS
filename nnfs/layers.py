import numpy as np
from nnfs.initializers import zeros, he_normal


class Parameter:
    def __init__(self, initial_value):
        self.shape = initial_value.shape
        self.value = initial_value
        self.grad = np.zeros(initial_value.shape)


class Layer:
    def get_parameters(self):
        return []

    def get_loss(self):
        return 0.0


class Linear(Layer):
    def __init__(self, n_inputs, n_neurons,
                 weights_inititalizer=he_normal,
                 bias_initializer=zeros,
                 weights_regularizer=None,
                 bias_regularizer=None):
        self.weights = Parameter(weights_inititalizer(n_inputs, n_neurons))
        self.biases = Parameter(bias_initializer(1, n_neurons))
        self.weights_regularizer = weights_regularizer
        self.bias_regularizer = bias_regularizer

    def forward(self, inputs):
        self._cached_inputs = inputs
        return np.dot(inputs, self.weights.value) + self.biases.value

    def backward(self, grad_out):
        grad_in = np.dot(grad_out, self.weights.value.T)
        self.weights.grad = np.dot(self._cached_inputs.T, grad_out)
        if self.weights_regularizer:
            self.weights.grad += self.weights_regularizer.get_grad(self.weights.value)
        self.biases.grad = np.sum(grad_out, axis=0)
        if self.bias_regularizer:
            self.biases.grad += self.bias_regularizer.get_grad(self.biases.value)
        return grad_in

    def get_parameters(self):
        return [self.weights, self.biases]

    def get_loss(self):
        loss = 0.0
        if self.weights_regularizer:
            loss += self.weights_regularizer(self.weights.value)
        if self.bias_regularizer:
            loss += self.bias_regularizer(self.biases.value)
        return loss


class Sigmoid(Layer):
    def forward(self, inputs):
        self._cached_inputs = inputs
        return 1.0 / (1.0 + np.exp(-inputs))

    def backward(self, grad_out):
        sig = 1.0 / (1.0 + np.exp(-self._cached_inputs))
        return grad_out * sig * (1.0 - sig)


class ReLU(Layer):
    def forward(self, inputs):
        self._cached_inputs = inputs
        return np.maximum(0.0, inputs)

    def backward(self, grad_out):
        grad_in = np.where(self._cached_inputs < 0.0, 0.0, 1.0)
        return grad_out * grad_in


class Softmax(Layer):
    def forward(self, inputs):
        maxs = np.max(inputs, axis=1).reshape((-1, 1))
        exps = np.exp(inputs - maxs)
        self._cached_outputs = exps / np.sum(exps, axis=1).reshape((-1, 1))
        return self._cached_outputs

    def backward(self, grad_out):
        a = np.empty((grad_out.shape[0], 1))
        for i in range(a.shape[0]):
            a[i, :] = np.dot(grad_out[i, :], self._cached_outputs[i, :])
        return self._cached_outputs * (grad_out - a)
