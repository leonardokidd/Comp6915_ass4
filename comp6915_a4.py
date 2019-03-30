# -*- coding: utf-8 -*-
"""test of COMP6915 a5.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kMEEUANCHhToYShyvbfmJ3nfFNTs0tXc

# **Computer Science 6915 - Winter 2019 Assignment 4**


This Assignement is using TensorFlow create a deep neural network model to classify house numbers. For this task, use the images provided in the the Street View House Numbers (SVHN) Dataset (Format 2) available at http://ufldl.stanford.edu/housenumbers/. Use the train data set to train your network and the test dataset to evaluate your network performance.

Import all the required packages:
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import color
from matplotlib import pyplot as plt
from scipy.io import loadmat
import tensorflow as tf
import tensorflow.keras as keras
from keras import backend as K, regularizers, optimizers
from keras.models import load_model, Sequential
from keras.layers import MaxPooling2D, Convolution2D, Activation, Dropout, Flatten, Dense, InputLayer
from keras.layers.normalization import BatchNormalization
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img
from keras.callbacks import EarlyStopping, ModelCheckpoint
from google.colab import files

"""Define all the constants will be used in the network:

Image dimensions: height is 32, width is 32, and channel is 3.

Model selection: range between 1~3.

Number of epochs: 50.

Number of class number: 10.
"""

img_dims = (32,32,3)
model_option = 2
all_models = False
epochs = 50
NUM_MLP_LAYERS = 2
train_url = "http://ufldl.stanford.edu/housenumbers/train_32x32.mat"
test_url = "http://ufldl.stanford.edu/housenumbers/test_32x32.mat"
optimizer = 'adam'
loss="sparse_categorical_crossentropy"
metrics=['accuracy']
es = keras.callbacks.EarlyStopping(
      monitor='val_loss', verbose=0, patience=3)

"""**Functions define:**

Models comparison:

When all_models parameter is turned on, show all validation accuracy/training accuracy graphy of different models for comparison.

Dataset augmentation:


We apply gaussian filter to blure the original image as the preprocessing function  and rotation to augment the data. For each orignial image, we generate another two augmented images. Finally, the training data consists of orignal image following with two augmented images if the augment option is set to True.
"""

# for plotting multiple models - from https://www.tensorflow.org/tutorials/keras/overfit_and_underfit
def plot_history(histories, key='acc'):
  plt.figure(figsize=(16,10))
    
  for historyPair in histories:
    name = list(historyPair.keys())[0]
    history = historyPair.get(name)
    val = plt.plot(history.epoch, history.history['val_'+key],
                   '--', label=name.title()+' Val')
    plt.plot(history.epoch, history.history[key], color=val[0].get_color(),
             label=name.title()+' Train')

  plt.xlabel('Epochs')
  plt.ylabel(key.replace('_',' ').title())
  plt.legend()
  plt.xlim([0,max(history.epoch)])
  
  # for plotting predictions - from https://www.tensorflow.org/tutorials/keras/basic_classification
def plot_image(i, predictions_array, true_label, img):
  predictions_array, true_label, img = predictions_array[i], true_label[i], img[i]
  plt.grid(False)
  plt.xticks([])
  plt.yticks([])
  
  plt.imshow(img, cmap=plt.cm.binary)

  predicted_label = np.argmax(predictions_array)
  if predicted_label == true_label:
    color = 'blue'
  else:
    color = 'red'
  
  plt.xlabel("{} {:2.0f}% ({})".format((predicted_label+1)%10,
                                100*np.max(predictions_array),
                                (true_label+1)%10),
                                color=color)

# for plotting array of predictions - from https://www.tensorflow.org/tutorials/keras/basic_classification
def plot_value_array(i, predictions_array, true_label):
  predictions_array, true_label = predictions_array[i], true_label[i]
  plt.grid(False)
  plt.xticks([])
  plt.yticks([])
  thisplot = plt.bar(range(10), predictions_array, color="#777777")
  plt.ylim([0, 1]) 
  predicted_label = np.argmax(predictions_array)
 
  thisplot[predicted_label].set_color('red')
  thisplot[int(true_label)].set_color('blue')

# Define gaussian filter to blure the image
def imgBlur(image):
  result = gaussian_filter(image, sigma=1)
  return result

augment = ImageDataGenerator(
    rotation_range=10,
    shear_range=10.0,
    brightness_range=[0.9,0.95],
    zoom_range=0.1,
    preprocessing_function=imgBlur
)

# From each original image, generate a dataset with original image
# followed by two other augmented images
def img_augmenting(img):
  images = []
  height, width, channels = img.shape
  img = img.reshape(1, height, width, channels)
  images.append(img)
  for idx, batch in enumerate(augment.flow(img, batch_size=2)):
    images.append(batch)
    if idx >= 2: # Only two augmented images will be generated
      break
  return images

# Load data by using url with the option of turn on/off the dataset augmentation
def load_url(url, augment):
  repo = np.DataSource()
  file = repo.open(url)
  mat_data = loadmat(file.name) # Load the mat file data
  X = np.moveaxis(mat_data['X'], -1, 0) # Get features from dataset
  y = mat_data['y'].flatten()-1 # Get class from dataset
  
  # If augment option is turned on, 
  # insert augmentation data to original data and class set
  if augment:
    dataList = []
    classList = []
    for img_element, class_element in zip(X, y):
      aug_images = img_augmenting(img_element)
      for aug in aug_images:
        dataList.append(aug)
        classList.append(class_element)
    X = np.vstack(dataList)
    y = np.vstack(classList).flatten()
  X = np.true_divide(X, 255.0)
  return X, y

"""Set the dataset format to image channels as the last data dimension, and load trainning and test data by using URL."""

# enforce image format
keras.backend.set_image_data_format('channels_last')
# Load datasets with or without image augmentation
train_data, train_class = load_url(train_url, True)
test_data, test_class = load_url(test_url, False)    # don't augment the test set

if len(np.unique(train_class)) != len(np.unique(test_class)):
  print("The class number between training data and test data are not same")
class_num = len(np.unique(train_class))

# Display the data and class set shape for training and test dataset.
print("train data shape: ", train_data.shape)
print("train class shape: ", train_class.shape)
print("test data shape: ", test_data.shape)
print("test class shape: ", test_class.shape)

"""Display some sample data and it's corresponding class. The value is randomly selected."""

plt.figure(figsize=(10,10))
for i in range(25):
    rnd = np.random.randint(0,train_data.shape[0])
    plt.subplot(5, 5, i+1)
    plt.xticks([])
    plt.yticks([])
    plt.grid(False)
    plt.imshow(train_data[rnd])
    plt.xlabel((train_class[rnd]+1)%10)
plt.show()

"""**Neural Network models:**

One multilayer perceptron network and two different structured Covelutional Neural Networks are built to compare the results. 

Create multilayer perceptron network with two regular densely-connected NN layers between the input and output layer.
"""

# MLP
mlpModel = keras.models.Sequential()
mlpModel.add(keras.layers.Flatten(input_shape=img_dims))
for n in range(NUM_MLP_LAYERS):
    mlpModel.add(keras.layers.Dense(512, activation='relu'))
mlpModel.add(keras.layers.Dense(class_num, activation='softmax'))
mlpModel.compile(optimizer=optimizer, loss=loss, metrics=metrics)

mlpModel.summary()

"""Create first Convolutional Neural Network with batch normalization as preprocessing function,  three different size of 2D Convelution layers, and two Densely-connected layers."""

# cnn1
cnnModel = keras.models.Sequential()
cnnModel.add(keras.layers.InputLayer(input_shape=img_dims))
cnnModel.add(keras.layers.BatchNormalization())

# Add three 2D Convolutional layers
cnnModel.add(keras.layers.Conv2D(64, kernel_size=(3, 3), padding='same',
                 activation='relu'))
cnnModel.add(keras.layers.Conv2D(64, kernel_size=(3, 3), padding='same',
                 activation='relu'))
cnnModel.add(keras.layers.Conv2D(64, kernel_size=(3, 3), padding='same',
                 activation='relu'))
cnnModel.add(keras.layers.Conv2D(64, kernel_size=(3, 3), padding='same',
                 activation='relu'))
cnnModel.add(keras.layers.MaxPooling2D((2, 2)))

cnnModel.add(keras.layers.Conv2D(128, kernel_size=(3, 3), padding='same',
                 activation='relu'))
cnnModel.add(keras.layers.Conv2D(128, kernel_size=(3, 3), padding='same',
                 activation='relu'))
cnnModel.add(keras.layers.Conv2D(128, kernel_size=(3, 3), padding='same',
                 activation='relu'))
cnnModel.add(keras.layers.Conv2D(128, kernel_size=(3, 3), padding='same',
                 activation='relu'))
cnnModel.add(keras.layers.MaxPooling2D(pool_size=(2, 2)))

cnnModel.add(keras.layers.Conv2D(128, kernel_size=(5, 5), padding='same',
              activation='relu'))
cnnModel.add(keras.layers.MaxPooling2D((2, 2)))

cnnModel.add(keras.layers.LocallyConnected2D(32, (3, 3), input_shape=img_dims))

cnnModel.add(keras.layers.MaxPooling2D(pool_size=(2, 2)))

cnnModel.add(keras.layers.Flatten())

# Add densely-connected NN layers and apply L1 regulation
cnnModel.add(keras.layers.Dense(128, activation='relu',
               activity_regularizer=keras.regularizers.l1(0.003)))

cnnModel.add(keras.layers.Dense(128, activation='relu',
               activity_regularizer=keras.regularizers.l1(0.003)))

cnnModel.add(keras.layers.Dense(128, activation='relu',
               activity_regularizer=keras.regularizers.l1(0.003)))
# cnnModel2.add(keras.layers.Dropout(0.3))

cnnModel.add(keras.layers.Dense(class_num, activation='softmax'))
cnnModel.compile(optimizer=optimizer, loss=loss, metrics=metrics)

cnnModel.summary()

"""Create second Convolutional Neural Network with four different size of 2D Convolution layers, and two Densely-connected layers. In addition, a dropout is used as network modifying regularization."""

# cnn2
cnnModel2 = keras.models.Sequential()
cnnModel2.add(keras.layers.Conv2D(32, (3, 3), padding='same',
              activation='relu', input_shape=img_dims))
cnnModel2.add(keras.layers.MaxPooling2D((2, 2)))
cnnModel2.add(keras.layers.Conv2D(64, (3, 3), padding='same',
              activation='relu'))
cnnModel2.add(keras.layers.MaxPooling2D((2, 2)))
cnnModel2.add(keras.layers.Conv2D(128, (3, 3), padding='same',
              activation='relu'))
cnnModel2.add(keras.layers.MaxPooling2D((2, 2)))
cnnModel2.add(keras.layers.Conv2D(128, (3, 3), padding='same',
              activation='relu'))
cnnModel2.add(keras.layers.MaxPooling2D((2, 2)))
cnnModel2.add(keras.layers.Flatten())
cnnModel2.add(keras.layers.Dropout(0.5))
cnnModel2.add(keras.layers.Dense(512, activation='relu'))
cnnModel2.add(keras.layers.Dense(128, activation='relu'))
cnnModel2.add(keras.layers.Dense(class_num, activation='softmax'))
cnnModel2.compile(optimizer=optimizer, loss=loss, metrics=metrics)

cnnModel2.summary()

"""Train the data with different Neural Network models and show the accuracy diagram with possible train all the models and compare the results."""

if not all_models:
  if model_option == 1:
    model = mlpModel
  elif model_option == 2:
    model = cnnModel
  elif model_option == 3:
    model = cnnModel2

  modelhistory = model.fit(train_data,train_class,
                      epochs=epochs, validation_data=(test_data,test_class),
                      batch_size = 512, callbacks=[es])
  plt.plot(modelhistory.history['val_acc'])
  plt.plot(modelhistory.history['acc'])
  plt.legend(['validation accuracy', 'training accuracy'])
  plt.title("Accuracy")
  pass
else:
  
  model3 = mlpModel
  model1 = cnnModel
  model2 = cnnModel2
  
  #model1 run cnn1
  model1history = model1.fit(train_data,train_class,
                    epochs=epochs, validation_data=(test_data,test_class),
                    batch_size = 512, callbacks=[es])
  # model2 run cnn2
  model2history = model2.fit(train_data,train_class,
                      epochs=epochs, validation_data=(test_data,test_class),
                      batch_size = 512, callbacks=[es])
  
  # model 3 run mlp
  model3history = model3.fit(train_data,train_class,
                      epochs=epochs, validation_data=(test_data,test_class),
                      batch_size = 512, callbacks=[es])

# add models to this list to add to history plot
  history_list = []
  if all_models:
    history_list.append({'MLP':model3history})
    history_list.append({'cnn1':model1history})
    history_list.append({'cnn2':model2history})
  else:
    history_list.append({'model':modelhistory})
  plot_history(history_list)

"""Next 2 cells show predictions of model2 and graphs of random images showing percentage of predictions"""

predictions = model.predict(test_data)

# Plot the first X test images, their predicted label, and the true label
# Color correct predictions in blue, incorrect predictions in red
num_rows = 5
num_cols = 5
num_images = num_rows*num_cols
plt.figure(figsize=(2*2*num_cols, 2*num_rows))
for i in range(num_images):
  j = np.random.randint(0,test_data.shape[0])
  plt.subplot(num_rows, 2*num_cols, 2*i+1)
  plot_image(j, predictions, test_class, test_data)
  plt.subplot(num_rows, 2*num_cols, 2*i+2)
  plot_value_array(j, predictions, test_class)
plt.show()

"""Finally, save the model as output and download the file."""

model.save("CNN_SVHN.h5")
files.download("CNN_SVHN.h5")