from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import sys
from werkzeug.utils import secure_filename

# Add current directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import our modules
import analytics

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to store uploaded file path
CURRENT_FILE = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_dataset', methods=['POST'])
def upload_dataset():
    global CURRENT_FILE
    
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Only CSV files are supported'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        CURRENT_FILE = filepath
        
        # Read and analyze
        df = pd.read_csv(filepath)
        
        # Validate required columns
        required_cols = ['date', 'product_id', 'price', 'quantity_sold']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return jsonify({
                'status': 'error', 
                'message': f'Missing required columns: {", ".join(missing_cols)}'
            }), 400
        
        # Get product list
        products = ['ALL_PRODUCTS'] + sorted(df['product_id'].unique().tolist())
        
        return jsonify({
            'status': 'success',
            'records': len(df),
            'products': products,
            'date_range': f"{df['date'].min()} to {df['date'].max()}"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/run_analysis', methods=['POST'])
def run_analysis():
    global CURRENT_FILE
    
    try:
        if not CURRENT_FILE or not os.path.exists(CURRENT_FILE):
            return jsonify({'status': 'error', 'message': 'Please upload a dataset first'}), 400
        
        # Get parameters
        product_id = request.form.get('product_id', 'ALL_PRODUCTS')
        growth_rate = float(request.form.get('growth_rate', 15))
        holding_pct = float(request.form.get('holding_pct', 20))
        ordering_cost = float(request.form.get('ordering_cost', 1500))
        
        # Validate parameters
        if growth_rate < -50 or growth_rate > 200:
            return jsonify({'status': 'error', 'message': 'Growth rate must be between -50% and 200%'}), 400
        
        if holding_pct < 0 or holding_pct > 100:
            return jsonify({'status': 'error', 'message': 'Holding cost must be between 0% and 100%'}), 400
        
        if ordering_cost < 0:
            return jsonify({'status': 'error', 'message': 'Ordering cost must be positive'}), 400
        
        # Run analysis
        result = analytics.run_full_suite(
            CURRENT_FILE, 
            product_id, 
            holding_pct, 
            ordering_cost, 
            growth_rate
        )
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'ADAPT Analytics System v3.2'})

if __name__ == '__main__':
    print("=" * 70)
    print("ADAPT Analytics System v3.2")
    print("=" * 70)
    print("Server starting on http://localhost:5000")
    print("Press CTRL+C to stop")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=5000)
