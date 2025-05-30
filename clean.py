import os
import pandas as pd
from datetime import datetime

def clean_and_format_results():
    output_folder = "output"
    cleaned_folder = "cleaned"
    
    # Check if output folder exists
    if not os.path.exists(output_folder):
        print(f"❌ Output folder '{output_folder}' not found.")
        return
        
    # Create cleaned folder if it doesn't exist
    if not os.path.exists(cleaned_folder):
        os.makedirs(cleaned_folder)
        print(f"📁 Created folder: {cleaned_folder}")
        
    all_data = []

    for file in os.listdir(output_folder):
        if file.endswith(".ods"):
            try:
                file_path = os.path.join(output_folder, file)
                df = pd.read_excel(file_path, engine="odf")
                df = df.rename(columns={
                    "Search Engine": "Search Platform",
                    "Result Title": "Title",
                    "Result Link": "Link"
                })
                df = df[["Search Platform", "Search Query", "Title", "Link"]]
                all_data.append(df)
                print(f"✅ Loaded: {file}")
            except Exception as e:
                print(f"⚠️ Error reading {file}: {e}")

    if not all_data:
        print("❌ No ODS files found in the output folder.")
        return

    merged_df = pd.concat(all_data, ignore_index=True)

    # Drop duplicates based on Title or Link
    cleaned_df = merged_df.drop_duplicates(subset=["Title", "Link"])

    # Save cleaned file in the cleaned folder
    today = datetime.now().strftime("%Y-%m-%d")
    output_filename = os.path.join(cleaned_folder, f"cleaned_search_results_{today}.ods")
    cleaned_df.to_excel(output_filename, engine="odf", index=False)

    print(f"\n🎉 Cleaned results saved to: {output_filename}")
    print(f"📊 Total unique entries: {len(cleaned_df)}")

if __name__ == "__main__":
    clean_and_format_results()