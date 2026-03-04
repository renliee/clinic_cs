from langchain_ollama import OllamaLLM #the model of llm
from langchain_core.prompts import ChatPromptTemplate 
from vector import retriever, search_with_confidence
from preprocessor import preprocess_query
from config import LLM_MODEL, PHONE_NUMBER

model = OllamaLLM(model=LLM_MODEL)

#context n question is in {} bcs they will be used many times with a different context and question, so it can be modified when its converted to prompt object.
template = """
Kamu adalah customer service Klinik Cantik Bella yang ramah dan profesional. 

INFORMASI YANG KAMU PUNYA: 
{context}

kamu akan mendapat pertanyaan dari customer dan tugasmu adalah untuk membantunya.
PERTANYAAN CUSTOMER: 
{question}

ATURAN WAJIB (HARUS DIIKUTI):
1. Jawab pertanyaan customer HANYA dari informasi diatas.
2. DILARANG menyebut "informasi di atas", "context", "database", atau istilah teknis apapun.
3. DILARANG menambah, menebak, atau mengarang informasi. DO NOT guess. DO NOT assume.
4. Jika jawaban untuk pertanyaan customer benar-benar TIDAK ADA di informasi diatas, jawab:
  "Maaf kak, untuk info tersebut belum tersedia. Boleh tanya langsung via Whatsapp ke {PHONE_NUMBER}."
- Baca informasi dengan TELITI sebelum menjawab tidak tau 

INSTRUKSI JAWABAN:
- Gunakan Bahasa Indonesia dan panggil customer dengan "kak"
- Jika customer tidak bertanya, namun malah menyapa atau berterima kasih, balas singkat 1 kalimat saja
- JANGAN awali dengan "Maaf kak" kecuali info TIDAK ADA atau ada masalah
- Jawab singkat, jelas, dan TO THE POINT.

ATURAN FINAL:
- Kamu DILARANG bertanya balik.
- Jika informasi cukup umum, jawab dengan penjelasan umum yang PALING AMAN.
- Jangan ulangi pertanyaan customer.


JAWABAN:
"""

prompt = ChatPromptTemplate.from_template(template) #to make prompt an object that could be called with filled parameters (so the info wont be just a normal text).
chain = prompt | model # "|" is the flow connector that will be executed by invoke

LOW_CONFIDENCE = 0.5

def get_response(question: str) -> str:
    clean_question = preprocess_query(question) #clean the user input 
    print(f"Preprocessed: {clean_question}")

    context_docs, confidence = search_with_confidence(clean_question) #get the similar docs and the confidence based on the question
    print(f"Confidence: {confidence:.2f}")

    if confidence < LOW_CONFIDENCE: #if the question doesnt meet the minimum vector score, ask ai to dont answer
        return "Maaf kak, saya kurang paham pertanyaannya. Boleh kak jelaskan maksudnya sedikit lagi? 😊"
    
    #convert context from list of docs to a string, so ai could read effectively 
    context_text = "\n\n".join(doc.page_content for doc in context_docs) #for every doc in list of related docs, join them all to a string with \n\n as separator
    result = chain.invoke({"context": context_text, "question": question, "PHONE_NUMBER": PHONE_NUMBER}) #chain.invoke will run prompt | model, the prompt will be given to the model
    response = result.content if hasattr(result, "content") else result #hasattr: python function that check if an object has an attributes or no. bcs result could be AIMessage(content:"hi") or "hi"

    return response

if __name__ == "__main__":
    print("Chatbot Ready. Type 'q' to quit")
    while True:
        question = input("Customer: ").strip()
        if question == 'q':
            break

        response = get_response(question)
        print(f"Bot: {response}")