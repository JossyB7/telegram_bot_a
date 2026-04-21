import io
import os
import logging
import numpy as np
import cv2
from PIL import Image, ImageEnhance
from psd_tools import PSDImage
from rembg import remove, new_session

logger = logging.getLogger(__name__)

# Pre-load AI model for speed
session = new_session("u2netp")

def process_image_with_psd(user_image_path, psd_template_path, output_path, placeholder_name="USER_PHOTO"):
    try:
        psd = PSDImage.open(psd_template_path)
        
        # --- 1. BACKGROUND REMOVAL ---
        with open(user_image_path, "rb") as i:
            input_data = i.read()
        
        user_no_bg_bytes = remove(input_data, session=session)
        user_no_bg = Image.open(io.BytesIO(user_no_bg_bytes)).convert("RGBA")

        # --- 2. VIBRANCE & SATURATION ---
        # SATURATION: 1.4 makes colors 40% more vivid
        sat_converter = ImageEnhance.Color(user_no_bg)
        user_no_bg = sat_converter.enhance(1.4)
        
        # VIBRANCE (Simulated via Contrast/Sharpness)
        # Boosting contrast slightly makes the 'vibrance' feel stronger
        con_converter = ImageEnhance.Contrast(user_no_bg)
        user_no_bg = con_converter.enhance(1.1)

        # --- 3. AUTO-ZOOM & CENTERING ---
        placeholder = next((l for l in psd.descendants() if l.name == placeholder_name), None)
        if not placeholder:
            raise ValueError(f"Target layer '{placeholder_name}' not found.")

        left, top, right, bottom = placeholder.bbox
        target_h, target_w = bottom - top, right - left

        # --- Face detection: try to find a face so we can center the crop on it ---
        face_center_x_ratio = 0.5  # default: horizontal center
        face_center_y_ratio = 0.4  # default: slightly above vertical center (head-room heuristic)
        face_detected = False

        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)

            # Convert PIL RGBA → BGR for OpenCV
            img_array = np.array(user_no_bg.convert("RGB"))
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(
                img_gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
            )

            if len(faces) > 0:
                # Use the largest detected face (most likely the subject)
                largest = max(faces, key=lambda f: f[2] * f[3])
                fx, fy, fw, fh = largest
                face_center_x_ratio = (fx + fw / 2) / user_no_bg.width
                face_center_y_ratio = (fy + fh / 2) / user_no_bg.height
                face_detected = True
                logger.info(f"Face detected at ({fx}, {fy}, {fw}, {fh}); "
                            f"center ratio ({face_center_x_ratio:.2f}, {face_center_y_ratio:.2f})")
            else:
                logger.info("No face detected; falling back to aspect-ratio-preserving resize.")
        except Exception as e:
            logger.warning(f"Face detection failed ({e}); falling back to aspect-ratio-preserving resize.")

        if face_detected:
            # Scale the image so it fills the entire layer (cover, not contain)
            src_w, src_h = user_no_bg.width, user_no_bg.height
            scale = max(target_w / src_w, target_h / src_h)
            scaled_w = int(src_w * scale)
            scaled_h = int(src_h * scale)
            user_scaled = user_no_bg.resize((scaled_w, scaled_h), Image.LANCZOS)

            # Determine crop origin so the face center lands at the layer center
            face_px_x = face_center_x_ratio * scaled_w
            face_px_y = face_center_y_ratio * scaled_h

            crop_x = int(face_px_x - target_w / 2)
            crop_y = int(face_px_y - target_h / 2)

            # Clamp so we never crop outside the scaled image
            crop_x = max(0, min(crop_x, scaled_w - target_w))
            crop_y = max(0, min(crop_y, scaled_h - target_h))

            user_resized = user_scaled.crop((crop_x, crop_y, crop_x + target_w, crop_y + target_h))
            paste_x = left
            paste_y = top
        else:
            # Fallback: aspect-ratio-preserving resize (original behaviour)
            aspect = user_no_bg.width / user_no_bg.height
            new_h = target_h
            new_w = int(new_h * aspect)
            user_resized = user_no_bg.resize((new_w, new_h), Image.LANCZOS)
            paste_x = left + (target_w - new_w) // 2
            paste_y = top

        # --- 4. FINAL COMPOSITING ---
        final_canvas = Image.new("RGBA", psd.size, (0, 0, 0, 0))
        
        for layer in psd:
            if not layer.is_visible():
                continue

            if layer.name == placeholder_name:
                # Place the user photo behind the template frame
                final_canvas.alpha_composite(user_resized, (paste_x, paste_y))
                
            try:
                layer_img = layer.composite().convert("RGBA")
                final_canvas.alpha_composite(layer_img, layer.offset)
            except Exception as e:
                logger.warning(f"Skipping layer {layer.name}: {e}")

        # Save result as high-quality JPEG
        final_canvas.convert("RGB").save(output_path, "JPEG", quality=95, optimize=True)
        return output_path

    except Exception as e:
        logger.error(f"Error: {e}")
        raise e
