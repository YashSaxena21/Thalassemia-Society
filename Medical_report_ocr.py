import os
import pytesseract
from PIL import Image, ImageEnhance
import streamlit as st
import re
import base64

# Function to extract text from image using OCR
def extract_text_from_image(image):
    gray_image = image.convert("L")  # Convert image to grayscale
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced_image = enhancer.enhance(2)  # Increase contrast for better OCR accuracy
    text = pytesseract.image_to_string(enhanced_image, config="--psm 6")  # Extract text
    return ' '.join(text.splitlines()).strip()  # Clean up extracted text

# Function to extract patient's name from text
def extract_patient_name(text):
    match = re.search(r"(?:Name[:\-]?\s*|mr[\.]?\s*|mr\s*\.?\s*)([A-Za-z\s,]+)", text)
    if match:
        name = match.group(1).strip().replace(',', '.')  # Replace commas with periods
        name = name.upper()  # Capitalize the name
        return name
    return None

# Function to handle report file and move it to the patient's folder
def handle_report(file, destination_path):
    destination_path = destination_path.strip()
    if not os.path.isdir(destination_path):
        return "Invalid path! Please ensure the destination folder exists."
    
    image = Image.open(file)
    text_content = extract_text_from_image(image)
    
    # Extract the patient's name
    patient_name = extract_patient_name(text_content)
    if patient_name:
        folder_path = os.path.join(destination_path, patient_name)
        os.makedirs(folder_path, exist_ok=True)  # Create folder if it doesn't exist
        report_path = os.path.join(folder_path, file.name)
        with open(report_path, "wb") as f:
            f.write(file.getbuffer())  # Save the file to the folder
        return f"Report successfully saved in folder: {folder_path}"
    else:
        return "Could not extract patient's name. Please check the report format."

# Streamlit app with improved UX and design
def main():
    def image_to_base64(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()

    # Path to your local image
    image_path = r"C:\Users\yashs\Downloads\Thalassemia Society.jpg"

    # Convert the image to base64
    icon_base64 = image_to_base64(image_path)

    # Set page config with the base64 image as the icon
    st.set_page_config(page_title="Medical Report OCR", page_icon=f"data:image/jpg;base64,{icon_base64}", layout="wide")
    
    # Add an image at the top for branding or guidance
    st.image(r"C:\Users\yashs\Downloads\Thalassemia Society.jpg", caption="Medical Report OCR", width=400)


    st.title("Thalassemia Society Bareilly Medical Report Organizer")
    
    # Add some styled instructions and a brief description
    st.markdown("""
    ## Welcome to the Medical Report OCR tool!
    Upload a medical report image, and we'll automatically extract the patient's name and organize the report into a folder for you. 
    Enter a destination folder where the report will be saved.
    """)

    # File uploader for the medical report
    uploaded_file = st.file_uploader("Upload the Medical Report Image", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    # Add file preview
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Report Image", use_column_width=True)
    
    # Manual destination folder input (stylized with custom placeholder text)
    destination_folder = st.text_input("Destination Folder Path", "Enter path here (e.g., C:/Reports)", label_visibility="collapsed")
    
    # Stylish submit button with custom styles
    submit_button = st.button("Process Report", use_container_width=True)
    
    # Handle report when the button is clicked
    if submit_button and uploaded_file and destination_folder:
        with st.spinner("Processing report... Please wait."):
            result = handle_report(uploaded_file, destination_folder)
            st.success(result)  # Display success message
        
    elif submit_button:
        st.warning("Please upload a medical report and specify a destination folder.")

    # Improve the UX for error messages or empty states
    if not uploaded_file:
        st.markdown("""
        <p style="color:grey; font-size: 16px; text-align: center;">
            Upload a report to get started! Only image files (PNG, JPG) are supported.
        </p>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
