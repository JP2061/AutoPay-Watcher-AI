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


***Prototype Development:***
- **Proof of Concept (PoC):** [TODO: Describe the core functions tested in the PoC]

- **Minimum Viable Product (MVP):** [TODO: Describe the intended end-to-end user flow]


## 2. Development Environment and Setup

***Technologies Used:***
- [TODO: Complete Technologies Used]

***Dependencies:***

The required Python libraries are listed in `requirements.txt`.

- [TODO: Complete Dependencies]

***Main Project Files:***
- [TODO: Complete Main Project Files]

***Installation and Setup Explanations:***

- **Install Dependencies:**
  - [TODO: Explain how to install the required Python libraries from `requirements.txt`.]

- **System Configuration:**
  - [TODO: Explain how to configure the required environment variables and the OpenAI API key without revealing credentials.]

- **Run the Prototype:**
  - [TODO: Explain the details for launching the Streamlit application, explaining the execution process,
    required configurations, expected behavior, and how to verify that the prototype runs successfully.]
- **README Reference:**
  - Refer to the [README](../README.md) for basic installation, setup, and application launch instructions.

## 3. Code Implementation

The following sections describe the main components of the application. Each team member will explain their part in implementing the code including describing the functions and their integration with main, the details of implementation and the development progress.

***Email Upload and Streamlit Dashboard*** – [TODO: Team Member Name]

- **Functions**
  - [TODO: List functions]
- **Implementation**
  - [TODO: Code explanation and details of implementation,including key design decisions and why the chosen approaches were used.]
- **Implementation Status**
  - [TODO: In Progress / Completed]
- **Planned Work**
  - [TODO: Describe functionality or improvements that have not yet been implemented.]
    

***Email Parsing and AI Integration*** – Joshua Peng

- **Functions**
  - [TODO: List functions]
- **Implementation**
  - Once Users manually upload subscription emails in .eml format and Python reads the email files and extract the text needed for analysis, the email contents will then be sent through the OpenAI API to the LLM. The AI will return the subscription information in JSON format, including the subscription name, price, renewal date and cancellation terms.
  - We chose to use an LLM because different companies may explain their renewal dates and cancellation policies in diffrent ways. The LLM can understand these differences without requiring us to manually write rules for every possible email format.
- **AI Model and API**
  - **Model:** [TODO: Model ID]
  - **Prompt:** [TODO: Actual prompt used]
  - **API Workflow:**Python will send an API request containing the email text and a prompt with instructions to the LLM. The LLM will return the extracted subscription information in JSON format, and Python will then read the JSON response and pass the extracted information to other parts of the application for data validation and cancellation date calculations.
  - **Input:** Text extracted from subscription emails uploaded in .eml format
  - **Output:** JSON containing the subscription name, price, billing frequency, renewal date and cancellation terms. If information is missing, we will tell the AI to return unknown instead of guessing the information.
  - **AI Limitations:** The LLM may not always identify the correct information, especially when emails have unclear working or do not include all the subscription details. This could lead to inaccurate cancellation dates if the information is not checked. 
  - **Technical Contribution:** The AI extraction component will include developing a prompt that instructs the LLM to identify important subscription information from emails. We will use the OpenAI's Python library to connect the application to the OpenAI API and process the information returned by the LLM into JSON format. We will also test the extraction using sample subscription emails with different renewal dates and cancellation policies. Based on the results of these tests, we can adjust the prompt given to the LLM to improve accuracy.
- **Planned Work**
  - Develop the prompt and decide how the subscription information will be organized in JSON format.
  - Select the OpenAI API model and connect it to the Python application.
  - Test the AI extraction using sample subscription emails with different formats and cancellation policies.
  - Compare the information extracted by the LLM with the actual information written in the emails.
  - Adjust the prompt based on the testing results to improve accuracy.
  - Connect the extracted information in JSON to the data validation and cancellation date calculation part of the application.
- **Implementation Status**
  - Progress:
    - 10/29/2026: Initial project planning, GitHub repository setup and discussion of team responsibilities and development plans for each part of the application.
    - 11/13/2026: Implementation and documentation for the AI extraction part of the application.
  - Completed:\
    [TODO: Sections completed and date]

***Data Validation and Cancellation Calculations*** – [TODO: Team Member Name]

- **Functions**
  - [TODO: List functions]
- **Implementation**
  - [TODO: Code explanation and details of implementation,including key design decisions and why the chosen approaches were used.]
- **Implementation Status**
  - [TODO: In Progress / Completed]
- **Planned Work**
  - [TODO: Describe functionality or improvements that have not yet been implemented.]

***Calendar Reminder Generation*** – [TODO: Team Member Name]

- **Functions**
  - [TODO: List functions]
- **Implementation**
  - [TODO: Code explanation and details of implementation,including key design decisions and why the chosen approaches were used.]
- **Implementation Status**
  - [TODO: In Progress / Completed]
- **Planned Work**
  - [TODO: Describe functionality or improvements that have not yet been implemented.]
    
***Main - Functions Integration:***
- [TODO: Explain how the main application connects the four components]

## 4. Testing and Reproducibility

***Testing Procedures:***
- [TODO: Complete Testing Procedures]

***Sample Test:***
- **Input File:** [TODO: Sample email filename and file path]
- **Expected Output:** [TODO: Expected subscription details]
- **Actual Output:** [TODO: Results from testing]
- **Test Status:** [TODO: Passed / Failed / Not Tested]

***Reproducibility:***
- Follow Sections 3–4 of the [README](../README.md) to install and run the prototype.
- [TODO: Provide step-by-step instructions for reproducing the sample result]

***Preliminary Results:***
- [TODO: Summarize preliminary results and testing observations]

## 5. Known Limitations and Remaining Code Integration Work

***Known Limitations:***
- [TODO: Complete Known Limitations. Describe current technical limitations and issues.]]

***Remaining Tasks:***
- [TODO: Summarize remaining tasks for the overall project, including integrating all four components and completing end-to-end testing.]
  
## 6. Summary of Project Team and Responsibilities

[TODO: Fill in name and responsibility, and update the progress status (Planned, In Progress or Completed) and dates as development progresses. Ex. Planned-10/29/26, In Progress-11/2/26, Completed-11/15/26]

| **Member** | **Name** | **Responsibility** | **Progress** |
|---|---|---|---|
| Member 1 | [TODO – Member 1] | Email Upload and Dashboard |[TODO] |
| Member 2 | Joshua Peng | Email Parsing and AI Integration |Planned-10/29/26, In Progress-11/13/2026|
| Member 3 | [TODO – Member 3] | Data Validation and Cancellation Calculations |[TODO] |
| Member 4 | [TODO – Member 4] | Calendar Reminder Generation |[TODO] |
