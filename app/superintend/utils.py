""" Takes a list and packs it into str """
def stringify(doc) -> str:
    string = ""
    for item in doc:
        string += f"{item}\n\n"
    return string

""" Takes reponse from R1, returns either thought toks or resp (no thoughts) only """
def postproc_r1(response: str, think_only: bool=False):
    if think_only:
        return response.split('</think>')[0] # Return only the think toks    
    return response.split('</think>')[1]

""" If 'yes' is in response return True, otherwise No """
def bool_resp(response: str) -> bool:
    return 'yes' in response.lower()

