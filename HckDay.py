from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
import traceback

# Import your existing scripts
# Assuming these are importable modules; adjust the imports as needed
from text_extractor import process_invoices
import buckets
from condb import DB
from bson import ObjectId
import datetime

def safe_json(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json(i) for i in obj]
    return obj

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/process_invoice', methods=['POST'])
def process_invoice():
    # Check if file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    try:
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the invoice using your existing scripts
        # 1. Extract data
        extracted_data = process_invoices(filename, "whatarethosehackuta", folder= app.config['UPLOAD_FOLDER'])
        
        # 2. Classify data
        key = buckets.get_api_key()
        prompt = buckets.create_invoice_dictionary_prompt(extracted_data)
        classified_data = buckets.generate_gemini_content(prompt,key)
        
        # 3. Upload to MongoDB
        d = DB()
        upload_result = d.insert_invoice(classified_data)
        
        # Optionally remove the file after processing
        os.remove(filepath)
        
        # Return results
        return jsonify({"message": "Invoice processed successfully"}), 200

    
    except Exception as e:
        # Log the error
        error_details = traceback.format_exc()
        print(f"Error processing invoice: {error_details}")
        
        # Clean up - remove file if it exists
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({
            'status': 'error',
            'message': f'Error processing invoice: {str(e)}',
        }), 500

    # Add a health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # In production, you would use a proper WSGI server like gunicorn
    app.run(debug=True, host='0.0.0.0', port=5000)