import os
import base64

def encode_image_to_base64(image_path):
    with open(image_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
        ext = os.path.splitext(image_path)[1].lstrip('.')
        return f"data:image/{ext};base64,{encoded}"
