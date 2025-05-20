
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import tempfile
import docx
import pandas as pd
import pdfplumber

app = Flask(__name__)
CORS(app)

openai.api_key = 'your-openai-api-key'

def read_pdf(file_path):
    text = ''
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + '\n'
    return text

def read_docx(file_path):
    doc = docx.Document(file_path)
    return '\n'.join([p.text for p in doc.paragraphs])

def read_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        return df.to_string()
    except Exception as e:
        return f"Error reading Excel: {str(e)}"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    suffix = os.path.splitext(file.filename)[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        file.save(temp_file.name)
        if suffix == '.pdf':
            content = read_pdf(temp_file.name)
        elif suffix == '.docx':
            content = read_docx(temp_file.name)
        elif suffix in ['.xls', '.xlsx']:
            content = read_excel(temp_file.name)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

    # Call OpenAI GPT model
    prompt = f"Extract key audit-relevant insights from this document:\n{content[:3000]}"
    try:
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "system", "content": "You are a senior auditor reviewing client documents."},
                {"role": "user", "content": prompt}
            ]
        )
        summary = response['choices'][0]['message']['content']
    except Exception as e:
        summary = f"OpenAI error: {str(e)}"

    return jsonify({'summary': summary})

if __name__ == '__main__':
    app.run(debug=True)
