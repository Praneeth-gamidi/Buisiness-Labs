import hashlib, time, requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .config import SITEMAP_URL, DELAY
from .store import upsert, reconcile

HEADERS={"User-Agent":"BusinessLabsKnowledgeBrain/0.1 educational crawler"}
TARGET_HOST="support.brilliantdirectories.com"

def sitemap_urls():
    r=requests.get(SITEMAP_URL,headers=HEADERS,timeout=25); r.raise_for_status()
    urls=[x.get_text(strip=True) for x in BeautifulSoup(r.text,"xml").find_all("loc")]
    result=[]
    for url in urls:
        if "sitemap" in url.lower() or url.endswith(".xml"):
            if urlparse(url).hostname != TARGET_HOST:
                result.append(url)
                continue
            try:
                child=requests.get(url,headers=HEADERS,timeout=25)
                if child.ok and "<urlset" in child.text:
                    result.extend(x.get_text(strip=True) for x in BeautifulSoup(child.text,"xml").find_all("loc"))
                else: result.append(url)
            except requests.RequestException: result.append(url)
            time.sleep(DELAY)
        else: result.append(url)
    return list(dict.fromkeys(x for x in result if urlparse(x).scheme in ("http","https")))

def extract(url):
    r=requests.get(url,headers=HEADERS,timeout=25)
    if r.status_code==404: return None
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"lxml")
    for tag in soup(["script","style","nav","footer","header","noscript"]): tag.decompose()
    title=soup.title.get_text(" ",strip=True) if soup.title else url
    main=soup.select_one("article,main,.article-body,.content") or soup.body or soup
    text=main.get_text(" ",strip=True)
    chunks=[text[i:i+1200] for i in range(0,len(text),1000) if text[i:i+1200].strip()]
    return title,text,chunks

def ingest():
    urls=sitemap_urls(); seen=set()
    target_urls=[url for url in urls if urlparse(url).hostname==TARGET_HOST]
    crawl_complete=bool(target_urls)
    indexed=0
    print(f"Found {len(urls)} URLs; delay={DELAY}s")
    for n,url in enumerate(urls,1):
        if urlparse(url).hostname != TARGET_HOST: continue
        try:
            result=extract(url)
            if result:
                title,content,chunks=result
                if len(content)>80:
                    upsert(url,title,hashlib.sha256(content.encode()).hexdigest(),chunks); seen.add(url); indexed+=1
                else:
                    crawl_complete=False
        except requests.RequestException as e:
            crawl_complete=False
            print(f"Failed {url}: {e}")
        print(f"{n}/{len(urls)}")
        time.sleep(DELAY)
    if crawl_complete and indexed:
        reconcile(seen)
    else:
        print("Skipped stale-page reconciliation because the crawl was incomplete or yielded no usable pages.")
    print(f"Indexed {len(seen)} pages")
if __name__=="__main__": ingest()
