import pdf2image
from PIL import Image
import pytesseract


def extract_text_from_scanned_pdf():
    pdf_path = "file.pdf"
    images = pdf2image.convert_from_path(pdf_path)

    text = ""
    for image in images:
        # image = images[0]
        # Extract text from each image
        text += pytesseract.image_to_string(image)

    return text


def temp_save_txt(txt, savepath="temp.txt"):
    with open(savepath, "w") as file:
        file.write(txt)


extracted_text = extract_text_from_scanned_pdf()
