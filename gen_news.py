from groq import Groq
import xml.etree.ElementTree as ET
import shortuuid
import os

document_path = "documents/"
trash_path = "documents/trash/"

class News:
    def __init__(self, title, prompt, length, content):
        self.title = title
        self.prompt = prompt
        self.content = content
        self.length = length

        if not os.path.exists(document_path) or not os.path.exists(trash_path):
            raise RuntimeError(f"documents or trash directory not found at {document_path} or {trash_path}")

def parse_news():
    news = []

    for i, file in enumerate(os.listdir('documents')):
        if not os.path.isfile(document_path+file):
            continue

        filename = file
        file_path = os.path.join(document_path, filename)

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            doc = dict(title=root[0].text, prompt=root[1].text, 
                    length=root[2].text, content=root[3].text, 
                    days=root[4].text, uuid=root[5].text, 
                    author=root[6].text, tag=root[7].text, short=(root[3].text)[0:150])
            
            int(doc['days'])

            news.append(doc)
        except:
            os.rename(file_path, os.path.join(trash_path,file))

    news = sorted(news, key=lambda story:int(story['days']))
    return news

def create_story(title: str, content: str, prompt: str="none", length: str="none", days: str="0", author: str="Julia Herald", tag: str="Technology"):
    root = ET.Element("document")
    tit = ET.SubElement(root, "title") 
    tit.text = title

    prom = ET.SubElement(root, "prompt") 
    prom.text = prompt

    len = ET.SubElement(root, "length") 
    len.text = length

    cont = ET.SubElement(root, "content") 
    cont.text = content

    da = ET.SubElement(root, "days") 
    da.text = days

    ui = ET.SubElement(root, "uuid") 
    ui.text = shortuuid.uuid()

    auth = ET.SubElement(root, "author") 
    auth.text = author

    t = ET.SubElement(root, "tag") 
    t.text = tag

    tree = ET.ElementTree(root) 

    try:
        with open(f"{document_path}/story_{ui.text}.xml", "wb") as f:
            tree.write(f)
    except FileExistsError or FileNotFoundError:
        print("Unable to make story xml file")
    except Exception as e:
        print(f"Unknown exceptin occured when creating story XML file: {e}")
 