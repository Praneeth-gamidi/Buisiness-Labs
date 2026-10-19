import dotenv from "dotenv";
import { z } from "zod";
import { generateText, LLMOutputError, parseJsonObject, providerName } from "./llm-provider.js";
dotenv.config({path:"../.env"});
export type Email={id:string;subject:string;body:string;customerName?:string;companyVoice?:string};
const DraftSchema=z.object({subject:z.string(),reply:z.string(),needsHuman:z.boolean(),reason:z.string()});
const KnowledgeSchema=z.object({
 answer:z.string(),
 sources:z.array(z.object({title:z.string(),url:z.string()})),
 needs_human:z.boolean(),
 llm_provider:z.string().optional(),
});
export async function draftReply(email:Email){
 const base=process.env.TASK1_BASE_URL||"http://localhost:8000";
 const r=await fetch(`${base}/query`,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({question:`Subject: ${email.subject}\nEmail: ${email.body}`,top_k:5}),signal:AbortSignal.timeout(30_000)});
 if(!r.ok)throw new Error(`Knowledge Brain API error ${r.status}`);
 const kb=KnowledgeSchema.parse(await r.json());
 const raw=await generateText([
  {role:"system",content:"Draft concise, professional support emails. Do not invent policy. Never claim the email was sent. Flag uncertainty. Return only a JSON object with subject, reply, needsHuman, reason."},
  {role:"user",content:`Customer: ${email.customerName||"Customer"}. Company voice: ${email.companyVoice||"warm and professional"}. Email subject: ${email.subject}. Email: ${email.body}. Knowledge answer: ${kb.answer}. Sources: ${kb.sources.map(s=>s.title+" "+s.url).join("\n")}. Needs human: ${kb.needs_human}`},
 ],700);
 let parsed;
 try {parsed=DraftSchema.parse(parseJsonObject(raw));}
 catch(error){if(error instanceof LLMOutputError)throw error;throw new LLMOutputError("The model returned an invalid email draft; no draft was accepted.");}
 return {emailId:email.id,knowledge:kb,draft:JSON.stringify(parsed,null,2),requiresHumanReview:kb.needs_human||parsed.needsHuman,llmProvider:providerName()};
}
