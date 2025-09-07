# Enhanced PDF Extraction with OCR Setup

This document explains how to set up OCR capabilities for enhanced PDF text extraction.

## Overview

The system now has two methods for extracting text from PDFs:

1. **Direct Text Extraction** (pdfplumber) - Fast, works for text-based PDFs
2. **OCR Fallback** (Tesseract + pytesseract) - Slower, works for image-based or scanned PDFs

## Installation Steps

### 1. Install Python Packages

The OCR-related packages are already added to `requirements.txt`:

```bash
pip install pytesseract Pillow pdf2image
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR Binary

#### Windows:
1. Download Tesseract installer from: https://github.com/tesseract-ocr/tesseract/wiki
2. Install to default location (usually `C:\Program Files\Tesseract-OCR\`)
3. Add to PATH or configure pytesseract path in code

#### macOS:
```bash
brew install tesseract
```

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### 3. Configure Tesseract Path (Windows Only)

If Tesseract is not in PATH, you can configure it in the code:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## How It Works

### Extraction Process Flow

1. **Try Direct Text Extraction** using pdfplumber
   - Fast and efficient for text-based PDFs
   - Works for most modern PDF documents

2. **Fallback to OCR** if:
   - Direct extraction fails completely
   - Less than 50 characters extracted (likely image-based PDF)

3. **OCR Process**:
   - Convert PDF pages to images using pdf2image
   - Apply Tesseract OCR to extract text from images
   - Process first 3 pages only for performance

4. **OpenAI Processing**:
   - Pass extracted text (from either method) to OpenAI
   - Extract MRN and DOB using AI analysis

### Log Output Examples

**Direct Text Extraction Success:**
```
INFO - Extracted 1247 characters of text from PDF using pdfplumber
```

**OCR Fallback Used:**
```
INFO - Direct text extraction failed or insufficient. Attempting OCR...
INFO - Performing OCR on page 1
INFO - OCR extracted 856 characters
INFO - Extracted 856 characters of text from PDF using OCR
```

## Testing OCR Setup

Run the test script to verify OCR setup:

```bash
python test_enhanced_pdf_extraction.py
```

This will:
- Check if OCR libraries are available
- Verify Tesseract installation
- Test PDF extraction with a real patient document

## Performance Considerations

- **pdfplumber**: Very fast (~0.1-0.5 seconds)
- **OCR**: Slower (~2-10 seconds depending on PDF complexity)
- **Memory**: OCR uses more memory for image processing

## Troubleshooting

### Common Issues

1. **"pytesseract not found"**
   - Install: `pip install pytesseract`

2. **"Tesseract not installed"**
   - Install Tesseract binary (see installation steps above)

3. **"TesseractNotFoundError"**
   - Add Tesseract to PATH or configure path in code

4. **OCR returns poor results**
   - PDF may have poor image quality
   - Consider adjusting OCR settings or preprocessing images

### Fallback Behavior

If OCR libraries are not available:
- System logs warning message
- Falls back to direct text extraction only
- No functional impact - just no OCR fallback capability

## Configuration

The OCR fallback is automatic and requires no configuration. The system will:
- Always try direct text extraction first
- Only use OCR when needed
- Log which method was successful
- Include extraction method in results

## Benefits

With OCR fallback, the system can now handle:
- Scanned PDF documents
- Image-based PDFs
- PDFs with embedded images containing text
- Documents where direct text extraction fails

This significantly improves the robustness of MRN and DOB extraction from medical documents.
