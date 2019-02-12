import numpy as np
import os
import string
from os.path import expanduser
from . import util
import logging
from skimage import io
from skimage import transform

import tarfile



def load_subject(subject_path,image_size,skip):
    
    folders= sorted(os.listdir(subject_path))
    data= np.zeros((0,image_size[0],image_size[1], 3),dtype='uint8')
    labels= np.array(())
    
    # cargar cada folder con sus labels
    for (i, folderName) in enumerate(folders):
        label_i= ord(folderName) - 97
        files= sorted(os.listdir(os.path.join(subject_path,folderName)))
        files = [f for f in files if f.startswith("color")]
        files=files[::skip]

        folder_data=np.zeros((len(files), image_size[0], image_size[1], 3),dtype='uint8')
        for (j, filename) in enumerate(files):
            image_filepath=os.path.join(subject_path, folderName,filename)
            image=io.imread(image_filepath)
            image = transform.resize(image, (image_size[0], image_size[1]), preserve_range=True)

            labels= np.append(labels, label_i)
            folder_data[j,:,:,:]=image
        data= np.vstack((data, folder_data))
    return data, labels               

from multiprocessing import Pool

def list_diff(a,b):
    s = set(b)
    return [x for x in a if x not in s]

def load_images(folder_path,image_size,skip,test_subjects):

    train_subjects=list_diff(["A","B","C","D","E"],test_subjects)


    def f(subject): return load_subject(os.path.join(folder_path,subject),image_size,skip)

    train_subject_data=map(f, train_subjects)
    x_train,y_train=zip(*train_subject_data)

    x_train = np.vstack(x_train)
    y_train = np.hstack(y_train)

    test_subject_data = map(f, test_subjects)
    x_test, y_test = zip(*test_subject_data)
    x_test = np.vstack(x_test)
    y_test = np.hstack(y_test)

    return x_train, x_test, y_train, y_test


def download_and_extract(folderpath):
    if not os.path.exists(folderpath):
        logging.warning("Creating folder %s..." % folderpath)
        os.mkdir(folderpath)

    filename = "fingerspelling5.tar.bz2"
    zip_filepath = os.path.join(folderpath, filename)

    if not os.path.exists(zip_filepath):
        logging.warning("Downloading Pugeault's Fingerspelling dataset to folder %s ..." % zip_filepath)
        origin = "http://www.cvssp.org/FingerSpellingKinect2011/fingerspelling5.tar.bz2"
        util.download_file(origin, zip_filepath)

    if not os.path.exists(os.path.join(folderpath,"dataset5")):
        logging.warning("Extracting images to %s..." % folderpath)
        with tarfile.open(zip_filepath, "r:bz2") as tar_ref:
            tar_ref.extractall(folderpath)


def load_data(folderpath,image_size=(32,32),skip=1,test_subjects=["E"]):
    folderpath = os.path.join(folderpath, "pugeault")
    # make folder for pugeault
    if not os.path.exists(folderpath):
        os.mkdir(folderpath)
    # make folder for options
    dataset_options="subjects"+"".join(test_subjects)+f"_skip{skip}_size{image_size[0]}x{image_size[1]}"

    #download dataset
    test_subjects_string="".join(test_subjects)
    np_filename=f"pugeault_color_{dataset_options}.npz"
    np_filepath=os.path.join(folderpath,np_filename)
    if not os.path.exists(np_filepath):
        logging.warning("Downloading/extracting/recoding dataset...")
        # download dataset (if necessary)
        download_and_extract(folderpath)
        folderpath = os.path.join(folderpath, "dataset5")
        logging.warning("Loading images from %s..." % folderpath)
        x_train, x_test, y_train, y_test = load_images(folderpath, image_size, skip, test_subjects)
        logging.warning("Done.")
        logging.warning("Saving binary version of dataset to %s" % np_filepath)
        np.savez(np_filepath, x_train=x_train, x_test=x_test, y_train=y_train, y_test=y_test)
        logging.warning("Done.")
    else:
        logging.warning(f"Found binary version of pugeault's dataset in {np_filepath}, loading...")
        data=np.load(np_filepath)
        x_train, x_test, y_train, y_test=(data["x_train"],data["x_test"],data["y_train"],data["y_test"])


    input_shape=(32,32,3)

    labels = string.ascii_lowercase[:25]
    return x_train, x_test, y_train, y_test,input_shape,labels

