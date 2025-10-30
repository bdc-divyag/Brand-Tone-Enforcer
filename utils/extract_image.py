import easyocr
import base64
import io
from PIL import Image

def extract_from_image(file_path):
    """Extract text and return (text, base64_image) using EasyOCR."""
    reader = easyocr.Reader(['en'], gpu=False)  # set gpu=True if available
    results = reader.readtext(file_path, detail=0)
    text = "\n".join(results)

    # Convert image to base64
    image = Image.open(file_path)
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    return text, img_b64
