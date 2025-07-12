<div align="center">
    
# Version 1.0
    
# 👻 Ghost Core OSINT Tool

![Ghost Core Banner](https://s14.gifyu.com/images/bK9B8.png)

**Coming soon:** In the next Version 1.1 update I will be adding...

* **Auto Clicker:** A utility to automate mouse clicks, allowing for repetitive tasks to be performed efficiently.

* **Port Scanner:** A tool to identify open ports on a target IP address, providing insights into potential network vulnerabilities (passive scanning only, no active exploitation).

* **Email Tracker:** Integrates with public breach databases to check if an email address has been compromised in known data breaches.

</div>

<div align="center">

#

# 📸 Screenshots

<img width="1920" height="1048" alt="1" src="https://github.com/user-attachments/assets/762f678e-2fb8-44b0-b041-4bba24996e51" />

#


<img width="1920" height="1046" alt="2" src="https://github.com/user-attachments/assets/0c413e24-b706-4e46-a1a2-e45e3ad96a30" />

#


<img width="1920" height="1048" alt="3" src="https://github.com/user-attachments/assets/773fee72-a439-496f-860d-c53705d1b180" />

#


<img width="1917" height="1050" alt="4" src="https://github.com/user-attachments/assets/2f928c63-78cd-459b-8c3a-15e241446e46" />

#


<img width="1920" height="1049" alt="5" src="https://github.com/user-attachments/assets/d4c7e622-2d04-42af-9435-8d168c66117d" />

</div>

#

Ghost Core is a sophisticated Open-Source Intelligence (OSINT) tool designed to assist in gathering publicly available information from various online sources. Built with Python and PyQt6, it provides a sleek, intuitive graphical user interface (GUI) for performing tasks such as IP tracking, phone number analysis, username reconnaissance across social media, and simulated vehicle information lookups.

## ✨ Features

Ghost Core is equipped with several powerful modules, each designed to extract specific types of public information:

### 🌐 IP Tracker
This module allows you to gather detailed geographical and network information about any public IP address. It aggregates data from multiple reputable IP lookup APIs to provide a comprehensive overview.

* **Geographical Data:** City, Region, Country, Continent, Latitude, Longitude.
* **Network Information:** ISP (Internet Service Provider), Organization (ORG), ASN (Autonomous System Number), Domain.
* **Timezone Details:** Timezone ID, Abbreviation, DST status, UTC offset, Current Time.
* **Mapping Integration:** Provides a direct link to Google Maps for visual location pinpointing.
* **Aggregated Results:** Combines data from `ipwho.is`, `ip-api.com`, `ipapi.co`, and `freegeoip.app` for robust results and a "Best Judgment" summary.

### 📞 Phone Number Tracker
Leveraging the `phonenumbers` library, this module helps in analyzing international phone numbers to extract carrier, location, and formatting details.

* **Basic Information:** Location description, Region Code, Timezone, and Operator/Carrier name.
* **Validity & Core Details:** Checks if the number is valid and possible, extracts country code and national number.
* **Number Type Identification:** Determines if the number is mobile, fixed-line, toll-free, premium rate, VoIP, etc.
* **Number Formats:** Provides the number in International, E.164, National, Mobile Dialing, and RFC3966 formats.
* **Best Judgment:** Consolidates key information into a concise summary.

### 👤 Username Tracker
This module performs reconnaissance across a vast array of social media platforms and websites to determine if a given username is in use. It uses concurrent requests to quickly check hundreds of sites.

* **Extensive Site List:** Checks over 300 popular social media, gaming, development, and niche platforms.
* **Concurrent Scanning:** Utilizes multi-threading to speed up the search process.
* **Clear Status Indication:** Differentiates between "Username Found" (with URL) and "Username not found" for each site.
* **Progress Bar:** Provides real-time feedback on the scanning progress.

### 📶 WiFi Grabber (Windows Only)
The WiFi Grabber module is designed to retrieve saved Wi-Fi network names (SSIDs) and their corresponding passwords from a Windows operating system.

**IMPORTANT DISCLAIMER:** This feature is **only compatible with Windows operating systems** and may require **Administrator privileges** to function correctly. Use this feature responsibly and only on systems you are authorized to access. Misuse of this tool may have legal consequences.

* **Lists Saved Profiles:** Displays all Wi-Fi profiles saved on the system.
* **Retrieves Passwords:** Attempts to extract the "Key Content" (password) for each profile.
* **Error Handling:** Provides informative messages if admin privileges are required or if an error occurs.

## ⚠️ Disclaimers

* **Ethical Use:** Ghost Core is an OSINT tool intended for legal and ethical information gathering from publicly available sources. The developer is not responsible for any misuse of this software.
* **Data Accuracy:** While efforts are made to use reliable sources, the accuracy and completeness of data retrieved via external APIs cannot be guaranteed.
* **API Limitations:** External APIs may have rate limits, usage restrictions, or may change their endpoints, which could affect the functionality of the tool.
* **WiFi Grabber:** This module is **Windows-specific** and may require **Administrator privileges**. Use with caution and only on authorized systems.

## 🛠️ Installation

To run Ghost Core, you need Python 3 and the specified libraries.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/Ghost-Core.git](https://github.com/your-username/Ghost-Core.git)
    cd Ghost-Core
    ```
    *(Replace `your-username` with your actual GitHub username if you fork it)*

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install PyQt6 requests phonenumbers
    ```

## 🚀 Usage

To start Ghost Core, navigate to the project directory in your terminal and run:

```bash
python main.py
```
(Assuming your main script file is named main.py)
### Navigating the Application:
* Use the navigation panel on the left to switch between different OSINT modules (Show Your IP, IP Tracker, Phone Number Tracker, Username Tracker, WiFi Grabber, Exit).
* Click on an item in the navigation list or use the Right Arrow key to focus on the input/action area of the selected module.
* Press Enter or Return on input fields to trigger the associated action.
### Module Specific Instructions:
* Show Your IP: Click "Get My IP" to display your public IP address. Once displayed, the button changes to "Copy IP" to copy it to your clipboard.
* IP Tracker: Enter any public IP address (e.g., 8.8.8.8) into the input field and click "Track IP".
* Phone Number Tracker: Enter a phone number, including the international country code (e.g., +12125551234), and click "Track Phone Number".
* Username Tracker: Enter a username (e.g., astro) into the input field and click "Track Username". The progress bar will indicate the scanning progress.
* WiFi Grabber: Read and check the disclaimer checkbox, then click "Scan Wi-Fi Passwords". Remember this is Windows-only and may require admin rights.
## 🤝 Contributing
Contributions are welcome! If you have suggestions for improvements, new features, or bug fixes, please feel free to:

1.  Fork the repository.
2.  Create a new branch (git checkout -b feature/YourFeatureName).
3.  Make your changes.
4.  Commit your changes (git commit -m 'Add new feature').
5.  Push to the branch (git push origin feature/YourFeatureName).
6.  Open a Pull Request.
