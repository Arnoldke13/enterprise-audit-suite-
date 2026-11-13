import pandas as pd

def clean_and_merge(file_list, remove_duplicates=True):
    all_frames = []
    
    for file in file_list:
        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        df = df.dropna(how="all").copy()
        df["source_file"] = file.name
        all_frames.append(df)

    merged_df = pd.concat(all_frames, ignore_index=True)
    raw_count = len(merged_df)

    if remove_duplicates:
        data_cols = [c for c in merged_df.columns if c != "source_file"]
        merged_df = merged_df.drop_duplicates(subset=data_cols).reset_index(drop=True)

    removed_count = raw_count - len(merged_df)
    return merged_df, raw_count, removed_count
