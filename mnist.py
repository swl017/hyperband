#!/usr/bin/env python

"""
    mnist.py
"""

import json
import numpy as np
from hashlib import md5

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense
from keras.callbacks import EarlyStopping

from sklearn.model_selection import train_test_split

from keras import backend as K
def limit_mem():
    cfg = K.tf.ConfigProto()
    cfg.gpu_options.allow_growth = True
    cfg.gpu_options.visible_device_list="0"
    K.set_session(K.tf.Session(config=cfg))

limit_mem()

class MNISTModel:
    
    def __init__(self):
        (X_train, y_train), (X_test, y_test) = mnist.load_data()
        X_train = X_train.reshape(X_train.shape[0], 28, 28, 1)
        X_test = X_test.reshape(X_test.shape[0], 28, 28, 1)
        X_train = X_train.astype('float32')
        X_test = X_test.astype('float32')
        X_train /= 255
        X_test /= 255
        
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, train_size=0.8, random_state=123)
        
        self.X_train, self.y_train = X_train, y_train
        self.X_val, self.y_val = X_val, y_val
        self.X_test, self.y_test = X_test, y_test
        
        self.input_shape = self.X_train.shape[1:]
        self.n_classes = self.y_train.max() + 1
    
    def rand_config(self):
        return {
            'n_layers'   : np.random.choice([1, 2, 3, 4, 5]),
            'init'       : np.random.choice(['uniform', 'normal', 'glorot_uniform', 'glorot_normal', 'he_uniform', 'he_normal']),
            'batch_size' : np.random.choice([16, 32, 64, 128, 256]),
            'optimizer'  : np.random.choice(['rmsprop', 'adagrad', 'adadelta', 'adam']),
            
            'n_filters_0'   : np.random.choice([8, 16, 32, 64]),
            'kernel_size_0' : np.random.choice([2, 3, 4]),
            'n_filters_1'   : np.random.choice([8, 16, 32, 64]),
            'kernel_size_1' : np.random.choice([2, 3, 4]),
            'pool_size'     : np.random.choice([2, 3, 4]),
            'dropout_0'     : np.random.choice([0.125, 0.25, 0.5]),
            'dense_0'       : np.random.choice([64, 128, 256, 512]),
            'dropout_1'     : np.random.choice([0.125, 0.25, 0.5]),
        }
    
    def _make_model(self, config):
        model = Sequential()
        model.add(Conv2D(config['n_filters_0'], kernel_size=(config['kernel_size_0'], config['kernel_size_0']), 
            activation='relu', input_shape=self.input_shape))
        model.add(Conv2D(config['n_filters_1'], kernel_size=(config['kernel_size_1'], config['kernel_size_1']), 
            activation='relu'))
        model.add(MaxPooling2D(pool_size=(config['pool_size'], config['pool_size'])))
        model.add(Dropout(config['dropout_0']))
        model.add(Flatten())
        model.add(Dense(config['dense_0'], activation='relu'))
        model.add(Dropout(config['dropout_1']))
        model.add(Dense(self.n_classes, activation='softmax'))
        model.compile(loss='sparse_categorical_crossentropy', optimizer=config['optimizer'], metrics=['acc'])
        return model
    
    def eval_config(self, config, iters, verbose=False):
        model = self._make_model(config)
        
        early_stopping = EarlyStopping(monitor='val_acc', patience=5, verbose=0)
        
        _ = model.fit(
            self.X_train, self.y_train,
            epochs=int(round(iters)),
            batch_size=config['batch_size'],
            verbose=verbose,
            callbacks=[early_stopping],
            validation_data=(self.X_val, self.y_val),
        )
        
        preds_val = model.predict(self.X_val, batch_size=512).argmax(1)
        acc_val = (preds_val == self.y_val).mean()
        
        preds_test = model.predict(self.X_test, batch_size=512).argmax(1)
        acc_test = (preds_test == self.y_test).mean()
        
        return {
            "obj" : 1 - acc_val,
            "config" : config,
            "iters" : iters,
            "converged" : model.stop_training,
            "_meta" : {
                "acc_val"  : acc_val,
                "acc_test" : acc_test,
            }
        }

if __name__ == "__main__":
    from hyperband import HyperBand
    model = MNISTModel()
    HyperBand(model, max_iter=81, eta=3).run()

self = MNISTModel()
config = self.rand_config()
self.eval_config(config, 10, verbose=True)

