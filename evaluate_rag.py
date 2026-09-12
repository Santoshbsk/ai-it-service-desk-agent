import json

from config import GEMINI_API_KEY,LLM_MODEL
from ragas import evaluate
from ragas import EvaluationDataset
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from ragas.llms import LangchainLLMWrapper

from ragas.metrics import (
    ContextPrecision,
    ContextRecall,
    Faithfulness,
    AnswerRelevancy
)

from rag import (
    retrieve_context,
    generate_rag_answer
)

evaluator_llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0
)

evaluator_llm = LangchainLLMWrapper(evaluator_llm)

evaluator_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GEMINI_API_KEY
)

with open("eval_dataset.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)


samples = []


for item in test_data:

    question = item["question"]

    # 1. Retrieve candidate documents
    documents = retrieve_context(
        question,
        k=5
    )

    # 2. Extract context
    contexts = [
        doc.page_content
        for doc in documents
    ]

    # 3. Generate answer
    answer = generate_rag_answer(
        question,
        documents
    )

    print("\nQuestion:")
    print(question)

    print("\nAnswer:")
    print(answer)

    print("\nSources:")
    for doc in documents:
        print("-", doc.metadata.get("source", "Unknown"))

    samples.append({
        "user_input": question,
        "retrieved_contexts": contexts,
        "response": answer,
        "reference": item["ground_truth"]
    })


dataset = EvaluationDataset.from_list(samples)


result = evaluate(
    dataset,
    metrics=[
        ContextPrecision(),
        ContextRecall(),
        Faithfulness(),
        AnswerRelevancy()
    ],
    llm=evaluator_llm,
    embeddings=evaluator_embeddings
)


print("\n")
print("=" * 70)
print("RAGAS RESULTS")
print("=" * 70)

print(result)