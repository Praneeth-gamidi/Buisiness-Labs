import fs from "node:fs"; import path from "node:path";
export function saveFeedback(data:unknown){
 const file=path.resolve("data","inbox_feedback.jsonl"); fs.mkdirSync(path.dirname(file),{recursive:true});
 fs.appendFileSync(file,JSON.stringify({...data as object,recordedAt:new Date().toISOString()})+"\n");
 // Conservative starter: never auto-send until category-level quality is evaluated.
}
