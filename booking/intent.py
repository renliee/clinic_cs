from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

model = OllamaLLM(model="qwen2.5:14b") #the model of llm

prompt = ChatPromptTemplate.from_messages([   #method to make a great prompt to llm with system 
    ("system", """Kamu adalah classifier untuk customer service klinik.
    
Klasifikasikan intent customer ke salah satu kategori:
- BOOKING: mau booking/reservasi/daftar/janji temu
- FAQ: tanya info (harga, lokasi, jam buka, treatment)
- CANCEL: batalkan booking
- RESCHEDULE: ganti jadwal
- CHITCHAT: sapaan, terima kasih, basa-basi
- UNCLEAR: tidak jelas maksudnya

Jawab HANYA dengan satu kata intent (BOOKING/FAQ/CANCEL/RESCHEDULE/CHITCHAT/UNCLEAR)"""),
    ("user", "{message}") #why {} bcs message here will be variatif and will change everytime, depends on the user input
])

chain = prompt | model #chain is the flow system, so the prompt wil be invoked with message info and given to llm model

def classify_intent(message: str) -> str:
    try:
        result = chain.invoke({"message": message}) #invoke the chain with message of user input
        text = result.content if hasattr(result, "content") else str(result) #langchain could return string or object, hasattr: to detect if there is object in result or no
        intent = text.strip().upper() #to clean. strip: delete spaces.

        valid_intents = ["BOOKING", "FAQ", "CANCEL", "RESCHEDULE", "CHITCHAT", "UNCLEAR"]
        if intent not in valid_intents: #if there is not matched intent
            print(f"Intent Warning: Got '{intent}', defaulting to UNCLEAR")
            return "UNCLEAR" #will clarify again to user
        return intent  
    
    except Exception as e: #if error occurs
        print(f"Intent Error: {e}")
        return "UNCLEAR" #will clarify again to user

def classify_intent_fallback(message: str) -> str:
    intent = classify_intent(message) #call llm to generate intent
    if intent != "UNCLEAR":
        print(f"CLASSIFY: {intent}") #DEBUGGING ONLY, DELETE LATER
        return intent
    #if intent is "UNCLEAR":
    msg = message.lower()
    if "?" in msg:
        return "FAQ"
    if any(kw in msg for kw in ["halo", "hai", "hi", "hlo", "thanks", "terima kasih", "thank you", "makasih", "makasi"]): #any: 1 true = executed
        return "CHITCHAT"
    
    return "UNCLEAR"
