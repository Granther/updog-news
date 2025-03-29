
""" Removes the <|START_QUOTE|>, <|END_QUOTE|> & <|LINK_SRC|> tokens """
def rm_quote_toks(content: str) -> str:
    return content.replace('<|START_QUOTE|>', '').replace('<|END_QUOTE|>', '').replace('<|LINK_SRC|>', '')

""" Takes content with above tokens in it and adds a quote and link from the list of tuples 'quotes' """
def insert_quotes(content: str, quotes: list) -> str:
    # Ensure a space exists between word and token
    content = content.lower().replace('|>', '|> '). replace('<|', ' <|').split() 
    cur_quote_id = 0
    print(content)
    i = 0
    while i < len(content)-1:
        if '<|start_quote|>' in content[i]:
            content.pop(i) # i is currently the word after where start_quote was
            while '<|end_quote|>' not in content[i-1]:
                content.pop(i)
                i += 1
        if '<|end_quote|>' in content[i-1]:
            content.pop(i) # Remove end_quote
            content.insert(i, f"<|QUOTE_ID-{cur_quote_id}|>") # Insert quote id tok to be replaced later
            continue
        i += 1

    print(content)

if __name__ == "__main__":
    content = 'Hello, its me joe: <|START_QUOTE|>"I love apples!" <|END_QUOTE|> Oh MAIN'
    insert_quotes(content, [])
