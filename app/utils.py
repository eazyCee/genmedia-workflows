import os
import io
from PIL import Image
from google import genai
from google.genai import types

def get_genai_client() -> genai.Client:
    """
    Initializes the Google GenAI client for Vertex AI.
    Uses GOOGLE_CLOUD_API_KEY if available, otherwise falls back to ADC.
    """
    api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
    if api_key:
        return genai.Client(
            vertexai=True,
            api_key=api_key
        )
    else:
        # Rely on Application Default Credentials (ADC)
        return genai.Client(vertexai=True)

def pil_to_part(image: Image.Image, mime_type: str = "image/png") -> types.Part:
    """
    Converts a PIL Image object into a types.Part object for the GenAI SDK.
    """
    buffered = io.BytesIO()
    # Save PIL image to buffer
    image.save(buffered, format="PNG" if "png" in mime_type.lower() else "JPEG")
    img_bytes = buffered.getvalue()
    
    return types.Part.from_bytes(
        data=img_bytes,
        mime_type=mime_type
    )

def generate_onbrand_asset(parts_list: list, prompt_text: str, aspect_ratio: str = "1:1") -> Image.Image:
    """
    Sends a multimodal request to the gemini-3.1-flash-image-preview model
    and returns the generated image.
    """
    client = get_genai_client()
    
    # Combine reference parts and the text prompt part
    contents = [
        types.Content(
            role="user",
            parts=parts_list + [types.Part.from_text(text=prompt_text)]
        )
    ]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=1.0,
        top_p=0.95,
        max_output_tokens=32768,
        response_modalities=["IMAGE"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size="1K",
            output_mime_type="image/png",
        ),
        thinking_config=types.ThinkingConfig(
            thinking_level="MINIMAL",
        ),
    )
    
    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=contents,
        config=generate_content_config,
    )
    
    # Extract the generated image from candidates
    if not response.candidates:
        raise ValueError("No candidates returned in the model response.")
        
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_bytes = part.inline_data.data
            return Image.open(io.BytesIO(image_bytes))
            
    raise ValueError("No image was found in the response parts.")
