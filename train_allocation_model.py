# train_allocation_model.py (minimal template—adapt to your actual features/labels)
from pathlib import Path
import tensorflow as tf
import numpy as np

# TODO: replace with your real dataset loading
X = np.random.rand(2000, 16).astype("float32")   # features
y = np.random.rand(2000, 4).astype("float32")    # allocation vector or score(s)

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(X.shape[1],)),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dense(y.shape[1], activation="linear"),
])
model.compile(optimizer="adam", loss="mse")
model.fit(X, y, epochs=10, batch_size=32, validation_split=0.1)

outdir = Path(__file__).resolve().parent / "models"
outdir.mkdir(exist_ok=True)
# Preferred: Keras v3 format
model.save(outdir / "allocation_model.keras")
print("Saved:", outdir / "allocation_model.keras")
