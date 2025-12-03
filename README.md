# 🤖 AI-Powered Telegram Assistant (Gemini & Google Sheets Integration)

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram)
![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange?style=for-the-badge&logo=google)
![Google Sheets](https://img.shields.io/badge/Database-Google%20Sheets-green?style=for-the-badge&logo=google-sheets)

This project is a comprehensive Telegram Bot application that leverages **Google Gemini 2.5flash** for Natural Language Processing (NLP) and Computer Vision tasks. It utilizes **Google Sheets** as a backend cloud database for user management, quota tracking, and conversation logging.

Developed as a **Computer Engineering Sophomore Project**, this repository demonstrates API integration, cloud data management, and secure software architecture practices.

---

## 🚀 Key Features

* **🧠 Context-Aware AI Chat:** Integrated with Google Gemini API to provide natural, coherent, and context-aware responses to user queries.
* **👁️ Computer Vision Analysis:** Capable of processing user-uploaded images and generating descriptive insights using multimodal AI capabilities.
* **☁️ Cloud Database Management:** Uses Google Sheets API to manage user data, enforcing a serverless database architecture.
* **📝 Conversation Memory:** Implements a sliding window memory mechanism to retain context from previous messages.
* **📊 Quota & Access Control:** Features a robust quota system where each user has a specific message limit. The bot automatically restricts access upon limit exhaustion.
* **🎫 Dynamic Promo Codes:** Includes a `/kod` command allowing users to redeem valid promotion codes for additional message quotas.
* **🛡️ Secure Architecture:** Sensitive data (API Tokens, Credentials) are isolated using environment variables (`.env`), adhering to industry security standards.

---

## 🛠️ Installation & Setup

Follow these steps to deploy the project on your local machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/efeadil/mega-project.git](https://github.com/efeadil/mega-project.git)
cd mega-project
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Google Sheets Configuration (Database)
The project utilizes Google Sheets as a relational database. To replicate the environment:

1.  Create a new **Google Sheet**.
2.  Create **3 separate worksheets (tabs)** named exactly as shown below.
3.  Set up the column headers in the first row of each sheet:

| Worksheet Name | Description | Required Columns (Row 1) |
| :--- | :--- | :--- |
| **Sayfa1** | Stores user quotas and limits | `A: User ID` \| `B: Message Count` \| `C: Limit` |
| **Codes** | Database of valid promo codes | `A: Codes` (e.g., `promo2025`) |
| **Logs** | Chat history and audit logs | `A: Date` \| `B: ID` \| `C: Name` \| `D: Message` \| `E: Response` |

  > [!WARNING]
 > **Crucial Step – Authentication (DO NOT SKIP!)**
> 1. Open your `credentials.json` file  
> 2. Copy the email address found inside the `"client_email"` field  
> 3. In your Google Sheet, click **Share** → paste that email → set permission as **Editor**
 > Without this step the bot will have no access to the sheet and will not work at all.

---

###  🔑 Environment Variables (.env)

Adhering to security best practices, API keys and secrets are never hardcoded into the source code. You must create a file named **`.env`** in the project root directory and define the following variables:

```ini
TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
GOOGLE_GEMINI_KEY=YOUR_GEMINI_API_KEY
SPREADSHEET_NAME=Your_Google_Sheet_Name
```
---
 > [!NOTE]
> **Important Setup Note**
>
> Make sure that:
> - The Google Cloud Service Account JSON key file you downloaded is **renamed to `credentials.json`**
> - The file is placed in the **root directory** of the project (same level as `main.py` or `bot.py`)

> If the file has a different name or is in a subfolder, the bot will not find it and will fail to start.

---

## 🖥️ Usage

After completing the setup, run the bot with:

```bash
python main.py
```

When you see **`Bot working...`** in the console, the bot is up and running! 🚀

---


### Available Commands

- `/start` → Registers the user and shows the welcome message  
- `/kod [CODE]` → Redeem a promo code *(example: `/kod promo2025`)* to increase your message limit  
- **Text messages** → Start a natural conversation with the AI  
- **Photos / Images** → Activates the Computer Vision module (image analysis & description)

## 📂 Project Structure

```plaintext
📦 MegaProject
 ┣ 📜 main.py              # Main bot logic & entry point
 ┣ 📜 credentials.json     # Google Cloud Service Account key (gitignored)
 ┣ 📜 .env                 # Environment variables & API keys (gitignored)
 ┣ 📜 .gitignore           # Prevents sensitive files from being committed
 ┣ 📜 requirements.txt     # Python dependencies
 ┗ 📜 README.md            # You are here :)
```

---

## 🛡️ Security & Disclaimer

> [!IMPORTANT]
> This project is developed **exclusively for educational purposes** as part of the Computer Engineering curriculum.

- **Data Privacy**  
  Sensitive files (`.env` and `credentials.json`) are **automatically excluded** from the repository using `.gitignore` to prevent any credential leaks.

- **Data Storage**  
  All chat logs and user data are stored **only** in your private Google Sheet.  
  No data is ever sent to third parties or external servers.

---

**Developer**  
**Adil Efe**  
2ⁿᵈ Year Computer Engineering Student  

Thanks for stopping by — hope you find it useful! 🚀
