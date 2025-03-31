import base64

""" Given a title, generate an image and return it as a base64 utf-8 encoded string """
def generate_image(title: str) -> str:
    with open("donald.jpg", "rb") as img:
        s = base64.b64encode(img.read())
        return s.decode("utf-8")

