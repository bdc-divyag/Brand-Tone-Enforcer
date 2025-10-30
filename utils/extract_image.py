from PIL import Image
import pytesseract
import base64
import io
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
def extract_from_image(file_path):
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    return text, img_b64
