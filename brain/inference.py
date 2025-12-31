import modal
import os

# Define the Modal Stub (now usually just App)
app = modal.App("magma-brain")

# 1. Define the Environment
# We need specific versions for Qwen3 support (transformers>=4.49.0)
image = (
    modal.Image.debian_slim()
    # Install system dependencies if any are needed for pillow/opencv (but slim usually ok for basic)
    .pip_install(
        "fastapi[standard]",
        "transformers>=4.49.0",
        "torch",
        "accelerate",
        "qwen-vl-utils",
        "pillow",
        "einops"
    )
)

# 2. Define Persistence
# Create a volume to store model weights so we don't redownload every time
vol = modal.Volume.from_name("magma-weights", create_if_missing=True)
MODEL_DIR = "/model"
MODEL_ID = "batwBMW/Magma-R1-4B-AndroidControl"

@app.cls(
    image=image,
    gpu="A10G",  # Or "T4" if A10G is overkill/unavailable, but prompt requested A10G
    volumes={MODEL_DIR: vol},  # Mount the volume at /model
    container_idle_timeout=300,  # Keep warm for 5 minutes
    timeout=600 # timeout for the function execution
)
class MagmaBrain:
    def __init__(self):
        # This will run when the container starts
        # We rely on the volume for persistence.
        pass

    @modal.enter()
    def load_model(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor

        print(f"Loading model {MODEL_ID} from {MODEL_DIR}...")
        
        # We use the volume path as the cache_dir.
        # If files exist, transformers will use them. If not, it downloads them there.
        # trust_remote_code=True is CRITICAL for Qwen3/Magma
        
        self.processor = AutoProcessor.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            cache_dir=MODEL_DIR
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            cache_dir=MODEL_DIR
        )
        # Ensure model is in eval mode
        self.model.eval()
        print("Model loaded successfully.")

    @modal.web_endpoint(method="POST")
    def analyze(self, item: dict):
        """
        Input: {'image': 'base64_string', 'prompt': 'text_string'}
        Output: JSON string from the model
        """
        import base64
        import io
        from PIL import Image
        from qwen_vl_utils import process_vision_info

        image_b64 = item.get("image")
        prompt_text = item.get("prompt", "Describe this UI.")

        if not image_b64:
            return {"error": "No image provided"}

        # Decode image
        try:
            image_data = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            return {"error": f"Invalid image data: {str(e)}"}

        # Prepare messages
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt_text},
                ],
            }
        ]

        # Process input
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.model.device)

        # Generate
        generated_ids = self.model.generate(**inputs, max_new_tokens=512)
        
        # Trim the input tokens from the output
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

        return output_text[0]

# Local testing block
if __name__ == "__main__":
    import base64
    
    # Create a dummy image for testing if run locally
    # verification: modal run brain/inference.py
    print("To test, run: modal run brain/inference.py")
    
    with modal.enable_root_logging():
        pass
