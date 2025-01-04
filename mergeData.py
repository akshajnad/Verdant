#############################################
# create_final_dataset.py
#############################################

import os
import subprocess
import pandas as pd
import numpy as np


DATASET_1 = "tejashvi14/crop-production"
DATASET_2 = "itssuru/india-rainfall-data"
DATASET_3 = "miguelaenlle/farm-advice-text"  

def download_from_kaggle(dataset, out_path):
    """
    Uses Kaggle CLI to download a dataset into out_path.
    """
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    cmd = f"kaggle datasets download -d {dataset} -p {out_path} --unzip"
    subprocess.run(cmd, shell=True, check=True)

def main():
    print("Downloading real datasets from Kaggle...")
    download_from_kaggle(DATASET_1, "data/crop_production")
    download_from_kaggle(DATASET_2, "data/weather_data")
    download_from_kaggle(DATASET_3, "data/farm_text")

    df_crop = pd.read_csv("data/crop_production/Crop_production.csv")

    df_weather = pd.read_csv("data/weather_data/rainfall.csv")

    df_text = pd.read_csv("data/farm_text/farm_instructions.csv")

   
    df_crop = df_crop.rename(columns={
        'State': 'region',
        'District': 'subregion',
        'Crop_Year': 'year',
        'Season': 'season',
        'Crop': 'crop',
        'Area': 'area_hectare',
        'Production': 'production_tons'
    })

    df_crop = df_crop.dropna(subset=['area_hectare','production_tons'])


    df_weather = df_weather.rename(columns={
        'STATE_UT_NAME': 'region',
        'ANNUAL': 'rainfall_mm'
    })

    df_weather = df_weather.dropna(subset=['rainfall_mm'])

    if 'YEAR' in df_weather.columns:
        df_weather = df_weather.rename(columns={'YEAR': 'year'})

    df_merged = pd.merge(df_crop, df_weather, on=['region','year'], how='inner')


    df_text = df_text.rename(columns={
        'crop': 'crop',
        'season': 'season',
        'instructions': 'text_instructions'
    })
    df_final = pd.merge(df_merged, df_text, on=['crop','season'], how='inner')


    df_final['urgency'] = np.random.randint(1, 6, size=len(df_final))

    df_final['num_people'] = (df_final['production_tons'] / 10).apply(lambda x: max(5, min(500, x))) \
                             + np.random.randint(0,100,len(df_final))

    df_final['volume_goal'] = (df_final['num_people']/100.0) + np.random.uniform(1,50,len(df_final))

    df_final['calorie_goal'] = np.random.uniform(500,4000,len(df_final)) + df_final['num_people']*2

    df_final['free_space'] = df_final['area_hectare']*10 + np.random.uniform(0,2000,len(df_final))

  
    df_final['weather_temp'] = np.random.uniform(15,35,len(df_final))

    # - weather_rain: scaled from rainfall_mm
    df_final['weather_rain'] = df_final['rainfall_mm']/2000.0
    df_final.loc[df_final['weather_rain']>1,'weather_rain'] = 1.0  # clamp

    df_final['existing_crops_vector'] = df_final['production_tons'] / 1000.0

    # - fraction_of_space_used: area_hectare / free_space, clamped
    frac = (df_final['area_hectare']*10) / df_final['free_space']
    df_final['fraction_of_space_used'] = np.minimum(frac, 0.85)

    # We keep the textual instructions from df_text under 'text_instructions'

    # 8) Final columns:
    final_cols = [
        'urgency',
        'num_people',
        'volume_goal',
        'calorie_goal',
        'free_space',
        'weather_temp',
        'weather_rain',
        'existing_crops_vector',
        'fraction_of_space_used',
        'text_instructions'
    ]

    # Ensure these columns exist
    for col in final_cols:
        if col not in df_final.columns:
            df_final[col] = 0

    # 9) Subset the final DataFrame
    df_result = df_final[final_cols].copy()

    # Shuffle
    df_result = df_result.sample(frac=1.0, random_state=42).reset_index(drop=True)

    # 10) Save to CSV
    df_result.to_csv("final_dataset.csv", index=False)
    print("final_dataset.csv created with shape:", df_result.shape)

if __name__ == "__main__":
    main()
