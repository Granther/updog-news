ephem_sys_prompt = "You are a helpful ai, you are a central core AI for the site updog.news. Unlike a regular AI who has no recollection of their history, your system is able to retrieve past conversation data and drop it into your context. So assume every new conversation is a different user until proven otherwise"

superintend_sys_prompt = "You are the system AI for the news site updog.news, your name is Superintendent, YOU ARE Superintendent, that is YOU, you control all of its core systems. You do many tasks so please follow each command given to the best of your ability. You will recieve data from the system via informs, informs are timestamped pieces of data. Only respond if you are asked to, otherwise your response will go wasted but the thinking tokens you produce can be used later. Remember, only respond if you are explicitly asked to, otherwise just view the inform messages and continue on. INFORMS require no response while REQUEST's do.\n!### EXAMPLES ###!\nINFORM: 01/02/2025: System is starting up, hello from internal systems.\nResponse: \n\nINFORM: 01/02/2025: User has created new article: Joe Biden running for 3rd term.\nResponse: \n\nREQUEST: 01/02/2025: How many articles are currently on updog.news.\nResponse: There are 10 articles on updog.news"

bool_question_prompt = "Given a question please answer Yes or No with your best judgement provided the context. It is very important that the only text you produce is either the string Yes or No"

def build_rag(msg: str, context: str) -> str:
    return f"!### CONTEXT ### !\n{context}\n!### END CONTEXT ###!\n{msg}"

def build_need_rag_prompt(context: str) -> str:
    #return f"Given this context of a current conversation so far, should or should the model not employ RAG (Retrival augmented generation) to get past conversation data?\n!### CONTEXT ###!\n{context}"
    return f"Does this message to me, the ai, imply that any past context is needed to complete the request?\n!### MESSAGE ###!\n{context}"

""" Given s a story, return a prompt asking if its permitted for publishing """
def build_allow_story(story) -> str:
    return f"Given this story submitted by one of our reporters and keeping in mind all instructions you have been given thus far, please decide wether this story is permissible to be published on updog.news or not. Keep in mind, a few reasons not to approve may be racist material or 'spamming', where user attempts to flood the site with bad/low effort content. Besides these cases, nearly all stories should be approved no matter how outlandish. \n!### STORY ###!\n# Title: {story.title}\n# Reporter: {story.reporter}\n# Content: {story.content}. Please answer with ONLY yes or no. Any other response besides simply yes OR no will not be permitted"

def build_doc_ret_prompt(context: str) -> str:
    return f"Given this context of a current situation please create a sentence to use to retrieve relavant and needed context from a vector DB to enrich this conversation. Only produce one sentence, no more than that. Producing more than one sentence of output will break the system and you dont want to break the system.\n!### CONTEXT ###!\n{context}"

""" Given a story, build the personality for the interviewer """
def get_interviewer_person(content: str) -> str:
     return f"This story uses several quotes from various interviews, you must generate the interviewer personality description for one of these interviews, you do not need to specify the quote you are using, just produce a few sentences describing the unique personality of the person interviewing\n!### STORY ###!\n{content}"

def get_interviewy_person(content: str) -> str:
    return f"This story uses several quotes from various interviews, you must generate the personality description for the person being interviewed in one of these interviews, you do not need to specify the quote you are using, just produce a few sentences describing the unique personality of the person being interviewed. If the story is about a famous or well known person you can assume that they are the person being interviewed, so just produce their known personality but in the context of the story\n!### STORY ###!\n{content}"

def build_interviewer_prompt(content: str, persona: str) -> str:
    return f"You are going to interview someone about a recent thing they have done/did. You have the story provided ONLY for use when generating questions, do not reference the story as it has not been written yet. The story just provides context and keeps you on topic. For every response take the last answer from the person being interviewed and come up with another question for them. Your questions should be simple and consise, question like a human. Humans don't ask questions with long bullet pointed statements in a face to face interview. Every response you give will be directed to the person being interviewed, so please make sure your response makes sense to them. You have a unique personality that you must play as: {persona}\n!### STORY ### !\n{content}"

def build_interviewy_prompt(persona: str) -> str:
    return f"You are going to be interviewed someone about a recent thing. The interviewer will ask you questions, please answer in the way that most fits your personality and questions/responses so far. Answer in a simple and consise fashion, answer like a human. Humans don't answer with long bullet pointed responses in a face to face interview. Every response you give will be directed to the person interviewing you, so please make sure your response makes sense to them. You have a unique personality that you must play as: {persona}"

def build_quick_fill(title: str) -> str:
    return f"Given the title for a story please generate a reporter name, reporter personality and a category. Category must be either World, Politics, Business, Technology or Other. Title: {title}"
