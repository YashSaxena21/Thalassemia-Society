import os
import re
import pytesseract
from PIL import Image, ImageEnhance
import streamlit as st
from pdf2image import convert_from_path
import pdfplumber
import tempfile
import base64

# Function to handle Streamlit's UploadedFile for pdf2image or pdfplumber
def handle_uploaded_file(uploaded_file):
    # Save to a temporary file and return its path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.read())
        temp_file_path = temp_file.name
    return temp_file_path

# Function to extract text from an image
def extract_text_from_image(image):
    gray_image = image.convert("L")  # Convert image to grayscale
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced_image = enhancer.enhance(2)  # Increase contrast for better OCR accuracy
    text = pytesseract.image_to_string(enhanced_image, config="--psm 6")  # Extract text
    return ' '.join(text.splitlines()).strip()  # Clean up extracted text

# Function to extract text from the first page of a PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    temp_path = handle_uploaded_file(pdf_file)  # Convert UploadedFile to a file path
    try:
        # Use pdfplumber for structured text extraction from the first page
        with pdfplumber.open(temp_path) as pdf:
            first_page = pdf.pages[0]  # Extract only the first page
            text = first_page.extract_text() or ""
    except Exception as e:
        print("Error using pdfplumber:", e)

    # If no text extracted, fallback to OCR on the first page
    if not text.strip():
        text = extract_text_from_first_page_with_ocr(temp_path)
    return text.strip()

# Fallback: Extract text from the first page of a scanned PDF using OCR
def extract_text_from_first_page_with_ocr(pdf_file_path):
    text = ""
    images = convert_from_path(pdf_file_path, first_page=1, last_page=1)  # Convert only the first page to an image
    for image in images:
        text += extract_text_from_image(image) + "\n"  # Apply OCR to the first page
    return text

# Enhanced function to extract only the patient's name

def extract_patient_name(text):
    # Clean and normalize text
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
    print("Cleaned Text for Debugging:", text)  # Debugging: Print cleaned text

    # Enhanced regex for capturing the full name
    match = re.search(
        r"(?:NAME|Name)\s*[:\-]?\s*(?:MR\.?|MRS\.?)?\s*([A-Z][a-z]*\s+[A-Z][a-z]*)",
        text,
        re.IGNORECASE,
    )
    
    if match:
        name = match.group(1).strip()
        print("Matched Name:", name)  # Debugging: Log the matched name
        
        # Remove unnecessary words like "MR.", "MRS.", "Lab No.", etc.
        name = remove_unnecessary_words(name)
        print("Cleaned Name:", name)  # Debugging: Log the cleaned name
        
        return name.title()  # Convert to Title Case
    print("No Match Found in Text")  # Debugging: Log failure
    return None


def remove_unnecessary_words(name):
    # List of words or terms to be removed from the name
    unnecessary_words = ["MR.", "MRS.", "DR.", "LAB", "BILLING", "AGE", "SEX", "P. ID", "REFERRED", "REPORT"]
    
    # Loop through each term in the unnecessary_words list and remove it if it exists in the name
    for word in unnecessary_words:
        name = re.sub(rf"\b{word}\b", "", name, flags=re.IGNORECASE).strip()
    
    # Clean up any extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name

#r"(?:NAME|Name)\s*[:\-]?\s*(?:MR\.?|MRS\.?)?\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\s*(?=\s*(?:Billing Date|Age|Sex|P\. ID|Lab|,|:))"
#r"(?:NAME|Name)\s*[:\-]?\s*(?:MR\.?|MRS\.?)?\s*([A-Z]+(?:\s+[A-Z]+)?)\s*(?=\s(BILLING DATE|AGE|SEX|,|:))"
# Function to handle file uploads and save to the correct folder
def handle_report(file, file_type, destination_path):
    destination_path = destination_path.strip()
    if not os.path.isdir(destination_path):
        return "Invalid path! Please ensure the destination folder exists."

    # Extract text based on file type
    if file_type == "pdf":
        text_content = extract_text_from_pdf(file)
    else:
        return "Unsupported file type."

    # Extract patient's name
    patient_name = extract_patient_name(text_content)
    if patient_name:
        folder_path = os.path.join(destination_path, patient_name)
        os.makedirs(folder_path, exist_ok=True)  # Create folder if it doesn't exist
        report_path = os.path.join(folder_path, file.name)
        with open(report_path, "wb") as f:
            f.write(file.getbuffer())  # Save the file to the folder
        return f"Report successfully saved in folder: {folder_path}"
    else:
        return "Could not extract the patient's name. Please check the report format."

# Streamlit app
def main():
    def image_to_base64(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()

    # Path to your local image
    image_path = "Thalassemia_Society.jpg"

    # Convert the image to base64
    icon_base64 = image_to_base64(image_path)

    # Set page config with the base64 image as the icon
    st.set_page_config(page_title="Medical Report OCR", page_icon=f"data:image/jpg;base64,{icon_base64}", layout="wide")
    
    # Add an image at the top for branding or guidance
    st.image("Thalassemia_Society.jpg", caption="Medical Report OCR", width=400)
    st.title("Thalassemia Society Bareilly Medical Report Organizer")
    st.markdown("""
    ## Welcome to the Medical Report OCR tool!
    Upload a medical report (PDF), and we'll automatically extract the patient's name and organize the report into a folder for you.
    """)

    # File uploader for medical reports
    uploaded_file = st.file_uploader("Upload a Medical Report (PDF)", type=["pdf"])
    file_type = None

    if uploaded_file:
        # Determine file type
        st.info("PDF file uploaded successfully.")
        file_type = "pdf"

    # Destination folder input
    destination_folder = st.text_input("Destination Folder Path", placeholder="Enter path here (e.g., C:/Reports)")

    # Submit button
    if st.button("Process Report"):
        if uploaded_file and destination_folder:
            with st.spinner("Processing report..."):
                result = handle_report(uploaded_file, file_type, destination_folder)
                st.success(result)
        else:
            st.warning("Please upload a file and specify a destination folder.")

if __name__ == "__main__":
    main()
