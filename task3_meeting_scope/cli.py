import argparse,json
from pathlib import Path
from .agents import build
from llm_provider import LLMConfigurationError, LLMOutputError, LLMProviderError
def main():
 p=argparse.ArgumentParser();p.add_argument("transcript");p.add_argument("--output",default="outputs/proposal.json");p.add_argument("--previous-scope");a=p.parse_args()
 previous=json.loads(Path(a.previous_scope).read_text()) if a.previous_scope else None
 try:
  result=build(Path(a.transcript).read_text(encoding="utf-8"),previous)
 except (LLMConfigurationError, LLMOutputError, LLMProviderError, RuntimeError) as error:
  p.exit(1,f"Generation failed: {error}\n")
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
 print(f"Draft saved to {out}; human approval required.")
if __name__=="__main__":main()
