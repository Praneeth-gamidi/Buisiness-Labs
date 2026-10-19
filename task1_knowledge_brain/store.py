import sqlite3
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from .config import CHROMA_PATH, SQLITE_PATH

client = chromadb.PersistentClient(path=CHROMA_PATH)
embedding = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection("help_center_articles", embedding_function=embedding)

def db():
    con = sqlite3.connect(SQLITE_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS pages(url TEXT PRIMARY KEY,title TEXT,hash TEXT,status TEXT,last_seen TEXT DEFAULT CURRENT_TIMESTAMP)""")
    con.execute("""CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY,question TEXT,answer TEXT,urls TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    return con

def upsert(url, title, digest, chunks):
    with db() as con:
        con.execute("""INSERT INTO pages(url,title,hash,status,last_seen) VALUES(?,?,?,'active',CURRENT_TIMESTAMP)
        ON CONFLICT(url) DO UPDATE SET title=excluded.title,hash=excluded.hash,status='active',last_seen=CURRENT_TIMESTAMP""", (url,title,digest))
    old = collection.get(where={"url":url})
    if old.get("ids"): collection.delete(ids=old["ids"])
    if chunks:
        collection.upsert(ids=[f"{url}::chunk::{i}" for i in range(len(chunks))],
            documents=chunks, metadatas=[{"url":url,"title":title,"chunk":i} for i in range(len(chunks))])

def reconcile(seen):
    with db() as con:
        for (url,) in con.execute("SELECT url FROM pages WHERE status='active'").fetchall():
            if url not in seen:
                con.execute("UPDATE pages SET status='removed' WHERE url=?", (url,))
                old=collection.get(where={"url":url})
                if old.get("ids"): collection.delete(ids=old["ids"])

def retrieve(query, k=5):
    if not collection.count(): return []
    r=collection.query(query_texts=[query],n_results=min(k,collection.count()))
    return [{"text":d,"url":r["metadatas"][0][i].get("url",""),"title":r["metadatas"][0][i].get("title","Untitled")} for i,d in enumerate(r["documents"][0])]

def save_feedback(q,a,urls):
    import json
    with db() as con: con.execute("INSERT INTO feedback(question,answer,urls) VALUES(?,?,?)",(q,a,json.dumps(urls)))
    uid=f"expert-feedback::{abs(hash(q+a))}"
    collection.upsert(ids=[uid],documents=[f"Question: {q}\nVerified answer: {a}"],metadatas=[{"url":uid,"title":"Verified expert answer"}])
