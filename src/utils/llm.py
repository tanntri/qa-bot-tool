from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

class LLMModel:
    def __init__(self, model_name: str = "gpt-4o"):
        if not model_name:
            model_name = "gpt-4o"
        self.model = ChatOpenAI(model=model_name, temperature=0.0)

    def get_model(self):
        return self.model
    
class EmbeddingModel:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        if not model_name:
            model_name = "text-embedding-3-small"
        self.embedding_model = OpenAIEmbeddings(model=model_name)

    def get_embedding_model(self):
        return self.embedding_model
    
if __name__ == "__main__":
    llm_instance = LLMModel()  
    llm_model = llm_instance.get_model()
    response=llm_model.invoke("How to fix upload stuck at 99%?")

    print(response)