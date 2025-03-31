import base64

from flask import Flask
import torch
from diffusers import FluxPipeline
from io import BytesIO

pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload() #save some VRAM by offloading the model to CPU. Remove this if you have enough GPU power

app = Flask(__name__)

@app.route("/<title>")
def index(title: str):
    prompt = f"Generate a news cover image for this title: {title}"
    image = pipe(
        prompt,
        guidance_scale=0.0,
        num_inference_steps=4,
        max_sequence_length=256,
        generator=torch.Generator("cpu").manual_seed(0)
    ).images[0]

    # Convert the image to base64 without saving to disk
    buffered = BytesIO()
    image.save(buffered, format="PNG")  # or use "JPEG" if you prefer
    base64_bytes = base64.b64encode(buffered.getvalue())

    # Decode the Base64 bytes to a UTF-8 string
    base64_string = base64_bytes.decode("utf-8")
    return base64_string

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5500")
