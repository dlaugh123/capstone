#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
#import traceback

def load_whisky_data(remove_guests=True,remove_USwhiskies=False, remove_thresh=0, pointscale=False, fill_missing_age=True, min_whiskies_per_region=0):

    """
    Load whisky data and optionally process it.
    
    Args:
        remove_guests (bool): If True, removes guest scores.  Defaults to True.
        remove_USwhiskies (bool): If True, removes US whiskies scores.  Defaults to False.
        remove_thresh (int): If above 0, removes outlier values below X.  Defaults to 0.
        pointscale (bool): If True, rescales the scores after we've removed outliers.  Defaults to False.
        fill_missing_age (bool): If True, sets a placeholder for missing whisky ages and adds a field noting this.  Defaults to True.
        min_whiskies_per_region (int): If above 0, removes any region that has lower than X unique whiskies.  Defaults to 0.

    Returns:
        pd.DataFrame: Processed DataFrame containing the whisky data.
    """
    try:
        # variables
        scores_df = None
        whiskies_df = None
        data = None
        file_path = 'Master Data File.xlsx'
        scores_tab = 'Scores'
        whiskies_tab = 'Whiskies'
    
        # Test that the file is in the right place
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return None
        
        # Load the Scores from the master Excel file
        scores_df = pd.read_excel(file_path, sheet_name=scores_tab)
#        print("Scores Data Loaded:", scores_df.shape)
        
        # Load the Whiskies from the master Excel file with specified dtypes
        columns_to_keep = ['Whisky_ID', 'Whisky_Distillery', 'Whisky_Age_Corrected', 'Whisky_Description',
                   'Whisky_Region', 'Whisky_ABV', 'Whisky_Price', 'Meeting_Number', 'Whisky_Bottling']
        dtype_dict = {
            'Whisky_ID': float,
            'Whisky_Distillery': str,
            'Whisky_Age_Corrected': float,
            'Whisky_Description': str,
            'Whisky_Region': str,
            'Whisky_ABV': float,
            'Whisky_Price': float,
            'Meeting_Number': float,
            'Whisky_Bottling': str
        }

        whiskies_df = pd.read_excel(file_path, sheet_name=whiskies_tab,usecols=columns_to_keep, dtype=dtype_dict)
#        print("Whiskies Data Loaded:", whiskies_df.shape)

        # Create a new true/false field set to whether the whisky is a distillery or independent bottling, then drop the original field
        whiskies_df['Whisky_OB'] = (whiskies_df['Whisky_Bottling'] == 'OB').astype(int)
        whiskies_df = whiskies_df.drop(columns=['Whisky_Bottling'])

        # Create a new field indicating when in a particular meeting a whisky was tasted, then drop Meeting_Number (it is already in Scores)
        whiskies_df['Tasting_Position'] = whiskies_df.groupby('Meeting_Number')['Whisky_ID'].rank(method='first').astype(int)
        whiskies_df = whiskies_df.drop(columns=['Meeting_Number'])
        
        # Perform a left join to ensure no score data is lost
        data = pd.merge(scores_df, whiskies_df, on='Whisky_ID', how='left')
        
        # Drop the guest scores if remove_guests = True
        if remove_guests and 'Guest' in data.columns:
            data = data[data['Guest'] != 1]
        
        # Drop US whiskies USwhiskies = True
        if remove_USwhiskies:
            data = data[data['Whisky_Region'] != 'USA']
        
        # Drop low scoring outliers if remove_below = True
        if remove_thresh>0:
            avg_scores = data.groupby('Whisky_ID')['Whisky_Score'].mean()
            low_score_whiskies = avg_scores[avg_scores < remove_thresh].index
            data = data[~data['Whisky_ID'].isin(low_score_whiskies)]
            data = data[data['Whisky_Score'] >= remove_thresh]
        
        # Rescale if pointscale = True
        if pointscale:
            data['Whisky_Score'] = (data['Whisky_Score'] - remove_thresh) * 10

        # Filter out regions with fewer than min_whiskies_per_region unique Whisky_IDs
        if min_whiskies_per_region > 0:
            region_counts = data.groupby('Whisky_Region')['Whisky_ID'].nunique()
            valid_regions = region_counts[region_counts >= min_whiskies_per_region].index
            data = data[data['Whisky_Region'].isin(valid_regions)]
            
        # Create a new field for missing age values and set to -1 if  the guest scores if fill_missing_age = True
        if fill_missing_age:
            data['Age_Missing'] = data['Whisky_Age_Corrected'].isna().astype(int)
            data['Whisky_Age_Corrected'] = data['Whisky_Age_Corrected'].fillna(-1)

        return data

    except Exception as e:
       print(f"Error loading data: {e}")
#       traceback.print_exc()
       return None        




