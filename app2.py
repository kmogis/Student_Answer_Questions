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

    return render_template('answer_form.html', question_id=question_id)
