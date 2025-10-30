from models.schema import CriticResponse
import re

def parse_output(text: str) -> CriticResponse:
    """Parse OpenAI response - handles multiple formats"""
    
    print(f"\n{'='*60}")
    print(f"RAW TEXT TO PARSE:")
    print(f"{'='*60}")
    print(text)
    print(f"{'='*60}\n")
    
    problems_list = []
    fixes_list = []
    
    # Method 1: Try regex with flexible whitespace
    problems_match = re.search(r'Problems?:\s*(.*?)(?=Fixes?:|$)', text, re.DOTALL | re.IGNORECASE)
    fixes_match = re.search(r'Fixes?:\s*(.*?)$', text, re.DOTALL | re.IGNORECASE)
    
    if problems_match:
        problems_text = problems_match.group(1).strip()
        print(f"🔍 Found Problems Section:\n{problems_text}\n")
        
        # Extract lines starting with dash or just non-empty lines
        for line in problems_text.split('\n'):
            line = line.strip()
            if line and line not in ['Problems:', 'Fixes:']:
                # Remove leading dash, bullet, asterisk
                cleaned = re.sub(r'^[-•*]\s*', '', line).strip()
                if cleaned:
                    problems_list.append(cleaned)
    
    if fixes_match:
        fixes_text = fixes_match.group(1).strip()
        print(f"🔍 Found Fixes Section:\n{fixes_text}\n")
        
        # Extract lines starting with dash or just non-empty lines
        for line in fixes_text.split('\n'):
            line = line.strip()
            if line and line not in ['Problems:', 'Fixes:']:
                # Remove leading dash, bullet, asterisk
                cleaned = re.sub(r'^[-•*]\s*', '', line).strip()
                if cleaned:
                    fixes_list.append(cleaned)
    
    # Method 2: Fallback - Line by line parsing
    if not problems_list or not fixes_list:
        print("⚠️ Regex failed, trying line-by-line parsing...")
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # Check for section headers
            if 'problem' in line_lower and ':' in line_lower:
                current_section = 'problems'
                # Check if content is on same line after colon
                if ':' in line_stripped:
                    content = line_stripped.split(':', 1)[1].strip()
                    if content and content.startswith('-'):
                        cleaned = re.sub(r'^[-•*]\s*', '', content).strip()
                        if cleaned:
                            problems_list.append(cleaned)
                continue
                
            elif 'fix' in line_lower and ':' in line_lower:
                current_section = 'fixes'
                # Check if content is on same line after colon
                if ':' in line_stripped:
                    content = line_stripped.split(':', 1)[1].strip()
                    if content and content.startswith('-'):
                        cleaned = re.sub(r'^[-•*]\s*', '', content).strip()
                        if cleaned:
                            fixes_list.append(cleaned)
                continue
            
            # Process bullet points
            if line_stripped and (line_stripped.startswith('-') or 
                                  line_stripped.startswith('•') or 
                                  line_stripped.startswith('*')):
                cleaned = re.sub(r'^[-•*]\s*', '', line_stripped).strip()
                
                if cleaned and current_section == 'problems':
                    problems_list.append(cleaned)
                elif cleaned and current_section == 'fixes':
                    fixes_list.append(cleaned)
    
    # Final output
    print(f"\n✅ PARSING COMPLETE:")
    print(f"   Problems: {len(problems_list)} items")
    print(f"   Fixes: {len(fixes_list)} items")
    
    if problems_list:
        print(f"\n📋 Problems List:")
        for i, p in enumerate(problems_list, 1):
            print(f"   {i}. {p[:100]}...")
    
    if fixes_list:
        print(f"\n🔧 Fixes List:")
        for i, f in enumerate(fixes_list, 1):
            print(f"   {i}. {f[:100]}...")
    
    print(f"\n{'='*60}\n")
    parts = text.split('Fixes:', 1)
    
    problems_section = parts[0].replace('Problems:', '').strip()
    fixes_section = parts[1].strip() if len(parts) > 1 else ""
    problems_list = [
        line.strip().lstrip('-•* ').strip() 
        for line in problems_section.split('\n') 
        if line.strip() and line.strip().lstrip('-•* ').strip() and line.strip() != '*'
    ]
    
    fixes_list = [
        line.strip().lstrip('-•* ').strip() 
        for line in fixes_section.split('\n') 
        if line.strip() and line.strip().lstrip('-•* ').strip() and line.strip() != '*'
    ]
    # Return result (no fallback messages)
    return CriticResponse(
        problems=problems_list if problems_list else ["No problems identified"],
        fixes=fixes_list if fixes_list else ["No fixes needed"]
    )