### AutoPay Watcher AI – Technical Documentation
This document describes the application's architecture, code implementation details, testing, and development progress.

## 1. System Architecture
***Architecture Overview:***
AutoPay Watcher AI uses Streamlit for the user interface, SQLite for storing uploaded emails and subscription information, and the OpenAI API for AI extraction. Users upload subscription emails, which are parsed and saved in the database. The stored email content is then analyzed by the AI to extract important subscription details, including billing information, renewal dates, and cancellation requirements. The extracted information is passed to the validation component, which checks the data and calculates recommended cancellation dates with an additional safety buffer. The results can be reviewed and saved through the dashboard. The calendar reminder component will use the calculated cancellation dates to generate reminders that users can add to their calendars.

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
## 2. Development Progress: PoC-to-MVP
### Proof of Concept (PoC)
Our PoC focuses on testing whether the OpenAI API can successfully analyze subscription emails uploaded through our Streamlit application and dashboard and extract important information into JSON format. Python reads the uploaded .eml files and sends the email text to the LLM for analysis. The AI identifies subscription details, including the subscription name, price, billing frequency, renewal date, and cancellation terms. Python then validates the extracted information and calculates a recommended cancellation date based on the company's cancellation policy, with an additional safety buffer. 
### Minimum Viable Product (MVP)
Our MVP builds on the PoC by integrating the components into a complete Streamlit application. So far, our team has integrated email uploading, SQLite storage, AI extraction, and validation. In addition, users can select saved emails for AI analysis, review extracted subscription details, and select to calculate recommended cancellation dates. The dashboard organizes subscriptions into Free Trials and Active Subscriptions. Planned work toward the MVP includes completing downloadable .ics calendar reminders for Google Calendar, Outlook, and Apple Calendar, allowing users to edit subscription details, and further testing the end-to-end workflow with different subscription emails. Optional future features include Gmail syncing and additional AI-assisted cancellation features.


## 3. Development Environment and Main Files

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

## 4. Code Implementation

### Email Upload and Streamlit Dashboard – joshua gragg

**Function names**

**Dashboard functions (`dashboard_ui.py`):**
- `render_app()` — Initializes the application interface and displays the selected dashboard page.
- `render_sidebar()` — Provides navigation between Overview, Email inbox, Manage records, and Team integration.
- `render_mail_upload()` — Handles email uploading, saved email selection, duplicate import messages, and optional AI analysis.
- `render_dashboard()` — Displays active subscriptions, free trials, upcoming renewal dates, and estimated recurring costs.
- `render_subscription_card()` — Displays individual subscription details.
- `render_manage()` — Provides interfaces for adding, editing, archiving, and restoring subscription records.
- `subscription_form()` — Handles subscription data entry and editing.
- `render_integration()` — Provides an interface for importing JSON subscription records.

**Database and email functions (`autopay_core.py`):**
- `initialize_database()` — Creates the SQLite database tables.
- `read_email()` — Parses uploaded `.eml` and `.txt` files.
- `add_email()` — Saves uploaded emails and checks for duplicates using SHA-256 hashes.
- `list_emails()` and `get_email()` — Retrieve saved emails.
- `email_for_ai()` — Prepares stored email information for AI extraction.
- `save_subscription()` and `list_subscriptions()` — Store, update, and retrieve subscription records.
- `archive_subscription()` — Archives or restores subscriptions.
- `delete_email()` — Removes stored emails.

**Code explanation and implementation**

The Email Upload and Dashboard component uses Streamlit to provide a web interface for managing recurring subscriptions and free trials.

Users can upload `.eml` and `.txt` files through the Email inbox page. The application parses these files to retrieve email information, including the sender, subject, date, and message body. Uploaded emails are stored locally in a SQLite database. Each email is checked using a SHA-256 hash to prevent duplicate imports.

The dashboard organizes saved subscription records into Free trials, Active subscriptions, and Needs review categories. It displays expected charges, billing frequencies, renewal dates, and available cancellation information. It also calculates estimated monthly and yearly recurring costs when sufficient billing information is available.

The Manage records page allows users to manually create, edit, archive, and restore subscription records.

The email upload component also connects to the team's AI extraction function. Users can select a saved email, request AI analysis, review the returned JSON data, and save the resulting subscription information to the dashboard.

The implementation separates the Streamlit user interface in `dashboard_ui.py` from the email parsing and SQLite database operations in `autopay_core.py`.

**Implementation status**

- Implemented: Streamlit dashboard and navigation.
- Implemented: Email upload and parsing.
- Implemented: SQLite database storage and retrieval.
- Implemented: SHA-256 duplicate detection.
- Implemented: Subscription display, editing, and archiving.
- Implemented in code: Optional AI extraction handoff and JSON import.
- Verified: Nine isolated database and storage checks passed.
- Remaining verification: Manual Streamlit interface testing and complete end-to-end AI integration testing.

### AI Extraction and Email Parsing – Joshua Peng

**Function names**
- `extract_subscription(email_content, client)` — Sends the email text to the OpenAI API and converts the returned JSON into a Python dictionary. This JSON parsing is different from reading an `.eml` file.
- `parse_email()` — Initially used to open sample `.eml` files and extract plain-text email content for standalone AI testing. It is not called in the current integrated workflow.

**Code explanation and implementation**
- The OpenAI API receives the parsed email text and extraction prompt. The AI returns JSON containing the subscription name, price, billing frequency, renewal date, and cancellation terms. Missing or unclear values are requested as `null` rather than guessed.
- The prompt was updated to handle free trials, cancellation notices, and cancellation-notice amounts and units (such as 24 hours or several days). Cleanup was also added for Markdown code fences before parsing the JSON response.
- We use an LLM because companies describe renewal dates and cancellation policies differently. Python passes the extracted information to the separate validation and cancellation-date component. The AI extraction component was connected to saved emails through main(), while the validation teammate handled the integration of extraction results with the dashboard and cancellation-date calculations.
- The `parse_email()` function was initially created to open `.eml` files and extract plain-text email content for testing the AI extraction component before integrating it with the dashboard. After integration, `main()` was modified to use the email content already parsed and stored in the SQLite database. The `initialize_database()` and `list_emails()` functions are used to access saved emails, a Streamlit selection box allows users to choose an email, and `get_email()` retrieves the selected record. The `selected_email["body_text"]` field contains the previously parsed email text, which is passed directly to `extract_subscription()` for AI analysis. This allows AI Extraction Test mode to use emails uploaded through the dashboard without parsing them again. After the OpenAI API returns JSON, the separate validation component processes the results for cancellation-date calculations and dashboard integration.
- **Model and prompt:** GPT-6 Luna. See the [extraction prompt and API implementation](https://github.com/JP2061/AutoPay-Watcher-AI/blob/76acfce378a14cd1ef2cf177914c13f22d1248ec/AutoPay%20Watcher%20AI.py#L40-L113).
- **Limitation:** The AI can misread unclear prices, dates, or policies, so the output should be checked against the original email.

**Implementation status**
- **Completed/updated:** Initial standalone `.eml` parsing for testing, database-based retrieval of already-parsed email text in `main()`, OpenAI extraction, JSON response parsing, and prompt improvements for missing details, free trials, and cancellation notices.
- **Integration/testing:** The extraction is accessible through the application's **AI Extraction Test** view using saved emails.

### Data Validation and Cancellation Calculations – Triet Nguyen

**Functions** 
- `valid_number()` — Check if a value is a finite, nonnegative integer or float.
- `validate_subscription()` — Receive extracted data as a dictionary, then check for required fields, valid data types, missing information. Call valid_number(value) when checking values.
- `calculate_cancellation_date()` — Receive extracted cancellation data and a safety buffer. Calculate the recommended cancellation date if possible, using given buffer. 
- `extract_for_dashboard()` — Call AI extraction, calculate the recommended cancellation date, and add the date and explanation notes to the extracted dictionary while preserving the existing notes.

**Code explanation and implementation**
- The function `validate_subscription()` takes in the extracted data, and checks if it's a python dictionary. Then it proceeds to check the rest of the information. Checks for missing fields, correct data types. Name, billing cycle, cancellation policy must be nonempty strings. Price and cancellation notice amount must be finite, nonnegative numbers. Renewal date must be a valid date in the format Month DD, YYYY. Cancellation notice unit must be hours, days, weeks, or months. For months, the notice amount must be a whole number. Calls function `valid_number()` when checking values. It then returns a list of strings describing the issues, or an empty list if there are none. These messages are displayed through Streamlit by `main()` in AI Extraction Test mode and `render_mail_upload()` in Dashboard mode.
- The function `calculate_cancellation_date()` takes in the extracted data and a safety buffer that is default to 1 day. First, it double-check if the required data is valid. The function subtracts the required notice period from the renewal date by hours, days, weeks using timedelta. For months it uses a separate calculation, which account for different month lengths and leap years. Then it subtracts the additional safety buffer amount from the calculated notice day. Returns the recommended date and `None` for error on success, returns `None` for recommended date and an error message on failure. Invalid calculation dates, data will return error message instead of a guessed date.
- The function `extract_for_dashboard()` takes in the email's text and the openAI client. Calls the extraction function `extract_subscription()` and receives a python dictionary. Then it calls `calculate_cancellation_date()` using the extracted data, and receives a recommended date or an error message. The recommended date is stored in `cancellation_deadline`, or `None` if calculation fails. The function adds notes explaining the calculation, safety buffer, a warning if recommended date has passed, or the error messages to the existing notes and returns the updated dictionary. In `main()`, this function is passed to dashboard as the extraction callback, which will be called when the user requests analysis.

**Implementation status**
- Completed: Data validation, cancellation calculations, dashboard integration are implemented. Supports different cancellation notice units (hours, days, weeks, months, with 1 day safety buffer). Calculated dates are recommendations and may require user review.
- Tested: Validation and calculations were tested with sample emails with valid and invalid inputs. Dashboard integration testing show that validation messages, recommended dates, and calculation notes appear in the right sections.
- Planned: Change text format, colors to improve date visibility. Correct remaining grammar and spacing issues.

### Calendar Reminder Generation – Nathan Felix

**Functions**
- make_reminder_ics() - Creates one calendar (.ics) file for a single subscription and returns it so it can be downloaded.
- make_reminders_ics() — Creates one calendar file that holds reminders for a list of subscriptions.
- build_event() and build_calendar() — Helper functions that build the calendar event and wrap it into the full .ics file. Smaller helpers handle date formatting and text cleanup so the file follows the calendar format rules.
  
**Code explanation and implementation**
- This part is in calendar_reminder.py and only uses Python's built in libraries, so it does not add anything to requirements.txt. It makes files in the .ics calendar format, which Google Calendar, Outlook, and Apple Calendar can all open.
- It takes the recommended cancellation date from the validation component and makes an all-day event titled "Cancel [service] before you're charged." The event also holds the price, renewal date, and cancellation notes.
- Each event has an alarm that reminds the user a set number of days before the date. The user can choose how many days ahead they want the reminder from the dashboard.
- On the dashboard, each subscription uses a download button that calls this module and hands the user the .ics file, which opens directly in their calendar app.
  
**Implementation status**
- Completed: The calendar_reminder.py module — .ics generation for one or many subscriptions, and the reminder alarm with an adjustable lead time.
- Tested: Ran the module to generate a sample .ics file and opened it in a calendar app to confirm the event and reminder show up correctly.
- Planned: A future version could add events straight to the user's Google Calendar through the Google Calendar API instead of downloading a file.
  
## 5. Testing and Reproducibility

We test with `.eml` subscription emails containing different renewal dates and cancellation requirements, including 24-hour, 48-hour, and multi-day notices. We compare the AI-extracted name, price, renewal date, and cancellation terms with the original email. We also check Python's recommended cancellation date against the stated policy and safety buffer.

To reproduce a sample result, import `samples/sample_email_1.eml`, run AI extraction, inspect JSON and validation messages in **AI Extraction Test**, and view the saved subscription in **Dashboard → Overview**.

### Sample test result

| Item | Result |
|---|---|
| Input | `samples/sample_email_1.eml` |
| Expected | Email text, extracted subscription JSON, validation feedback, and a recommended cancellation date when enough information is available. |
| Actual AI extraction | {
||"service_name":"Netflix Standard"
||"record_type":"subscription"
||"amount_cents":1799
||"currency":"USD"
||"frequency":"Monthly"
||"renewal_date":"2026-11-15"
||"trial_end_date":NULL
||"cancellation_deadline":"2026-11-13"
||"cancellation_instructions":"Cancel at least 24 hours before the next renewal to avoid being charged."
||"notes":"Recommended cancellation date: November 13, 2026. Includes a 1-day safety buffer. This is a recommendation, not a guranteed deadline.The recommended ||cancellation date has already passed, please review the policy.\nAI-reported notice: 24 hours before renewal. Not a verified deadline."
||} |
| Actual date calculation | November 13, 2026 |
| Comparison with source | All values for JSON field match with email source |
| Test status | Passed |

Additional checks: Re-import the same email to verify duplicate handling.

dashboard testing 
### Email Upload and Dashboard Testing – joshua gragg

The Email Upload and Dashboard components were tested using automated pytest tests and manual testing through the Streamlit interface. Testing focused on verifying email uploading, parsing, database storage, duplicate prevention, subscription management, and integration with the team's AI extraction component.

**Automated Testing**

Automated tests were performed using Python 3.13.5 and pytest 8.4.1 on Windows.

The tests verified the following functionality:

- Email parsing for `.eml` and `.txt` files.
- Validation of uploaded files, including invalid formats, empty files, and files exceeding the 2 MB limit.
- SQLite database initialization and storage.
- Duplicate email detection using SHA-256 hashes.
- Retrieval and deletion of saved emails.
- Subscription creation, editing, archiving, and restoration.
- Dashboard navigation and subscription display.
- Integration of AI-extracted JSON data with subscription records using mocked responses.
- Validation of missing or invalid subscription information.

**Automated Test Results**

| Test File | Passed | Failed |
|---|---:|---:|
| `test_member1.py` | 43 | 0 |
| `test_autopay_core.py` | 11 | 0 |
| `test_team_schema.py` | 4 | 0 |
| **Total** | **58** | **0** |

All 58 automated tests passed successfully in 2.79 seconds.

**Manual Testing**

Manual testing was also performed through the Streamlit application to verify the user-facing interface. This included uploading sample emails, viewing saved email contents, checking duplicate import handling, navigating the dashboard, and managing subscription records.

**Testing Conclusion**

All automated tests passed, and manual testing of the Streamlit application was previously completed. These results support the functionality of the Email Upload and Dashboard components and their integration with the application's local database.

The automated tests used temporary databases and mocked AI responses. Therefore, the results do not independently verify live OpenAI API responses or the complete calendar reminder workflow.
## 6. Technical Limitations

Some emails omit important billing or cancellation details, and the LLM may interpret unclear wording incorrectly. The prototype uses manually uploaded `.eml` files rather than direct Gmail syncing. OpenAI API access requires a valid key and may incur charges. Recommended cancellation dates should be checked against the original subscription terms.

Overall progress, remaining tasks, and team responsibilities are covered in the separate **Phase 2 Prototype Progress Report**.
