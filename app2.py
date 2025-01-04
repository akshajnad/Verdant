#############################################
# advanced_schedule_helper.py
#############################################
import os
import numpy as np
import tensorflow as tf
from transformers import GPT2Tokenizer, TFGPT2LMHeadModel

ALLOCATION_MODEL_PATH = os.path.join(os.path.dirname(__file__), "allocation_model.h5")
TEXT_MODEL_DIR = os.path.join(os.path.dirname(__file__), "text_generation_model")

# Load numeric model
allocation_model = tf.keras.models.load_model(ALLOCATION_MODEL_PATH)

# Load GPT-2 model & tokenizer
tokenizer = GPT2Tokenizer.from_pretrained(TEXT_MODEL_DIR)
gpt_model = TFGPT2LMHeadModel.from_pretrained(TEXT_MODEL_DIR)

def generate_text_instructions(prompt: str, max_length=250) -> str:
    """
    Generate step-by-step schedule instructions from GPT-2,
    based on real data training.
    """
    input_ids = tokenizer.encode(prompt, return_tensors="tf")
    output_sequences = gpt_model.generate(
        input_ids=input_ids,
        max_length=max_length,
        temperature=0.8,
        top_p=0.95,
        do_sample=True
    )
    text = tokenizer.decode(output_sequences[0], skip_special_tokens=True)
    return text

def build_prompt(request_info, weather_info):
    """
    Build a prompt that includes relevant numeric features,
    letting GPT-2 produce a multi-week schedule for that request.
    """
    prompt = (
        f"Provide a detailed multi-week planting and care schedule.\n"
        f"Request info:\n"
        f" - Urgency: {request_info.get('urgency', 1)}\n"
        f" - People: {request_info.get('num_people', 0)}\n"
        f" - Volume Goal: {request_info.get('volume_goal', 0)}\n"
        f" - Calorie Goal: {request_info.get('calorie_goal', 0)}\n"
        f" - Additional Needs: {request_info.get('additional_needs','')}\n"
        f"Weather forecast:\n"
        f" - Temperature: {weather_info.get('temperature', 20)} C\n"
        f" - Rain Probability: {weather_info.get('rain_prob',0.2)*100:.1f}%\n\n"
        f"Now write the weekly instructions:\n"
        f"Week 1:"
    )
    return prompt

def generate_full_schedule(requests, weather, free_space):
    """
    For each request:
      1) Predict fraction_of_space with 'allocation_model'
      2) Generate textual instructions with GPT-2
    Combine into one global schedule.
    """
    # Build numeric features for each request
    # We'll assume each request -> row: [urgency, num_people, volume_goal, calorie_goal, free_space, weather_temp, weather_rain, existing_crops=0]
    X_inputs = []
    for req in requests:
        row = [
            req.get("urgency",1),
            req.get("num_people",0),
            req.get("volume_goal",0),
            req.get("calorie_goal",0),
            free_space,  # from admin's total
            weather.get("temperature",20),
            weather.get("rain_prob",0.2),
            0.0  # existing_crops_vector placeholder
        ]
        X_inputs.append(row)

    X_inputs = np.array(X_inputs, dtype=float)
    frac_preds = allocation_model.predict(X_inputs)  # shape: (len(requests),1)

    schedule_res = []
    used_fraction = 0.0

    for i, req in enumerate(requests):
        fraction = frac_preds[i][0]
        used_fraction += fraction
        # Build prompt
        prompt = build_prompt(req, weather)
        instructions = generate_text_instructions(prompt, max_length=300)

        schedule_res.append({
            "request_id": req.get("id"),
            "fraction_space": fraction,
            "instructions": instructions
        })

    # Combine into a single textual output
    master_text = "=== COMPREHENSIVE SCHEDULE ===\n\n"
    for r in schedule_res:
        master_text += f"Request {r['request_id']} -> fraction {r['fraction_space']*100:.1f}%\n"
        master_text += f"{r['instructions']}\n\n"
    master_text += f"Total fraction used: {used_fraction*100:.1f}%\n\n"

    return {
        "schedule_list": schedule_res,
        "master_text": master_text
    }



#############################################
# advanced_schedule_helper.py
#############################################
import os
import numpy as np
import tensorflow as tf
from transformers import GPT2Tokenizer, TFGPT2LMHeadModel

ALLOCATION_MODEL_PATH = os.path.join(os.path.dirname(__file__), "allocation_model.h5")
TEXT_MODEL_DIR = os.path.join(os.path.dirname(__file__), "text_generation_model")

# Load numeric model
allocation_model = tf.keras.models.load_model(ALLOCATION_MODEL_PATH)

# Load GPT-2 model & tokenizer
tokenizer = GPT2Tokenizer.from_pretrained(TEXT_MODEL_DIR)
gpt_model = TFGPT2LMHeadModel.from_pretrained(TEXT_MODEL_DIR)

def generate_text_instructions(prompt: str, max_length=250) -> str:
    """
    Generate step-by-step schedule instructions from GPT-2,
    based on real data training.
    """
    input_ids = tokenizer.encode(prompt, return_tensors="tf")
    output_sequences = gpt_model.generate(
        input_ids=input_ids,
        max_length=max_length,
        temperature=0.8,
        top_p=0.95,
        do_sample=True
    )
    text = tokenizer.decode(output_sequences[0], skip_special_tokens=True)
    return text

def build_prompt(request_info, weather_info):
    """
    Build a prompt that includes relevant numeric features,
    letting GPT-2 produce a multi-week schedule for that request.
    """
    prompt = (
        f"Provide a detailed multi-week planting and care schedule.\n"
        f"Request info:\n"
        f" - Urgency: {request_info.get('urgency', 1)}\n"
        f" - People: {request_info.get('num_people', 0)}\n"
        f" - Volume Goal: {request_info.get('volume_goal', 0)}\n"
        f" - Calorie Goal: {request_info.get('calorie_goal', 0)}\n"
        f" - Additional Needs: {request_info.get('additional_needs','')}\n"
        f"Weather forecast:\n"
        f" - Temperature: {weather_info.get('temperature', 20)} C\n"
        f" - Rain Probability: {weather_info.get('rain_prob',0.2)*100:.1f}%\n\n"
        f"Now write the weekly instructions:\n"
        f"Week 1:"
    )
    return prompt

def generate_full_schedule(requests, weather, free_space):
    """
    For each request:
      1) Predict fraction_of_space with 'allocation_model'
      2) Generate textual instructions with GPT-2
    Combine into one global schedule.
    """
    # Build numeric features for each request
    # We'll assume each request -> row: [urgency, num_people, volume_goal, calorie_goal, free_space, weather_temp, weather_rain, existing_crops=0]
    X_inputs = []
    for req in requests:
        row = [
            req.get("urgency",1),
            req.get("num_people",0),
            req.get("volume_goal",0),
            req.get("calorie_goal",0),
            free_space,  # from admin's total
            weather.get("temperature",20),
            weather.get("rain_prob",0.2),
            0.0  # existing_crops_vector placeholder
        ]
        X_inputs.append(row)

    X_inputs = np.array(X_inputs, dtype=float)
    frac_preds = allocation_model.predict(X_inputs)  # shape: (len(requests),1)

    schedule_res = []
    used_fraction = 0.0

    for i, req in enumerate(requests):
        fraction = frac_preds[i][0]
        used_fraction += fraction
        # Build prompt
        prompt = build_prompt(req, weather)
        instructions = generate_text_instructions(prompt, max_length=300)

        schedule_res.append({
            "request_id": req.get("id"),
            "fraction_space": fraction,
            "instructions": instructions
        })

    # Combine into a single textual output
    master_text = "=== COMPREHENSIVE SCHEDULE ===\n\n"
    for r in schedule_res:
        master_text += f"Request {r['request_id']} -> fraction {r['fraction_space']*100:.1f}%\n"
        master_text += f"{r['instructions']}\n\n"
    master_text += f"Total fraction used: {used_fraction*100:.1f}%\n\n"

    return {
        "schedule_list": schedule_res,
        "master_text": master_text
    }


