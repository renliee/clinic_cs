from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import json
import re

from config import settings
from logger import get_logger

model = OllamaLLM(model=settings.llm_model)
logger = get_logger(__name__)

extractor_prompt = ChatPromptTemplate.from_messages([
("system", """
Kamu adalah information extractor untuk booking klinik.

CRITICAL EXTRACTION RULES:
1. Extract EXACTLY what user says - DO NOT guess or infer
2. If user doesn't mention something, return null
3. Extract numbers in time: "jam 6 sore" → "6 sore" (NOT just "sore")

Extract informasi ini:
- lokasi: ONLY if user says city name (Jakarta/Bekasi/Tangerang/Bandung/Kemang)
- treatment: ANY city or area name user mentions (Jakarta, Surabaya, Kemang, Tangerang, etc)
- tanggal: ONLY if user says date (besok, lusa, 5 Januari, dll)
- jam: Extract EXACTLY what user says about time. DO NOT convert to 24-hour format.(jam 6 sore, 14:00, 2 sore)
- nama: ONLY if user says "nama saya..." or explicit name

EXAMPLES:
Input: "Facial Glow kak"
Output: {{"lokasi": null, "treatment": "Facial Glow", "tanggal": null, "jam": null, "nama": null}}

Input: "jam 6 sore"
Output: {{"lokasi": null, "treatment": null, "tanggal": null, "jam": "6 sore", "nama": null}}

Input: "jam 9"
Output: {{"lokasi": null, "treatment": null, "tanggal": null, "jam": "9", "nama": null}}

Input: "14:00"
Output: {{"lokasi": null, "treatment": null, "tanggal": null, "jam": "14:00", "nama": null}}

Input: "booking facial bekasi besok jam 2 sore nama Dewi"
Output: {{"lokasi": "bekasi", "treatment": "facial", "tanggal": "besok", "jam": "2 sore", "nama": "Dewi"}}

CRITICAL: Output ONLY valid JSON object. No explanation, no markdown, no ```json.
Format: {{"lokasi": ..., "treatment": ..., "tanggal": ..., "jam": ..., "nama": ...}}
"""), ("user", "{message}")
])

extractor_chain = extractor_prompt | model

def extract_slots(message: str) -> dict:
    try:
        result = extractor_chain.invoke({"message": message})
        text = result.content if hasattr(result, "content") else str(result) #text = answer of ai in string

        logger.debug("Raw LLM output", extra={"output": text})
        clean = text.strip()
        try:
            #json.loads: parse literal json string to dictionary object and validate if the json is wrong or unclean
            slots = json.loads(clean) #if not valid, will stop here and jump to the except branch
            return _normalize_slots(slots) #if valid, return the dictionary. (needed to be converted to dict bcs python cant work with json literal string)
        except json.JSONDecodeError: #if json isnt clean or wrong
            pass #continue to robust parsing
        
        clean = _remove_markdown(clean) #cleaning the text by removing common markdown 
        try:
            slots = json.loads(clean) #validate and parse the json to dict
            return _normalize_slots(slots) #if valid, return it
        except json.JSONDecodeError:
            pass
        
        #if json still invalid
        json_obj = _extract_json_robust(clean) #clean it with more robust parsing
        if json_obj: 
            try:
                slots = json.loads(json_obj) #validate the json
                return _normalize_slots(slots) #if clean, return it
            except json.JSONDecodeError: #if the json still messy or there is an error
                pass
        
        #show that extraction failed and will return null json
        logger.warning("Extractor Failed: Could not parse JSON from response", extra={"output": text[:300]}) #extra = what llm answer
        return {**_empty_slots(), "_parse_error": True} # ** = copy "_empty_slots()" kw dict to this dict and add '"_parse_error": True' as a new kw and value

    except Exception as e: #if there is an unexpected error, return null json 
        logger.error("Extractor unexpected error", extra={"error": str(e)}, exc_info=True)
        return {**_empty_slots(), "_parse_error": True} #will be used in handler.py
    
#function to remove not needed strings, and try to return cleaned json only 
def _remove_markdown(text: str) -> str: 
    # 1) try capturing json object in some common pattern ai usually does
    pattern = r'```\s*(?:json)?\s*(\{.*?\}|\[.*?\])\s*```' #() = capture group. ?: = dont capture it to group. .*? = save all char unaggresively until next } or ]. \s* = consume all spaces like \n, \t
    match = re.search(pattern, text, flags=re.DOTALL | re.I)  #re.DOTALL: so '.' at '.*?' can match newline.
    if match:
        return match.group(1).strip() #if matched, take the {} part, bcs it should be the json, then clear the space at the start and at the end
        
    # 2) common prefix: not match, then try another pattern: remove common prefixes
    prefixes = ["json:", "result:", "output:", "here is", "here's", "response:", "result -"]
    text_stripped = text.strip()
    text_lower = text_stripped.lower()
    for prefix in prefixes:
        if text_lower.startswith(prefix):
            return text_stripped[len(prefix):].strip() #ex: "json:", len = 5. from "json: {"a": 1}", save the string starting from index 5 then use strip, so the saved string: '{"a": 1}'
        
    # 3) if no 1 and 2 failed, try to trim the text after first { or [
    first = min(
        [idx for idx in (text.find('{'), text.find('[')) if idx != -1] or [None] #first [] means: if idx != -1 then add it to list. ex: [4, 6] or [None] -> bcs of 'or' -> min([4,6] -> first = 4.
    )
    if first != None: #if there is { or [ in text 
        return text[first:].strip() #return the string starting from that { untill the end
    
    return text_stripped #if all fails
 
 #last defense and fallback to clean json
def _extract_json_robust(text: str) -> str:
    #find the string in {}, even if nested {} still handled. will error if the {} unbalanced
    try:
        start = text.find('{') #find will return the index of the char at (-1 if char isnt found)
        if start == -1: #if '{' not found
            return None
        
        count = 0
        for i in range(start, len(text)): #count from the '{' untill end of the string
            if text[i] == '{':
                count += 1
            elif text[i] == '}':
                count -= 1
                if count == 0: 
                    return text[start:i+1] #return the string from { untill last }
    except:
        pass

    return None

#to clean the dictionary so it will wont be any error / inconsistent 
def _normalize_slots(slots: dict) -> dict:
    normalized = {} 

    for key in ["lokasi", "treatment", "tanggal", "jam", "nama"]:
        value = slots.get(key) # .get(key) bcs .get is safer, if slots[key] and they key isnt there, will occurs error. but using .get, will generate the keyword and add None as its value

        if value in [None, "null", "", "None", "none", "NULL", "Null", "NONE", "N/A", "-"]: #if its null, convert it to Python None
            normalized[key] = None 
        elif isinstance(value, str): #isinstance: method from python to check a variable data types
            normalized[key] = value.strip() #if string: then strip it
        else: #if not a string and is a value, just use it directly
            normalized[key] = value
    
    return normalized #return the dictionary

#if all the extractor error or bad user input , just return all the dict as None
def _empty_slots() -> dict: 
    return {
        "lokasi": None,
        "treatment": None,
        "tanggal": None,
        "jam": None,
        "nama": None
    }