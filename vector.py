from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader #TextLoader: to read/load txt files
from langchain_text_splitters import CharacterTextSplitter #splitter text for llm
import os #to check if vector db already exists

db_location = "./chroma_clinic_db" # "./" : the location of this file. 
embeddings = OllamaEmbeddings(model="mxbai-embed-large") #prepare the embeddings model (will convert data to vector)

if os.path.exists(db_location): #if vector db already exists, make a connection to it
    vector_store = Chroma(  #connect to "clinic_faq" at "db_location" and use "embeddings" model. note: each location can consist more than 1 collection_name
        collection_name="clinic_faq",
        persist_directory = db_location,
        embedding_function=embeddings
    )
else: #if not found, create new vector db
    #loader = only to prepare the txt reader(txt unread yet).
    loader = TextLoader("clinic_knowledge_base.txt", encoding="utf-8") #encoding="utf-8": Originally txt was bytes on the computer, but using utf-8 rules to convert it to char, then will store that char to documents (so the data in docs wont be in bytes but char)
    documents = loader.load() #use .load() to execute the loader then make a document to store it. Document is an object in python that consist page_content(main message) and metadata(notes, if user didnt input: will be {}), could add id if wanted to

    #to split long text to smaller chunks for llm (not great for llm if the text is too long)
    splitter = CharacterTextSplitter( #a method to split a text
        separator="\n---\n", #split everytime finds "\n---\n"
        chunk_size=2500, #chunk_size: max char of a chunk. chunk_overlap: last 100 char from the chunk before is repeated in the next chunk
        chunk_overlap=0
    )

    chunks = splitter.split_documents(documents) #execute the full documents into chunks: list of smaller docs, using splitter rules

    vector_store = Chroma( #make a connection to a spesific vector_db ("clinic_faq")
        collection_name="clinic_faq", #name of the vector db at the location
        persist_directory=db_location, #location of vector db
        embedding_function=embeddings #the embeddings model to convert data to vector
    )
    #after connecting with a spesific db (vector_store) add the data using add_documents
    vector_store.add_documents(documents=chunks) #add_documents: indirect method from Chroma, it reads text from documents, convert it by the embeddings model of vector_store, and save it to vector_store("clinic_faq") 

def search_with_confidence(query: str, k: int=4, threshold: float=1.5):
    results = vector_store.similarity_search_with_score(query, k=k) #method from chroma that return list of tuple of (doc, score). 2 params: the query(string that wanted to compare) and "k": count of most similar docs. ex: [(Document(page_content="Halo kak", metadata={...}), 0.12), (docs2(),score2)]
    if not results: #if there is no documents
        return [], 0.0 #return null docs and 0 confidence
    
    filtered = [(doc, score) for doc, score in results if score < threshold] #filter the list of tuples so all of their score is below 1.5
    if not filtered: #if all docs similarity >= 1.5
        return [], 0.0 
    
    docs = [doc for doc, score in filtered] #save all the docs
    best_score = min(score for doc, score in filtered) #get the lowest score as the confidence level
    confidence = max(0, min(1, 1-(best_score/2))) #min and max here are to make sure cofidence value is within 0 and 1, so there wont be any errors

    return docs, confidence #ex: confidence = 0.9 -> 90% sure

#retriever = just in case wanna go back using old code
retriever = vector_store.as_retriever(search_kwargs={"k": 4}) #as_retriever: indirect method from chroma that convert vector_store to retriever object and will return 5 most similar docs