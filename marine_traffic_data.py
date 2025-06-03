import os
import cloudscraper
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Config
base_url = "https://www.vesselfinder.com/vessels/details/"

# REGNOS is optional/visible, so fallback is safe
vessel_list_raw = os.environ.get("VESSELS", "")
vessel_list = [i.strip() for i in vessel_list_raw.split(",") if i.strip()]

print(f"Vessel list: {vessel_list}")

if not vessel_list:
    print("No vessels found in the list environment variable.")
    exit(1)

# Initialize session
scarper = cloudscraper.create_scraper()

summary = []

for i, imonr in enumerate(vessel_list, 1):
    print(f"Processing vessel {i}: {imonr}")

    # Fetch the vessel page
    vessel_url = f"{base_url}/{imonr}"
    response = scarper.get(vessel_url)
    if response.status_code != 200:
        print(f"Failed to fetch data for {imonr}")
        summary.append([imonr, "Data fetch failed", "-", "-"])
        continue

    # Parse the page content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the required data
    try:
        # Find the destination label section
        vessel_name = soup.find('h1', class_= 'title').get_text(strip=True) if soup.find('h1', class_='title') else "Vessel info. not found."

        print(f"Vessel: {vessel_name}")

        # Find the destination section of the HTML
        if soup.find('div', class_='vi__r1 vi__sbt'):
            # Destination name
            destination = soup.find('a', class_='_npNa').get_text(strip=True) if soup.find('a', class_='_npNa') else "Destination not found."
            eta = soup.find('span', class_='_mcol12ext').get_text(strip=True).replace("ETA: ", "") if soup.find('span', class_='_mcol12ext') else "ETA not found."
        
            print(f"Destination: {destination}")
            print(f"{eta}")
        else:
            print("Destination section not found.")
        summary.append([imonr, vessel_name, destination, eta])
    except AttributeError:
        print("Vessel name not found.")
        summary.append([imonr, "Vessel name not found.", "-", "-"])

# Build HTML table
table_html = """
<table border="1" cellpadding="4" cellspacing="0">
    <tr>
        <th>IMO nr.</th>
        <th>Vessel Name</th>
        <th>Destination</th>
        <th>ETA</th>
    </tr>
"""
for row in summary:
    table_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
table_html += "</table>"

# Email setup
smtp_server = os.environ.get("SMTP_SERVER")
smtp_user = os.environ.get("SMTP_USER")
smtp_pass = os.environ.get("SMTP_PASS")
email_to = os.environ.get("EMAIL_TO")

msg = MIMEMultipart("alternative")
msg["Subject"] = "Vessel Destination Report"
msg["To"] = email_to

html_content = f"""
<html>
  <body>
    <p>Here is the daily vessel destination summary:</p>
    {table_html}
  </body>
</html>
"""
msg.attach(MIMEText(html_content, "html"))

try:
    with smtplib.SMTP_SSL(smtp_server) as server:
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, email_to, msg.as_string())
        print("Summary email sent.")
except smtplib.SMTPAuthenticationError as e:
    print(e.smtp_error.decode())
