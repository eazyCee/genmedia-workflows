import os
import io
import datetime
from PIL import Image
from google import genai
from google.genai import types
from google.cloud import storage

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

def upload_image_to_gcs(image: Image.Image, bucket_name: str, workflow_name: str) -> str:
    """
    Uploads a PIL Image to a specified Google Cloud Storage bucket.
    Returns the GCS URI (e.g., gs://bucket-name/generated_assets/mixer_20260525_123456.png)
    """
    if not bucket_name:
        raise ValueError("GCS Bucket Name is not configured.")
        
    # Convert image to bytes
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    
    # Construct filename: e.g., generated_assets/mixer_20260525_123456.png
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    destination_blob_name = f"generated_assets/{workflow_name.lower()}_{timestamp}.png"
    
    # Initialize GCS client (uses standard ADC)
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    
    # Upload bytes
    blob.upload_from_string(img_bytes, content_type="image/png")
    
    return f"gs://{bucket_name}/{destination_blob_name}"

def upload_custom_asset_to_gcs(image: Image.Image, bucket_name: str, asset_type: str, workflow_name: str) -> str:
    """
    Uploads a custom user-uploaded reference image to a specified GCS bucket.
    Returns the GCS URI (e.g., gs://bucket/custom_uploads/logos/mixer_logo_20260525_170000.png)
    """
    if not bucket_name:
        raise ValueError("GCS Bucket Name is not configured.")
        
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    destination_blob_name = f"custom_uploads/{asset_type}/{workflow_name.lower()}_{timestamp}.png"
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    # Upload bytes
    blob.upload_from_string(img_bytes, content_type="image/png")
    
    return f"gs://{bucket_name}/{destination_blob_name}"

def audit_generated_image(image: Image.Image, brand_guidelines: str) -> str:
    """
    Uses Gemini to analyze the generated image against the specified brand guidelines.
    Returns a text evaluation/scorecard.
    """
    client = get_genai_client()
    
    # Convert PIL Image to part
    img_part = pil_to_part(image)
    
    audit_prompt = f"""
    You are an expert brand manager and design director.
    Analyze the provided image and evaluate how well it adheres to these Brand Guidelines:
    ---
    {brand_guidelines}
    ---
    
    Please provide a structured Brand Compliance Report:
    1. Overall Score: (Give a percentage, e.g., 85%)
    2. Colorway Adherence: (Score out of 10 and a brief comment)
    3. Product & Logo Placement: (Score out of 10 and a brief comment)
    4. Aesthetic & Lighting Mood: (Score out of 10 and a brief comment)
    5. Actionable Feedback/Suggestions: (List 2-3 concrete ways to improve the next generation prompt or arrangement to align better with the guidelines)
    
    Be objective, critical, and constructive. Format the response nicely in Markdown.
    """
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[img_part, audit_prompt]
    )
    
    return response.text

def outpaint_image(image: Image.Image, target_aspect_ratio: str, guidelines: str) -> Image.Image:
    """
    Uses Gemini 3.1 Flash Image Preview to outpaint and extend the canvas of the given image.
    """
    img_part = pil_to_part(image)
    
    prompt = f"""
    You are given this source image.
    Your task is to outpaint and extend this image to fit a {target_aspect_ratio} aspect ratio.
    Seamlessly extend the background details on the sides or top/bottom to match the original style: {guidelines}.
    The central subjects (product, model, logo) must remain completely identical, sharp, and unmodified.
    Ensure no stretching, distorting, or duplicate subjects are generated in the expanded areas.
    """
    
    return generate_onbrand_asset(
        parts_list=[img_part],
        prompt_text=prompt,
        aspect_ratio=target_aspect_ratio
    )

def isolate_product_image(image: Image.Image) -> Image.Image:
    """
    Uses Gemini 3.1 Flash Image Preview to segment the main product and place it on a clean studio white background.
    """
    img_part = pil_to_part(image)
    
    prompt = """
    Isolate the main product shown in the provided image.
    Remove all background objects, surfaces, shadows, and environment details.
    Recreate the product with high detail on a clean, solid, professional studio white background.
    Do not modify the product itself, its labels, colors, or branding.
    """
    
    return generate_onbrand_asset(
        parts_list=[img_part],
        prompt_text=prompt,
        aspect_ratio="1:1"
    )

def list_gcs_gallery_images(bucket_name: str, limit: int = 12) -> list:
    """
    Lists the latest images stored in the GCS bucket under generated_assets/
    """
    if not bucket_name:
        return []
        
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # List blobs under prefix
    blobs = list(bucket.list_blobs(prefix="generated_assets/"))
    
    # Filter image blobs
    img_blobs = [b for b in blobs if b.name.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # Sort by updated time descending (newest first)
    img_blobs.sort(key=lambda x: x.updated, reverse=True)
    
    # Slice to limit
    img_blobs = img_blobs[:limit]
    
    gallery = []
    for blob in img_blobs:
        try:
            img_bytes = blob.download_as_bytes()
            gallery.append({
                "name": blob.name,
                "bytes": img_bytes,
                "updated": blob.updated,
                "short_name": os.path.basename(blob.name)
            })
        except Exception:
            pass
        
    return gallery

def delete_gcs_blob(bucket_name: str, blob_name: str):
    """
    Deletes a specific blob from GCS.
    """
    if not bucket_name or not blob_name:
        return
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    if blob.exists():
        blob.delete()



