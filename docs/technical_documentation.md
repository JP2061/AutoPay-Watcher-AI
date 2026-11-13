### AutoPay Watcher AI – Technical Documentation
This document describes the application's architecture, implementation, testing, and development progress.

## 1. System Architecture
***Application Workflow:***

**Set Up Streamlit Application & Dashboard**\
Create the Python web interface for\
subscription email input and management\
↓\
**Implement Email Upload (.eml)**\
Email manual upload and Python processing\
*(Optional Gmail syncing if time allows)\
↓\
**AI Information Extraction**\
Use OpenAI API and GPT-6 Luna to\
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
    

***Email Parsing and AI Integration*** – [TODO: Team Member Name]

- **Functions**
  - [TODO: List functions]
- **Implementation**
  - [TODO: Code explanation and details of implementation,including key design decisions and why the chosen approaches were used.]
- **AI Model and API**
  - **Model:** [TODO: Model ID]
  - **Prompt:** [TODO: Actual prompt used]
  - **API Workflow:** [TODO: Explain API calls and how responses are processed]
  - **Input:** [TODO: Describe input sent to the model]
  - **Output:** [TODO: Describe expected output]
  - **AI Limitations:** [TODO: Describe model limitations]
  - **Technical Contribution:** [TODO: Explain the team's own implementation and integration work]
- **Implementation Status**
  - [TODO: In Progress / Completed]
- **Planned Work**
  - [TODO: Describe functionality or improvements that have not yet been implemented.]

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
| Member 2 | Joshua Peng | Email Parsing and AI Integration |Planned-10/29/26, In Progress-11/2/26|
| Member 3 | [TODO – Member 3] | Data Validation and Cancellation Calculations |[TODO] |
| Member 4 | [TODO – Member 4] | Calendar Reminder Generation |[TODO] |
