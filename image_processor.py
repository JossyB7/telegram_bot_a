import io
import os
import logging
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

        # Calculate best fit (Preserving Aspect Ratio)
        aspect = user_no_bg.width / user_no_bg.height
        
        # Smart Fit: Adjust based on whether the photo is portrait or landscape
        new_h = target_h
        new_w = int(new_h * aspect)
        
        # High-quality resize
        user_resized = user_no_bg.resize((new_w, new_h), Image.LANCZOS)
        
        # Horizontal Centering
        paste_x = left + (target_w - new_w) // 2

        # --- 4. FINAL COMPOSITING ---
        final_canvas = Image.new("RGBA", psd.size, (0, 0, 0, 0))
        
        for layer in psd:
            if not layer.is_visible():
                continue

            if layer.name == placeholder_name:
                # Place the user photo behind the template frame
                final_canvas.alpha_composite(user_resized, (paste_x, top))
                continue
                
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
