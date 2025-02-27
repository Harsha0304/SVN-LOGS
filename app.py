from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import csv
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Define the output CSV file path
CSV_FILE = "svn_log.csv"


@app.route("/")
def index():
    """Render the homepage."""
    return render_template("index.html")


@app.route("/process_svn_log", methods=["POST"])
def process_svn_log():
    """Fetch SVN logs, process them, and generate a CSV file."""
    data = request.json
    svn_url = data.get("svn_url")

    if not svn_url:
        return jsonify({"status": "error", "message": "SVN URL is required!"})

    try:
        # Run SVN log command and get output in XML format
        svn_command = ["svn", "log", svn_url, "--xml", "-v", "--quiet", "-r", "HEAD:1"]
        result = subprocess.run(svn_command, capture_output=True, text=True, check=True)
        log_data = result.stdout

        # Parse the XML response from SVN
        root = ET.fromstring(log_data)

        # Extract log entries
        logs = []
        for log_entry in root.findall("logentry"):
            revision = log_entry.get("revision")
            author = log_entry.findtext("author", default="Unknown")
            date = log_entry.findtext("date", default="Unknown")

            logs.append([revision, author, date])

        # Save logs to a CSV file
        with open(CSV_FILE, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Revision", "Author", "Date"])
            csv_writer.writerows(logs)

        return jsonify({"status": "success", "file_url": f"/download/{CSV_FILE}"})

    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"SVN command failed: {e}"})

    except ET.ParseError:
        return jsonify({"status": "error", "message": "Failed to parse SVN log output"})


@app.route("/download/<filename>")
def download_file(filename):
    """Allow users to download the generated CSV file."""
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found!", 404


if __name__ == "__main__":
    app.run(debug=True)
