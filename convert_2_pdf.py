import os
from pathlib import Path
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import subprocess

def classify_file(file_path):
    office_extensions = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt"}
    pdf_extension = ".pdf"

    file_extension = Path(file_path).suffix.lower()

    if file_extension in office_extensions:
        return "office"
    elif file_extension == pdf_extension:
        return "pdf"
    else:
        return "txt"

def add_pdf_extension(filename):
    file_path = Path(filename)
    if file_path.name.endswith(".pdf"):
        return f"{file_path.name}"
    if file_path.name.startswith('.'):
        return f"{file_path.name[1:]}.pdf"
    else:
        return f"{file_path.name}.pdf"

def pdf_to_pdf(pdf_file, output_pdf):
    print(f"Copying to PDF: {pdf_file}")
    shutil.copy(pdf_file, output_pdf)
    print(f"PDF successfully copied: {output_pdf}")

def office_to_pdf(input_file, output_pdf):
    print(f"creating PDF: {input_file}")
    try:
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", input_file, "--outdir", output_pdf], check=True)
        print(f"Successfully converted {input_file} to {output_pdf}")
    except subprocess.CalledProcessError as e:
        print(f"Error converting file: {e}")
    print(f"PDF successfully created: {output_pdf}")

def text_to_pdf(text_file, output_pdf):
    print(f"Converting to PDF: {text_file}")
    with open(text_file, 'r', encoding='utf-8') as file:
        content = file.readlines()

    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    y_position = height - 40  # Original position on the page

    for line in content:
        if y_position < 40:  # PIf we are on the end of the page
            c.showPage()  # Creates new page
            y_position = height - 40

        c.drawString(40, y_position, line.strip())
        y_position -= 15  # Shift down

    c.save()
    print(f"PDF successfully created: {output_pdf}")

def convert_files(files, input_directory, output_pdf_root):
    delete_all_files(output_pdf_root)
    for file in files:
        path_parts = Path(file).parts[0:]
        out_file = add_pdf_extension("-".join(path_parts))
        file_type = classify_file(file)
        if file_type == "office":
            office_to_pdf(os.path.join(input_directory, file), output_pdf_root)
        elif file_type == "pdf":
            pdf_to_pdf(os.path.join(input_directory, file), os.path.join(output_pdf_root, out_file))
        else:
            text_to_pdf(os.path.join(input_directory, file), os.path.join(output_pdf_root, out_file))

def delete_all_files(directory):
    path = Path(directory)
    for file in path.glob("*"):
        if file.is_file():
            file.unlink()
            print(f"Deleted: {file}")