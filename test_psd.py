from psd_tools import PSDImage
import os

try:
    psd = PSDImage.open('psd_templates/template.psd')
    print(f"PSD loaded successfully!")
    print(f"Dimensions: {psd.size}")
    
    # Count all layers
    all_layers = list(psd.descendants())
    print(f"Total layers: {len(all_layers)}")
    
    # Find USER_PHOTO layer
    user_photo_found = False
    for layer in all_layers:
        if layer.name == "USER_PHOTO":
            print(f"Found USER_PHOTO layer: {layer.name}")
            print(f"Type: {type(layer).__name__}")
            print(f"Visible: {layer.is_visible()}")
            if hasattr(layer, 'bbox'):
                print(f"Bbox: {layer.bbox}")
            user_photo_found = True
            break
    
    if not user_photo_found:
        print("USER_PHOTO layer not found!")
        print("\nAll layer names:")
        for i, layer in enumerate(all_layers):
            print(f"{i+1:2d}. '{layer.name}' - {type(layer).__name__}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
