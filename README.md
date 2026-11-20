# AutoPay Watcher AI

## 1. Project Overview

[TODO: Complete Project Overview]

## 2. Project Features

| **Feature** | **Description** |
|---|---|
| **Email Upload and Dashboard** | [TODO – Member 1 - Complete Description] |
| **AI Information Extraction** | Uses the OpenAI API to analyze subscription emails and extract important details, including subscription name, price, billing frequency, renewal date and cancellation terms, into JSON format. |
| **Data Validation and Cancellation Calculations** | [TODO – Member 3 - Complete Description ] |
| **Calendar Reminders** | [TODO – Member 4 - Complete Description] |

## 3. Installation and Setup

### Prerequisites

Before installing and running AutoPay Watcher AI, ensure the following are available:

- **Python 3:** Required to run the application and install its dependencies. [Download Python](https://www.python.org/downloads/).
- **Git:** Used to clone the project repository from GitHub. [Download Git](https://git-scm.com/downloads/).
- **OpenAI API Key:** Required for AI-powered extraction of subscription information from emails. Obtain a key from the [OpenAI Platform](https://platform.openai.com/api-keys).

Verify Python and Git installations:

```bash
python --version
git --version
```

**1. Clone the repository:**

```bash
git clone https://github.com/JP2061/AutoPay-Watcher-AI.git
cd AutoPay-Watcher-AI
```

**2. Create a virtual environment:**

```bash
python -m venv .venv
```

**3. Activate the virtual environment** (choose your operating system):

> **Windows (PowerShell)**
> ```powershell
> .\.venv\Scripts\Activate.ps1
> ```
>
> **macOS/Linux**
> ```bash
> source .venv/bin/activate
> ```

**4. Install dependencies:**

```bash
python -m pip install -r requirements.txt
```

**5. Configure the API key:**\
Create a copy of `.env.example` named `.env` and replace the placeholder with your OpenAI API key:

```dotenv
OPENAI_API_KEY=your_api_key_here
```

Keep the `.env` file and API credentials private. The project’s `.gitignore` prevents Git from tracking `.env`.

## 4. Run the Prototype

### Required Project Files

These files are included in the cloned repository; no separate downloads are needed.

| File | Purpose |
|---|---|
| `AutoPay Watcher AI.py` | Main Streamlit application |
| `dashboard_ui.py` | Dashboard and email upload interface |
| `autopay_core.py` | Email and subscription database operations |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment configuration template |
| `samples/` and `tests/` | Sample emails and automated tests |

Keep the Python files in their repository locations so their imports work.

### Start the Application (from the repository root)

```bash
python -m streamlit run "AutoPay Watcher AI.py"
```

Once Streamlit launches, the application opens in your browser (usually at `http://localhost:8501`), displaying **Dashboard** under **Application Mode** with the **Overview** page selected by default.

To reproduce the main workflow:

1. While in **Dashboard** application mode, **select Email inbox** from the left sidebar. In the main dashboard area on the right, **select Upload emails**, **choose** `samples/sample_email_1.eml` or another sample email from the `samples/` folder, and **click Import selected emails**. If an email has already been imported, the duplicate will be skipped and will not be added to the database again.
2. While in **Email inbox**, under **Saved emails**, **choose an email to inspect** from the dropdown menu and review its contents.
3. Then, scroll down to **Analyze selected email with team AI** and **click the button** to extract subscription information from the selected email.
4. Review the extracted JSON and subscription details, then **click Save reviewed AI result to dashboard**.
5. To verify the extracted JSON fields and view their validation results, **switch Application Mode to AI Extraction Test** in the left sidebar. From the **Saved Emails** dropdown menu, **select the previously imported email** or another email stored in the database to test. Then review **Parsed Email Content**, **Extracted Subscription Information** (JSON), **Validation Messages**, and **Recommended Cancellation Date**.
6. In the **left sidebar**, under **Application Mode**, **select Dashboard**. Then, under the dashboard navigation, **select Overview** to view the saved subscription. You can also **select Manage records** to edit its details.

**Note:** AI extraction uses the OpenAI API and may incur usage charges when testing the application.

## 5. Technical Documentation

See [Technical Documentation](docs/technical_documentation.md) for architecture, implementation, AI integration, testing, team responsibilities, limitations, and remaining work.
