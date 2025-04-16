import os
import time
from time import sleep
import datetime
import threading

import shortuuid

from app.config import NewsConfig
from app.logger import create_logger
from .prompts import ephem_sys_prompt, superintend_sys_prompt, bool_question_prompt, build_rag, build_need_rag_prompt, build_allow_story, build_doc_ret_prompt, build_interviewy_prompt, build_interviewer_prompt, get_interviewy_person, get_interviewer_person, build_quick_fill, get_iview_title, build_fix_schrod_title, gen_news_prompt
from .utils import stringify, postproc_r1, bool_resp, extract_tok_val, pretty_interview
from app.models import Interview, Story
from app import db

logger = create_logger(__name__)

def_reporter = "Jim Scrimbus"
def_category = "World"
def_personality = "Just a humble writer at Updog news, hes a little politically incorrect though"
def_iviewer_name = "Jimothy Honest"
def_iviewer_persona = "Just a simple Honest guy, he hates kids though, like he cant stop talking about it"
def_iviewy_name = "Elon Musk"
def_iviewy_persona = "Hey, its me, Elon Musk, meet my son slkasiaoifhwqoiehfwpoifh"
allowed_categories = ["World", "Technology", "Business", "Politics", "Other"]

class News:
    def __init__(self, config: NewsConfig, core):
        self.config = config
        self.max_interview_q = 2
        self.core = core

    """ Takes title, returns (reporter, personality, category """
    def quick_fill(self, title: str):
        logger.debug("Starting Quick fill to core")
        # Use quick model 
        resp = self.core.request(build_quick_fill(title), quick=True)
        reporter = extract_tok_val(resp, "REPORTER")
        if not reporter:
            reporter = def_reporter
        category = extract_tok_val(resp, "CATEGORY")
        if not category or category not in allowed_categories:
            category = def_category 
        personality = extract_tok_val(resp, "PERSONALITY")
        if not personality:
            personality = def_personality
        
        logger.debug(f"{reporter}, {personality}, {category}")

        return (reporter, personality, category)

    """ Generate the 2 personalities for the interview. Interviewer and Interviewy """
    def _gen_interv_persons(self, content: str):
        interviewer = self.core.request(get_interviewer_person(content))
        interviewy = self.core.request(get_interviewy_person(content))
        return (interviewer, interviewy)

    """ Given the story, and interview (name, personality) generate a interview """
    def _gen_interview(self, app, story) -> str:
        with app.app_context():
            content = story.content
            logger.debug("Generating interview")
            n_interview_q = 0
            model = "gemma2-9b-it"
            iviewer_resp = postproc_r1(self.core.request(get_interviewer_person(content), sticky=False))
            iviewy_resp = postproc_r1(self.core.request(get_interviewy_person(content), sticky=False))
            
            iviewer_name, iviewer_persona = extract_tok_val(
                    iviewer_resp, 
                    "NAME", 
                    default=def_iviewer_name
            ), extract_tok_val(
                    iviewer_resp, 
                    "PERSONA", 
                    default=def_iviewer_persona
            )

            iviewy_name, iviewy_persona = extract_tok_val(
                    iviewy_resp, 
                    "NAME", 
                    default=def_iviewy_name
            ), extract_tok_val(
                    iviewy_resp, 
                    "PERSONA", 
                    default=def_iviewy_persona
            ) 

            viewer_prompt = build_interviewer_prompt(
                    content, 
                    persona=iviewer_persona, 
                    name=iviewer_name
            ) # The interviewer knows about the story
            viewy_prompt = build_interviewy_prompt(
                    persona=iviewy_persona, 
                    name=iviewy_name
            )

            iview_title = extract_tok_val(postproc_r1(self.core.request(
                get_iview_title(
                    content=content,
                    iviewer=iviewer_name,
                    iviewy=iviewy_name,
                )
            )), "TITLE", default=f"{iviewer_name} interviews {iviewy_name}")

            viewer_messages, viewy_messages = [{"role": "system", "content": viewer_prompt}, {"role": "user", "content": "BEGINNING OF INTERVIEW"}], [{"role": "system", "content": viewy_prompt}]

            #logger.debug(f"Interviewer personality: {iviewer_resp}")
            #logger.debug(f"Interviewy personality: {iviewy_resp}")

            interview_content = [] # List of dicts
            while n_interview_q < self.max_interview_q:
                # Gen question
                #question = postproc_r1(self._submit_task(self._groq_chat, viewer_messages, model)).replace('\n', '')
                question = self.core.chat(viewer_messages)
                sleep(1.5) # Give the API a break so we dont over use

                # Make sure interviewer knows what he asked
                viewer_messages.append({"role": "assistant", "content": question})
                viewer_messages.append({"role": "system", "content": viewer_prompt})

                # Add to interviewy context
                viewy_messages.append({"role": "user", "content": question})
                # Ask them to answer
                #answer = postproc_r1(self._submit_task(self._groq_chat, viewy_messages, model)).replace('\n', '')
                answer = self.core.chat(viewy_messages)
                sleep(1.5)

                # Make sure personas know what they produces
                viewy_messages.append({"role": "assistant", "content": answer})
                viewy_messages.append({"role": "system", "content": viewy_prompt})
                # Add answer to interviewer context
                viewer_messages.append({"role": "user", "content": answer})
                
                interview_content.append({"question": question, "answer": answer})
                n_interview_q += 1
            uuid = shortuuid.uuid()
            logger.debug(f"Finished interview with uuid: {uuid}")
            formatted_iview = pretty_interview(interview_content)
            self.core.embed_interview(interview_content, uuid)
            quote_first_gen = extract_tok_val(content, "QUOTE", default="")
            quote = self.core.query("quotes", question=quote_first_gen, metadata={"type": "answer"})
            #print("QUOTE: ", quote)
            interview = Interview(uuid=uuid, title=iview_title, content=formatted_iview, interviewer=iviewer_name, interviewy=iviewy_name)
            db.session.add(interview)
            db.session.commit()

    """ Async generation of interviews for story, uses passed 'app' for context """
    def _gen_interviews(self, app, story):
        threading.Thread(target=self._gen_interview, args=(app, story), daemon=True).start()

    """ Since some chat platforms dont allow building a URL with spaces, they must be escaped, basically decompresses a title """
    def fix_schrod_title(self, old_title: str) -> str:
        return extract_tok_val(postproc_r1(self.core.request(build_fix_schrod_title(old_title))), "TITLE", default=old_title)

    """ Pass in entire story and return wether Super allows it or not """
    def _allow_story(self, story) -> bool:
        resp = self.core.request(build_allow_story(story))
        return bool_resp(postproc_r1(resp))

    """ Helper to change class of html tags to work with TailwindCSS for display """
    def _fix_html_class(self, content: str) -> str:
        extra_h = 'mt-6'
        extra_p = 'my-3'
        h1 = f'<h1 class="text-3xl font-playfair font-bold {extra_h}">'
        h2 = f'<h2 class="text-2xl font-playfair font-bold {extra_h}">'
        h3 = f'<h3 class="text-xl font-playfair font-bold {extra_h}">'
        h4 = f'<h4 class="text-lg font-playfair font-bold {extra_h}">'
        h5 = f'<h5 class="text-md font-playfair font-bold {extra_h}">'
        p = f'<p class={extra_p}>'
        return content.replace('<h1>', h1).replace('<h2>', h2).replace('<h3>', h3).replace('<h4>', h4).replace('<h5>', h5).replace('<p>', p)

    def _fix_html_class_(self, content: str) -> str:
        extra_h = 'mt-6'
        extra_p = 'my-3'
        h1 = f'<h1 class="text-3xl font-playfair font-bold {extra_h}">'
        h2 = f'<h2 class="text-2xl font-playfair font-bold {extra_h}">'
        h3 = f'<h3 class="text-xl font-playfair font-bold {extra_h}">'
        h4 = f'<h4 class="text-lg font-playfair font-bold {extra_h}">'
        h5 = f'<h5 class="text-md font-playfair font-bold {extra_h}">'
        p = f'<p class={extra_p}>'
        return content.replace('<h1>', h1).replace('<h2>', h2).replace('<h3>', h3).replace('<h4>', h4).replace('<h5>', h5).replace('<p>', p)


    """ Given the title and person generates the news story content """
    def _gen_news_content(self, title: str, persona: str) -> str:
        return self.core.request(f'### Title: {title}\n### Persona: {persona}', sys_prompt=gen_news_prompt, quick=True, sticky=False)

    def get_similar_titles(self, title: str, n_results: int=3) -> list:
        return self.core.query("titles", title, n_results=n_results, bad_doc=title)

    """ Given the params for the story as a dict
    - Generates story and fixes CSS classes
    - Creates SQL entry
    - Ensures that superintend will allow the story on the site
    - Async generates the interviews relavent
    - No return only side effects 
    """
    def write_new_story(self, app, item: dict):
        with app.app_context():
            try:
                content = self._gen_news_content(item['title'], item['personality'])
                content = self._fix_html_class(content)
                story = Story(title=item['title'], content=content, reporter=item['reporter'], catagory=item['catagory'])
                if not self._allow_story(story):
                    raise Exception("Superintendent denied your story")
                self.core.embed([story.title], "titles")
                self._gen_interviews(app, story) # Dispatches new thread in hoodlem
                db.session.add(story)
                db.session.commit()
            except Exception as e:
                raise e

# """ Given a context dynamically created prompt to generate a document ret string and return document """
# def _retrieve_context(self, prompt: str, uuid: str) -> str:
#     messages = [{"role": "user", "content": prompt}]
#     resp = self.raw_chat(messages)
#     print(resp)
#     return self.core.query("chats", resp, bad_uuid=uuid)