import pandas as pd

def clean_and_merge(file_list, remove_duplicates=True):
    all_frames = []
    
    for file in file_list:
        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
        
        # Drop completely empty columns (such as Unnamed: 0)
        df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed', case=False)]
        
        # Standardize column headers to lowercase with underscores
        clean_cols = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        
        # Force every column name inside this file to be unique
        seen = {}
        unique_cols = []
        for col in clean_cols:
            if col in seen:
                seen[col] += 1
                unique_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                unique_cols.append(col)
        df.columns = unique_cols
        
        # Drop completely empty rows and tag source file
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
