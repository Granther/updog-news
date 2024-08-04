from groq import Groq
import xml.etree.ElementTree as ET
import shortuuid
import os


class GenerateNews():
    def __init__(self, config):
        self.config = config
        if not os.path.exists(config.documents_path) or not os.path.exists(config.trash_path):
            raise RuntimeError(f"documents or trash directory not found at {config.documents_path} or {config.trash_path}")

    def parse_news(self):
        news = []

        for i, file in enumerate(os.listdir(self.config.documents_path)):
            if not os.path.isfile(self.config.documents_path+file):
                continue

            required = ["content", "title", "uuid"]
            filename = file
            file_path = os.path.join(self.config.documents_path, filename)

            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                for item in root:
                    if item.text != None or item.text == '': # Exit loop for cur iter if not empty
                        continue

                    if item.tag in required:
                        raise Exception
                    
                    match item.tag:
                        case "prompt":
                            item.text = None
                        case "length":
                            item.text = None
                        case "days":
                            item.text = self.config.def_days_old
                        case "author":
                            item.text = self.config.def_author
                        case "tag":
                            item.text = self.config.def_tag

                doc = dict(title=root[0].text, prompt=root[1].text, 
                        length=root[2].text, content=root[3].text, 
                        days=root[4].text, uuid=root[5].text, 
                        author=root[6].text, tag=root[7].text, short=(root[3].text)[0:150])
                
                news.append(doc)
            except:
                os.rename(file_path, os.path.join(self.config.trash_path, file))

        news = sorted(news, key=lambda story:int(story['days']))
        return news

    def create_story(self, title: str, content: str, prompt: str=None, length: str=None, days: str="0", author: str = None, tag: str = None):
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
            with open(f"{self.config.documents_path}/story_{ui.text}.xml", "wb") as f:
                tree.write(f)
            return ui.text
        except FileExistsError or FileNotFoundError:
            print("Unable to make story xml file")
        except Exception as e:
            print(f"Unknown exceptin occured when creating story XML file: {e}")

