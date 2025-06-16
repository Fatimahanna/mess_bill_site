from flask import Flask, render_template, request, redirect, session, url_for, send_file
import csv
from datetime import datetime
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here'  # Replace with a strong key

def load_bill_data():
    data = {}
    with open('bills.csv', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data[row['admission_no'].lower()] = row
    return data

def record_payment(details):
    try:
        with open('payments.csv', 'r', newline='') as file:
            existing_rows = list(csv.reader(file))
            sl_no = len(existing_rows)
    except FileNotFoundError:
        sl_no = 0

    with open('payments.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            sl_no + 1,
            details['old_room'],
            details['new_room'],
            details['name'],
            details['admission_no'],
            details['bill_amount'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bill', methods=['POST'])
def bill():
    admission_no = request.form['admission_no'].lower()
    data = load_bill_data()
    if admission_no in data:
        student = data[admission_no]
        upi_link = f"upi://pay?pa=yourupi@bank&pn=MessPayment&am={student['bill_amount']}&cu=INR"
        return render_template('bill.html', student=student, upi_link=upi_link)
    else:
        return "Admission number not found."

@app.route('/confirm', methods=['POST'])
def confirm():
    student = {
        'name': request.form['name'],
        'admission_no': request.form['admission_no'],
        'old_room': request.form['old_room'],
        'new_room': request.form['new_room'],
        'bill_amount': request.form['bill_amount']
    }
    record_payment(student)
    return render_template('confirm.html', name=student['name'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['admin'] = True
            return redirect('/paid')
        else:
            return "Invalid login", 401
    return render_template('login.html')

@app.route('/paid')
def paid():
    if not session.get('admin'):
        return redirect('/login')

    paid = []
    total = 0
    try:
        with open('payments.csv', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                paid.append(row)
                total += float(row[5])
    except FileNotFoundError:
        pass

    return render_template('paid.html', paid=paid, total_amount=total)

@app.route('/unpaid')
def unpaid():
    if not session.get('admin'):
        return redirect('/login')

    bill_data = load_bill_data()
    paid_admission_nos = set()

    try:
        with open('payments.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 5:
                    paid_admission_nos.add(row[4].strip().lower())
    except FileNotFoundError:
        pass

    unpaid_list = [row for row in bill_data.values() if row['admission_no'].lower() not in paid_admission_nos]
    return render_template('unpaid.html', unpaid=unpaid_list)

@app.route('/download/paid')
def download_paid():
    if not session.get('admin'):
        return redirect('/login')

    rows = []
    try:
        with open('payments.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        pass

    df = pd.DataFrame(rows, columns=["SL NO", "Old Room", "New Room", "Name", "Admission No", "Amount", "Timestamp"])
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return send_file(output, download_name="paid_students.xlsx", as_attachment=True)

@app.route('/download/unpaid')
def download_unpaid():
    if not session.get('admin'):
        return redirect('/login')

    bill_data = load_bill_data()
    paid_nos = set()

    try:
        with open('payments.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 5:
                    paid_nos.add(row[4].strip().lower())
    except FileNotFoundError:
        pass

    unpaid = [row for row in bill_data.values() if row['admission_no'].lower() not in paid_nos]
    df = pd.DataFrame(unpaid)
    df.columns = [col.title().replace("_", " ") for col in df.columns]

    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return send_file(output, download_name="unpaid_students.xlsx", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
