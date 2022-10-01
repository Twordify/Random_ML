# -*- coding: utf-8 -*-
"""Rice_copy.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1n3fHuo8xIdImZsuW4PoWcevTfY0R6jGR
"""

! pip install kaggle

! mkdir ~/.kaggle

! cp kaggle.json ~/.kaggle/

! chmod 600 ~/.kaggle/kaggle.json

! kaggle datasets download muratkokludataset/rice-image-dataset

! unzip rice-image-dataset

!pip install split-folders

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cv2
import os
import random
from pathlib import Path
import splitfolders
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from keras.preprocessing.image import ImageDataGenerator
from keras.applications.vgg16 import VGG16

dataset_input = Path('/content/Rice_Image_Dataset')
dataset_output = Path('/content/Rice_Image_Dataset/Splited')
train_path = Path('/content/Rice_Image_Dataset/Splited/train')
test_path = Path('/content/Rice_Image_Dataset/Splited/test')
val_path = Path('/content/Rice_Image_Dataset/Splited/val')
splitfolders.ratio(dataset_input, output=dataset_output, seed=42, ratio=(.8, .1, .1))

arborio = [fn for fn in os.listdir(f'{dataset_input}/Arborio') if fn.endswith('.jpg')]
bastmati = [fn for fn in os.listdir(f'{dataset_input}/Basmati') if fn.endswith('.jpg')]
ipsala = [fn for fn in os.listdir(f'{dataset_input}/Ipsala') if fn.endswith('.jpg')]
jasmine = [fn for fn in os.listdir(f'{dataset_input}/Jasmine') if fn.endswith('.jpg')]
karacadag = [fn for fn in os.listdir(f'{dataset_input}/Karacadag') if fn.endswith('.jpg')]
rice = [arborio, bastmati, ipsala, jasmine, karacadag]
rice_species = []
for i in os.listdir(train_path):
    rice_species+=[i]
rice_species.sort()

image_count = len(list(dataset_input.glob('*/*.jpg')))

counter = 0
rice_count = []
for species in rice_species:
  print(f'Number of {species} images: {len(rice[counter])}')
  rice_count.append(len(rice[counter]))
  counter += 1

def show_sample_images(): 
  plt.figure()
  plt.figure(figsize=(12,12))
  directory = os.listdir(train_path)
  directory.sort()
  i = 0
  for species in directory:
      i+= 1
      sample_image = random.choice(os.listdir(f'{train_path}/{species}'))
      sample_image_path = os.path.join(f'{train_path}/{species}', sample_image)
      img=cv2.imread(sample_image_path)
      plt.subplot(1, 5, i)
      plt.title(species)
      plt.axis('off')
      plt.imshow(img)

show_sample_images()

batch_size = 128
img_height, img_width = 175, 175
input_shape = (img_height, img_width, 3)

datagen = ImageDataGenerator(rescale=1./255)

train_ds = datagen.flow_from_directory(
    train_path,
    target_size = (img_height, img_width),
    batch_size = batch_size,
    subset = "training",
    class_mode='categorical')

val_ds = datagen.flow_from_directory(
    val_path,
    target_size = (img_height, img_width),
    batch_size = batch_size,
    class_mode='categorical',
    shuffle=False)

test_ds = datagen.flow_from_directory(
    test_path,
    target_size = (img_height, img_width),
    batch_size = batch_size,
    class_mode='categorical',
    shuffle=False)

def plot_train_history(history):
    plt.figure(figsize=(15,5))
    plt.subplot(1,2,1)
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.title('Model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'], loc='upper left')
    
    plt.subplot(1,2,2)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'], loc='upper left')
    plt.show()

model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(32,(3,3), activation='relu', input_shape=input_shape),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Conv2D(32,(3,3),activation='relu',padding='same'),
    tf.keras.layers.BatchNormalization(axis = 3),
    tf.keras.layers.MaxPooling2D(pool_size=(2,2),padding='same'),
    tf.keras.layers.Dropout(0.3),
    
    tf.keras.layers.Conv2D(64,(3,3),activation='relu',padding='same'),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Conv2D(64,(3,3),activation='relu',padding='same'),
    tf.keras.layers.BatchNormalization(axis = 3),
    tf.keras.layers.MaxPooling2D(pool_size=(2,2),padding='same'),
    tf.keras.layers.Dropout(0.3),
    
    tf.keras.layers.Conv2D(128,(3,3),activation='relu',padding='same'),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Conv2D(128,(3,3),activation='relu',padding='same'),
    tf.keras.layers.BatchNormalization(axis = 3),
    tf.keras.layers.MaxPooling2D(pool_size=(2,2),padding='same'),
    tf.keras.layers.Dropout(0.5),
    
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(512, activation='relu'),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.25),
    tf.keras.layers.Dense(5, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.summary()

models_dir = "saved_models"
if not os.path.exists(models_dir):
    os.makedirs(models_dir)

checkpointer = ModelCheckpoint(filepath='saved_models/model.hdf5', 
                               monitor='val_accuracy', mode='max',
                               verbose=1, save_best_only=True)
early_stopping = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=3)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2,patience=2, min_lr=0.001)
callbacks=[early_stopping, reduce_lr, checkpointer]

history1 = model.fit(train_ds, epochs = 40, validation_data = val_ds, callbacks=callbacks)

model.load_weights('saved_models/model.hdf5')
plot_train_history(history1)

new_model.summary()

from sklearn.metrics import classification_report
species = os.listdir(train_path)
species.sort()
Y_pred = model.predict(test_ds)
y_pred = np.argmax(Y_pred, axis=1)
report1 = classification_report(test_ds.classes, y_pred, target_names=species, output_dict=True)
df1 = pd.DataFrame(report1).transpose()
df1

vgg16 = VGG16(weights="imagenet", include_top=False, input_shape=input_shape)
vgg16.trainable = False
inputs = tf.keras.Input(input_shape)
x = vgg16(inputs, training=False)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.Dense(1024, activation='relu')(x)
x = tf.keras.layers.Dense(5, activation='softmax')(x)
model_vgg16 = tf.keras.Model(inputs, x)

model_vgg16.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model_vgg16.summary()

checkpointer = ModelCheckpoint(filepath='saved_models/model_vgg16.hdf5', 
                               monitor='val_accuracy', mode='max',
                               verbose=1, save_best_only=True)
early_stopping = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=3)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2,patience=2, min_lr=0.001)
callbacks=[early_stopping, reduce_lr, checkpointer]

history2 = model_vgg16.fit(train_ds, epochs = 40, validation_data = val_ds, callbacks=callbacks)

model_vgg16.load_weights('saved_models/model_vgg16.hdf5')
plot_train_history(history2)

vgg16.trainable = True
model_vgg16.compile(optimizer=keras.optimizers.Adam(1e-5),
              loss='categorical_crossentropy', metrics=['accuracy'])

history3 = model_vgg16.fit(train_ds, epochs = 40, validation_data = val_ds, callbacks=callbacks)

model_vgg16.load_weights('saved_models/model_vgg16.hdf5')

Y_pred = model_vgg16.predict(test_ds)

y_pred = np.argmax(Y_pred, axis=1)
confusion_mtx = confusion_matrix(y_pred, test_ds.classes)
f,ax = plt.subplots(figsize=(12, 12))
sns.heatmap(confusion_mtx, annot=True, 
            linewidths=0.01,
            linecolor="white", 
            fmt= '.1f',ax=ax,)
sns.color_palette("rocket", as_cmap=True)

plt.xlabel("Predicted Label")
plt.ylabel("True Label")
ax.xaxis.set_ticklabels(test_ds.class_indices)
ax.yaxis.set_ticklabels(rice_classes)
plt.title("Confusion Matrix")
plt.show()

report2 = classification_report(test_ds.classes, y_pred, target_names=rice_classes, output_dict=True)
df2 = pd.DataFrame(report1).transpose()
df2

plt.figure(figsize=(10, 10))
x, label= train_ds.next()
for i in range(9):
    plt.subplot(3, 3, i+1)
    plt.imshow(x[i])
    result = np.where(label[i]==1)
    predict = model_vgg16(tf.expand_dims(x[i], 0))
    score = tf.nn.softmax(predict[0])
    score_label = rice_classes[np.argmax(score)]
    plt.title(f'Truth: {rice_classes[result[0][0]]}\nPrediction:{score_label}')
    plt.axis(False)