from tensorflow.keras.utils import Sequence
import pandas as pd
import numpy as np


class FacialKeyPointsDataset(Sequence):
    def __init__(self, csv_file, root_dir, output_size, batch_size, shuffle=False, normalization="scaler"):
        self.keypts_frame = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.output_size = output_size
        self.batch_size = batch_size
        self.shuffle = shuffle
        if normalization == 'scaler':
            self.mean = self.keypts_frame.iloc[:, 1:].values.mean()
            self.std = self.keypts_frame.iloc[:, 1:].values.std()
            print(self.mean, self.std)
        elif normalization == 'vector':
            self.mean = self.keypts_frame.iloc[:, 1:].values.mean(axis=0).reshape(-1, 1)
            self.std = self.keypts_frame.iloc[:, 1:].values.std(axis=0).reshape(-1, 1)

            print(self.mean.shape, self.mean.shape)
        elif normalization == 'none':
            self.mean = 0
            self.std = 1
        else:
            raise ValueError("normalization must be one of 'scaler', 'vector', or 'none'")

        self.on_epoch_end()


    def on_epoch_end(self):
        self.indecies = np.arange(len(self.keypts_frame))
        # np.random.shuffle(self.indecies)


    def __len__(self):
        return floor(len(self.keypts_frame) / self.batch_size)

    def __getitem__(self, idx):
        X = np.empty((self.batch_size, *self.output_size, 1))
        y = np.empty((self.batch_size, 136, 1))

        indecies = self.indecies[idx*self.batch_size:(idx+1)*self.batch_size]

        for index in range(len(indecies)):
            image_name = os.path.join(self.root_dir,
                               self.keypts_frame.iloc[indecies[index], 0])
            
            image = mpimg.imread(image_name)
            
            # if image has an alpha color channel, get rid of it
            if(image.shape[2] == 4):
                image = image[:,:,0:3]
            
            key_pts = self.keypts_frame.iloc[indecies[index], 1:].to_numpy()
            image, key_pts = self.rescale(image, key_pts)
            image, key_pts = self.randomCrop(image, key_pts)
            image, key_pts = self.normalize(image, key_pts)
            image = image.reshape(*self.output_size, 1).astype(np.float32)
            key_pts = key_pts.astype(np.float32)

            X[index,] = image
            y[index] = key_pts

        return X, y

    def normalize(self, image, key_pts):
        image_copy = np.copy(image)
        key_pts_copy = np.copy(key_pts)

        # convert image to grayscale
        image_copy = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # scale color range from [0, 255] to [0, 1]
        image_copy=  image_copy/255.0
        
        # scale keypoints to be centered around 0 with a range of [-1, 1]
        key_pts_copy = (key_pts_copy - self.mean)/self.std
        return image_copy, key_pts_copy
    
    def randomCrop(self, image, key_pts):
        key_pts = key_pts.reshape(-1, 2)
        h, w = image.shape[:2]
        new_h, new_w = self.output_size

        top = np.random.randint(0, h - new_h)
        left = np.random.randint(0, w - new_w)

        image = image[top: top + new_h,
                      left: left + new_w]

        key_pts = key_pts - [left, top]

        return image, key_pts.reshape(-1, 1)
    
    def rescale(self, image, key_pts):
        key_pts = key_pts.reshape(-1, 2)
        h, w = image.shape[:2]

        new_h, new_w = self.output_size

        new_h, new_w = int(new_h) + 4, int(new_w) + 4 # to be cropped later

        img = cv2.resize(image, (new_w, new_h))
        
        key_pts = key_pts * [new_w / w, new_h / h]

        return img, key_pts.reshape(-1, 1)

    