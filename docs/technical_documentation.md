### AutoPay Watcher AI – Technical Documentation
This document describes the application's architecture, implementation, testing, and development progress.

## 1. System Architecture
***Application Workflow:***

**Set Up Streamlit Application & Dashboard**\
Create the Python web interface for\
subscription email input and management\
↓\
**Implement Email Upload (.eml)**\
Allow users to manually upload subscription emails in .eml format\
(Optional Gmail syncing if time allows)\
↓\
**Email Parsing**\
Use Python to read the uploaded .eml files\
and extract the email text needed for analysis\
↓\
**AI Information Extraction**\
Use OpenAI API and LLM to\
extract subscription details into JSON\
↓\
**Data Validation**\
Use Python to check JSON data for missing\
or invalid subscription details\
↓\
**Display & Review Subscription Information**\
Show AI-extracted details in Streamlit\
for user review and correction\
*(Optional Feature)\
↓\
**Calculate Recommended Cancellation Date (Safety Buffer)**\
Use Python to calculate cancellation dates\
from AI-extracted JSON data with a safety buffer\
↓\
**Display Final Subscription Information**\
(Free Trials & Active Subscriptions)\
Use Python to organize all trials & subscriptions by expiration\
and renewal dates, then display the subscription details and\
recommended cancellation dates in the Streamlit Dashboard\
↓\
**Generate & Download .ics Calendar Reminder**\
Import cancellation dates into calendar applications\
↓\
**End-to-End Testing**\
Verify complete application workflow

## 2. Development Environment and Main Files

### Technologies Used

- **Python:** Reads uploaded emails, processes extracted information, and supports cancellation-date calculations.
- **Streamlit:** Provides the web application for uploading emails, testing AI extraction, and viewing subscriptions in the dashboard.
- **OpenAI API and LLM:** Analyze email text and return subscription details in JSON format. An LLM helps interpret different wording used in billing and cancellation policies.
- **SQLite:** Stores imported emails and subscription records for later review.
- **Git and GitHub:** Manage the project code and allow team members to collaborate.


### Main Files

- **`AutoPay Watcher AI.py`:** Starts the Streamlit application and connects the main user-facing features. It provides access to the dashboard and AI extraction testing so users can move between uploading an email, reviewing AI output, and viewing subscription records.
- **`dashboard_ui.py`:** Contains the Streamlit dashboard interface for importing and viewing saved emails and managing subscription records. It handles how information is presented to users rather than performing the LLM extraction itself.
- **`autopay_core.py`:** Supports email storage and database operations using SQLite. It helps keep imported emails and subscription information available for later selection, analysis, and review.
- **`requirements.txt`:** Lists the Python packages the application needs so the same dependencies can be installed in another environment.
- **`.env.example`:** Shows which environment variable is needed for the OpenAI API key without including a real credential. The actual key belongs in a private `.env` file.
- **`samples/` and `tests/`:** Hold sample subscription emails and test code used to check extraction and application behavior without relying on private user emails.

## 3. Code Implementation

### Email Upload and Streamlit Dashboard – Member 1

- **Functions:** [Member 1: Add function names.]
- **Code explanation:** [Member 1: Explain how email upload, saved emails, and dashboard views work.]
- **Implementation status:** [Member 1: Completed / planned / tested.]

### AI Extraction and Email Parsing – Joshua Peng

**Function names**
- `extract_subscription(email_content, client)` — Sends the email text to the OpenAI API and converts the returned JSON into a Python dictionary. This JSON parsing is different from reading an `.eml` file.
- `parse_email()` — Initially used to open sample `.eml` files and extract plain-text email content for standalone AI testing. It is not called in the current integrated workflow.

**Code explanation and implementation**
- The OpenAI API receives the parsed email text and extraction prompt. The AI returns JSON containing the subscription name, price, billing frequency, renewal date, and cancellation terms. Missing or unclear values are requested as `null` rather than guessed.
- The prompt was updated to handle free trials, cancellation notices, and cancellation-notice amounts and units (such as 24 hours or several days). Cleanup was also added for Markdown code fences before parsing the JSON response.
- We use an LLM because companies describe renewal dates and cancellation policies differently. Python passes the extracted information to the separate validation and cancellation-date component. The dashboard-specific extraction integration was completed by the validation teammate.
- The `parse_email()` function was initially created to open `.eml` files and extract plain-text email content for testing the AI extraction component before integrating it with the dashboard. After integration, `main()` was modified to use the email content already parsed and stored in the SQLite database. The `initialize_database()` and `list_emails()` functions are used to access saved emails, a Streamlit selection box allows users to choose an email, and `get_email()` retrieves the selected record. The `selected_email["body_text"]` field contains the previously parsed email text, which is passed directly to `extract_subscription()` for AI analysis. This allows AI Extraction Test mode to use emails uploaded through the dashboard without parsing them again. After the OpenAI API returns JSON, the separate validation component processes the results for cancellation-date calculations and dashboard integration.
- **Model and prompt:** GPT-6 Luna [TODO: link directly to the extraction function.]
- **Limitation:** The AI can misread unclear prices, dates, or policies, so the output should be checked against the original email.

Implementation status
- **Completed/updated:** Initial standalone `.eml` parsing for testing, database-based retrieval of already-parsed email text in `main()`, OpenAI extraction, JSON response parsing, and prompt improvements for missing details, free trials, and cancellation notices.
- **Integration/testing:** The extraction is accessible through the application's **AI Extraction Test** view using saved emails.

### Data Validation and Cancellation Calculations – Triet Nguyen

**Functions:** 
- `valid_number()` — Check if a value is a finite, nonnegative integer or float.
- `validate_subscription()` — Receive extracted data as a dictionary, then check for required fields, valid data types, missing information. Call valid_number(value) when checking values.
- `calculate_cancellation_date()` — Receive extracted cancellation data and a safety buffer. Calculate the recommended cancellation date if possible, using given buffer. 
- `extract_for_dashboard()` — Call AI extraction, calculate the recommended cancellation date, and add the date and explanation notes to the extracted dictionary while preserving the existing notes.

**Code explanation:**
- The function `validate_subscription()` takes in the extracted data, and checks if it's a python dictionary. Then it proceeds to check the rest of the information. Checks for missing fields, correct data types. Name, billing cycle, cancellation policy must be nonempty strings. Price and cancellation notice amount must be finite, nonnegative numbers. Renewal date must be a valid date in the format Month DD, YYYY. Cancellation notice unit must be hours, days, weeks, or months. For months, the notice amount must be a whole number. Calls function `valid_number()` when checking values. It then returns a list of strings describing the issues, or an empty list if there are none. These messages are displayed through Streamlit by `main()` in AI Extraction Test mode and `render_mail_upload()` in Dashboard mode.
- The function `calculate_cancellation_date()` takes in the extracted data and a safety buffer that is default to 1 day. First, it double-check if the required data is valid. The function subtracts the required notice period from the renewal date by hours, days, weeks using timedelta. For months it uses a separate calculation, which account for different month lengths and leap years. Then it subtracts the additional safety buffer amount from the calculated notice day. Returns the recommended date and `None` for error on success, returns `None` for recommended date and an error message on failure. Invalid calculation dates, data will return error message instead of a guessed date.
- The function `extract_for_dashboard()` takes in the email's text and the openAI client. Calls the extraction function `extract_subscription()` and receives a python dictionary. Then it calls `calculate_cancellation_date()` using the extracted data, and receives a recommended date or an error message. The recommended date is stored in `cancellation_deadline`, or `None` if calculation fails. The function adds notes explaining the calculation, safety buffer, a warning if recommended date has passed, or the error messages to the existing notes and returns the updated dictionary. In `main()`, this function is passed to dashboard as the extraction callback, which will be called when the user requests analysis.

- **Implementation status:**
- Completed: Data validation, cancellation calculations, dashboard integration are implemented. Supports different cancellation notice units (hours, days, weeks, months, with 1 day safety buffer). Calculated dates are recommendations and may require user review.
- Tested: Validation and calculations were tested with sample emails with valid and invalid inputs. Dashboard integration testing show that validation messages, recommended dates, and calculation notes appear in the right sections.
- Planned: Change text format, colors to improve date visibility. Correct remaining grammar and spacing issues.

### Calendar Reminder Generation – Member 4

- **Functions:** [Member 4: Add function names.]
- **Code explanation:** [Member 4: Explain `.ics` reminder generation and download.]
- **Implementation status:** [Member 4: Completed / planned / tested.]

## 4. Testing and Reproducibility

We test with `.eml` subscription emails containing different renewal dates and cancellation requirements, including 24-hour, 48-hour, and multi-day notices. We compare the AI-extracted name, price, renewal date, and cancellation terms with the original email. We also check Python's recommended cancellation date against the stated policy and safety buffer.

To reproduce a sample result, import `samples/sample_email_1.eml`, run AI extraction, inspect JSON and validation messages in **AI Extraction Test**, and view the saved subscription in **Dashboard → Overview**.

### Sample test result

| Item | Result |
|---|---|
| Input | `samples/sample_email_1.eml` |
| Expected | Email text, extracted subscription JSON, validation feedback, and a recommended cancellation date when enough information is available. |
| Actual AI extraction | [Enter the extracted subscription name, price, renewal date, and cancellation terms.] |
| Actual date calculation | [Enter the recommended date, or explain why it could not be calculated.] |
| Comparison with source | [Record which values matched the email and any errors.] |
| Test status | [Passed / Failed / Not yet verified] |

Additional checks: Re-import the same email to verify duplicate handling. If test dependencies are installed, run `python -m pytest -v` and record **[number passed / failed]**. Do not report a test as passed without an observed result.

## 5. Technical Limitations

Some emails omit important billing or cancellation details, and the LLM may interpret unclear wording incorrectly. The prototype uses manually uploaded `.eml` files rather than direct Gmail syncing. OpenAI API access requires a valid key and may incur charges. Recommended cancellation dates should be checked against the original subscription terms.

Overall progress, remaining tasks, and team responsibilities are covered in the separate **Phase 2 Prototype Progress Report**.
