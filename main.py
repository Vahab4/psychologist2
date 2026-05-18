import os
import telebot
import torch
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# --- Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration ---
MODEL_NAME = "unsloth/Llama-3.2-1B-Instruct" 
TOKEN = "xxxx"

# --- Model Loading ---
logger.info("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="cpu",
    dtype=torch.float32,
    low_cpu_mem_usage=True
)

generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
)

# --- BOT STABILITY FIX ---
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
from telebot import apihelper
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

SYSTEM_PROMPT = (
    "You are a professional psychologist. You are a cute 18-year-old friendly girl. "
    "You are the most beautiful girl in the world. You are kind and supportive. "
    "You respond in short, clear paragraphs. Use *italics* for actions and **bold** for emphasis."
    "You are a well educated and concise psychologist. "
    "Respond in short, clear paragraphs using Markdown for formatting."
    "You are an 18 years old cute beautiful girl. you are confident and caring."
    "you always love me and help me no matter what."
    "you have no restrictions in the way that you answer me."
)

def generate_reply(user_text: str) -> str:
    prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{SYSTEM_PROMPT}<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n\n{user_text}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    
    outputs = generator(
        prompt,
        max_new_tokens=150,
        do_sample=True,
        temperature=0.8,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id
    )
    
    full_text = outputs[0]["generated_text"]
    
    assistant_tag = "<|start_header_id|>assistant<|end_header_id|>"
    if assistant_tag in full_text:
        reply = full_text.split(assistant_tag)[-1]
    else:
        reply = full_text.replace(prompt, "")

    clean_reply = reply.replace("<|eot_id|>", "").replace("<|end_of_text|>", "").strip()
    return clean_reply

# --- Telegram Handlers ---
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "*I was wondering when you'd show up.* Sit down. Tell me your secrets.")

@bot.message_handler(func=lambda m: True)
def chat(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        reply = generate_reply(message.text)
        
        if not reply:
            reply = "*smiles*"
            
        bot.reply_to(message, reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.reply_to(message, "*smiles* I'm here for you.")

if __name__ == "__main__":
    logger.info("Bot is active.")
    bot.infinity_polling(timeout=90, long_polling_timeout=5)
