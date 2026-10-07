import os
import cv2
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    preprocess_input
)

from tensorflow.keras.layers import (
    Dense,
    GlobalAveragePooling2D,
    Dropout,
    Input,
    Concatenate,
    Embedding,
    Flatten,
    BatchNormalization
)

from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam

from tensorflow.keras.callbacks import (
    ReduceLROnPlateau,
    EarlyStopping,
    ModelCheckpoint,
    CSVLogger
)

from tensorflow.keras.preprocessing.image import ImageDataGenerator


# ============================================================
# 1. CONFIGURATION
# ============================================================

CSV_PATH = "./data/HAM10000_metadata.csv"
IMAGE_DIR = "./data/HAM10000_images/"

MODEL_DIR = "./models/"
GRAPH_DIR = "./graphs/"

EPOCHS_PHASE_1 = 5
EPOCHS_PHASE_2 = 20

TOTAL_EPOCHS = EPOCHS_PHASE_1 + EPOCHS_PHASE_2

BATCH_SIZE = 32
K_FOLDS = 5

IMG_SIZE = (224, 224)

CLASSES = [
    "Actinic keratoses",
    "Basal cell carcinoma",
    "Benign keratosis",
    "Dermatofibroma",
    "Melanoma",
    "Melanocytic nevi",
    "Vascular lesions"
]

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)


# ============================================================
# GRAPH SETTINGS
# ============================================================

sns.set_theme(style="whitegrid")

plt.rcParams.update({
    "font.size": 12,
    "font.family": "sans-serif"
})


# ============================================================
# 2. DATA BALANCING
# ============================================================

def balance_dataframe_hybrid(df_train, target_size=2000):

    balanced_groups = []

    for class_index, group in df_train.groupby("target"):

        if len(group) < target_size:

            sampled_group = group.sample(
                n=target_size,
                replace=True,
                random_state=42
            )

        else:

            sampled_group = group.copy()

        balanced_groups.append(sampled_group)

    df_balanced = pd.concat(balanced_groups)

    df_balanced = df_balanced.sample(
        frac=1,
        random_state=42
    ).reset_index(drop=True)

    return df_balanced


# ============================================================
# 3. IMAGE AUGMENTATION
# ============================================================

augmenter = ImageDataGenerator(

    rotation_range=15,

    width_shift_range=0.1,

    height_shift_range=0.1,

    zoom_range=0.1,

    horizontal_flip=True,

    fill_mode="reflect"

)


# ============================================================
# 4. MULTIMODAL DATA GENERATOR
# ============================================================

class MultimodalGenerator(tf.keras.utils.Sequence):

    def __init__(
        self,
        df,
        image_dir,
        batch_size,
        img_size,
        num_classes,
        is_training=True,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.df = df.reset_index(drop=True)

        self.image_dir = image_dir

        self.batch_size = batch_size

        self.img_size = img_size

        self.num_classes = num_classes

        self.is_training = is_training

        self.indices = np.arange(len(self.df))

        if self.is_training:

            np.random.shuffle(self.indices)


    def __len__(self):

        return int(
            np.ceil(
                len(self.df) / self.batch_size
            )
        )


    def on_epoch_end(self):

        if self.is_training:

            np.random.shuffle(self.indices)


    def __getitem__(self, index):

        start = index * self.batch_size

        end = (index + 1) * self.batch_size

        batch_indices = self.indices[start:end]

        batch_df = self.df.iloc[batch_indices]

        batch_size_actual = len(batch_df)


        X_images = np.zeros(
            (
                batch_size_actual,
                self.img_size[0],
                self.img_size[1],
                3
            ),
            dtype=np.float32
        )


        X_age = np.zeros(
            (
                batch_size_actual,
                1
            ),
            dtype=np.float32
        )


        X_sex = np.zeros(
            (
                batch_size_actual,
                1
            ),
            dtype=np.int32
        )


        X_anatomy = np.zeros(
            (
                batch_size_actual,
                1
            ),
            dtype=np.int32
        )


        Y = np.zeros(
            (
                batch_size_actual,
                self.num_classes
            ),
            dtype=np.float32
        )


        for i, (_, row) in enumerate(batch_df.iterrows()):

            img_path = os.path.join(
                self.image_dir,
                row["image_id"]
            )


            img = cv2.imread(img_path)


            if img is not None:

                img = cv2.resize(
                    img,
                    self.img_size
                )


                img = cv2.cvtColor(
                    img,
                    cv2.COLOR_BGR2RGB
                )


                img = img.astype(np.float32)


                if self.is_training:

                    img = augmenter.random_transform(img)


                X_images[i] = preprocess_input(img)


            else:

                print(
                    f"[WARNING] Image not found: {img_path}"
                )


            X_age[i] = row["age_scaled"]

            X_sex[i] = row["sex_encoded"]

            X_anatomy[i] = row["anatomy_encoded"]


            Y[i] = tf.keras.utils.to_categorical(
                int(row["target"]),
                num_classes=self.num_classes
            )


        return (
            {
                "image_input": X_images,
                "age_input": X_age,
                "sex_input": X_sex,
                "anatomy_input": X_anatomy
            },
            Y
        )


# ============================================================
# 5. BUILD MULTIMODAL MODEL
# ============================================================

def build_phase1_model(num_classes, vocab_sizes):


    # --------------------------------------------------------
    # IMAGE INPUT
    # --------------------------------------------------------

    img_input = Input(
        shape=(224, 224, 3),
        name="image_input"
    )


    # --------------------------------------------------------
    # MOBILENETV2
    # --------------------------------------------------------

    base_model = MobileNetV2(

        weights="imagenet",

        include_top=False,

        input_tensor=img_input

    )


    # Freeze MobileNet initially

    base_model.trainable = False


    # --------------------------------------------------------
    # IMAGE FEATURES
    # --------------------------------------------------------

    x_vis = GlobalAveragePooling2D()(
        base_model.output
    )


    x_vis = Dropout(0.3)(x_vis)


    # --------------------------------------------------------
    # AGE INPUT
    # --------------------------------------------------------

    age_input = Input(
        shape=(1,),
        name="age_input"
    )


    # --------------------------------------------------------
    # SEX INPUT
    # --------------------------------------------------------

    sex_input = Input(
        shape=(1,),
        dtype="int32",
        name="sex_input"
    )


    # --------------------------------------------------------
    # ANATOMY INPUT
    # --------------------------------------------------------

    anatomy_input = Input(
        shape=(1,),
        dtype="int32",
        name="anatomy_input"
    )


    # --------------------------------------------------------
    # SEX EMBEDDING
    # --------------------------------------------------------

    sex_emb = Embedding(

        input_dim=vocab_sizes["sex"],

        output_dim=4

    )(sex_input)


    sex_emb = Flatten()(sex_emb)


    # --------------------------------------------------------
    # ANATOMY EMBEDDING
    # --------------------------------------------------------

    anatomy_emb = Embedding(

        input_dim=vocab_sizes["anatomy"],

        output_dim=8

    )(anatomy_input)


    anatomy_emb = Flatten()(anatomy_emb)


    # --------------------------------------------------------
    # TABULAR FEATURES
    # --------------------------------------------------------

    x_tab = Concatenate()([

        age_input,

        sex_emb,

        anatomy_emb

    ])


    x_tab = Dense(
        64,
        activation="relu"
    )(x_tab)


    x_tab = Dropout(0.2)(x_tab)


    # --------------------------------------------------------
    # MULTIMODAL FUSION
    # --------------------------------------------------------

    fusion = Concatenate()([

        x_vis,

        x_tab

    ])


    fusion = Dense(
        256,
        activation="relu"
    )(fusion)


    fusion = Dropout(0.3)(fusion)


    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    output = Dense(

        num_classes,

        activation="softmax",

        name="diagnostic_output"

    )(fusion)


    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model = Model(

        inputs=[

            img_input,

            age_input,

            sex_input,

            anatomy_input

        ],

        outputs=output

    )


    # --------------------------------------------------------
    # COMPILE
    # --------------------------------------------------------

    model.compile(

        optimizer=Adam(
            learning_rate=5e-4
        ),

        loss=tf.keras.losses.CategoricalCrossentropy(
            label_smoothing=0.05
        ),

        metrics=[

            "accuracy",

            tf.keras.metrics.AUC(
                name="auc"
            )

        ]

    )


    return model


# ============================================================
# 6. PHASE 2 FINE TUNING
# ============================================================

def unfreeze_for_phase2(model):


    # Find MobileNet base model

    base_model = None


    for layer in model.layers:

        if isinstance(
            layer,
            tf.keras.Model
        ):

            if "mobilenet" in layer.name.lower():

                base_model = layer

                break


    # If found, unfreeze selected layers

    if base_model is not None:


        base_model.trainable = True


        # Freeze first layers

        for layer in base_model.layers[:-30]:

            layer.trainable = False


        # Keep BatchNorm frozen

        for layer in base_model.layers:

            if isinstance(
                layer,
                BatchNormalization
            ):

                layer.trainable = False


    # Compile again

    model.compile(

        optimizer=Adam(
            learning_rate=1e-4
        ),

        loss=tf.keras.losses.CategoricalCrossentropy(
            label_smoothing=0.05
        ),

        metrics=[

            "accuracy",

            tf.keras.metrics.AUC(
                name="auc"
            )

        ]

    )


    return model


# ============================================================
# 7. EVALUATION
# ============================================================

def evaluate_fold(model, val_gen):


    print("\n[SYSTEM] Generating predictions...")


    y_pred_probs = model.predict(
        val_gen,
        verbose=1
    )


    y_pred_classes = np.argmax(
        y_pred_probs,
        axis=1
    )


    y_true_list = []


    for _, y in val_gen:

        y_true_list.extend(
            np.argmax(
                y,
                axis=1
            )
        )


    y_true_classes = np.array(
        y_true_list
    )


    # Safety check

    min_length = min(

        len(y_true_classes),

        len(y_pred_classes)

    )


    y_true_classes = y_true_classes[:min_length]

    y_pred_classes = y_pred_classes[:min_length]


    # Accuracy

    accuracy = np.mean(

        y_pred_classes == y_true_classes

    )


    # Precision Recall F1

    precision, recall, f1, _ = precision_recall_fscore_support(

        y_true_classes,

        y_pred_classes,

        average="weighted",

        zero_division=0

    )


    # Confusion matrix

    cm = confusion_matrix(

        y_true_classes,

        y_pred_classes,

        labels=np.arange(len(CLASSES))

    )


    # Specificity

    FP = cm.sum(axis=0) - np.diag(cm)

    FN = cm.sum(axis=1) - np.diag(cm)

    TP = np.diag(cm)

    TN = cm.sum() - (
        FP + FN + TP
    )


    specificity_arr = np.divide(

        TN,

        TN + FP,

        out=np.zeros_like(
            TN,
            dtype=float
        ),

        where=(TN + FP) != 0

    )


    class_weights = np.bincount(

        y_true_classes,

        minlength=len(CLASSES)

    )


    specificity = np.average(

        specificity_arr,

        weights=class_weights

    )


    return (

        y_true_classes,

        y_pred_classes,

        accuracy,

        precision,

        recall,

        f1,

        specificity

    )


# ============================================================
# 8. GENERATE REPORTS
# ============================================================

def generate_single_fold_reports(

    y_true,

    y_pred,

    accuracy,

    precision,

    recall,

    f1,

    specificity

):


    print(
        "\n[GRAPHICS] Generating graphs..."
    )


    # --------------------------------------------------------
    # METRICS GRAPH
    # --------------------------------------------------------

    metric_names = [

        "Accuracy",

        "Precision",

        "Sensitivity\n(Recall)",

        "F1 Score",

        "Specificity"

    ]


    metric_values = [

        accuracy,

        precision,

        recall,

        f1,

        specificity

    ]


    plt.figure(
        figsize=(10, 6),
        dpi=300
    )


    bars = plt.bar(

        metric_names,

        metric_values

    )


    plt.ylim(0, 1.1)


    plt.title(
        "Overall Validation Performance Metrics",
        fontsize=16,
        fontweight="bold"
    )


    plt.ylabel("Score")


    for bar in bars:

        height = bar.get_height()

        plt.text(

            bar.get_x()
            + bar.get_width() / 2,

            height + 0.02,

            f"{height:.4f}",

            ha="center"

        )


    plt.tight_layout()


    plt.savefig(

        os.path.join(

            GRAPH_DIR,

            "SingleFold_Comprehensive_Metrics.png"

        )

    )


    plt.close()


    # --------------------------------------------------------
    # CONFUSION MATRIX
    # --------------------------------------------------------

    cm = confusion_matrix(

        y_true,

        y_pred,

        labels=np.arange(len(CLASSES))

    )


    plt.figure(

        figsize=(12, 10),

        dpi=300

    )


    sns.heatmap(

        cm,

        annot=True,

        fmt="d",

        cmap="Blues",

        xticklabels=CLASSES,

        yticklabels=CLASSES

    )


    plt.title(

        "Diagnostic Confusion Matrix",

        fontsize=16,

        fontweight="bold"

    )


    plt.ylabel("True Class")

    plt.xlabel("Predicted Class")


    plt.xticks(

        rotation=45,

        ha="right"

    )


    plt.tight_layout()


    plt.savefig(

        os.path.join(

            GRAPH_DIR,

            "SingleFold_Confusion_Matrix.png"

        )

    )


    plt.close()


    # --------------------------------------------------------
    # CLASS RECALL
    # --------------------------------------------------------

    class_totals = cm.sum(axis=1)


    class_recall = np.divide(

        np.diag(cm),

        class_totals,

        out=np.zeros_like(

            class_totals,

            dtype=float

        ),

        where=class_totals != 0

    )


    plt.figure(

        figsize=(12, 6),

        dpi=300

    )


    bars = plt.bar(

        CLASSES,

        class_recall

    )


    plt.ylim(0, 1.1)


    plt.title(

        "AI Sensitivity Per Skin Cancer Type",

        fontsize=16,

        fontweight="bold"

    )


    plt.ylabel("Recall")


    plt.xticks(

        rotation=45,

        ha="right"

    )


    for bar in bars:

        height = bar.get_height()

        plt.text(

            bar.get_x()
            + bar.get_width() / 2,

            height + 0.02,

            f"{height:.2f}",

            ha="center"

        )


    plt.tight_layout()


    plt.savefig(

        os.path.join(

            GRAPH_DIR,

            "SingleFold_Class_Sensitivity.png"

        )

    )


    plt.close()


    print(

        "[SUCCESS] All graphs saved successfully."

    )


# ============================================================
# 9. MAIN TRAINING PIPELINE
# ============================================================

def main():

    print(
        "[SYSTEM] Booting High-Accuracy Hybrid Training Pipeline..."
    )


    # ========================================================
    # CHECK DATASET
    # ========================================================

    if not os.path.exists(CSV_PATH):

        print(
            f"[ERROR] Metadata file not found:\n{CSV_PATH}"
        )

        return


    if not os.path.exists(IMAGE_DIR):

        print(
            f"[ERROR] Image directory not found:\n{IMAGE_DIR}"
        )

        return


    # ========================================================
    # LOAD DATA
    # ========================================================

    df = pd.read_csv(CSV_PATH)


    print(
        f"[SYSTEM] Metadata loaded: {len(df)} records"
    )


    # Add jpg extension

    df["image_id"] = df["image_id"].apply(

        lambda x:

        f"{x}.jpg"

        if not str(x).endswith(".jpg")

        else str(x)

    )


    # ========================================================
    # FIX MISSING VALUES
    # ========================================================

    df["age"] = df["age"].fillna(

        df["age"].mean()

    )


    df["sex"] = df["sex"].fillna(

        "unknown"

    )


    df["localization"] = df["localization"].fillna(

        "unknown"

    )


    # ========================================================
    # SCALE AGE
    # ========================================================

    scaler = StandardScaler()


    df["age_scaled"] = scaler.fit_transform(

        df[["age"]]

    ).flatten()


    # ========================================================
    # ENCODE SEX
    # ========================================================

    le_sex = LabelEncoder()


    df["sex_encoded"] = le_sex.fit_transform(

        df["sex"].astype(str)

    )


    # ========================================================
    # ENCODE ANATOMY
    # ========================================================

    le_anatomy = LabelEncoder()


    df["anatomy_encoded"] = le_anatomy.fit_transform(

        df["localization"].astype(str)

    )


    # ========================================================
    # ENCODE DIAGNOSIS
    # ========================================================

    le_dx = LabelEncoder()


    df["target"] = le_dx.fit_transform(

        df["dx"]

    )


    vocab_sizes = {

        "sex": len(le_sex.classes_),

        "anatomy": len(
            le_anatomy.classes_
        )

    }


    print("\n[SYSTEM] Classes found:")


    for index, class_name in enumerate(
        le_dx.classes_
    ):

        print(

            f"  {index}: {class_name}"

        )


    # ========================================================
    # STRATIFIED SPLIT
    # ========================================================

    skf = StratifiedKFold(

        n_splits=K_FOLDS,

        shuffle=True,

        random_state=42

    )


    fold_no = 1


    for train_index, val_index in skf.split(

        df["image_id"],

        df["target"]

    ):


        print("\n")

        print("=" * 60)

        print(
            "INITIATING SINGLE FOLD"
        )

        print("=" * 60)


        # ====================================================
        # FILE PATHS
        # ====================================================

        phase1_ckpt = os.path.join(

            MODEL_DIR,

            f"fold{fold_no}_phase1.keras"

        )


        phase2_ckpt = os.path.join(

            MODEL_DIR,

            f"fold{fold_no}_phase2.keras"

        )


        best_model_path = os.path.join(

            MODEL_DIR,

            f"fold{fold_no}_best_model.keras"

        )


        final_model_path = os.path.join(

            MODEL_DIR,

            "dermosphere_model.keras"

        )


        log_path = os.path.join(

            MODEL_DIR,

            f"fold{fold_no}_training.csv"

        )


        # ====================================================
        # PREPARE DATA
        # ====================================================

        train_df_raw = df.iloc[
            train_index
        ].copy()


        val_df = df.iloc[
            val_index
        ].copy()


        train_df_balanced = (
            balance_dataframe_hybrid(
                train_df_raw
            )
        )


        print(

            f"[SYSTEM] Original training samples: "
            f"{len(train_df_raw)}"

        )


        print(

            f"[SYSTEM] Balanced training samples: "
            f"{len(train_df_balanced)}"

        )


        print(

            f"[SYSTEM] Validation samples: "
            f"{len(val_df)}"

        )


        # ====================================================
        # GENERATORS
        # ====================================================

        train_gen = MultimodalGenerator(

            train_df_balanced,

            IMAGE_DIR,

            BATCH_SIZE,

            IMG_SIZE,

            len(CLASSES),

            is_training=True

        )


        val_gen = MultimodalGenerator(

            val_df,

            IMAGE_DIR,

            BATCH_SIZE,

            IMG_SIZE,

            len(CLASSES),

            is_training=False

        )


        # ====================================================
        # IMPORTANT FIX
        # ALWAYS CREATE MODEL FIRST
        # ====================================================

        model = build_phase1_model(

            len(CLASSES),

            vocab_sizes

        )


        print(

            "\n[SUCCESS] Model architecture created."

        )


        # ====================================================
        # CHECK PREVIOUS TRAINING
        # ====================================================

        initial_epoch = 0


        if os.path.exists(log_path):

            try:

                log_df = pd.read_csv(
                    log_path
                )


                if (

                    not log_df.empty

                    and "epoch" in log_df.columns

                ):

                    initial_epoch = int(

                        log_df["epoch"].max()

                    ) + 1


                    print(

                        f"[SYSTEM] Previous training detected."

                    )


                    print(

                        f"[SYSTEM] Last completed epoch: "
                        f"{initial_epoch}"

                    )


            except Exception as e:

                print(

                    f"[WARNING] Could not read training log: {e}"

                )


        # ====================================================
        # IF TRAINING ALREADY COMPLETED
        # ====================================================

        if initial_epoch >= TOTAL_EPOCHS:


            print(

                "\n[SYSTEM] Previous training is already complete."

            )


            # Load best model

            if os.path.exists(best_model_path):

                print(

                    "[SYSTEM] Loading best saved model..."

                )


                model = tf.keras.models.load_model(

                    best_model_path,

                    compile=False

                )


            elif os.path.exists(phase2_ckpt):


                print(

                    "[SYSTEM] Loading Phase 2 model..."

                )


                model = tf.keras.models.load_model(

                    phase2_ckpt,

                    compile=False

                )


            elif os.path.exists(phase1_ckpt):


                print(

                    "[SYSTEM] Loading Phase 1 model..."

                )


                model = tf.keras.models.load_model(

                    phase1_ckpt,

                    compile=False

                )


            else:


                print(

                    "[WARNING] No saved checkpoint found."

                )


                print(

                    "[SYSTEM] Starting training from scratch."

                )


                initial_epoch = 0


        # ====================================================
        # PHASE 1
        # ====================================================

        if initial_epoch < EPOCHS_PHASE_1:


            print(

                "\n[PHASE 1] Training fusion layers..."

            )


            model = build_phase1_model(

                len(CLASSES),

                vocab_sizes

            )


            phase1_callbacks = [

                ModelCheckpoint(

                    phase1_ckpt,

                    save_best_only=False,

                    verbose=1

                ),


                CSVLogger(

                    log_path,

                    append=(initial_epoch > 0)

                )

            ]


            model.fit(

                train_gen,

                validation_data=val_gen,

                epochs=EPOCHS_PHASE_1,

                initial_epoch=initial_epoch,

                callbacks=phase1_callbacks,

                verbose=1

            )


            initial_epoch = EPOCHS_PHASE_1


        # ====================================================
        # PHASE 2
        # ====================================================

        if initial_epoch < TOTAL_EPOCHS:


            print(

                "\n[PHASE 2] Fine-tuning MobileNetV2..."

            )


            # If Phase 1 checkpoint exists,
            # load it before fine-tuning

            if os.path.exists(phase1_ckpt):


                model = tf.keras.models.load_model(

                    phase1_ckpt,

                    compile=False

                )


            model = unfreeze_for_phase2(
                model
            )


            phase2_callbacks = [

                ModelCheckpoint(

                    best_model_path,

                    monitor="val_accuracy",

                    save_best_only=True,

                    mode="max",

                    verbose=1

                ),


                ModelCheckpoint(

                    phase2_ckpt,

                    save_best_only=False,

                    verbose=1

                ),


                CSVLogger(

                    log_path,

                    append=True

                ),


                ReduceLROnPlateau(

                    monitor="val_loss",

                    factor=0.5,

                    patience=2,

                    verbose=1,

                    min_lr=1e-7

                ),


                EarlyStopping(

                    monitor="val_accuracy",

                    patience=6,

                    restore_best_weights=True,

                    verbose=1

                )

            ]


            model.fit(

                train_gen,

                validation_data=val_gen,

                epochs=TOTAL_EPOCHS,

                initial_epoch=initial_epoch,

                callbacks=phase2_callbacks,

                verbose=1

            )


        # ====================================================
        # LOAD BEST MODEL FOR EVALUATION
        # ====================================================

        print(

            "\n[SYSTEM] Loading best model for evaluation..."

        )


        if os.path.exists(best_model_path):


            model = tf.keras.models.load_model(

                best_model_path,

                compile=False

            )


            print(

                "[SUCCESS] Best validation model loaded."

            )


        elif os.path.exists(phase2_ckpt):


            model = tf.keras.models.load_model(

                phase2_ckpt,

                compile=False

            )


            print(

                "[SUCCESS] Phase 2 model loaded."

            )


        elif os.path.exists(phase1_ckpt):


            model = tf.keras.models.load_model(

                phase1_ckpt,

                compile=False

            )


            print(

                "[SUCCESS] Phase 1 model loaded."

            )


        else:


            print(

                "[WARNING] No checkpoint found. Using current model."

            )


        # ====================================================
        # EVALUATION
        # ====================================================

        (

            y_true,

            y_pred,

            accuracy,

            precision,

            recall,

            f1,

            specificity

        ) = evaluate_fold(

            model,

            val_gen

        )


        # ====================================================
        # PRINT RESULTS
        # ====================================================

        print("\n")

        print("=" * 60)

        print("FINAL MODEL PERFORMANCE")

        print("=" * 60)


        print(

            f"Accuracy     : {accuracy * 100:.2f}%"

        )


        print(

            f"Precision    : {precision:.4f}"

        )


        print(

            f"Recall       : {recall:.4f}"

        )


        print(

            f"F1 Score     : {f1:.4f}"

        )


        print(

            f"Specificity  : {specificity:.4f}"

        )


        print("=" * 60)


        # ====================================================
        # GENERATE GRAPHS
        # ====================================================

        generate_single_fold_reports(

            y_true,

            y_pred,

            accuracy,

            precision,

            recall,

            f1,

            specificity

        )


        # ====================================================
        # SAVE FINAL MODEL
        # ====================================================

        model.save(

            final_model_path

        )


        print(

            f"\n[SUCCESS] Final model saved at:\n"
            f"{final_model_path}"

        )


        # Only one fold

        break


    print(

        "\n[SYSTEM] Run complete."

    )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    main()