

import streamlit as st
import os
import json
import gspread
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from oauth2client.service_account import ServiceAccountCredentials

# Define API key
OPENAI_API_KEY = ""

# Initialize the OpenAI LLM with the API key and temperature
llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.9)

def setup_ad_chains():
    # Define prompt templates for Google, Facebook, and TikTok Ads
    google_ads_prompt = PromptTemplate(
        input_variables=['brand_name', 'industry', 'url', 'offers', 'business_type', 'audience_demographics', 'cta'],
        template="Generate 5 headlines and 3 descriptions for a {business_type} named {brand_name} in the {industry} industry offering {offers}. The target audience includes {audience_demographics}. The objective is to drive clicks and sales on the website {url} with a call to action: {cta}. Ensure the format is suitable for Google Ads."
    )
    facebook_ads_prompt = PromptTemplate(
        input_variables=['brand_name', 'industry', 'url', 'offers', 'business_type', 'audience_demographics', 'cta'],
        template="Generate primary text, 3 headlines, and 3 descriptions for a {business_type} named {brand_name} in the {industry} industry offering {offers}. The target audience includes {audience_demographics}. The objective is to drive clicks and sales on the website {url} with a call to action: {cta}. Ensure the format is suitable for Facebook Ads."
    )
    tiktok_ads_prompt = PromptTemplate(
        input_variables=['brand_name', 'industry', 'url', 'offers', 'business_type', 'audience_demographics', 'cta'],
        template="Generate primary text, 3 headlines, and 3 descriptions for a {business_type} named {brand_name} in the {industry} industry offering {offers}. The target audience includes {audience_demographics}. The objective is to drive clicks and sales on the website {url} with a call to action: {cta}. Ensure the format is suitable for TikTok Ads."
    )

    # Setup LLM Chains for each ad platform
    google_ads_chain = LLMChain(llm=llm, prompt=google_ads_prompt, verbose=True, output_key="google_ads")
    facebook_ads_chain = LLMChain(llm=llm, prompt=facebook_ads_prompt, verbose=True, output_key="facebook_ads")
    tiktok_ads_chain = LLMChain(llm=llm, prompt=tiktok_ads_prompt, verbose=True, output_key="tiktok_ads")

    return google_ads_chain, facebook_ads_chain, tiktok_ads_chain

def export_to_google_sheets(data, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('generative-ai-418805-b73a3e84380a.json', scope)
    client = gspread.authorize(creds)

    sheet = client.create(sheet_name)
    worksheet = sheet.get_worksheet(0)

    header = ["Platform", "Headlines", "Descriptions"]
    worksheet.append_row(header)

    for row in data:
        worksheet.append_row([row[0], json.dumps(row[1]), row[2]])

    # Share the sheet with your email
    your_email = "aman@warroominc.com"  # Replace with your email
    sheet.share(your_email, perm_type='user', role='writer')

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet.id}"
    st.success(f"Data successfully exported to Google Sheets: [Generated Ad Copies]({sheet_url})")
    return sheet_url

# Custom CSS to adjust the main container width and font size
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 90%;
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }
    .ad-results {
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize the ad chains
google_ads_chain, facebook_ads_chain, tiktok_ads_chain = setup_ad_chains()

# Streamlit UI setup
st.title("Kedet Ads Copy Generator")
ad_platform = st.radio("Select Ad Platform", ["Google Ads", "Facebook Ads", "TikTok Ads", "All"])
brand_name = st.text_input("Brand Name")
industry = st.text_input("Industry (e.g., Retail, Healthcare, Technology)")
website_url = st.text_input("Website URL")
offers = st.text_input("Add Offer Details")
business_type = st.text_input("Business Type (e.g., E-commerce, Service Provider, B2B, B2C)")
audience_demographics = st.text_area("Audience Demographics (e.g., age, gender, interests). Enter multiple values separated by commas.")
cta = st.text_input("Call to Action (e.g., Buy Now, Sign Up)")

if st.button("Generate Ad Copies"):
    variables = {
        "brand_name": brand_name,
        "industry": industry,
        "url": website_url,
        "offers": offers,
        "business_type": business_type,
        "audience_demographics": audience_demographics,
        "cta": cta
    }

    # Get results from OpenAI
    openai_result_google = google_ads_chain.run(variables) if ad_platform in ["Google Ads", "All"] else None
    openai_result_facebook = facebook_ads_chain.run(variables) if ad_platform in ["Facebook Ads", "All"] else None
    openai_result_tiktok = tiktok_ads_chain.run(variables) if ad_platform in ["TikTok Ads", "All"] else None

    # Display results in columns with adjusted widths and uniform font size
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.subheader("Generated Ad Copies from OpenAI:")
        if openai_result_google:
            st.markdown("**Google Ads:**", unsafe_allow_html=True)
            st.markdown(f"<div class='ad-results'>{openai_result_google}</div>", unsafe_allow_html=True)
        if openai_result_facebook:
            st.markdown("**Facebook Ads:**", unsafe_allow_html=True)
            st.markdown(f"<div class='ad-results'>{openai_result_facebook}</div>", unsafe_allow_html=True)
        if openai_result_tiktok:
            st.markdown("**TikTok Ads:**", unsafe_allow_html=True)
            st.markdown(f"<div class='ad-results'>{openai_result_tiktok}</div>", unsafe_allow_html=True)

    # Store the export data in session state
    export_data = []
    if openai_result_google:
        export_data.append(["OpenAI Google Ads", openai_result_google, ""])
    if openai_result_facebook:
        export_data.append(["OpenAI Facebook Ads", openai_result_facebook, ""])
    if openai_result_tiktok:
        export_data.append(["OpenAI TikTok Ads", openai_result_tiktok, ""])

    st.session_state["export_data"] = export_data

if "export_data" in st.session_state and st.button("Export to Sheets"):
    sheet_url = export_to_google_sheets(st.session_state["export_data"], "Generated_Ad_Copies")
    st.markdown(f"**[Click here to open the Google Sheet]({sheet_url})**", unsafe_allow_html=True)
