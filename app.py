import sys


import gradio as gr
from openai import OpenAI
from utils.extract_image import extract_from_image
from utils.extract_video import extract_from_video
from utils.extract_ppt import extract_from_ppt
from utils.load_guideline import load_guidelines
from utils.parse_output import parse_output
from models.schema import CriticResponse

from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

guidelines, company = load_guidelines()

# def critic_agent(input_type, file=None, text_input=""):
#     extracted_text = ""
#     images = []

#     if input_type == "Text":
#         extracted_text = text_input
    
#     elif input_type == "Image" and file:
#         extracted_text, img = extract_from_image(file.name)
#         images.append(img)

#     elif input_type == "PPT" and file:
#         extracted_text, images = extract_from_ppt(file.name)

#     elif input_type == "Video" and file:
#         extracted_text = extract_from_video(file.name)

#     prompt = f"""

# You are an AI Brand Compliance Critic. Your job is to critically evaluate whether the provided content aligns with the company's branding, tone, messaging, and compliance rules.

# Perform a STRICT evaluation based on:

# 1️⃣ Company Guidelines (brand values, claims allowed, tone of voice, messaging rules):
# {company}

# 2️⃣ Content-Type–Specific Rules:
# {guidelines[input_type.lower()]["checks"]}

# ---

# You MUST assess the content in these aspects:

# A. **Brand Relevance**  
# - Does the content clearly relate to the company, its offerings, or target audience?  
# - Any mismatch with company positioning or industry domain?

# B. **Brand Tone & Messaging Accuracy**  
# - Detect tone deviations (too casual/harsh/salesy if not allowed)
# - Identify any statements that conflict with brand-approved claims

# C. **Brand Safety & Risk Compliance**  
# - Check for misleading, competitive, offensive, or legally risky elements

# D. **Type-Specific Alignment**  
# - Evaluate only those attributes that affect brand perception (visual compliance, textual alignment)

# ---

# Content to Analyze:
# {extracted_text} 

# ---

# OUTPUT FORMAT (MANDATORY — DO NOT CHANGE):
# Problems:
# - Bullet points listing ONLY issues that conflict with brand guidelines, messaging rules, or compliance standards
# - No stylistic or formatting criticism unless it violates brand rules

# Fixes:
# - Bullet points providing corrections SPECIFIC TO brand alignment:
#     ✅ Rewrite suggestions that use approved tone and messaging
#     ✅ Replace incorrect/unauthorized claims with brand-approved messages
#     ✅ Suggestions must strengthen connection to brand identity, values, audience
# - DO NOT mention formatting, structure, or grammar fixes unless they directly impact branding

# If the content fully meets company standards, respond in the same structure:

# Problems:
# - No major issues found

# Fixes:
# - Content aligns fully with brand guidelines
# """


#     messages = [
#         {
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": prompt},
#             ]
#         }
#     ]

#     if images:
#         for img in images:
#             messages[0]["content"].append({
#                 "type": "image_url",
#                 "image_url": {
#                     "url": f"data:image/png;base64,{img}"
#                 }
#             })

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=messages,
#         max_tokens=500 ,
        
#     )

#     text_resp = response.choices[0].message.content

#     print(f"OpenAI Response: {text_resp}")

#     validated = parse_output(text_resp)

#     clean_problems = [p for p in validated.problems if p and p.strip() != '*']
#     clean_fixes = [f for f in validated.fixes if f and f.strip() != '*']

#     # Format with bold headers
#     result = "<b>Problems:</b><br>" + "<br>".join(f"- {p}" for p in clean_problems)
#     result += "<br><br><b>Fixes:</b><br>" + "<br>".join(f"- {f}" for f in clean_fixes)

#     return result

def critic_agent(input_type, file=None, text_input=""):
    extracted_text = ""
    images = []

    if input_type == "Text":
        extracted_text = text_input
    
    elif input_type == "Image" and file:
        extracted_text, img = extract_from_image(file.name)
        images.append(img)

    elif input_type == "PPT" and file:
        # returns list of (slide_text, slide_img)
        extracted_text, images = extract_from_ppt(file.name)

    elif input_type == "Video" and file:
        extracted_text = extract_from_video(file.name)

    all_responses = []

    # Handle Text and Video directly (single evaluation)
    if input_type in ["Text", "Video"]:
        prompt = f"""
You are an AI Brand Compliance Critic. Your job is to critically evaluate whether the provided content aligns with the company's branding, tone, messaging, and compliance rules.

# Perform a STRICT evaluation based on:

# 1️⃣ Company Guidelines (brand values, claims allowed, tone of voice, messaging rules):
# {company}

# 2️⃣ Content-Type–Specific Rules:
# {guidelines[input_type.lower()]["checks"]}

# ---

# You MUST assess the content in these aspects:

# A. **Brand Relevance**  
# - Does the content clearly relate to the company, its offerings, or target audience?  
# - Any mismatch with company positioning or industry domain?

# B. **Brand Tone & Messaging Accuracy**  
# - Detect tone deviations (too casual/harsh/salesy if not allowed)
# - Identify any statements that conflict with brand-approved claims

# C. **Brand Safety & Risk Compliance**  
# - Check for misleading, competitive, offensive, or legally risky elements

# D. **Type-Specific Alignment**  
# - Evaluate only those attributes that affect brand perception (visual compliance, textual alignment)

# ---

# Content to Analyze:
# {extracted_text} 

# ---

# OUTPUT FORMAT (MANDATORY — DO NOT CHANGE):
# Problems:
# - Bullet points listing ONLY issues that conflict with brand guidelines, messaging rules, or compliance standards
# - No stylistic or formatting criticism unless it violates brand rules

# Fixes:
# - Bullet points providing corrections SPECIFIC TO brand alignment:
#     ✅ Rewrite suggestions that use approved tone and messaging
#     ✅ Replace incorrect/unauthorized claims with brand-approved messages
#     ✅ Suggestions must strengthen connection to brand identity, values, audience
# - DO NOT mention formatting, structure, or grammar fixes unless they directly impact branding

# If the content fully meets company standards, respond in the same structure:

# Problems:
# - No major issues found

# Fixes:
# - Content aligns fully with brand guidelines
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            max_tokens=500
        )

        text_resp = response.choices[0].message.content
        validated = parse_output(text_resp)
        clean_problems = [p for p in validated.problems if p and p.strip() != '*']
        clean_fixes = [f for f in validated.fixes if f and f.strip() != '*']

        result = "<b>Problems:</b><br>" + "<br>".join(f"- {p}" for p in clean_problems)
        result += "<br><br><b>Fixes:</b><br>" + "<br>".join(f"- {f}" for f in clean_fixes)
        return result

    # Handle Image input (text + single image)
    elif input_type == "Image":
        prompt = f"""
You are an AI Brand Compliance Critic. Your job is to critically evaluate whether the provided content aligns with the company's branding, tone, messaging, and compliance rules.

# Perform a STRICT evaluation based on:

# 1️⃣ Company Guidelines (brand values, claims allowed, tone of voice, messaging rules):
# {company}

# 2️⃣ Content-Type–Specific Rules:
# {guidelines[input_type.lower()]["checks"]}

# ---

# You MUST assess the content in these aspects:

# A. **Brand Relevance**  
# - Does the content clearly relate to the company, its offerings, or target audience?  
# - Any mismatch with company positioning or industry domain?

# B. **Brand Tone & Messaging Accuracy**  
# - Detect tone deviations (too casual/harsh/salesy if not allowed)
# - Identify any statements that conflict with brand-approved claims

# C. **Brand Safety & Risk Compliance**  
# - Check for misleading, competitive, offensive, or legally risky elements

# D. **Type-Specific Alignment**  
# - Evaluate only those attributes that affect brand perception (visual compliance, textual alignment)

# ---

# Content to Analyze:
# {extracted_text} 

# ---

# OUTPUT FORMAT (MANDATORY — DO NOT CHANGE):
# Problems:
# - Bullet points listing ONLY issues that conflict with brand guidelines, messaging rules, or compliance standards
# - No stylistic or formatting criticism unless it violates brand rules

# Fixes:
# - Bullet points providing corrections SPECIFIC TO brand alignment:
#     ✅ Rewrite suggestions that use approved tone and messaging
#     ✅ Replace incorrect/unauthorized claims with brand-approved messages
#     ✅ Suggestions must strengthen connection to brand identity, values, audience
# - DO NOT mention formatting, structure, or grammar fixes unless they directly impact branding

# If the content fully meets company standards, respond in the same structure:

# Problems:
# - No major issues found

# Fixes:
# - Content aligns fully with brand guidelines
"""

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{images[0]}"}}
            ]
        }]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500
        )

        text_resp = response.choices[0].message.content
        validated = parse_output(text_resp)
        clean_problems = [p for p in validated.problems if p and p.strip() != '*']
        clean_fixes = [f for f in validated.fixes if f and f.strip() != '*']

        result = "<b>Problems:</b><br>" + "<br>".join(f"- {p}" for p in clean_problems)
        result += "<br><br><b>Fixes:</b><br>" + "<br>".join(f"- {f}" for f in clean_fixes)
        return result

    # Handle PPT input (slide-by-slide)
    # Handle PPT input (slide-by-slide)
    elif input_type == "PPT":
        slide_counter = 1
        for slide_text, slide_img in images:
            # Skip slides with no image AND no text
            if not slide_img and not slide_text.strip():
                slide_counter += 1
                continue
            
            # If there's no image but there's text, still process it
            if not slide_img:
                print(f"⚠️ Slide {slide_counter}: No image found, processing text only")
                slide_prompt = f"""
You are an AI Brand Compliance Critic. Evaluate this PPT **slide {slide_counter}**.

Perform a STRICT evaluation based on:

1️⃣ Company Guidelines (brand values, claims allowed, tone of voice, messaging rules):
{company}

2️⃣ Content-Type–Specific Rules:
{guidelines[input_type.lower()]["checks"]}

---

You MUST assess the content in these aspects:

A. **Brand Relevance**  
- Does the content clearly relate to the company, its offerings, or target audience?  
- Any mismatch with company positioning or industry domain?

B. **Brand Tone & Messaging Accuracy**  
- Detect tone deviations (too casual/harsh/salesy if not allowed)
- Identify any statements that conflict with brand-approved claims

C. **Brand Safety & Risk Compliance**  
- Check for misleading, competitive, offensive, or legally risky elements

D. **Type-Specific Alignment**  
- Evaluate only those attributes that affect brand perception (visual compliance, textual alignment)

---

Content to Analyze:
{slide_text}

---

OUTPUT FORMAT (MANDATORY — DO NOT CHANGE):
Problems:
- Bullet points listing ONLY issues that conflict with brand guidelines, messaging rules, or compliance standards
- No stylistic or formatting criticism unless it violates brand rules

Fixes:
- Bullet points providing corrections SPECIFIC TO brand alignment:
    ✅ Rewrite suggestions that use approved tone and messaging
    ✅ Replace incorrect/unauthorized claims with brand-approved messages
    ✅ Suggestions must strengthen connection to brand identity, values, audience
- DO NOT mention formatting, structure, or grammar fixes unless they directly impact branding

If the content fully meets company standards, respond in the same structure:

Problems:
- No major issues found

Fixes:
- Content aligns fully with brand guidelines
"""
                messages = [{
                    "role": "user",
                    "content": [{"type": "text", "text": slide_prompt}]
                }]
            else:
                # Process with both text and image
                slide_prompt = f"""
You are an AI Brand Compliance Critic. Evaluate this PPT **slide {slide_counter}**.

Perform a STRICT evaluation based on:

1️⃣ Company Guidelines (brand values, claims allowed, tone of voice, messaging rules):
{company}

2️⃣ Content-Type–Specific Rules:
{guidelines[input_type.lower()]["checks"]}

---

You MUST assess the content in these aspects:

A. **Brand Relevance**  
- Does the content clearly relate to the company, its offerings, or target audience?  
- Any mismatch with company positioning or industry domain?

B. **Brand Tone & Messaging Accuracy**  
- Detect tone deviations (too casual/harsh/salesy if not allowed)
- Identify any statements that conflict with brand-approved claims

C. **Brand Safety & Risk Compliance**  
- Check for misleading, competitive, offensive, or legally risky elements

D. **Type-Specific Alignment**  
- Evaluate only those attributes that affect brand perception (visual compliance, textual alignment)

---

Slide Text Content:
{slide_text}

Please also analyze the visual content in the provided image.

---

OUTPUT FORMAT (MANDATORY — DO NOT CHANGE):
Problems:
- Bullet points listing ONLY issues that conflict with brand guidelines, messaging rules, or compliance standards
- No stylistic or formatting criticism unless it violates brand rules

Fixes:
- Bullet points providing corrections SPECIFIC TO brand alignment:
    ✅ Rewrite suggestions that use approved tone and messaging
    ✅ Replace incorrect/unauthorized claims with brand-approved messages
    ✅ Suggestions must strengthen connection to brand identity, values, audience
- DO NOT mention formatting, structure, or grammar fixes unless they directly impact branding

If the content fully meets company standards, respond in the same structure:

Problems:
- No major issues found

Fixes:
- Content aligns fully with brand guidelines
"""
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": slide_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{slide_img}"}}
                    ]
                }]

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=500
                )

                text_resp = response.choices[0].message.content
                validated = parse_output(text_resp)
                clean_problems = [p for p in validated.problems if p and p.strip() != '*']
                clean_fixes = [f for f in validated.fixes if f and f.strip() != '*']

                # Only include slides that have actual issues
                has_issues = any(
                    keyword not in problem.lower() 
                    for problem in clean_problems 
                    for keyword in ['no major issues', 'no issues', 'fully aligns', 'no content provided']
                )
                
                if has_issues and clean_problems:
                    formatted = f"<b>🖼️ Slide {slide_counter}</b><br><b>Problems:</b><br>" + "<br>".join(f"- {p}" for p in clean_problems)
                    formatted += "<br><b>Fixes:</b><br>" + "<br>".join(f"- {f}" for f in clean_fixes)
                    all_responses.append(formatted)
            
            except Exception as e:
                print(f"❌ Error processing slide {slide_counter}: {e}")
                all_responses.append(f"<b>🖼️ Slide {slide_counter}</b><br>⚠️ Error: {str(e)}")
            
            slide_counter += 1

        return "<hr>".join(all_responses)

import gradio as gr

def ui():
    with gr.Blocks() as interface:
        gr.Markdown("### 🔍 Brand Tone Enforcer – AI Critic Agent")

        input_type = gr.Radio(
            ["Image", "Video", "PPT", "Text"], 
            label="Select Input Type", 
            interactive=True
        )

        # Conditional input fields (initially hidden)
        file_upload = gr.File(label="Upload File", visible=False)
        text_box = gr.Textbox(label="Enter Text", lines=4, visible=False)

        output = gr.HTML(label="AI Output")
        btn = gr.Button("Analyze")

        # Logic to switch fields based on input type
        def toggle_inputs(choice):
            if choice == "Text":
                return gr.update(visible=False), gr.update(visible=True)
            else:
                return gr.update(visible=True), gr.update(visible=False)

        input_type.change(toggle_inputs, input_type, [file_upload, text_box])

        btn.click(
            critic_agent, 
            [input_type, file_upload, text_box], 
            output
        )

    return interface


if __name__ == "__main__":
    ui().launch(share=True,debug=True)
