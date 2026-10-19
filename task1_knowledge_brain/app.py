from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from llm_provider import LLMConfigurationError, LLMProviderError, generate_text, provider_name
from .store import retrieve, save_feedback
from .ingest import ingest

app=FastAPI(title="Knowledge Brain API",version="0.1")
class Question(BaseModel):
    question:str=Field(min_length=3,max_length=4000)
    top_k:int=Field(default=5,ge=1,le=10)
class Feedback(BaseModel):
    question:str
    expert_answer:str
    source_urls:list[str]=Field(default_factory=list)
@app.get("/health")
def health(): return {"status":"ok","service":"knowledge-brain"}
@app.post("/query")
def query(req:Question):
    chunks=retrieve(req.question,req.top_k)
    if not chunks: return {"answer":"I could not find enough indexed information. Please ask a human expert.","sources":[],"needs_human":True,"llm_provider":provider_name()}
    context="\n\n".join(f"[Source {i+1}] {x['title']} | {x['url']}\n{x['text']}" for i,x in enumerate(chunks))
    try:
        answer=generate_text([
            {"role":"system","content":"Answer only from context. Never invent policies. If evidence is insufficient, say so and request human review. Cite as [Source 1]."},
            {"role":"user","content":f"Question: {req.question}\n\nContext:\n{context}"},
        ],max_tokens=900)
    except LLMConfigurationError as error:
        raise HTTPException(503,str(error)) from None
    except LLMProviderError as error:
        status=429 if error.code=="rate_limit" else 504 if error.code=="timeout" else 502
        raise HTTPException(status,str(error)) from None
    uncertain=any(s in answer.lower() for s in ["i don't know","not enough information","cannot determine"])
    selected_provider=provider_name()
    return {"answer":answer,"sources":[{"title":x["title"],"url":x["url"],"excerpt":x["text"][:250]} for x in chunks],"needs_human":uncertain or selected_provider=="mock","llm_provider":selected_provider}
@app.post("/feedback")
def feedback(req:Feedback):
    save_feedback(req.question,req.expert_answer,req.source_urls)
    return {"saved":True}
@app.post("/admin/ingest",status_code=202)
def start_ingest(tasks:BackgroundTasks):
    tasks.add_task(ingest)
    return {"accepted":True}
