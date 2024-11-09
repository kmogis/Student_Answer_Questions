import sqlite3
import qrcode
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template, request, redirect, g, send_file
# Initialize the Flask app
app = Flask(__name__)

# Database path
DATABASE = 'responses.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Close the database connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def insert_sample_data():
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO questions (question_text, qr_code_link) VALUES (?, ?)",
                   ("When is your birthday?", "/static/qr_1.png"))
        db.commit()
        
@app.route('/generate-all-qr')
def generate_all_qr():
    db = get_db()
    questions = db.execute("SELECT question_id FROM questions").fetchall()

    for question in questions:
        question_id = question[0]
        base_url = "http://127.0.0.1:5001"  # Replace with your deployed app URL if needed
        qr_url = f"{base_url}/answer/{question_id}"

        qr = qrcode.make(qr_url)
        qr_file_path = f"static/qr_{question_id}.png"
        qr.save(qr_file_path)
        print(f"QR code for question {question_id} generated and saved at {qr_file_path}")

    return "QR codes for all questions generated and saved in the static folder."

# Route to display the answer form
@app.route('/generate-qr/<int:question_id>')
def generate_qr(question_id=1):
    try:
        base_url = "http://127.0.0.1:5001"  # Replace this with your deployed app URL if needed
        qr_url = f"{base_url}/answer/{question_id}"

        # Generate the QR code
        qr = qrcode.make(qr_url)
        qr_file_path = f"static/qr_{question_id}.png"
        qr.save(qr_file_path)
        return f"QR code for question {question_id} generated and saved at {qr_file_path}. Use this image in your slides."
    except Exception as e:
        return f"An error occurred while generating the QR code: {e}"
    
# Route to view all responses
@app.route('/responses')
def view_responses():
    db = get_db()
    responses = db.execute("SELECT * FROM responses").fetchall()
    return render_template('responses.html', responses=responses)

@app.route('/thank-you/<int:question_id>')
def thank_you(question_id=1):  # Use a dynamic question ID if needed
    db = get_db()
    # Get the count of each response text for a specific question
    responses = db.execute("SELECT response_text, COUNT(*) as count FROM responses WHERE question_id = ? GROUP BY response_text", (question_id,)).fetchall()

    # Prepare data for the pie chart
    labels = [row[0] for row in responses]
    sizes = [row[1] for row in responses]

    # Create the pie chart
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f'Poll Results for Question {question_id}')
    plt.axis('equal')

    # Save the chart as an image in memory and encode it in base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    # Encode the image as a base64 string to embed in the HTML
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    return render_template('thank_you.html', img_data=img_base64)
        
if __name__ == '__main__':
    init_db()  # Run this once to create the tables
    insert_sample_data()  # Run this once to insert sample data
    app.run(port=5001)  # Use a different port, e.g., 5001