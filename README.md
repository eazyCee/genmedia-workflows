# OnBrand Asset Creator 🎨

OnBrand Asset Creator is a Streamlit application designed to eliminate image-generation ambiguities. It provides structured, guided workflows that combine product images, model images, logos, colorways, and preapproved environment settings to generate brand-compliant marketing assets. 

The application is powered by **Gemini 3.1 Flash Image Preview** on Google Vertex AI.

---

## Features

### 🔄 Workflow A: Product + Model Mixer
- Upload a product image.
- Upload a model image.
- Add custom placement instructions (e.g., "Make the model wear these sunglasses").
- Generates a high-quality unified image where the model is using or wearing the product naturally.

### 🏷️ Workflow B: Brand Guideline Asset Creator
- **Brand Logos:** Select from preapproved logos or upload a custom logo.
- **Brand Colorways:** Choose a pre-defined brand color palette (e.g., Warm Terracotta, Minimalist Sage, Neon Cyberpunk, Classic Luxury).
- **Product Images:** Choose from preapproved product shapes or upload a custom product image.
- **Environment Settings:** Choose from studio lighting, nature settings, cafes, or office spaces.
- Generates high-end commercial ads that strictly respect your brand guidelines.

### 🏪 Workflow C: Storefront Visualizer
- Upload your logo, brand sign, banner design, or custom artwork.
- Choose from preapproved blank storefront templates or upload your own storefront canvas.
- Select preapproved storefront styles (e.g. Luxury Boutique, Cozy Cafe, Modern Tech Store, Minimalist Apparel).
- Generates ultra-realistic visualizations showing how your design fits naturally on the storefront window, sign bracket, or billboard facade, matching reflections, perspectives, and shadows perfectly.

---

## Directory Structure

```text
/Users/clifftangel/Documents/genmedia/
├── Dockerfile
├── README.md
├── requirements.txt
├── app/
│   ├── main.py           # Streamlit App entry point
│   ├── utils.py          # Vertex AI API interactions
│   └── assets/
│       ├── logos/        # Preapproved logo assets
│       ├── products/     # Preapproved product assets
│       └── storefronts/  # Preapproved blank storefront templates
```

---

## 📁 Predefined Assets & Developer Guide

All predefined options (Logos, Products, and Storefront Templates) in this application are **dynamically loaded** from their respective asset directories. 

Adding a new predefined asset does **not** require modifying any application code! Simply drop your new image into the appropriate directory following this standard layout:

### Asset Directory Locations:
*   **Brand Logos:** `app/assets/logos/`
*   **Brand Products:** `app/assets/products/`
*   **Storefront Templates:** `app/assets/storefronts/`

### How to Add Custom Preapproved Images:
1.  **Prepare your image:** Make sure the image is in a standard format (`.png`, `.jpg`, or `.jpeg`). For logos and products, a transparent background or a high-contrast outline is highly recommended.
2.  **Name the file nicely:** Name the file using snake_case or kebab-case. The app will automatically translate the filename into a clean, title-cased display option in the dropdown/selectors.
    *   *Example:* Saving a file as `ultra_minimal_logo.png` inside `app/assets/logos/` will automatically appear in the Streamlit selector as **Ultra Minimal Logo**.
3.  **Refresh the App:** Streamlit will automatically pick up the new image on the next generation or page reload!

---

## Running Locally

### 1. Set up virtual environment and dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Authentication & Environment Variables
The app uses the Google GenAI Python SDK. You can authenticate in one of two ways:

#### Option A: Using an API Key (Easiest for local test)
Set the `GOOGLE_CLOUD_API_KEY` environment variable:
```bash
export GOOGLE_CLOUD_API_KEY="your-vertex-ai-api-key"
```

#### Option B: Using Application Default Credentials (ADC)
Authenticate using the Google Cloud CLI:
```bash
gcloud auth application-default login
```

### 3. Run the Streamlit App
```bash
streamlit run app/main.py
```
The app will be accessible at `http://localhost:8501`.

---

## Deploying to Google Cloud Run

You can deploy this containerized Streamlit app directly to **Google Cloud Run** in just a few commands.

### 1. Configure Google Cloud CLI
Make sure you are logged in and have set your active project:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs
Enable the Cloud Build, Cloud Run, and Vertex AI (Generative Language/AI) APIs:
```bash
gcloud services enable run.googleapis.com \
                       builds.googleapis.com \
                       aiplatform.googleapis.com
```

### 3. Build & Deploy using Cloud Build and Cloud Run
Run the following command from the root of this project:
```bash
gcloud run deploy onbrand-asset-creator \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080
```

> [!IMPORTANT]
> **Service Account Permissions:**  
> Ensure that the default Cloud Run service account (or the custom service account you assign to the Cloud Run service) has the **Vertex AI User** (`roles/aiplatform.user`) role. This allows the service to call Gemini 3.1 on Vertex AI using ADC without needing hardcoded API keys.

---

## Technologies Used
- **Frontend Framework:** Streamlit
- **AI Model:** `gemini-3.1-flash-image-preview` via Vertex AI
- **Language:** Python 3.11
- **Containerization:** Docker
- **Deployment:** Google Cloud Run
# genmedia-workflows
