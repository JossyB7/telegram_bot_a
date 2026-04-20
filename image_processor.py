import io
import logging
from PIL import Image
from psd_tools import PSDImage
from rembg import remove, new_session  # Added new_session

logger = logging.getLogger(__name__)

# Initialize a global session with the small model to save RAM
# This only downloads the model once and keeps it in memory efficiently.
session = new_session("u2netp")


def process_image_with_psd(user_image_path, psd_template_path, output_path, placeholder_name="USER_PHOTO"):
    """
    Refined logic for the right-side arch design with RAM optimization.
    """
    try:
        # Load PSD and setup canvas
        psd = PSDImage.open(psd_template_path)
        canvas_size = psd.size

        # Background Removal using the optimized session
        with open(user_image_path, "rb") as i:
            input_data = i.read()

        # We pass the pre-loaded session here to avoid reloading the model
        user_no_bg_bytes = remove(input_data, session=session)
        user_no_bg = Image.open(io.BytesIO(user_no_bg_bytes)).convert("RGBA")

        # Find the USER_PHOTO placeholder layer
        placeholder = next((l for l in psd.descendants() if l.name == placeholder_name), None)
        if not placeholder:
            available = [l.name for l in psd.descendants()]
            raise ValueError(f"Layer '{placeholder_name}' not found. Available: {available}")

        # Get coordinates for placement
        left, top, right, bottom = placeholder.bbox
        target_h, target_w = bottom - top, right - left

        # Scale and Center the User photo
        aspect = user_no_bg.width / user_no_bg.height
        new_h = target_h
        new_w = int(new_h * aspect)
        user_resized = user_no_bg.resize((new_w, new_h), Image.LANCZOS)
        paste_x = left + (target_w - new_w) // 2

        # Initialize the final flyer canvas
        final_canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

        # Start the bottom-to-top stacking loop
        for layer in psd:
            if layer.name == placeholder_name:
                # Step A: Paste the user
                final_canvas.alpha_composite(user_resized, (paste_x, top))

                # Step B: Re-draw the arch frame over the user
                arch_pixels = layer.composite().convert("RGBA")
                final_canvas.alpha_composite(arch_pixels, layer.offset)
                continue

            if layer.is_visible():
                # Render groups like 'Text' and 'Adjustments'
                # composite() ensures Amharic fonts render correctly
                layer_img = layer.composite().convert("RGBA")
                final_canvas.alpha_composite(layer_img, layer.offset)

        # Export as high-quality JPEG
        final_canvas.convert("RGB").save(output_path, "JPEG", quality=95, optimize=True)
        return output_path

    except Exception as e:
        logger.error(f"Error in image processing: {str(e)}")
        raise e
