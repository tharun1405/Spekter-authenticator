from flask import Flask, render_template, request, redirect, url_for, flash
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = 'supersecretkey'  # Required for flash messages

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.String(8), nullable=False, unique=True)
    filename = db.Column(db.String(120), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_id():
    last_upload = Upload.query.order_by(Upload.id.desc()).first()
    if last_upload:
        last_id = int(last_upload.photo_id[4:])
        new_id = last_id + 4
    else:
        new_id = 0
    return f'spkt{new_id:04}'  # Ensure the total length is 4 characters

@app.route('/')
def index():
    return redirect(url_for('verification'))

@app.route('/verification')
def verification():
    return render_template('verification.html')

@app.route('/verify', methods=['POST'])
def verify():
    verification_code = request.form['verification_code']
    if verification_code == '123456':  # Example verification code
        return redirect(url_for('upload'))
    else:
        flash('Invalid verification code. Please try again.')
        return redirect(url_for('verification'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = None
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
        elif 'camera_file' in request.files and request.files['camera_file'].filename != '':
            file = request.files['camera_file']

        if file and allowed_file(file.filename):
            photo_id = generate_id()
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{photo_id}_{filename}")
            file.save(file_path)

            # Save the file information to the database
            new_upload = Upload(photo_id=photo_id, filename=f"{photo_id}_{filename}")
            db.session.add(new_upload)
            db.session.commit()

            return redirect(url_for('upload_success', photo_id=photo_id))
        else:
            flash('No selected file or invalid file type')
            return redirect(request.url)

    return render_template('upload.html')

@app.route('/success/<photo_id>')
def upload_success(photo_id):
    upload = Upload.query.filter_by(photo_id=photo_id).first_or_404()
    file_path = url_for('static', filename=f"uploads/{upload.filename}")
    return render_template('upload_success.html', photo_id=photo_id, file_path=file_path)

@app.route('/display/<photo_id>')
def display_photo(photo_id):
    upload = Upload.query.filter_by(photo_id=photo_id).first()
    if upload:
        file_path = url_for('static', filename=f"uploads/{upload.filename}")
        return render_template('display.html', photo_id=photo_id, file_path=file_path)
    else:
        flash('Photo ID not found. Please try again.')
        return redirect(url_for('search_page'))

@app.route('/search', methods=['POST'])
def search_photos():
    photo_id = request.form['search_id']
    return redirect(url_for('display_photo', photo_id=photo_id))

@app.route('/search_page')
def search_page():
    return render_template('search.html')

@app.route('/photos/<photo_id>', methods=['GET', 'POST'])
def display_photos(photo_id):
    if request.method == 'POST':
        username = request.form['username']
        return f"Hello, {username}! Here are the photos with ID: {photo_id}"
    return render_template('username_verification.html')

if __name__ == "__main__":
    # Ensure the database and table exist
    with app.app_context():
        db.create_all()
    app.run(debug=True)

