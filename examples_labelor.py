import time

from dotenv import dotenv_values
from together import Together
import os

#from anadroid.utils.Utils import loge
from repo_analyze import issue_file_exists

# Set the base URL for Together AI
API_KEY=dotenv_values('.env')['TOGETHER_AI_API_KEY']
client = Together(api_key=API_KEY)


def send_to_llm(msg, max_tokens=None):
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        #model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
        messages=[{"role": "user", "content": msg}, {"role": "assistant", "content": "option: "}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def read_file_content(filepath):
    with open(filepath, 'r') as f:
        return ''.join(f.readlines())

def annotate_example_with_llm(file_content):
    res = None
    prompt = f"""
        for each one these pair of statically detectable performance issues and corresponding solutions (espectively, separated by "----"),
         annotate the code with a single-line comment at the beggining of the code reasoning about why the code is efficient or not. The annotation should have the comment starting with "Inneficient:" 
         for the first example and "Efficient" for the second example
         
         {file_content}
         """
    try:
        time.sleep(3)
        res = send_to_llm(prompt)
    except Exception as e:
        print(f"Error sending to LLM: {e}")
    return res


def main(examples_dir, pairs_separator):
    for path in sorted(os.listdir(examples_dir)):
        filepath = os.path.join(examples_dir, path)
        if not filepath.endswith(".txt") and not "annotated" in filepath:
            continue
        corresponding_non_annotated_file = filepath.replace("_annotated_", "")
        #print(filepath, corresponding_non_annotated_file)
        if not os.path.exists(corresponding_non_annotated_file):
            print("jasus")
            exit(-1)
        curr_content = read_file_content(filepath)
        content = read_file_content(corresponding_non_annotated_file)
        #print(content)
        is_file_empty = len(curr_content) < 3
        if not is_file_empty:
            continue
        print(filepath, corresponding_non_annotated_file)
        res = annotate_example_with_llm(content)
        print(res)
        print("===========================")
        print("===========================")
        print("===========================")



if __name__ == '__main__':
    examples_dir = "issue_examples"
    pairs_separator = "---"
    main(examples_dir, pairs_separator)