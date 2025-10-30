import json

def load_guidelines():
    with open("guideline.json", "r") as f:
        guideline_data = json.load(f)

    with open("company_guidelines.txt", "r", encoding="utf-8", errors="ignore") as f:
        company_guidelines = f.read()


    return guideline_data, company_guidelines
