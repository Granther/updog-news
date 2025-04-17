from openai import OpenAI
from groq import Groq

from app.config import Keys, Model

""" Takes a list and packs it into str """
def stringify(doc) -> str:
    string = ""
    for item in doc:
        string += f"{item}\n\n"
    return string

""" Takes reponse from R1, returns either thought toks or resp (no thoughts) only """
def postproc_r1(response: str, think_only: bool=False):
    try:
        if think_only:
            return response.split('</think>')[0] # Return only the think toks    
        return response.split('</think>')[1]
    except:
        return response

""" If 'yes' is in response return True, otherwise No """
def bool_resp(response: str) -> bool:
    return 'yes' in response.lower()

""" Takes a string of text and a token_core (REPORTER_NAME) where token is <REPORTER_NAME> {name} </REPORTER_NAME>. Returns a list of all vals occuring in all sets"""
# Now we want to produce a list if there is multiple vals
def extract_tok_val(content: str, tok_core: str, default: str=None) -> list:
    # Ensure tokens have spaces on both sides and break apart into list
    content = content.replace('\n', ' ').replace('>', '> ').replace('<', ' <').split()
    opening, closing = f"<{tok_core}>", f"</{tok_core}>"
    val, in_val, vals = "", False, []
    for i, item in enumerate(content):
        if opening in item:
            in_val = True
            continue
        if closing in item:
            in_val = False
            # Append val to vals
            vals.append(val)
            # Set val to ""
            val = ""
        if i == len(content)-1: # Last item in list
            in_val = False
        # If in val we catch the append it to val
        if in_val:
            if closing in content[i+1]: # Closing is next token
                val += f"{item}" # No space added
            else:
                val += f"{item} "
    if not len(vals):
        return [default]
    return vals

""" Given a list of QA dicts, returns a prettier html unsafes str """
def pretty_interview(content: list) -> str:
    string = ""
    for item in content:
        string += f"<p class='my-3'>{item['question']}</p><p class='my-3'>{item['answer']}</p>"
        #string += f"{item['question']}<br>{item['answer']}<br><br>"
    return string    

""" Given a 'Model', which has a name and a backend, return the correct client """
def build_client(model: Model, keys: Keys):
    if model.backend == 'groq':
        return Groq(api_key=keys.GROQ_API_KEY)
    elif model.backend == 'featherless':
        return OpenAI(
                base_url="https://api.featherless.ai/v1",
                api_key=keys.FEATHERLESS_API_KEY,
            )
    else:
        raise Exception(f"Passed model ({model.name}) does not have correct backend ({model.backend})")

if __name__ == "__main__":
    print(extract_tok_val("Hello <REPORTER>James danial</REPORTER>", "REPORTER"))

