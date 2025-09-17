#before adding email and schedule functionality
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os, shutil
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'supersecretkey'

FOLDER_TO_BACKUP = "data_to_backup"
OUTPUT_FOLDER = "backups"
BUCKET_NAME = "my-mtech-backup-bucket"  # 🔁 Replace with your bucket
REGION = "ap-south-1"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'jpg', 'png', 'docx'}

os.makedirs(FOLDER_TO_BACKUP, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"backup_{timestamp}.zip"
    zip_path = os.path.join(OUTPUT_FOLDER, zip_name)
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', FOLDER_TO_BACKUP)

    s3 = boto3.client('s3', region_name=REGION)
    s3.upload_file(zip_path, BUCKET_NAME, f"backups/{zip_name}")
    return zip_name

def list_backups():
    return sorted(os.listdir(OUTPUT_FOLDER), reverse=True)

def list_uploaded_files():
    return sorted(os.listdir(FOLDER_TO_BACKUP))

def list_s3_files():
    s3 = boto3.client('s3', region_name=REGION)
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        return [obj['Key'] for obj in response.get('Contents', [])]
    except ClientError as e:
        print("Error:", e)
        return []

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('❌ No file selected')
        elif not allowed_file(file.filename):
            flash('❌ Invalid file type')
        else:
            filepath = os.path.join(FOLDER_TO_BACKUP, file.filename)
            file.save(filepath)
            flash(f'✅ File "{file.filename}" uploaded successfully!')
        return redirect(url_for('home'))

    backups = list_backups()
    return render_template("index.html", backups=backups)

@app.route('/backup')
def backup():
    zip_file = create_backup()
    flash(f'☁️ Backup {zip_file} created and uploaded to S3!')
    return redirect(url_for('home'))

@app.route('/uploads')
def uploads():
    files = list_uploaded_files()
    return render_template("uploads.html", files=files)

@app.route('/s3-files')
def s3_files():
    files = list_s3_files()
    return render_template("s3_files.html", files=files)

@app.route('/s3-download/<path:filename>')
def s3_download(filename):
    s3 = boto3.client('s3', region_name=REGION)
    download_path = os.path.join("downloads", os.path.basename(filename))
    os.makedirs("downloads", exist_ok=True)
    try:
        s3.download_file(BUCKET_NAME, filename, download_path)
        return send_file(download_path, as_attachment=True)
    except ClientError as e:
        flash("❌ Error downloading file from S3.")
        return redirect(url_for('s3_files'))

@app.route('/s3-delete/<path:filename>')
def s3_delete(filename):
    s3 = boto3.client('s3', region_name=REGION)
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
        flash(f'🗑️ File "{filename}" deleted from S3!')
    except ClientError as e:
        flash("❌ Failed to delete file from S3.")
    return redirect(url_for('s3_files'))

if __name__ == "__main__":
    app.run(debug=True)



# #after adding backup and schedule functionality
# from flask import Flask, render_template, request, redirect, url_for, flash, send_file
# import os, shutil, threading, time, schedule, smtplib
# from datetime import datetime
# import boto3
# from botocore.exceptions import ClientError
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

# app = Flask(__name__)
# app.secret_key = 'supersecretkey'

# FOLDER_TO_BACKUP = "data_to_backup"
# OUTPUT_FOLDER = "backups"
# BUCKET_NAME = "my-mtech-backup-bucket"   # Replace with your bucket
# REGION = "ap-south-1"
# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv', 'jpg', 'png', 'docx'}

# # Email config
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# SENDER_EMAIL = "youremail@gmail.com"       # Replace
# SENDER_PASSWORD = "yourpassword"       # Use App Password (not Gmail password!)
# ADMIN_EMAIL = "youremail@gmail.com"       # Replacesame as senderemail

# os.makedirs(FOLDER_TO_BACKUP, exist_ok=True)
# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# # To store user-selected backup time
# scheduled_time = None

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def send_email_notification(zip_name, files_backed_up):
#     """Send an email when backup is done"""
#     try:
#         msg = MIMEMultipart()
#         msg['From'] = SENDER_EMAIL
#         msg['To'] = ADMIN_EMAIL
#         msg['Subject'] = f"✅ Backup Successful - {zip_name}"

#         body = f"""
#         Hello Admin,

#         The backup process was successful.

#         Backup File: {zip_name}
#         Files Included:
#         {chr(10).join(files_backed_up)}

#         Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
#         Location: AWS S3 Bucket - {BUCKET_NAME}/backups/

#         Regards,
#         Automated Backup Scheduler
#         """

#         msg.attach(MIMEText(body, 'plain'))

#         server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
#         server.starttls()
#         server.login(SENDER_EMAIL, SENDER_PASSWORD)
#         server.sendmail(SENDER_EMAIL, ADMIN_EMAIL, msg.as_string())
#         server.quit()
#         print("📧 Email sent successfully")
#     except Exception as e:
#         print("❌ Failed to send email:", e)

# def create_backup():
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     zip_name = f"backup_{timestamp}.zip"
#     zip_path = os.path.join(OUTPUT_FOLDER, zip_name)
#     shutil.make_archive(zip_path.replace('.zip', ''), 'zip', FOLDER_TO_BACKUP)

#     s3 = boto3.client('s3', region_name=REGION)
#     s3.upload_file(zip_path, BUCKET_NAME, f"backups/{zip_name}")

#     files = os.listdir(FOLDER_TO_BACKUP)
#     send_email_notification(zip_name, files)
#     return zip_name

# def list_backups():
#     return sorted(os.listdir(OUTPUT_FOLDER), reverse=True)

# def list_uploaded_files():
#     return sorted(os.listdir(FOLDER_TO_BACKUP))

# def list_s3_files():
#     s3 = boto3.client('s3', region_name=REGION)
#     try:
#         response = s3.list_objects_v2(Bucket=BUCKET_NAME)
#         return [obj['Key'] for obj in response.get('Contents', [])]
#     except ClientError as e:
#         print("Error:", e)
#         return []

# # ---------------- Scheduler Thread ----------------
# def run_scheduler():
#     while True:
#         schedule.run_pending()
#         time.sleep(1)

# # Start scheduler thread
# threading.Thread(target=run_scheduler, daemon=True).start()

# # ---------------- Flask Routes ----------------
# @app.route('/', methods=['GET', 'POST'])
# def home():
#     global scheduled_time
#     if request.method == 'POST':
#         if "file" in request.files:
#             file = request.files.get('file')
#             if not file or file.filename == '':
#                 flash('❌ No file selected')
#             elif not allowed_file(file.filename):
#                 flash('❌ Invalid file type')
#             else:
#                 filepath = os.path.join(FOLDER_TO_BACKUP, file.filename)
#                 file.save(filepath)
#                 flash(f'✅ File "{file.filename}" uploaded successfully!')
#         elif "backup_time" in request.form:  # Set schedule
#             scheduled_time = request.form["backup_time"]
#             schedule.clear()  # Clear old jobs
#             schedule.every().day.at(scheduled_time).do(create_backup)
#             flash(f"⏰ Daily backup scheduled at {scheduled_time}")
#         return redirect(url_for('home'))

#     backups = list_backups()
#     return render_template("index.html", backups=backups, scheduled_time=scheduled_time)

# @app.route('/backup')
# def backup():
#     zip_file = create_backup()
#     flash(f'☁️ Backup {zip_file} created, uploaded to S3, and email sent!')
#     return redirect(url_for('home'))

# @app.route('/uploads')
# def uploads():
#     files = list_uploaded_files()
#     return render_template("uploads.html", files=files)

# @app.route('/s3-files')
# def s3_files():
#     files = list_s3_files()
#     return render_template("s3_files.html", files=files)

# @app.route('/s3-download/<path:filename>')
# def s3_download(filename):
#     s3 = boto3.client('s3', region_name=REGION)
#     download_path = os.path.join("downloads", os.path.basename(filename))
#     os.makedirs("downloads", exist_ok=True)
#     try:
#         s3.download_file(BUCKET_NAME, filename, download_path)
#         return send_file(download_path, as_attachment=True)
#     except ClientError:
#         flash("❌ Error downloading file from S3.")
#         return redirect(url_for('s3_files'))

# @app.route('/s3-delete/<path:filename>')
# def s3_delete(filename):
#     s3 = boto3.client('s3', region_name=REGION)
#     try:
#         s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
#         flash(f'🗑️ File "{filename}" deleted from S3!')
#     except ClientError:
#         flash("❌ Failed to delete file from S3.")
#     return redirect(url_for('s3_files'))

# if __name__ == "__main__":
#     app.run(debug=True)
