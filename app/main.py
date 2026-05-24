import os
import streamlit as st
from PIL import Image
from utils import pil_to_part, generate_onbrand_asset

# Set page configuration
st.set_page_config(
    page_title="OnBrand Asset Creator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Base paths for preapproved assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGOS_DIR = os.path.join(BASE_DIR, "assets", "logos")
PRODUCTS_DIR = os.path.join(BASE_DIR, "assets", "products")
MODELS_DIR = os.path.join(BASE_DIR, "assets", "models")
STOREFRONTS_DIR = os.path.join(BASE_DIR, "assets", "storefronts")

def load_preapproved_assets(directory_path) -> dict:
    """
    Dynamically scans the specified directory for PNG/JPG images,
    and returns a dictionary mapping a clean title-cased name to the file name.
    Example: 'tech_minimal.png' -> 'Tech Minimal'
    """
    if not os.path.exists(directory_path):
        return {}
    assets = {}
    for filename in sorted(os.listdir(directory_path)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Convert snake_case/kebab-case to title case
            clean_name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
            assets[clean_name] = filename
    return assets

# Load assets dynamically
PREAPPROVED_LOGOS = load_preapproved_assets(LOGOS_DIR)
PREAPPROVED_PRODUCTS = load_preapproved_assets(PRODUCTS_DIR)
PREAPPROVED_MODELS = load_preapproved_assets(MODELS_DIR)
PREAPPROVED_STOREFRONTS = load_preapproved_assets(STOREFRONTS_DIR)

# Preapproved Colorways
COLORWAYS = {
    "Warm Terracotta": "Warm earthy tones, terracotta, cream, soft sand, gentle gold highlights, organic and natural feel",
    "Minimalist Sage": "Cool sage greens, clean white, light oak wood, brushed silver, modern and peaceful vibe",
    "Neon Cyberpunk": "Vibrant magenta, electric blue, dark charcoal, neon cyan accents, futuristic high-contrast energy",
    "Classic Luxury": "Deep emerald, obsidian black, polished brass, warm amber, rich premium elegant atmosphere"
}

# Preapproved Settings for Brand Creator
SETTINGS = {
    "Nature / Outdoor": "Sun-dappled forest floor with moss-covered stones, natural outdoor soft morning light, foliage bokeh",
    "Studio Lighting": "Clean studio environment, soft shadows, professional three-point studio lighting, solid minimalist grey backdrop",
    "Cozy Café": "Rustic dark wooden tabletop in a warm sun-lit cafe, soft blurred coffee shop background, inviting warm atmosphere",
    "Modern Office": "Sleek white marble desk in a bright, minimalist high-rise office, soft bokeh of a clean city skyline through the window"
}

# Preapproved Storefront Styles for Visualizer
STOREFRONT_STYLES = {
    "Luxury Boutique": "A high-end luxury boutique storefront with elegant ambient warm interior lights, minimal dark metal window framing, premium feel.",
    "Cozy Cafe Exterior": "A charming European-style cafe facade with warm rustic brick walls, dark canvas awning, beautiful hanging plants, and inviting storefront presence.",
    "Modern Tech Store": "A sleek minimalist high-tech electronics shop facade with glowing cool neutral lights, large seamless glass panel sheets, polished light grey concrete details.",
    "Minimalist Apparel": "A neat Scandinavian-style clothing store facade with light oak wood framing, light neutral cream paint, and bright modern display."
}

# App Title & Subtitle
st.title("🎨 OnBrand Asset Creator")
st.markdown(
    """
    Eliminate the ambiguities of image creation.
    Choose one of the structured workflows below to generate high-quality, brand-compliant assets using Vertex AI.
    """
)

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Global Settings")
    aspect_ratio = st.selectbox(
        "Aspect Ratio",
        options=["1:1", "3:4", "4:3", "16:9", "9:16", "auto"],
        index=0,
        help="The aspect ratio of the generated image"
    )
    
    st.divider()
    st.markdown(
        """
        **Using Gemini 3.1 Flash Image Preview**
        
        This app connects to Vertex AI. Please ensure your environment has the required Google Cloud credentials configured.
        """
    )

# Define tabs for workflows
tab1, tab2, tab3 = st.tabs([
    "🔄 Product + Model Mixer", 
    "🏷️ Brand Asset Creator", 
    "🏪 Storefront Visualizer"
])

# ==========================================================
# TAB 1: PRODUCT + MODEL MIXER
# ==========================================================
with tab1:
    st.header("Product + Model Mixer")
    st.markdown(
        "Combine a product image and a model image into a high-quality, seamless fashion shot."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Product Image")
        uploaded_product_mixer = st.file_uploader(
            "Upload product photo (PNG/JPG)", 
            type=["png", "jpg", "jpeg"], 
            key="mixer_product"
        )
        if uploaded_product_mixer:
            prod_img = Image.open(uploaded_product_mixer)
            st.image(prod_img, caption="Product Uploaded", use_container_width=True)
            
    with col2:
        st.subheader("2. Model Image")
        uploaded_model_mixer = st.file_uploader(
            "Upload model photo (PNG/JPG)", 
            type=["png", "jpg", "jpeg"], 
            key="mixer_model"
        )
        if uploaded_model_mixer:
            model_img = Image.open(uploaded_model_mixer)
            st.image(model_img, caption="Model Uploaded", use_container_width=True)
            
    st.divider()
    
    st.subheader("3. Placement Instructions (Optional)")
    placement_instruction = st.text_area(
        "Specific placement instructions (Leave blank for high-quality automatic synthesis):",
        placeholder="e.g., 'Place the sneakers on the model's feet naturally, matching lighting and perspective.'",
        help="Describe exactly how the product should blend onto the model if you have a specific preference."
    )
    
    generate_mixer = st.button("✨ Generate Mixed Asset", type="primary")
    
    if generate_mixer:
        if not uploaded_product_mixer or not uploaded_model_mixer:
            st.error("Please upload both a product image and a model image.")
        else:
            with st.spinner("Synthesizing images using Gemini... This may take up to 30 seconds."):
                try:
                    prod_part = pil_to_part(prod_img)
                    model_part = pil_to_part(model_img)
                    
                    # Prompt engineered with visual design and commercial photography best practices
                    base_mixer_prompt = """
                    You are an expert commercial fashion and product photographer.
                    Analyze the provided product image and the model image carefully.
                    Generate a single, highly cohesive, ultra-realistic commercial fashion photograph.
                    The model must be naturally wearing, holding, or using the product as the main focal point.
                    Maintain immaculate physical shadow alignment, seamless material/edge blending, realistic surface textures, correct camera perspective, and high-end professional studio lighting.
                    The composition must feel highly organic, clean, and premium.
                    """
                    
                    if placement_instruction.strip():
                        prompt_text = base_mixer_prompt + f"\nAdditionally, follow this specific arrangement detail: {placement_instruction}."
                    else:
                        prompt_text = base_mixer_prompt
                    
                    result_img = generate_onbrand_asset(
                        parts_list=[prod_part, model_part],
                        prompt_text=prompt_text,
                        aspect_ratio=aspect_ratio
                    )
                    
                    st.success("Mixer Asset Generated Successfully!")
                    st.image(result_img, caption="Generated Mixed Asset", use_container_width=True)
                    
                    import io
                    buf = io.BytesIO()
                    result_img.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    st.download_button(
                        label="📥 Download Image",
                        data=byte_im,
                        file_name="mixed_asset.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"An error occurred during image generation: {str(e)}")

# ==========================================================
# TAB 2: BRAND ASSET GENERATOR
# ==========================================================
with tab2:
    st.header("Brand Guideline Asset Creator")
    st.markdown(
        "Create high-quality marketing assets combining your product, brand logo, preapproved settings, and colorways."
    )
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("1. Brand Logo")
        logo_choice = st.radio(
            "Select a preapproved brand logo:",
            options=list(PREAPPROVED_LOGOS.keys()) + ["Custom Upload..."],
            key="brand_logo_choice"
        )
        
        logo_to_use = None
        if logo_choice == "Custom Upload...":
            uploaded_logo = st.file_uploader("Upload your custom logo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="brand_logo_upload")
            if uploaded_logo:
                logo_to_use = Image.open(uploaded_logo)
                st.image(logo_to_use, caption="Custom Logo Preview", width=150)
        else:
            logo_path = os.path.join(LOGOS_DIR, PREAPPROVED_LOGOS[logo_choice])
            logo_to_use = Image.open(logo_path)
            st.image(logo_to_use, caption=f"{logo_choice} Preview", width=150)
            
        st.divider()
        
        st.subheader("2. Brand Colorway")
        colorway_choice = st.selectbox(
            "Select a preapproved colorway palette:",
            options=list(COLORWAYS.keys())
        )
        st.info(f"**Palette Details:** {COLORWAYS[colorway_choice]}")
        
        st.divider()
        
        st.subheader("3. Model Image (Optional)")
        model_choice_brand = st.radio(
            "Select a preapproved model silhouette or upload custom (Optional):",
            options=["None"] + list(PREAPPROVED_MODELS.keys()) + ["Custom Upload..."],
            key="brand_model_choice"
        )
        
        model_to_use_brand = None
        if model_choice_brand == "Custom Upload...":
            uploaded_model_brand = st.file_uploader("Upload model image (PNG/JPG)", type=["png", "jpg", "jpeg"], key="brand_model_upload")
            if uploaded_model_brand:
                model_to_use_brand = Image.open(uploaded_model_brand)
                st.image(model_to_use_brand, caption="Custom Model Preview", width=150)
        elif model_choice_brand != "None":
            model_path_brand = os.path.join(MODELS_DIR, PREAPPROVED_MODELS[model_choice_brand])
            model_to_use_brand = Image.open(model_path_brand)
            st.image(model_to_use_brand, caption=f"{model_choice_brand} Preview", width=150)
        
    with col_right:
        st.subheader("4. Product Image")
        product_choice = st.radio(
            "Select a preapproved product or upload custom:",
            options=list(PREAPPROVED_PRODUCTS.keys()) + ["Custom Upload..."],
            key="brand_product_choice"
        )
        
        product_to_use = None
        if product_choice == "Custom Upload...":
            uploaded_product_brand = st.file_uploader("Upload your product (PNG/JPG)", type=["png", "jpg", "jpeg"], key="brand_product_upload")
            if uploaded_product_brand:
                product_to_use = Image.open(uploaded_product_brand)
                st.image(product_to_use, caption="Custom Product Preview", width=150)
        else:
            product_path = os.path.join(PRODUCTS_DIR, PREAPPROVED_PRODUCTS[product_choice])
            product_to_use = Image.open(product_path)
            st.image(product_to_use, caption=f"{product_choice} Preview", width=150)
            
        st.divider()
        
        st.subheader("5. Environment Setting")
        setting_choice = st.selectbox(
            "Select a preapproved environment setting:",
            options=list(SETTINGS.keys())
        )
        st.info(f"**Setting Details:** {SETTINGS[setting_choice]}")
        
    st.divider()
    
    st.subheader("6. Marketing & Style Enhancements (Optional)")
    extra_prompt = st.text_input(
        "Additional text instructions/details",
        placeholder="e.g., 'Add a few water droplets on the surface', 'Keep it ultra minimalist with clean composition'",
        key="brand_extra_prompt"
    )
    
    generate_brand = st.button("✨ Generate Brand-Aligned Asset", type="primary", key="btn_brand")
    
    if generate_brand:
        if logo_to_use is None:
            st.error("Please ensure a logo is selected or uploaded.")
        elif product_to_use is None:
            st.error("Please ensure a product image is selected or uploaded.")
        else:
            with st.spinner("Generating brand-aligned masterpiece... This may take up to 30 seconds."):
                try:
                    logo_part = pil_to_part(logo_to_use)
                    product_part = pil_to_part(product_to_use)
                    
                    parts_list = [logo_part, product_part]
                    if model_to_use_brand:
                        parts_list.append(pil_to_part(model_to_use_brand))
                    
                    setting_desc = SETTINGS[setting_choice]
                    color_desc = COLORWAYS[colorway_choice]
                    
                    prompt_text = f"""
                    Generate a premium, professional marketing advertisement.
                    The main focus is the product.
                    The product must be placed centrally and naturally within this environment setting: {setting_desc}.
                    The logo must be clearly but elegantly integrated onto the product packaging/surface, or placed as a subtle watermark in a corner.
                    The color palette and lighting of the entire scene must strictly adhere to these brand guidelines: {color_desc}.
                    Ensure hyper-realistic rendering, accurate shadows, premium product highlights, and a high-end commercial aesthetic.
                    """
                    
                    if model_to_use_brand:
                        prompt_text += "\nThe model provided in the reference image must be clearly present in the scene, interacting with or showcasing the product naturally."
                    
                    if extra_prompt.strip():
                        prompt_text += f"\nAdditional styling request: {extra_prompt}."
                        
                    result_brand_img = generate_onbrand_asset(
                        parts_list=parts_list,
                        prompt_text=prompt_text,
                        aspect_ratio=aspect_ratio
                    )
                    
                    st.success("Brand-Aligned Asset Generated Successfully!")
                    st.image(result_brand_img, caption="Generated Brand Asset", use_container_width=True)
                    
                    import io
                    buf_brand = io.BytesIO()
                    result_brand_img.save(buf_brand, format="PNG")
                    byte_brand_im = buf_brand.getvalue()
                    st.download_button(
                        label="📥 Download Brand Asset",
                        data=byte_brand_im,
                        file_name="brand_aligned_asset.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"An error occurred during brand asset generation: {str(e)}")

# ==========================================================
# TAB 3: STOREFRONT VISUALIZER
# ==========================================================
with tab3:
    st.header("Storefront Visualizer")
    st.markdown(
        "Visualize how your logo, design, artwork, or storefront banner would appear on a physical storefront window, hanging sign, or billboard."
    )
    
    col_vis_left, col_vis_right = st.columns(2)
    
    with col_vis_left:
        st.subheader("1. Your Design / Artwork")
        uploaded_design_vis = st.file_uploader(
            "Upload your brand artwork, logo, or banner (PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            key="vis_design"
        )
        if uploaded_design_vis:
            design_img = Image.open(uploaded_design_vis)
            st.image(design_img, caption="Uploaded Design/Artwork", width=200)
            
    with col_vis_right:
        st.subheader("2. Storefront Template")
        storefront_choice = st.radio(
            "Select a preapproved blank storefront template:",
            options=list(PREAPPROVED_STOREFRONTS.keys()) + ["Custom Upload..."],
            key="storefront_template_choice"
        )
        
        storefront_to_use = None
        if storefront_choice == "Custom Upload...":
            uploaded_storefront = st.file_uploader(
                "Upload a blank storefront template (PNG/JPG)",
                type=["png", "jpg", "jpeg"],
                key="vis_storefront_upload"
            )
            if uploaded_storefront:
                storefront_to_use = Image.open(uploaded_storefront)
                st.image(storefront_to_use, caption="Custom Storefront Template Preview", width=200)
        else:
            storefront_path = os.path.join(STOREFRONTS_DIR, PREAPPROVED_STOREFRONTS[storefront_choice])
            storefront_to_use = Image.open(storefront_path)
            st.image(storefront_to_use, caption=f"{storefront_choice} Template Preview", width=200)
            
    st.divider()
    
    col_vis_opt1, col_vis_opt2 = st.columns(2)
    
    with col_vis_opt1:
        st.subheader("3. Storefront Style Context")
        storefront_style_choice = st.selectbox(
            "Select style context for the storefront:",
            options=list(STOREFRONT_STYLES.keys())
        )
        st.info(f"**Style details:** {STOREFRONT_STYLES[storefront_style_choice]}")
        
    with col_vis_opt2:
        st.subheader("4. Additional Visual Instructions (Optional)")
        vis_extra_prompt = st.text_input(
            "Custom instruction for placement or atmosphere:",
            placeholder="e.g. 'Add realistic glass reflections and wet rain effect on the pavement', 'Sunset lighting'",
            key="vis_extra_prompt"
        )
        
    st.divider()
    
    generate_visualizer = st.button("✨ Generate Storefront Visualization", type="primary", key="btn_visualizer")
    
    if generate_visualizer:
        if design_img is None:
            st.error("Please upload your design or artwork image first.")
        elif storefront_to_use is None:
            st.error("Please ensure a storefront template is selected or uploaded.")
        else:
            with st.spinner("Synthesizing storefront visualization... This may take up to 30 seconds."):
                try:
                    design_part = pil_to_part(design_img)
                    storefront_part = pil_to_part(storefront_to_use)
                    
                    style_desc = STOREFRONT_STYLES[storefront_style_choice]
                    
                    prompt_text = f"""
                    Analyze the provided design image and the blank storefront template image.
                    Generate a highly realistic commercial photograph of the storefront.
                    Place the design image naturally and seamlessly onto the designated blank template area (such as the main display window, hanging sign bracket, or billboard facade space).
                    The storefront must embody this style: {style_desc}.
                    Ensure realistic reflections on the glass, perfect angular perspective alignment, natural lighting, and correct shadow projections.
                    The design should look like a physical part of the storefront, not just pasted on top.
                    """
                    
                    if vis_extra_prompt.strip():
                        prompt_text += f"\nExtra design detail request: {vis_extra_prompt}."
                        
                    result_vis_img = generate_onbrand_asset(
                        parts_list=[design_part, storefront_part],
                        prompt_text=prompt_text,
                        aspect_ratio=aspect_ratio
                    )
                    
                    st.success("Storefront Visualization Generated Successfully!")
                    st.image(result_vis_img, caption="Generated Storefront Preview", use_container_width=True)
                    
                    import io
                    buf_vis = io.BytesIO()
                    result_vis_img.save(buf_vis, format="PNG")
                    byte_vis_im = buf_vis.getvalue()
                    st.download_button(
                        label="📥 Download Storefront Visualization",
                        data=byte_vis_im,
                        file_name="storefront_visualization.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"An error occurred during storefront generation: {str(e)}")
