import os
import sys
import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TensorBoard, Callback
from datetime import datetime

# Configuration Constants
CSV_PATH = './data/HAM10000_metadata.csv'
IMAGE_DIR = './data/HAM10000_images/'
BEST_MODEL_PATH = './models/dermosphere_best_model.keras'
CHECKPOINT_PATH = './models/dermosphere_checkpoint.keras'
META_PATH = './models/checkpoint_meta.txt'
LOG_DIR = "./logs/fit/" + datetime.now().strftime("%Y%m%d-%H%M%S")
BATCH_SIZE = 32
IMAGE_SIZE = (224, 224)
TOTAL_EPOCHS = 25

def run_diagnostics():
    """Validates filesystem integrity and checks for Apple Silicon hardware acceleration."""
    print("\n==============================================")
    print("      DERMOSPHERE SYSTEM & PATH DIAGNOSTICS   ")
    print("==============================================")
    
    # 1. Hardware Verification Block
    gpus = tf.config.list_physical_devices('GPU')
    logical_gpus = tf.config.list_logical_devices('GPU')
    if gpus:
        print(f"[OK] Apple Silicon GPU Acceleration Detected! Active nodes: {len(gpus)}")
    else:
        print("[WARN] Running on CPU. Install 'tensorflow-metal' to unlock your Mac's GPU cores.")
        
    # 2. Filesystem Integrity Verification
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] Metadata missing! Check path: {CSV_PATH}")
        sys.exit(1)
    if not os.path.exists(IMAGE_DIR):
        print(f"[ERROR] Image target directory missing! Checked path: {IMAGE_DIR}")
        sys.exit(1)

    images = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f" -> Found {len(images)} flat images directly inside IMAGE_DIR.")
    
    if len(images) == 0:
        print("\n[CRITICAL] Keras cannot see images. Ensure files are flattened inside './data/HAM10000_images/'")
        sys.exit(1)
    print("==============================================\n")

# Advanced ML: Categorical Focal Loss Architecture
def categorical_focal_loss(gamma=2.0, alpha=0.25):
    def focal_loss_fixed(y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, tf.keras.backend.epsilon(), 1.0 - tf.keras.backend.epsilon())
        cross_entropy = -y_true * tf.math.log(y_pred)
        weight = alpha * tf.math.pow(1.0 - y_pred, gamma)
        loss = weight * cross_entropy
        return tf.reduce_sum(loss, axis=-1)
    return focal_loss_fixed

# ==========================================
# CUSTOM CALLBACK: Meta State Tracker
# Saves the completed epoch string to a tiny text ledger on disk
# ==========================================
class EpochMetaTracker(Callback):
    def __init__(self, meta_file_path):
        super().__init__()
        self.meta_file_path = meta_file_path
        
    def on_epoch_end(self, epoch, logs=None):
        # epoch is 0-indexed, so adding 1 marks the NEXT epoch to start from
        with open(self.meta_file_path, 'w') as f:
            f.write(str(epoch + 1))

def main():
    run_diagnostics()
        
    df = pd.read_csv(CSV_PATH)
    if not str(df['image_id'].iloc[0]).endswith('.jpg'):
        df['image_id'] = df['image_id'].apply(lambda x: f"{x}.jpg")
    
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['dx'])
    
    unique_classes = np.unique(train_df['dx'])
    class_weights_array = compute_class_weight(class_weight='balanced', classes=unique_classes, y=train_df['dx'])
    class_weights_dict = {i: weight for i, weight in enumerate(class_weights_array)}
    
    train_datagen = ImageDataGenerator(
        rescale=1./255, rotation_range=90, width_shift_range=0.1, height_shift_range=0.1,
        zoom_range=0.2, horizontal_flip=True, vertical_flip=True, fill_mode='nearest'
    )
    val_datagen = ImageDataGenerator(rescale=1./255)
    
    train_generator = train_datagen.flow_from_dataframe(
        dataframe=train_df, directory=IMAGE_DIR, x_col='image_id', y_col='dx',
        target_size=IMAGE_SIZE, batch_size=BATCH_SIZE, class_mode='categorical', shuffle=True
    )
    val_generator = val_datagen.flow_from_dataframe(
        dataframe=val_df, directory=IMAGE_DIR, x_col='image_id', y_col='dx',
        target_size=IMAGE_SIZE, batch_size=BATCH_SIZE, class_mode='categorical', shuffle=False
    )
    
    os.makedirs('./models', exist_ok=True)
    
    # Initialize baseline configurations
    initial_epoch = 0
    model = None
    custom_objects = {'focal_loss_fixed': categorical_focal_loss(gamma=2.0, alpha=0.25)}

    # ==========================================
    # RESUMPTION ENGINE INTERCEPTOR
    # ==========================================
    if os.path.exists(CHECKPOINT_PATH) and os.path.exists(META_PATH):
        try:
            with open(META_PATH, 'r') as f:
                saved_epoch = int(f.read().strip())
                
            if saved_epoch < TOTAL_EPOCHS:
                print(f"[RECOVERY ACTIVATED] Intercepting rolling state from checkpoint file.")
                print(f" -> Resuming training loop fluidly starting from Epoch: {saved_epoch + 1}")
                
                # Load the full compiler configuration, weights, and optimizer learning state
                model = tf.keras.models.load_model(CHECKPOINT_PATH, custom_objects=custom_objects)
                initial_epoch = saved_epoch
        except Exception as e:
            print(f"[WARN] Checkpoint ledger corrupted or unreadable: {e}. Falling back to clean initialize.")
            model = None

    # Fresh initialization sequence if no checkpoints are discovered on disk
    if model is None:
        print("[INITIALIZE] No tracking records found. Constructing fresh MobileNetV2 architecture...")
        base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
        base_model.trainable = False
        
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dropout(0.5)(x) 
        predictions = Dense(7, activation='softmax')(x)
        
        model = Model(inputs=base_model.input, outputs=predictions)
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss=categorical_focal_loss(gamma=2.0, alpha=0.25),
            metrics=['accuracy']
        )

    # ==========================================
    # STRATEGIC CALLBACK ORCHESTRATION
    # ==========================================
    # 1. Saves only the absolute best iteration for production web gateway usage
    best_saver = ModelCheckpoint(BEST_MODEL_PATH, monitor='val_loss', save_best_only=True, mode='min')
    
    # 2. Rolling checkpoint: Overwrites itself every epoch to keep storage minimal
    rolling_saver = ModelCheckpoint(CHECKPOINT_PATH, monitor='val_loss', save_best_only=False, mode='min')
    
    # 3. Text ledger sync
    meta_tracker = EpochMetaTracker(META_PATH)
    
    # 4. Standard structural constraints
    early_stop = EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6, verbose=1)
    tensorboard_callback = TensorBoard(log_dir=LOG_DIR, histogram_freq=1)
    
    print("\n--- Starting Active Model Training Loop ---")
    model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=TOTAL_EPOCHS,
        initial_epoch=initial_epoch, 
        class_weight=class_weights_dict,
        callbacks=[best_saver, rolling_saver, meta_tracker, early_stop, reduce_lr, tensorboard_callback]
    )
    
    # Wipes rolling states out once completion finishes completely
    if os.path.exists(META_PATH): os.remove(META_PATH)
    if os.path.exists(CHECKPOINT_PATH): os.remove(CHECKPOINT_PATH)
    print(f"\n[COMPLETE] Production-grade model saved to: {BEST_MODEL_PATH}")

if __name__ == '__main__':
    main()