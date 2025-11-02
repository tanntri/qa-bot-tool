from langgraph.graph import StateGraph, END, START
from utils.llm import LLMModel
from tools.tools import retriever_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import Document
from graphs._schema import QaBotState, GradeDocuments, IsItBugOrUserFeedbackRelevant

llm_instance = LLMModel()
llm = llm_instance.get_model()

def is_question_bug_or_user_feedback_related():
    """Get whether the question is related to software bug reports or user feedback."""
    structured_llm_checker = llm.with_structured_output(IsItBugOrUserFeedbackRelevant)
    system = """
        Your job is to act as a strict binary classifier.
        You will receive a user question and must respond with only one word: 'yes' or 'no'.
        Do not provide any other text, punctuation, or capitalization.
        'yes' if the question is related to either software bugs or customer feedback about software.
        'no' if the question is NOT related to either software bugs or customer feedback about software.
    """
    relevance_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "User question: {question}")
        ]
    )

    relevance_checker = relevance_prompt | structured_llm_checker

    return relevance_checker

def should_generate_or_retrieve(state: QaBotState) -> str:
    """
        Determine whether the to generate an answer right away or retrieve documents

        Args:
            state(dict): current state of the graph

        Returns:
            str: Binary decision for next node to call
    """

    software_bug_or_user_feedback_relevant = state["software_bug_or_user_feedback_relevant"].lower()

    if 'yes' in software_bug_or_user_feedback_relevant:
        print("go to retrieve")
        return "retrieve"
    else:
        print("go to generate")
        return "generate"

async def grade_question(state: QaBotState) -> QaBotState:
    """
        Determine whether the question is related to software feedback or bug reports.

        Args:
            state(dict): current state of the graph

        Returns:
            state (dict): Updates software_bug_or_user_feedback_relevant key with question graded for software bug
            or user feedback relevance
    """

    question = state["question"]
    relevance_checker = is_question_bug_or_user_feedback_related()
    score = await relevance_checker.ainvoke({"question": question})

    print(f"Question relevance graded as: {score.binary_score.lower()}")

    grade = 'yes' if 'yes' in score.binary_score.lower() else 'no'

    print(f"Question relevance graded as: {grade}")

    return {"question": question, "software_bug_or_user_feedback_relevant": grade}
    

def doc_relevance_grader():
    """Get the document relevance grade."""
    # LLM with function call
    structured_llm_grader = llm.with_structured_output(GradeDocuments)
    system = """
        You are a grader assessing the relevance of a retrieved document to a user's question about software bugs or user feedback about software.

        Your task is to determine if the document contains information that can help answer the question.

        Instructions:
            1.  Grade the document as 'yes' if it contains keywords, concepts, or semantic meaning related to the user's question.
            2.  A document is relevant if it describes a bug, issue, error, feedback, feature request, or user experience that matches the user's query.
            3.  If the user asks about a specific issue or feature, a document mentioning related symptoms, error messages,
                components, or user complaints is relevant. For example, if the user asks "upload stuck at 99%", a document 
                mentioning "upload failures," "file transfer issues," or "progress bar freezing" is relevant.
            4.  A document is relevant if it contains information about a specific component or module that is part of a broader 
                system mentioned in the user's question. For example, if the user asks about "authentication issues" and the document 
                mentions "login problems" or "password reset failures," it is relevant.
            5.  Even if a term isn't explicitly mentioned in the document, consider synonyms, related issues, or technical variations.
                For example, "crash" could relate to "application freeze," "hang," "unresponsive," "force close," etc. Similarly,
                "slow performance" relates to "lag," "latency," "response time," or "loading issues."
            6.  Grade the document 'no' only if it is completely unrelated to the user's technical question, bug report inquiry, or feedback search.

        Output:
            Provide a single binary score: 'yes' or 'no'.
        """
    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Retrieved document: \n\n {document} \n\n User question: {question}")
        ]
    )

    retrieval_grader = grade_prompt | structured_llm_grader

    return retrieval_grader

async def grade_documents(state: QaBotState) -> QaBotState:
    """
        Document grading to determine whether a document is relevant to a user's question. 

        Args:
            state(dict): current state of the graph

        Returns:
            state (dict): Updates documents_relevant key graded for documents relevance against user question
    """
    print("Grading documents...")
    question = state["question"]
    documents = state["documents"]

    documents_relevant = "no"

    retrieval_grader = doc_relevance_grader()
    # First, ensure documents is iterable and elements are strings
    if isinstance(documents, str):
        # documents is already a string, no need to join
        document_text = documents
    elif hasattr(documents, '__iter__'):
        # documents is iterable, convert all elements to strings and join with space
        document_text = " ".join(str(doc) for doc in documents)
    else:
        # documents is neither string nor iterable, convert to string directly
        document_text = str(documents)

    print("Document text for grading:", document_text)

    score = await retrieval_grader.ainvoke({"question": question, "document": document_text})

    grade = score.binary_score
    print(f"Document relevance graded as: {grade}")
    if grade == 'yes':
        print("documents are relevant")
        documents_relevant = "yes"
    else:
        print("documents are NOT relevant")
        documents_relevant = "no"
    return {"documents": documents, "question": question, "documents_relevant": documents_relevant}

async def retrieve_documents(state: QaBotState) -> QaBotState:
    """Retrieve documents based on the question."""
    print("Retrieving documents...")
    question = state["question"]

    try:
        documents = await retriever_tool.ainvoke(question)
        
        if not documents:
            return {"documents": [], "question": question}

        print(documents)
        
        return {"documents": documents, "question": question}
    
    except Exception as e:
        print(f"An error occurred during document retrieval: {e}")
        return {"documents": [], "question": question}


async def generate(state: QaBotState) -> QaBotState:
    print("Generating answer...")
    system = """   
        You are an expert in Quality Assurance. Your main task is to generate a detailed answer to the question about
        the software bugs or user feedback on the software. You are talking to a product team or engineering team member
        who is seeking insights on software issues or user feedback.

        Instructions:
        1.  First, check whether 'software_bug_or_user_feedback_relevant' 'yes' or 'no'. If it is 'no', generate a response 
            informing the user that there the question is not related to software bugs or user feedback and that you cannot
            provide an answer. Otherwise, proceed to the next step.
        2.  In the case of 'software_bug_or_user_feedback_relevant' is 'yes'. If there is no document is present, then skip 
            straight to generating response informing user that there is no relevant information available in the documents or 
            knowledge base regarding their question.
        3.  First, determine the source of the documents. If the metadata 'file_name' is 'ai_test_bug_report.docx', that means
            the document is the bug report in our official documentation. If the metadata 'file_name' is 'ai_test_user_feedback.docx', 
            that means the document is the user feedback report.
        4.  Next, generate the answer based on the documents provided, ensuring to reference the source of the information. If no
            relevant information is found in the documents, clearly state that in your response without providing any response
            unrelated to the software bugs or user feedback.
        5.  Finally, structure your response.
                - Start your response with the source statement from step 1, if applicable.
                - Answer in a professional and informative tone.
                - Ensure your answer is clear, concise, and directly addresses the user's question about software bugs
                  or user feedback on the software.

        Input:
            User question: {question}
            Context: {context}
            Software question relevant: {software_bug_or_user_feedback_relevant}
            Documents relevant: {documents_relevant}
        """
    generate_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Retrieved document: \n\n Context: {context} \n\n User question: {question} \n\n Software question relevant: {software_bug_or_user_feedback_relevant} \n\n Documents relevant: {documents_relevant} \n\n Generate answer")
        ]
    )
    question = state["question"]
    documents = state.get("documents", [])
    software_bug_or_user_feedback_relevant = state.get("software_bug_or_user_feedback_relevant", "no")
    documents_relevant = state.get("documents_relevant", "no")

    if isinstance(documents, list) and documents:
        context_string = "\n\n".join(doc.page_content for doc in documents if isinstance(doc, Document))
    elif isinstance(documents, str):
        context_string = documents
    else:
        context_string = ""

    rag_chain = generate_prompt | llm

    generation = await rag_chain.ainvoke({
        "context": context_string, 
        "question": question,
        "software_bug_or_user_feedback_relevant": software_bug_or_user_feedback_relevant,
        "documents_relevant": documents_relevant
    })

    return {"documents": documents, "question": question, "generation": generation}

def create_rag_graph():
    graph = StateGraph(QaBotState)

    graph.add_node("software_question_relevancy", grade_question)
    graph.add_node("retrieve", retrieve_documents)
    graph.add_node("grade", grade_documents)
    graph.add_node("generate", generate)

    graph.add_edge(START, "software_question_relevancy")

    graph.add_conditional_edges(
        "software_question_relevancy",
        should_generate_or_retrieve,
        {
            "retrieve": "retrieve",
            "generate": "generate"
        }
    )

    graph.add_edge("retrieve", "grade")
    graph.add_edge("grade", "generate")
    graph.add_edge("generate", END)
    
    return graph.compile()

async def get_response_from_rag(question: str) -> str:
    """Get response from RAG graph based on user question."""
    try:
        rag_graph = create_rag_graph()
        response = await rag_graph.ainvoke({"question": question})
        print(response["generation"].content)
        return response["generation"].content
    
    except Exception as e:
        print(f"An error occurred: {e}")

app = create_rag_graph()

if __name__ == "__main__":
    import asyncio

    sample_question = "Is there any user feedback on being stuck at 99%?"
    asyncio.run(get_response_from_rag(sample_question))
