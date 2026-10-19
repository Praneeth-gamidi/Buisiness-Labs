import express from "express";
import dotenv from "dotenv";
import { z } from "zod";
import { draftReply } from "./service.js";
import { saveFeedback } from "./learning.js";
import { LLMConfigurationError, LLMOutputError, LLMProviderError } from "./llm-provider.js";
dotenv.config({path:"../.env"});
const app=express(); app.use(express.json({limit:"1mb"}));
const Email=z.object({id:z.string(),subject:z.string(),body:z.string(),customerName:z.string().optional(),companyVoice:z.string().optional()});
app.get("/health",(_req,res)=>res.json({status:"ok",service:"inbox-agent"}));
app.post("/draft",async(req,res)=>{
 const parsed=Email.safeParse(req.body); if(!parsed.success)return res.status(400).json({error:parsed.error.flatten()});
 try {const result=await draftReply(parsed.data); res.json({...result,status:"awaiting_human_approval",canSendAutomatically:false});}
 catch(e){
  if(e instanceof LLMConfigurationError)return res.status(503).json({error:e.message});
  if(e instanceof LLMProviderError)return res.status(e.code==="rate_limit"?429:e.code==="timeout"?504:502).json({error:e.message});
  if(e instanceof LLMOutputError)return res.status(502).json({error:e.message});
  if(e instanceof Error && e.name==="TimeoutError")return res.status(504).json({error:"Knowledge Brain request timed out. Try again."});
  console.error("Draft processing failed",e instanceof Error?e.name:"unknown error");
  return res.status(502).json({error:"Unable to generate a draft. Check Task 1 and the LLM provider configuration."});
 }
});
app.post("/feedback",(req,res)=>{try{saveFeedback(req.body);res.json({saved:true,autoSendEnabled:false});}catch{res.status(400).json({error:"Invalid feedback"});}});
const port=Number(process.env.TASK2_PORT||3000);
app.listen(port,()=>console.log(`Inbox Agent on port ${port}`));
