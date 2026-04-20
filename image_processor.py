import io
import os
import logging
from PIL import Image
from psd_tools import PSDImage
from rembg import remove, new_session

logger = logging.getLogger(__name__)

# GLOBAL SESSION: This keeps the AI "Filter" loaded in RAM 
# so it doesn't have to re-download/reload every time.
session = new_session("u2netp")

def process_image_with_psd(user_image_path, psd_template_path, output_path, placeholder_name="USER_PHOTO"):
    """
    Handles AI Background removal, Auto-Zoom, and PSD Layer Compositing.
    """
    try:
        psd = PSDImage.open(psd_template_path)
        
        # --- FUNCTIONALITY 1: THE FILTER (Background Removal) ---
        with open(user_image_path, "rb") as i:
            input_data = i.read()
        
        # Remove background using the pre-loaded AI session
        user_no_bg_bytes = remove(input_data, session=session)
        user_no_bg = Image.open(io.BytesIO(user_no_bg_bytes)).convert("RGBA")

        # Find the target layer in your PSD
        placeholder = next((l for l in psd.descendants() if l.name == placeholder_name), None)
        if not placeholder:
            raise ValueError(f"Target layer '{placeholder_name}' not found in PSD.")

        # --- FUNCTIONALITY 2: THE ZOOM & CENTER ---
        left, top, right, bottom = placeholder.bbox
        target_h, target_w = bottom - top, right - left

        # Calculate aspect ratio to prevent stretching
        aspect = user_no_bg.width / user_no_bg.height
        new_h = target_h
        new_w = int(new_h * aspect)
        
        # High-quality resize (The "Zoom")
        user_resized = user_no_bg.resize((new_w, new_h), Image.LANCZOS)
        
        # Center horizontally within the placeholder area
        paste_x = left + (target_w - new_w) // 2

        # --- FINAL ASSEMBLY ---
        final_canvas = Image.new("RGBA", psd.size, (0, 0, 0, 0))
        
        for layer in psd:
            if layer.name == placeholder_name:
                # Place the user photo
                final_canvas.alpha_composite(user_resized, (paste_x, top))
                # Re-overlay the frame/arch to hide rough edges
                final_canvas.alpha_composite(layer.composite().convert("RGBA"), layer.offset)
                continue
                
            if layer.is_visible():
                layer_img = layer.composite().convert("RGBA")
                final_canvas.alpha_composite(layer_img, layer.offset)

        # Save as high-quality JPEG to keep file size small for Telegram
        final_canvas.convert("RGB").save(output_path, "JPEG", quality=95, optimize=True)
        return output_path

    except Exception as e:
        logger.error(f"Error in image_processor: {e}")
        raise e     raise e
