
from flask import Flask, render_template, request, redirect
import csv
from datetime import datetime

app = Flask(__name__)

def load_bill_data():
    data = {}
    with open('bills.csv', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data[row['admission_no'].lower()] = row  # 🔁 Convert to lowercase
    return data


def record_payment(details):
    with open('payments.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            details['name'],
            details['admission_no'],
            details['old_room'],
            details['new_room'],
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

if __name__ == '__main__':
    app.run(debug=True)
