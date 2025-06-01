
import litellm
import os

# os.environ['DEEPSEEK_API_KEY'] = ""

response = litellm.completion(
    model="deepseek/deepseek-chat", 
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    messages=[
       {"role": "user", "content": "don't return any other string other than linux command the user is looking for: 'find open ports in linux"}
   ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end='', flush=True)

