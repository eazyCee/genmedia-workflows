import os
import streamlit as st
from PIL import Image
from google.genai import types
from utils import pil_to_part, generate_onbrand_asset, upload_image_to_gcs, upload_custom_asset_to_gcs, audit_generated_image, outpaint_image, isolate_product_image, list_gcs_gallery_images, delete_gcs_blob

# Read optional GCS bucket for output archival
GCS_OUTPUT_BUCKET = os.environ.get("GCS_OUTPUT_BUCKET", "image-bucket-sandbox-dce")

# Set page configuration
st.set_page_config(
    page_title="OnBrand Asset Creator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for persistent generations and audits
if "mixer_result_img" not in st.session_state:
    st.session_state.mixer_result_img = None
if "mixer_resized_img" not in st.session_state:
    st.session_state.mixer_resized_img = None
if "mixer_audit_report" not in st.session_state:
    st.session_state.mixer_audit_report = None
if "mixer_chat_history" not in st.session_state:
    st.session_state.mixer_chat_history = []


if "brand_result_images" not in st.session_state:
    st.session_state.brand_result_images = []


if "vis_result_img" not in st.session_state:
    st.session_state.vis_result_img = None
if "vis_resized_img" not in st.session_state:
    st.session_state.vis_resized_img = None
if "vis_audit_report" not in st.session_state:
    st.session_state.vis_audit_report = None



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
tab1, tab2, tab3, tab4 = st.tabs([
    "🔄 Product + Model Mixer", 
    "🏷️ Brand Asset Creator", 
    "🏪 Storefront Visualizer",
    "🖼️ Asset Gallery"
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
        isolate_prod_mixer = False
        if uploaded_product_mixer:
            prod_img = Image.open(uploaded_product_mixer)
            st.image(prod_img, caption="Product Uploaded", use_container_width=True)
            isolate_prod_mixer = st.checkbox("🧹 Auto-isolate product (remove background)", key="mixer_isolate_prod")

            
    with col2:
        st.subheader("2. Model Image")
        model_choice_mixer = st.radio(
            "Select a preapproved model silhouette or upload custom:",
            options=list(PREAPPROVED_MODELS.keys()) + ["Custom Upload..."],
            key="mixer_model_choice"
        )
        
        model_img = None
        if model_choice_mixer == "Custom Upload...":
            uploaded_model_mixer = st.file_uploader(
                "Upload model photo (PNG/JPG)", 
                type=["png", "jpg", "jpeg"], 
                key="mixer_model_upload"
            )
            if uploaded_model_mixer:
                model_img = Image.open(uploaded_model_mixer)
                st.image(model_img, caption="Model Uploaded", use_container_width=True)
        else:
            model_path_mixer = os.path.join(MODELS_DIR, PREAPPROVED_MODELS[model_choice_mixer])
            model_img = Image.open(model_path_mixer)
            st.image(model_img, caption=f"{model_choice_mixer} Preview", use_container_width=True)
            
    st.divider()
    
    st.subheader("3. Placement Instructions (Optional)")
    placement_instruction = st.text_area(
        "Specific placement instructions (Leave blank for high-quality automatic synthesis):",
        placeholder="e.g., 'Place the sneakers on the model's feet naturally, matching lighting and perspective.'",
        help="Describe exactly how the product should blend onto the model if you have a specific preference."
    )
    
    generate_mixer = st.button("✨ Generate Mixed Asset", type="primary")
    
    if generate_mixer:
        if not uploaded_product_mixer:
            st.error("Please upload a product image.")
        elif model_img is None:
            st.error("Please ensure a model is selected or uploaded.")
        else:
            with st.spinner("Synthesizing images using Gemini... This may take up to 30 seconds."):
                try:
                    if not GCS_OUTPUT_BUCKET:
                        st.error("GCS Output Bucket is not configured. Cannot process uploads.")
                        st.stop()
                    
                    # 0. Isolate product if requested
                    if isolate_prod_mixer:
                        with st.spinner("🧹 Removing product background first..."):
                            try:
                                prod_img = isolate_product_image(prod_img)
                                st.image(prod_img, caption="Product Isolated Cutout", width=150)
                            except Exception as isolate_err:
                                st.warning(f"⚠️ Failed to isolate product background: {str(isolate_err)}. Proceeding with original image.")

                    try:
                        # 1. Product (always uploaded)
                        prod_gcs_uri = upload_custom_asset_to_gcs(prod_img, GCS_OUTPUT_BUCKET, "mixer_product", "mixer")
                        prod_part = types.Part.from_uri(file_uri=prod_gcs_uri, mime_type="image/png")
                        st.write(f"📸 Custom Product Reference stored in GCS: `{prod_gcs_uri}`")
                        
                        # 2. Model (preapproved or uploaded)
                        if model_choice_mixer == "Custom Upload...":
                            model_gcs_uri = upload_custom_asset_to_gcs(model_img, GCS_OUTPUT_BUCKET, "mixer_model", "mixer")
                            model_part = types.Part.from_uri(file_uri=model_gcs_uri, mime_type="image/png")
                            st.write(f"👤 Custom Model Reference stored in GCS: `{model_gcs_uri}`")
                        else:
                            model_part = pil_to_part(model_img)
                    except Exception as gcs_ref_err:
                        st.error(f"❌ Failed to upload reference images to GCS: {str(gcs_ref_err)}")
                        st.stop()
                    
                    # Prompt engineered with visual design and commercial photography best practices
                    base_mixer_prompt = """
                    You are an expert commercial fashion and product photographer.
                    Analyze the provided product image and the model image carefully.
                    Generate a single, highly cohesive, ultra-realistic commercial fashion photograph.
                    The model must be naturally wearing, holding, or using the product as the main focal point. Logically, the image should make sense.
                    For example, if the product is a can/bottle/packaging item, the model should be holding it as a consumer would in their hands unless explicitly stated otherwise.
                    If the product is an apparel, the model should be wearing them. So on and so forth.
                    
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
                    
                    # Store in session state and clear stale audit/resized states
                    st.session_state.mixer_result_img = result_img
                    st.session_state.mixer_resized_img = None
                    st.session_state.mixer_audit_report = None
                    
                    # Store a downscaled thumbnail copy in the chat history to prevent WebSocket size overflows
                    chat_thumb = result_img.copy()
                    chat_thumb.thumbnail((400, 400))
                    
                    st.session_state.mixer_chat_history = [
                        {"role": "user", "text": f"Generate fashion shot. Placement instruction: {placement_instruction.strip() if placement_instruction.strip() else 'None'}"},
                        {"role": "assistant", "image": chat_thumb}
                    ]
                    
                    # Optional GCS archival
                    if GCS_OUTPUT_BUCKET:
                        try:
                            gcs_uri = upload_image_to_gcs(result_img, GCS_OUTPUT_BUCKET, "mixer")
                            st.info(f"🚀 Asset also archived to Cloud Storage: `{gcs_uri}`")
                        except Exception as gcs_err:
                            st.warning(f"⚠️ Could not archive to GCS: {str(gcs_err)}")
                            
                except Exception as e:
                    st.error(f"An error occurred during image generation: {str(e)}")
                    
    # Persistent render block for Mixer generation results
    if st.session_state.mixer_result_img is not None:
        st.divider()
        st.subheader("Generated Mixed Asset")
        
        col_img, col_actions = st.columns([2, 1])
        
        with col_img:
            # Render using bytes to prevent Streamlit cache serialization bugs
            import io
            buf_img_m = io.BytesIO()
            st.session_state.mixer_result_img.save(buf_img_m, format="PNG")
            st.image(buf_img_m.getvalue(), caption="Original Mixer Output", use_container_width=True, output_format="PNG")
            
            if st.session_state.mixer_resized_img is not None:
                st.markdown("#### Expanded Canvas Version:")
                buf_res_m = io.BytesIO()
                st.session_state.mixer_resized_img.save(buf_res_m, format="PNG")
                st.image(buf_res_m.getvalue(), caption="Resized Mixer Output", use_container_width=True, output_format="PNG")
            
        with col_actions:
            st.subheader("Options")
            import io
            buf = io.BytesIO()
            img_to_download = st.session_state.mixer_resized_img if st.session_state.mixer_resized_img else st.session_state.mixer_result_img
            img_to_download.save(buf, format="PNG")
            byte_im = buf.getvalue()
            st.download_button(
                label="📥 Download Image",
                data=byte_im,
                file_name="mixed_asset.png",
                mime="image/png"
            )
            
            # Resizer Selector
            target_resizer_mixer = st.selectbox(
                "🖼️ Expand Canvas (Outpaint)",
                options=["Select...", "16:9", "9:16", "4:3", "1:1"],
                key="mixer_resizer_select"
            )
            if target_resizer_mixer != "Select...":
                with st.spinner("Expanding canvas..."):
                    try:
                        mix_guidelines_desc = f"Model placed with custom instruction: {placement_instruction.strip() if placement_instruction.strip() else 'None'}"
                        resized_img_mixer = outpaint_image(st.session_state.mixer_result_img, target_resizer_mixer, mix_guidelines_desc)
                        st.session_state.mixer_resized_img = resized_img_mixer
                        st.success(f"Canvas expanded to {target_resizer_mixer}!")
                        st.rerun()
                    except Exception as resize_err:
                        st.error(f"Resize failed: {str(resize_err)}")
            
            # Audit Trigger Button
            run_audit = st.button("📋 Run Brand Audit Report", key="mixer_run_audit_btn")
            if run_audit:
                with st.spinner("AI Brand Director is auditing your asset..."):
                    # Assemble guidelines to verify
                    mix_guidelines = f"""
                    Workflow Type: Product + Model Mixer
                    Placement Request: {placement_instruction.strip() if placement_instruction.strip() else 'Mix the product and the model naturally together with realistic lighting and camera perspective.'}
                    Desired Aspect Ratio: {aspect_ratio}
                    """
                    try:
                        audit_text = audit_generated_image(st.session_state.mixer_result_img, mix_guidelines)
                        st.session_state.mixer_audit_report = audit_text
                    except Exception as audit_err:
                        st.error(f"Failed to audit asset: {str(audit_err)}")
                        
            # Render report if available
            if st.session_state.mixer_audit_report is not None:
                st.markdown(st.session_state.mixer_audit_report)
                
        # 💬 Refinement Chat (Multi-Turn Dialogue)
        st.divider()
        st.subheader("💬 Refinement Chat (Multi-Turn Edit)")
        
        # Display chat history log
        assistant_indices = [i for i, t in enumerate(st.session_state.mixer_chat_history) if t["role"] == "assistant"]
        
        for idx, turn in enumerate(st.session_state.mixer_chat_history):
            if turn["role"] == "user":
                with st.chat_message("user"):
                    st.write(turn["text"])
            else:
                with st.chat_message("assistant"):
                    is_most_recent = (len(assistant_indices) > 0 and idx == assistant_indices[-1])
                    
                    import io
                    if is_most_recent:
                        # Render the latest generated image directly
                        buf_chat_img = io.BytesIO()
                        turn["image"].save(buf_chat_img, format="PNG")
                        st.image(buf_chat_img.getvalue(), width=350, caption="Refined Output (Most Recent)", output_format="PNG")
                    else:
                        # Collapse historical images to save container rendering bandwidth
                        with st.expander("👁️ Show Historical Image Preview", expanded=False):
                            buf_chat_img = io.BytesIO()
                            turn["image"].save(buf_chat_img, format="PNG")
                            st.image(buf_chat_img.getvalue(), width=300, caption=f"Refined Output (Turn {idx})", output_format="PNG")
                    
        # Multi-Turn Refinement Input Field
        refinement_query = st.chat_input("Suggest changes to improve or modify the image (e.g. 'Move the model to a sunny beach', 'Make the lighting warmer')")
        if refinement_query:
            # Append prompt to history list
            st.session_state.mixer_chat_history.append({"role": "user", "text": refinement_query})
            
            with st.spinner("Applying refinements..."):
                try:
                    prod_p = pil_to_part(prod_img)
                    model_p = pil_to_part(model_img)
                    prev_gen_p = pil_to_part(st.session_state.mixer_result_img)
                    
                    parts_list = [
                        types.Part.from_text(text="Original Product Reference:"),
                        prod_p,
                        types.Part.from_text(text="Original Model Reference:"),
                        model_p,
                        types.Part.from_text(text="Previous Generated Photograph:"),
                        prev_gen_p
                    ]
                    
                    refinement_prompt = f"""
                    Analyze the provided Original Product Reference, Original Model Reference, and Previous Generated Photograph.
                    The user wants to refine the Previous Generated Photograph with this adjustment:
                    ---
                    {refinement_query}
                    ---
                    
                    Please generate a brand new, updated commercial fashion photograph that implements these refinements.
                    Make sure to keep the product appearance and the model's face consistent with the original references, but apply the changes requested by the user.
                    Ensure professional studio lighting and clean compositions.
                    """
                    
                    refined_img = generate_onbrand_asset(
                        parts_list=parts_list,
                        prompt_text=refinement_prompt,
                        aspect_ratio=aspect_ratio
                    )
                    
                    # Update states
                    st.session_state.mixer_result_img = refined_img
                    st.session_state.mixer_resized_img = None
                    st.session_state.mixer_audit_report = None
                    
                    # Store a downscaled thumbnail copy in the chat history to prevent WebSocket size overflows
                    chat_thumb = refined_img.copy()
                    chat_thumb.thumbnail((400, 400))
                    st.session_state.mixer_chat_history.append({"role": "assistant", "image": chat_thumb})
                    
                    # GCS archival
                    if GCS_OUTPUT_BUCKET:
                        try:
                            upload_image_to_gcs(refined_img, GCS_OUTPUT_BUCKET, "mixer_refinement")
                        except:
                            pass
                            
                    st.rerun()
                except Exception as ref_err:
                    st.error(f"Refinement failed: {str(ref_err)}")

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
        
        colorway_choices = st.multiselect(
            "Select brand colorway palettes:",
            options=list(COLORWAYS.keys()),
            default=[list(COLORWAYS.keys())[0]],
            help="Select one or more colorway palettes. Selecting multiple will generate A/B testing variants."
        )
        with st.expander("Palette Details", expanded=True):
            for choice in colorway_choices:
                st.write(f"**{choice}:** {COLORWAYS[choice]}")
        
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
            
        isolate_prod_brand = st.checkbox("🧹 Auto-isolate product (remove background)", key="brand_isolate_prod")
        st.divider()
        
        setting_choices = st.multiselect(
            "Select environment settings:",
            options=list(SETTINGS.keys()),
            default=[list(SETTINGS.keys())[0]],
            help="Select one or more environment settings. Selecting multiple will generate A/B testing variants."
        )
        with st.expander("Setting Details", expanded=True):
            for choice in setting_choices:
                st.write(f"**{choice}:** {SETTINGS[choice]}")
        
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
            with st.spinner("Generating brand-aligned assets..."):
                try:
                    if not GCS_OUTPUT_BUCKET:
                        st.error("GCS Output Bucket is not configured. Cannot process uploads.")
                        st.stop()
                    
                    # 0. Isolate product if requested
                    if isolate_prod_brand:
                        with st.spinner("🧹 Removing product background first..."):
                            try:
                                product_to_use = isolate_product_image(product_to_use)
                                st.image(product_to_use, caption="Product Isolated Cutout", width=150)
                            except Exception as isolate_err:
                                st.warning(f"⚠️ Failed to isolate product background: {str(isolate_err)}. Proceeding with original image.")
                    
                    # Pre-upload components to GCS to avoid duplicate uploads in loop
                    try:
                        # 1. Logo (preapproved or custom uploaded)
                        if logo_choice == "Custom Upload...":
                            logo_gcs_uri = upload_custom_asset_to_gcs(logo_to_use, GCS_OUTPUT_BUCKET, "logos", "brand")
                            logo_part = types.Part.from_uri(file_uri=logo_gcs_uri, mime_type="image/png")
                        else:
                            logo_part = pil_to_part(logo_to_use)
                        
                        # 2. Product (preapproved or custom uploaded)
                        if product_choice == "Custom Upload..." or isolate_prod_brand:
                            prod_gcs_uri = upload_custom_asset_to_gcs(product_to_use, GCS_OUTPUT_BUCKET, "products", "brand")
                            product_part = types.Part.from_uri(file_uri=prod_gcs_uri, mime_type="image/png")
                        else:
                            product_part = pil_to_part(product_to_use)
                        
                        # 3. Model (Optional)
                        model_part = None
                        if model_to_use_brand:
                            if model_choice_brand == "Custom Upload...":
                                model_gcs_uri = upload_custom_asset_to_gcs(model_to_use_brand, GCS_OUTPUT_BUCKET, "models", "brand")
                                model_part = types.Part.from_uri(file_uri=model_gcs_uri, mime_type="image/png")
                            else:
                                model_part = pil_to_part(model_to_use_brand)
                            
                    except Exception as gcs_ref_err:
                        st.error(f"❌ Failed to upload reference images to GCS: {str(gcs_ref_err)}")
                        st.stop()
                    
                    combinations = []
                    for c_choice in colorway_choices:
                        for s_choice in setting_choices:
                            combinations.append((c_choice, s_choice))
                            
                    if len(combinations) > 4:
                        st.error("⚠️ Maximum of 4 variant combinations allowed to prevent timeout. Please reduce selections.")
                        st.stop()
                    
                    # Reset session state for brand results
                    st.session_state.brand_result_images = []
                    
                    progress_bar = st.progress(0.0)
                    for idx, (c_choice, s_choice) in enumerate(combinations):
                        setting_desc = SETTINGS[s_choice]
                        color_desc = COLORWAYS[c_choice]
                        
                        prompt_text = f"""
                        Generate a premium, professional marketing advertisement.
                        The main focus is the product and the model (if there is a model).
                        If there is a model, the model must be naturally wearing, holding, or using the product as the main focal point. Logically, the image should make sense.
                        For example, if the product is a can/bottle/packaging item, the model should be holding it as a consumer would in their hands unless explicitly stated otherwise.
                        If the product is an apparel, the model should be wearing them. So on and so forth.
                    
                        The product must be placed naturally within this environment setting: {setting_desc}.
                        The logo must be clearly but elegantly integrated onto the product packaging/surface, or placed as a subtle watermark in a corner.
                        The color palette and lighting of the entire scene must strictly adhere to these brand guidelines: {color_desc}.
                        Ensure hyper-realistic rendering, accurate shadows, premium product highlights, and a high-end commercial aesthetic.
                        """
                        if model_part:
                            prompt_text += "\nThe model provided in the reference image must be clearly present in the scene, interacting with or showcasing the product naturally."
                        if extra_prompt.strip():
                            prompt_text += f"\nAdditional styling request: {extra_prompt}."
                        
                        run_parts = [logo_part, product_part]
                        if model_part:
                            run_parts.append(model_part)
                        
                        with st.spinner(f"Generating Variant {idx+1}/{len(combinations)} ({c_choice} in {s_choice})..."):
                            result_brand_img = generate_onbrand_asset(
                                parts_list=run_parts,
                                prompt_text=prompt_text,
                                aspect_ratio=aspect_ratio
                            )
                            
                            # GCS output archival
                            gcs_uri = None
                            if GCS_OUTPUT_BUCKET:
                                try:
                                    gcs_uri = upload_image_to_gcs(result_brand_img, GCS_OUTPUT_BUCKET, "brand")
                                except Exception as gcs_err:
                                    pass
                            
                            st.session_state.brand_result_images.append({
                                "image": result_brand_img,
                                "colorway": c_choice,
                                "setting": s_choice,
                                "gcs_uri": gcs_uri,
                                "audit_report": None,
                                "resized_image": None
                            })
                            
                        progress_bar.progress((idx + 1) / len(combinations))
                        
                except Exception as e:
                    st.error(f"An error occurred during brand asset generation: {str(e)}")
                    
    # Render generated variant grid
    if st.session_state.brand_result_images:
        st.divider()
        st.subheader("Generated Brand Variants (A/B Testing)")
        
        # Grid layout: 2 columns maximum
        cols = st.columns(min(len(st.session_state.brand_result_images), 2))
        for idx, variant in enumerate(st.session_state.brand_result_images):
            col_idx = idx % 2
            with cols[col_idx]:
                st.markdown(f"#### Variant {idx+1}: **{variant['colorway']}** in **{variant['setting']}**")
                
                # Image Display (show resized/outpainted version if available) using bytes to prevent Streamlit cache serialization bugs
                import io
                if variant["resized_image"] is not None:
                    buf_res_b = io.BytesIO()
                    variant["resized_image"].save(buf_res_b, format="PNG")
                    st.image(buf_res_b.getvalue(), caption=f"Variant {idx+1} (Resized)", use_container_width=True)
                else:
                    buf_orig_b = io.BytesIO()
                    variant["image"].save(buf_orig_b, format="PNG")
                    st.image(buf_orig_b.getvalue(), caption=f"Variant {idx+1} (Original)", use_container_width=True)
                
                if variant["gcs_uri"]:
                    st.caption(f"☁️ GCS Archive: `{variant['gcs_uri']}`")
                
                # Download Button Preparation
                import io
                buf_brand = io.BytesIO()
                img_to_download = variant["resized_image"] if variant["resized_image"] else variant["image"]
                img_to_download.save(buf_brand, format="PNG")
                byte_brand_im = buf_brand.getvalue()
                
                # Variant Action Row
                st.download_button(
                    label="📥 Download Variant PNG",
                    data=byte_brand_im,
                    file_name=f"brand_variant_{idx+1}_{variant['colorway']}.png",
                    mime="image/png",
                    key=f"dl_btn_{idx}"
                )
                
                # Resizer Choice
                target_resizer = st.selectbox(
                    "🖼️ Expand Canvas (Outpaint):",
                    options=["Select...", "16:9", "9:16", "4:3", "1:1"],
                    key=f"resizer_select_{idx}"
                )
                if target_resizer != "Select...":
                    with st.spinner("Expanding canvas..."):
                        try:
                            outpaint_guidelines = f"Colorway: {variant['colorway']}, Setting: {variant['setting']}"
                            resized_img = outpaint_image(variant["image"], target_resizer, outpaint_guidelines)
                            variant["resized_image"] = resized_img
                            st.success(f"Canvas expanded to {target_resizer}!")
                            st.rerun()
                        except Exception as resize_err:
                            st.error(f"Resize failed: {str(resize_err)}")
                
                # Audit Trigger
                run_audit_b = st.button("📋 Run Brand Audit Report", key=f"brand_audit_btn_{idx}")
                if run_audit_b:
                    with st.spinner("AI Brand Director is auditing your asset..."):
                        brand_guidelines_text = f"""
                        Workflow Type: Brand Guideline Asset Creator
                        Selected Brand Logo: {logo_choice}
                        Selected Colorway Palette: {variant['colorway']} ({COLORWAYS[variant['colorway']]})
                        Selected Setting: {variant['setting']} ({SETTINGS[variant['setting']]})
                        Model Included: {'Yes (' + model_choice_brand + ')' if model_to_use_brand else 'No'}
                        Custom Style Instructions: {extra_prompt.strip() if extra_prompt.strip() else 'None'}
                        Desired Aspect Ratio: {aspect_ratio}
                        """
                        try:
                            audit_text_b = audit_generated_image(variant["image"], brand_guidelines_text)
                            variant["audit_report"] = audit_text_b
                        except Exception as audit_err:
                            st.error(f"Failed to audit: {str(audit_err)}")
                            
                # Show audit report under the variant card
                if variant["audit_report"] is not None:
                    st.markdown(variant["audit_report"])

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
        isolate_design_vis = False
        if uploaded_design_vis:
            design_img = Image.open(uploaded_design_vis)
            st.image(design_img, caption="Uploaded Design/Artwork", width=200)
            isolate_design_vis = st.checkbox("🧹 Auto-isolate design artwork (remove background)", key="vis_isolate_design")
            
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
                    if not GCS_OUTPUT_BUCKET:
                        st.error("GCS Output Bucket is not configured. Cannot process uploads.")
                        st.stop()
                    
                    # 0. Isolate design artwork background if requested
                    if isolate_design_vis:
                        with st.spinner("🧹 Removing artwork background first..."):
                            try:
                                design_img = isolate_product_image(design_img)
                                st.image(design_img, caption="Design Isolated Cutout", width=150)
                            except Exception as isolate_err:
                                st.warning(f"⚠️ Failed to isolate design background: {str(isolate_err)}. Proceeding with original artwork.")

                    try:
                        # 1. Design (always uploaded)
                        design_gcs_uri = upload_custom_asset_to_gcs(design_img, GCS_OUTPUT_BUCKET, "designs", "visualizer")
                        design_part = types.Part.from_uri(file_uri=design_gcs_uri, mime_type="image/png")
                        st.write(f"🎨 Custom Design Artwork stored in GCS: `{design_gcs_uri}`")
                        
                        # 2. Storefront (preapproved or custom uploaded)
                        if storefront_choice == "Custom Upload...":
                            storefront_gcs_uri = upload_custom_asset_to_gcs(storefront_to_use, GCS_OUTPUT_BUCKET, "storefronts", "visualizer")
                            storefront_part = types.Part.from_uri(file_uri=storefront_gcs_uri, mime_type="image/png")
                            st.write(f"🏪 Custom Storefront Template stored in GCS: `{storefront_gcs_uri}`")
                        else:
                            storefront_part = pil_to_part(storefront_to_use)
                    except Exception as gcs_ref_err:
                        st.error(f"❌ Failed to upload reference images to GCS: {str(gcs_ref_err)}")
                        st.stop()
                    
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
                    
                    # Store in session state and clear stale audit/resized states
                    st.session_state.vis_result_img = result_vis_img
                    st.session_state.vis_resized_img = None
                    st.session_state.vis_audit_report = None
                    
                    # Optional GCS archival
                    if GCS_OUTPUT_BUCKET:
                        try:
                            gcs_uri = upload_image_to_gcs(result_vis_img, GCS_OUTPUT_BUCKET, "visualizer")
                            st.info(f"🚀 Asset also archived to Cloud Storage: `{gcs_uri}`")
                        except Exception as gcs_err:
                            st.warning(f"⚠️ Could not archive to GCS: {str(gcs_err)}")
                            
                except Exception as e:
                    st.error(f"An error occurred during storefront generation: {str(e)}")
                    
    # Persistent render block for Storefront Visualizer generation results
    if st.session_state.vis_result_img is not None:
        st.divider()
        st.subheader("Generated Storefront Visualization")
        
        col_img_v, col_actions_v = st.columns([2, 1])
        
        with col_img_v:
            # Render using bytes to prevent Streamlit cache serialization bugs
            import io
            buf_img_v = io.BytesIO()
            st.session_state.vis_result_img.save(buf_img_v, format="PNG")
            st.image(buf_img_v.getvalue(), caption="Original Storefront Preview", use_container_width=True)
            
            if st.session_state.vis_resized_img is not None:
                st.markdown("#### Expanded Canvas Version:")
                buf_res_v = io.BytesIO()
                st.session_state.vis_resized_img.save(buf_res_v, format="PNG")
                st.image(buf_res_v.getvalue(), caption="Resized Storefront Preview", use_container_width=True)
            
        with col_actions_v:
            st.subheader("Options")
            import io
            buf_vis = io.BytesIO()
            img_to_download = st.session_state.vis_resized_img if st.session_state.vis_resized_img else st.session_state.vis_result_img
            img_to_download.save(buf_vis, format="PNG")
            byte_vis_im = buf_vis.getvalue()
            st.download_button(
                label="📥 Download Storefront Visualization",
                data=byte_vis_im,
                file_name="storefront_visualization.png",
                mime="image/png"
            )
            
            # Resizer Selector
            target_resizer_vis = st.selectbox(
                "🖼️ Expand Canvas (Outpaint)",
                options=["Select...", "16:9", "9:16", "4:3", "1:1"],
                key="vis_resizer_select"
            )
            if target_resizer_vis != "Select...":
                with st.spinner("Expanding canvas..."):
                    try:
                        vis_guidelines_desc = f"Storefront style: {storefront_style_choice} ({STOREFRONT_STYLES[storefront_style_choice]})"
                        resized_img_vis = outpaint_image(st.session_state.vis_result_img, target_resizer_vis, vis_guidelines_desc)
                        st.session_state.vis_resized_img = resized_img_vis
                        st.success(f"Canvas expanded to {target_resizer_vis}!")
                        st.rerun()
                    except Exception as resize_err:
                        st.error(f"Resize failed: {str(resize_err)}")
            
            # Audit Trigger Button
            run_audit_v = st.button("📋 Run Brand Audit Report", key="vis_run_audit_btn")
            if run_audit_v:
                with st.spinner("AI Brand Director is auditing your asset..."):
                    # Assemble guidelines to verify
                    vis_guidelines_text = f"""
                    Workflow Type: Storefront Visualizer
                    Selected Storefront Style: {storefront_style_choice} ({STOREFRONT_STYLES[storefront_style_choice]})
                    Custom Storefront Template: {'Yes' if storefront_choice == 'Custom Upload...' else 'No (' + storefront_choice + ')'}
                    Custom Visual Requests: {vis_extra_prompt.strip() if vis_extra_prompt.strip() else 'None'}
                    Desired Aspect Ratio: {aspect_ratio}
                    """
                    try:
                        audit_text_v = audit_generated_image(st.session_state.vis_result_img, vis_guidelines_text)
                        st.session_state.vis_audit_report = audit_text_v
                    except Exception as audit_err:
                        st.error(f"Failed to audit asset: {str(audit_err)}")
                        
            # Render report if available
            if st.session_state.vis_audit_report is not None:
                st.markdown(st.session_state.vis_audit_report)

# ==========================================================
# TAB 4: ASSET GALLERY
# ==========================================================
with tab4:
    st.header("🖼️ Generated Asset Gallery")
    st.markdown("Browse, download, and delete generated marketing assets archived in Cloud Storage.")
    
    if not GCS_OUTPUT_BUCKET:
        st.warning("⚠️ Cloud Storage Output Bucket is not configured. Gallery is unavailable.")
    else:
        st.info(f"📁 Displaying archived assets from GCS Bucket: `{GCS_OUTPUT_BUCKET}`")
        
        # Pull latest 16 items by default
        gallery_items = list_gcs_gallery_images(GCS_OUTPUT_BUCKET, limit=16)
        
        if not gallery_items:
            st.info("No generated assets found in GCS. Try creating some images first!")
        else:
            # Refresh control
            st.button("🔄 Refresh Gallery", key="gallery_refresh_btn")
            
            # Responsive 4-column layout
            cols = st.columns(4)
            for idx, item in enumerate(gallery_items):
                col_idx = idx % 4
                with cols[col_idx]:
                    st.image(item["bytes"], use_container_width=True, output_format="PNG")
                    st.caption(f"📅 {item['updated'].strftime('%b %d, %Y %H:%M:%S')}")
                    st.write(f"`{item['short_name']}`")
                    
                    col_dl, col_del = st.columns(2)
                    with col_dl:
                        st.download_button(
                            label="📥 Download",
                            data=item["bytes"],
                            file_name=item["short_name"],
                            mime="image/png",
                            key=f"gallery_dl_{idx}"
                        )
                    with col_del:
                        delete_click = st.button("🗑️ Delete", key=f"gallery_del_{idx}")
                        if delete_click:
                            with st.spinner("Deleting blob..."):
                                try:
                                    delete_gcs_blob(GCS_OUTPUT_BUCKET, item["name"])
                                    st.success("Deleted!")
                                    st.rerun()
                                except Exception as del_err:
                                    st.error(str(del_err))
