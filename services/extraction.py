import pdfplumber
from io import BytesIO
from fastapi import UploadFile


def extract_text_from_pdf(pdf_file: UploadFile) -> str:
    """
    Extracts text (including tables) from uploaded PDF file.
    Skips low-content pages and preserves table structure.
    """

    text = []

    try:
        file_bytes = pdf_file.file.read()
        pdf_stream = BytesIO(file_bytes)

        with pdfplumber.open(pdf_stream) as pdf:
            for i, page in enumerate(pdf.pages):
                
                page_text = page.extract_text(layout=True) or page.extract_text() or ""

                if len(page_text.strip()) < 50:
                    continue

                tables = page.extract_tables()
                table_str_list = []

                for table in tables:
                    if not table:
                        continue

                    safe_table = [
                        " | ".join(
                            str(cell).strip() if cell is not None else ""
                            for cell in row
                        )
                        for row in table
                        if any(cell is not None and str(cell).strip() for cell in row)
                    ]

                    if safe_table:
                        table_str = "\n".join(safe_table)
                        table_str_list.append(
                            f"\n\n[Table on Page {i+1}]\n{table_str}\n[End of Table]\n\n"
                        )

                text.append(page_text.strip())
                text.extend(table_str_list)

        full_text = "\n\n".join(text)

        return full_text

    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return ""