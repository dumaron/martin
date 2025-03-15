from openai import OpenAI
import os

singleton_client = None


def init_openai():
   global singleton_client

   if singleton_client is None:
      singleton_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

   return singleton_client


def ask_ai(question: str) -> str:
   client = init_openai()
   response = client.chat.completions.create(
      model='gpt-4-1106-preview',
      messages=[
         {"role": "user", "content": question},
      ],
   )
   return response.choices[0].message.content
