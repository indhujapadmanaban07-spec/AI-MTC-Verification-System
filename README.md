# AI-Based Material Test Certificate (MTC) Intelligent Verification System

## 📌 Project Overview
This project is an AI-powered solution designed to automate the validation and authentication of Material Test Certificates (MTC). Developed for the **SREC INNOVATE 2026 Industrial Hackathon & Project Expo**, this system aims to mitigate the risks of document forgery, human error, and manual delays in industrial supply chains.

By leveraging Artificial Intelligence, the system ingests MTC documents, extracts critical data points, and intelligently verifies the information against predefined standards to flag anomalies.

## ✨ Key Features
*   **Automated Document Processing:** Parses complex MTC documents to extract key material properties and specifications.
*   **Intelligent Verification:** Cross-references extracted data against valid standards to detect inconsistencies or potential forgery.
*   **Modular Architecture:** Includes dedicated modules for Error Level Analysis (ELA) detection, database management, and automated email notifications.

## 🛠️ Tech Stack & Architecture
*   **Language:** Python
*   **AI / Document Analysis:** *[Insert e.g., Tesseract, OpenCV, Scikit-learn]*
*   **Backend/Database:** *[Insert e.g., SQLite, Flask]*
*   **Project Structure:**
    *   `app/` - Main application logic
    *   `ela_detector/` - Image forensics and manipulation detection
    *   `extractor/` - Document parsing and data extraction
    *   `database/` - Data storage and management
    *   `email_service/` - Automated alerts and reporting

## 🚀 How It Works
1.  **Input:** The user uploads a Material Test Certificate (PDF/Image).
2.  **Extraction:** The system utilizes OCR and processing pipelines to extract text and tabular data.
3.  **Analysis:** AI models analyze the extracted data and check for structural/document anomalies (like image tampering using ELA).
4.  **Output:** The system generates a verification report flagging any suspicious or non-compliant data.

## 🏆 Acknowledgements
*   **Event:** SREC INNOVATE 2026 Industrial Hackathon & Project Expo
*   **Institution:** Sri Ramakrishna Engineering College, Coimbatore
*   **Mentor:** Dr. N. Saranya, AP/IT

## 👥 Author
*   **Indhuja P** (Information Technology)
