
def extract_tok_val_test():
    content = "Yo check it a <NEW_STORY> Joe Bomo sig momo </NEW_STORY> Anyway, I'm rizzing <NEW_STORY> Grimbuompus micheal </NEW_STORY>"
    tok_core = "NEW_STORY"
    default = "Grizm"

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

if __name__ == "__main__":
    print(extract_tok_val_test())