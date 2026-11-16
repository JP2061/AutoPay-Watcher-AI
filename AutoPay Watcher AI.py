# AutoPay Watcher AI Application

import streamlit as st
import os
import json
import math
from dotenv import load_dotenv
from openai import OpenAI
from email import policy
from email.parser import BytesParser
from datetime import datetime

load_dotenv()


# [TODO: Implement MAIL UPLOAD AND DASHBOARD Functions]


# Email Parsing and AI Information extraction functions
def parse_email(file_path):
    # Open and read .eml file
    with open(file_path, "rb") as file:
        email = BytesParser(policy=policy.default).parse(file)

    # Extract plain text from email
    body = email.get_body(preferencelist=("plain",))
    if body is not None:
        email_content = body.get_content()
    else:
        email_content = ""
    return email_content

def extract_subscription(email_content, client):
    # Send email text to LLM with prompt and instructions for extraction
    response = client.responses.create(
        model="gpt-6-luna",

        instructions="""
        Extract subcription information from emails.

        Interpret the cancellation plicy and identify 
        how much time before renewal the user must cancel.

        Return only a valid JSON object with these fields:
        name
        price
        billing_cycle
        renewal_date
        cancellation_policy
        cancellation_notice_amount
        cancellation_notice_unit        #Fixed typo

        For cancellation_notice_amount, return a number.

        For cancellation_notice_unit, use one of:       #Fixed typo
        hours, days, weeks, months

        Examples:
        "Cancel 24 hours before renewal" -> 24, hours
        "Cancel 48 hours before renewal" -> 48, hours
        "Cancel 3 days before renewal" -> 3, days
        "Cancel 2 weeks before renewal" -> 2, weeks     #Fixed from 3 to 2

        if cancellation policy is missing or unclear, 
        use null for the amount and unit.

        For renewal_date, use the format Month DD, YYYY.
        """,

        input=email_content
    )
    # Get the LLM response
    ai_extraction = response.output_text.strip()

    # Remove markdown formatting if present
    if ai_extraction.startswith("```json"):
        ai_extraction = ai_extraction[7:]
    elif ai_extraction.startswith("```"):
        ai_extraction = ai_extraction[3:]

    if ai_extraction.endswith("```"):
        ai_extraction = ai_extraction[:-3]
        
    # Remove extra spaces and newline characters
    ai_extraction = ai_extraction.strip()

    # Convert JSON response from AI into a Python dictionary
    extract_dict = json.loads(ai_extraction)

    return extract_dict

# [TODO: Implement DATA VALIDATION AND CANCELLATION DATES Functions]
def valid_number(value):
    # Check if value is a valid data type, is finite, and positive
    return (type(value) in (int, float)
            and (type(value) is int or math.isfinite(value))
            and value >= 0)

def validate_subscription(data):
    errors = []

    # Make sure data is a dictionary
    if not isinstance(data, dict):
        return ["Subscription information must be a dictionary."]

    # Check if name is a valid string
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("Subscription name is missing or invalid.")

    # Check if price is a valid number or empty
    price = data.get("price")
    if price is None:
        errors.append("Price is unknown; review the email.")
    elif not valid_number(price):
        errors.append("Price must be a finite, nonnegative number.")

    # Check if billing cycle and cancellation policy are valid strings
    for field in ("billing_cycle", "cancellation_policy"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is missing or invalid; review the email.")

    # Check if renewal date is in valid format
    renewal_date = data.get("renewal_date")
    try:
        datetime.strptime(renewal_date, "%B %d, %Y")
    except (ValueError, TypeError):
        errors.append("Renewal date must be a real date, such as November 30, 2026.")

    # Check the cancellation notice
    amount = data.get("cancellation_notice_amount")
    unit = data.get("cancellation_notice_unit")
    # Check if empty
    if amount is None or unit is None:
        errors.append("Cancellation notice is unknown or missing; review the policy.")
    # Check if finite and greater than 0
    elif not valid_number(amount):
        errors.append("Cancellation notice must be a finite, nonnegative number.")
    # Check the unit
    elif unit not in ("hours", "days", "weeks", "months"):
        errors.append("Cancellation notice unit must be hours, days, weeks, or months.")
    # Check for valid month number
    elif unit == "months" and amount != int(amount):
        errors.append("Month-based notice must be a whole number.")

    return errors

# [TODO: Implement AI CALENDAR REMINDERS Functions]


def main():
    # Commented out Streamlit function calls to test ai extraction
    """
    st.set_page_config(
        page_title="AutoPay Watcher AI",
        page_icon="📅",
        layout="wide"
    )
    st.title("AutoPay Wather AI")
    """

    # [TODO: Call and integrate all Functions in main()]

    # Test AI Extraction
    # Load OpenAI API Key
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("OpenAI API key is not available.")
        return
        
    client = OpenAI(api_key=api_key)
    try:
        # Email parsing
        file_path = "sample_email.eml" # Replace with sample_email.eml path
        email_content = parse_email(file_path)

        print("\nParsed Email Content:")
        print(email_content)

        # AI information extraction
        result = extract_subscription(email_content, client)

        print("\nExtracted Subscription Information:")
        print(json.dumps(result, indent=4))

     # Validate the extracted data and show issues for user review.
        issues = validate_subscription(result)
        print("\nValidation messages:")
        if issues:
            for issue in issues:
                print("-", issue)
        else:
            print("No validation problems found.")

    except Exception as error:
        print("Error:", error)



if __name__ == "__main__":
    main()