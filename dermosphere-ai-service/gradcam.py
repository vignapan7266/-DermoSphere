import cv2
import numpy as np
import tensorflow as tf

def generate_gradcam_heatmap(model, img_array, original_img_path, output_path, layer_name="Conv_1"):
    """
    Computes Grad-CAM activations for the top predicted category and generates an overlay file.
    """
    # 1. Isolate the final convolutional layer and the prediction top layers
    grad_model = tf.keras.models.Model(
        inputs=[model.inputs],
        outputs=[model.get_layer(layer_name).output, model.output]
    )
    
    # 2. Track gradients using the tape context manager
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        top_pred_index = tf.argmax(predictions[0])
        loss_value = predictions[:, top_pred_index]
        
    # 3. Extract the structural gradients relative to the final convolutional feature maps
    grads = tape.gradient(loss_value, conv_outputs)
    
    # 4. Compute mean intensity values across spatial feature maps
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # 5. Calculate weighted combinations of the spatial channels
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    
    # 6. Normalize the heatmap matrix using a ReLU operation
    heatmap = tf.maximum(heatmap, 0) / tf.reduce_max(heatmap)
    heatmap = heatmap.numpy()
    
    # 7. Format the structural heatmap overlay via OpenCV
    orig_img = cv2.imread(original_img_path)
    if orig_img is None:
        raise FileNotFoundError(f"Original image asset missing at: {original_img_path}")
        
    height, width, _ = orig_img.shape
    
    # Resize spatial dimensions to scale perfectly with original file sizes
    resized_heatmap = cv2.resize(heatmap, (width, height))
    
    # Quantize floating-point array to an 8-bit unsigned integer grid
    resized_heatmap = np.uint8(255 * resized_heatmap)
    
    # Colorize the raw intensity matrix into a Jet lookup map configuration
    colorized_heatmap = cv2.applyColorMap(resized_heatmap, cv2.COLORMAP_JET)
    
    # Superimpose the visual heatmap directly onto the clinical sample
    alpha = 0.4
    blended_output = cv2.addWeighted(colorized_heatmap, alpha, orig_img, 1.0 - alpha, 0)
    
    # Write the annotated graphic array to the microservice disk architecture
    cv2.imwrite(output_path, blended_output)
    return output_path