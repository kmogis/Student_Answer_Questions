import numpy as np

# Monkey-patch np.Inf if it's missing
if not hasattr(np, 'Inf'):
    np.Inf = np.inf

import os
import sqlite3
import qrcode
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template, request, redirect, g, send_file

# Initialize the Flask app
app = Flask(__name__)

# Database path (use an absolute path for deployment)
DATABASE = os.path.join(os.path.dirname(__file__), 'responses.db')

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
        try:
            db.execute("INSERT INTO questions (question_text, qr_code_link) VALUES (?, ?)",
                       ("Select the correct answer", "/static/qr_1.png"))
            db.commit()
        except sqlite3.IntegrityError:
            print("Sample data already exists, skipping insertion.")

@app.route('/answer/<int:question_id>', methods=['GET', 'POST'])
def answer_question(question_id):
    if request.method == 'POST':
        try:
            student_id = request.form['student_id']
            response_text = request.form['response_text']
            db = get_db()
            db.execute("INSERT INTO responses (student_id, question_id, response_text) VALUES (?, ?, ?)",
                       (student_id, question_id, response_text))
            db.commit()
            return redirect(f'/thank-you/{question_id}')
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "An error occurred while submitting your response. Please try again.", 500

    db = get_db()
    question = db.execute("SELECT question_text FROM questions WHERE question_id = ?", (question_id,)).fetchone()
    if question:
        return render_template('answer_form.html', question=question[0], question_id=question_id)
    else:
        return "Question not found", 404

# @app.route('/thank-you/<int:question_id>')
# def thank_you(question_id=1):
#     return "<h1>Thank you for your submission!</h1><p>Your response has been recorded.</p>"
    
@app.route('/generate-qr/<int:question_id>')
def generate_qr(question_id=1):
    try:
        base_url = request.host_url.rstrip('/')
        qr_url = f"{base_url}/answer/{question_id}"

        qr = qrcode.make(qr_url)
        img_io = io.BytesIO()
        qr.save(img_io, format='PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return f"An error occurred while generating the QR code: {e}"

@app.route('/thank-you/<int:question_id>')
def thank_you(question_id=1):
    try:
        db = get_db()
        responses = db.execute("SELECT response_text, COUNT(*) as count FROM responses WHERE question_id = ? GROUP BY response_text", (question_id,)).fetchall()

        # Prepare data for the pie chart
        labels = [row[0] for row in responses]
        sizes = [row[1] for row in responses]

        # Replace np.inf and np.Inf with 0 explicitly
        sizes = [0 if size == float('Inf') or np.isinf(size) or np.isnan(size) else size for size in sizes]

        # Check if sizes are valid (all zero sizes would not create a meaningful pie chart)
        if not any(sizes):
            return "No valid data to display in the pie chart."

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
    except Exception as e:
        return f"An error occurred while displaying the results: {e}"

if __name__ == '__main__':
    try:
        init_db()  # Run this once to create the tables
        insert_sample_data()  # Run this once to insert sample data
        app.run(host='0.0.0.0', port=5000)  # Listen on all network interfaces for deployment
    except Exception as e:
        print(f"An error occurred during app startup: {e}")
