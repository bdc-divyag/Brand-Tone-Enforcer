from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from openai import OpenAI
from utils.extract_image import extract_from_image
from utils.extract_video import extract_from_video
from utils.extract_ppt import extract_from_ppt
from utils.load_guideline import load_guidelines
from utils.parse_output import parse_output
from dotenv import load_dotenv
import tempfile
import shutil

load_dotenv()
app = FastAPI(title="Brand Tone Enforcer")

# Setup templates
templates = Jinja2Templates(directory="templates")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
guidelines, company = load_guidelines()

def critic_agent(input_type, file_path=None, text_input=""):
    extracted_text = ""
    images = []

    if input_type == "text":
        extracted_text = text_input
    
    elif input_type == "image" and file_path:
        extracted_text, img = extract_from_image(file_path)
        images.append(img)

    elif input_type == "ppt" and file_path:
        extracted_text, images = extract_from_ppt(file_path)

    elif input_type == "video" and file_path:
        extracted_text = extract_from_video(file_path)

    all_responses = []

    if input_type in ["text", "video"]:
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
        return {"problems": validated.problems, "fixes": validated.fixes}

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
        return {"problems": validated.problems, "fixes": validated.fixes}

    elif input_type == "PPT":
        slide_results = []
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
                
                has_issues = any(
                    keyword not in problem.lower() 
                    for problem in validated.problems 
                    for keyword in ['no major issues', 'no issues', 'fully aligns', 'no content provided']
                )
                
                if has_issues and validated.problems:
                    slide_results.append({
                        "slide": slide_counter,
                        "problems": validated.problems,
                        "fixes": validated.fixes
                    })
            
            except Exception as e:
                print(f"Error processing slide {slide_counter}: {e}")
            
            slide_counter += 1

        return {"slides": slide_results}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze(
    input_type: str = Form(...),
    file: UploadFile = File(None),
    text_input: str = Form(None)
):
    try:
        file_path = None
        
        if file:
            # Save uploaded file temporarily
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                file_path = tmp.name
        
        result = critic_agent(input_type, file_path, text_input or "")
        
        # Clean up temp file
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
        
        return JSONResponse(content={"success": True, "data": result})
    
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    import uvicorn
    print("   - http://127.0.0.1:8000")
    print("   - http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)