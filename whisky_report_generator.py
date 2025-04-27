import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import seaborn as sns
import os
from typing import Optional

import Data_Loading

class PDF(FPDF):
    def __init__(self):
        # Initialize parent class first
        super().__init__()
        # Initialize our custom attributes
        self.table_headers = []
        self.header_widths = []
        self.table_start_y = 0
        self.is_table_header = False
        self.left_margin = 0
        # Set auto page break
        self.set_auto_page_break(auto=True, margin=15)

    def set_table_header_props(self, headers, widths, left_margin=0):
        """Store the table headers and their widths for repeated use"""
        self.table_headers = headers
        self.header_widths = widths
        self.left_margin = left_margin
        
    def print_table_header(self):
        """Print the table header with bold font and blue background"""
        self.set_font("Arial", size=10, style='B')
        self.set_fill_color(200, 220, 255)  # Light blue
        self.set_x(self.left_margin)  # Set proper margin
        for header, width in zip(self.table_headers, self.header_widths):
            self.cell(width, 10, header, border=1, fill=True)
        self.ln()
        self.set_font("Arial", size=10, style='')  # Reset to normal font

    def header(self):
        """Override header method to repeat table headers on each page"""
        if self.is_table_header and self.page_no() > 1:  # Only repeat on pages after the first
            self.set_y(10)  # Set margin at top of page
            self.print_table_header()

def clean_text(text):
    """Clean text of special characters that might cause encoding issues"""
    if isinstance(text, str):
        # Replace problematic characters with ASCII equivalents
        replacements = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': '-',
            '…': '...',
            '\u2019': "'",  # Right single quotation mark
            '\u2018': "'",  # Left single quotation mark
            '\u201C': '"',  # Left double quotation mark
            '\u201D': '"',  # Right double quotation mark
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text.encode('ascii', 'replace').decode('ascii')
    return str(text)

def calculate_attendee_correlations(data: pd.DataFrame, attendee_name: str, min_common_whiskies: int = 50):
    """
    Calculate correlations between an attendee and all other attendees.
    
    Args:
        data: DataFrame containing all whisky scores
        attendee_name: The target attendee
        min_common_whiskies: Minimum number of common whiskies required for correlation
    
    Returns:
        DataFrame with correlations, sorted by correlation coefficient
    """
    # Get target attendee's scores
    target_scores = data[data['Attendee'] == attendee_name][['Whisky_ID', 'Whisky_Score']]
    
    # Get all other attendees
    other_attendees = data[data['Attendee'] != attendee_name]['Attendee'].unique()
    
    correlations = []
    for other_attendee in other_attendees:
        # Get other attendee's scores
        other_scores = data[data['Attendee'] == other_attendee][['Whisky_ID', 'Whisky_Score']]
        
        # Find common whiskies
        common_whiskies = pd.merge(target_scores, other_scores, 
                                 on='Whisky_ID', 
                                 suffixes=('_target', '_other'))
        
        if len(common_whiskies) >= min_common_whiskies:
            correlation = common_whiskies['Whisky_Score_target'].corr(common_whiskies['Whisky_Score_other'])
            correlations.append({
                'Attendee': other_attendee,
                'Correlation': correlation,
                'Common_Whiskies': len(common_whiskies)
            })
    
    return pd.DataFrame(correlations).sort_values('Correlation', ascending=False)

def find_largest_score_differences(data: pd.DataFrame, attendee_name: str):
    """
    Find the largest absolute differences between an attendee's scores and other members' scores,
    keeping only the single largest difference per whisky.
    """
    differences = []
    
    # Get target attendee's scores
    target_scores = data[data['Attendee'] == attendee_name][['Whisky_ID', 'Whisky_Score']]
    
    # Compare with each other attendee for each whisky
    for whisky_id in target_scores['Whisky_ID']:
        target_score = target_scores[target_scores['Whisky_ID'] == whisky_id]['Whisky_Score'].iloc[0]
        
        # Get other attendees' scores for this whisky
        other_scores = data[(data['Attendee'] != attendee_name) & 
                           (data['Whisky_ID'] == whisky_id)]
        
        # Find the largest difference for this whisky
        max_diff = 0
        max_diff_row = None
        
        for _, other_row in other_scores.iterrows():
            diff = abs(target_score - other_row['Whisky_Score'])
            if diff > max_diff:
                max_diff = diff
                max_diff_row = other_row
        
        if max_diff > 0 and max_diff_row is not None:
            differences.append({
                'Whisky_ID': whisky_id,
                'Description': max_diff_row['Whisky_Description'],
                'Distillery': max_diff_row['Whisky_Distillery'],
                'Age': max_diff_row['Whisky_Age_Corrected'],
                'Other_Attendee': max_diff_row['Attendee'],
                'Target_Score': target_score,
                'Other_Score': max_diff_row['Whisky_Score'],
                'Absolute_Difference': max_diff
            })
    
    return pd.DataFrame(differences).sort_values('Absolute_Difference', ascending=False)

def generate_personal_whisky_report(attendee_name: str, min_distillery_count: int = 5) -> Optional[str]:
    """
    Generate a personal whisky tasting report for a specific attendee.
    
    Args:
        attendee_name (str): Name of the attendee to generate report for
        min_distillery_count (int): Minimum number of whiskies required for a distillery to be included in top analysis
        
    Returns:
        str: Path to generated PDF report, or None if generation failed
    """
    try:
        # Load and validate data
        data = Data_Loading.load_whisky_data(
            remove_guests=True,
            remove_USwhiskies=False,
            remove_thresh=0,
            pointscale=False,
            fill_missing_age=True,
            min_whiskies_per_region=0
        )
        
        if data is None:
            raise ValueError("Failed to load whisky data")

        # Filter and prepare data
        current_focus = data[data['Attendee'] == attendee_name].copy()
        
        if len(current_focus) == 0:
            raise ValueError(f"No data found for attendee: {attendee_name}")

        # Calculate basic statistics
        attendee_stats = current_focus.groupby("Attendee").agg({
            'Meeting_Number': 'nunique',
            'Whisky_Score': ['count', 'mean'],
            'Whisky_Price': 'sum'
        }).reset_index()
        attendee_stats.columns = ['Attendee', 'meetings_attended', 'whiskies_scored', 'avg_score', 'total_price']

        # Process numerical data
        current_focus.loc[:, 'Whisky_Age_Corrected'] = current_focus['Whisky_Age_Corrected'].round(0)
        current_focus.loc[:, 'Whisky_ABV'] = current_focus['Whisky_ABV'] * 100
        current_focus['Age_Display'] = current_focus['Whisky_Age_Corrected'].apply(
            lambda x: 'NAN' if x == -1 else str(int(x)))

        # Generate distillery statistics
        top_distilleries = (current_focus.groupby('Whisky_Distillery')
                           .agg({'Whisky_Score': ['mean', 'count']})
                           .reset_index())
        top_distilleries.columns = ['Whisky_Distillery', 'avg_score', 'whisky_count']
        
        # Filter distilleries and get top/bottom
        filtered_distilleries = top_distilleries[top_distilleries['whisky_count'] >= 5]
        top_5 = filtered_distilleries .nlargest(5, 'avg_score')
        bottom_5 = filtered_distilleries .nsmallest(5, 'avg_score')

        # Generate region statistics
        top_regions = (current_focus.groupby('Whisky_Region')
                      .agg({'Whisky_Score': ['mean', 'count']})
                      .reset_index())
        top_regions.columns = ['Whisky_Region', 'avg_score', 'whisky_count']
        top_regions = top_regions.sort_values('whisky_count', ascending=False).head(10)

        # Filter regions and get top/bottom
        filtered_regions = top_regions[top_regions['whisky_count'] > min_distillery_count]
        top_3_regions = filtered_regions.nlargest(3, 'avg_score')
        bottom_3_regions = filtered_regions.nsmallest(3, 'avg_score')

        # Set up visualization style
        plt.style.use('seaborn-v0_8')
        sns.set_theme()

        # 1. Create trend chart
        plt.figure(figsize=(12, 6))
        scores_over_time = current_focus.sort_values('Whisky_ID')
        moving_avg = scores_over_time['Whisky_Score'].rolling(window=10, min_periods=1).mean()
        
        plt.plot(range(len(scores_over_time)), scores_over_time['Whisky_Score'], 
                'o', alpha=0.3, color='gray', label='Individual Scores')
        plt.plot(range(len(scores_over_time)), moving_avg, 
                '-', linewidth=2, color='blue', label='10-whisky Moving Average')
        
        plt.title('Scoring Trend Over Time\n10-whisky Moving Average', 
                  fontsize=16, fontname='Arial', fontweight='bold', pad=20)
        plt.xlabel('Whiskies Tasted (Chronological Order)', 
                  fontsize=16, fontname='Arial', fontweight='bold', labelpad=10)
        plt.ylabel('Score', 
                  fontsize=16, fontname='Arial', fontweight='bold', labelpad=10)
        plt.ylim(6, 10)
        plt.legend(prop={'family': 'Arial', 'size': 12, 'weight': 'bold'})
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        trend_chart = "trend_chart.png"
        plt.savefig(trend_chart, dpi=300, bbox_inches='tight')
        plt.close()

        # 2. Create distillery chart
        plt.figure(figsize=(12, 6))
        chart = sns.barplot(x='Whisky_Distillery', y='avg_score', data=filtered_distilleries)
        chart.set_title('Distilleries by Average Score\n(minimum 5 scores)', 
                        fontsize=16, fontname='Arial', fontweight='bold', pad=20)
        chart.set_xlabel('Distillery', 
                        fontsize=16, fontname='Arial', fontweight='bold', labelpad=10)
        chart.set_ylabel('Average Score', 
                        fontsize=16, fontname='Arial', fontweight='bold', labelpad=10)
        chart.set_ylim(6, 10)
        plt.xticks(range(len(filtered_distilleries)), filtered_distilleries['Whisky_Distillery'], 
                   rotation=45, ha='right', fontsize=12, fontname='Arial', fontweight='bold')
        plt.yticks(fontsize=12, fontname='Arial', fontweight='bold')
        plt.tight_layout()
        
        distillery_chart = "distillery_chart.png"
        plt.savefig(distillery_chart, dpi=300, bbox_inches='tight')
        plt.close()

        # 3. Create region chart
        plt.figure(figsize=(12, 6))
        chart = sns.barplot(x='Whisky_Region', y='avg_score', data=top_regions)
        chart.set_title('Regions by Average Score\n(most frequently scored)', 
                        fontsize=16, fontname='Arial', fontweight='bold', pad=20)
        chart.set_xlabel('Region', 
                        fontsize=16, fontname='Arial', fontweight='bold', labelpad=10)
        chart.set_ylabel('Average Score', 
                        fontsize=16, fontname='Arial', fontweight='bold', labelpad=10)
        chart.set_ylim(6, 10)
        plt.xticks(range(len(top_regions)), top_regions['Whisky_Region'], 
                   rotation=45, ha='right', fontsize=12, fontname='Arial', fontweight='bold')
        plt.yticks(fontsize=12, fontname='Arial', fontweight='bold')
        plt.tight_layout()
        
        region_chart = "region_chart.png"
        plt.savefig(region_chart, dpi=300, bbox_inches='tight')
        plt.close()

        # Calculate correlations and differences
        correlations_df = calculate_attendee_correlations(data, attendee_name, min_common_whiskies=50)
        differences_df = find_largest_score_differences(data, attendee_name)

        # Begin PDF generation
        pdf = PDF()

        # 1. Title page with summary stats and trend
        pdf.add_page()
        pdf.set_font("Arial", size=16, style='B')
        pdf.cell(200, 10, f"PMWC Report for {attendee_name}", ln=True, align='C')
        pdf.ln(10)

        # Add summary statistics
        for _, row in attendee_stats.iterrows():
            stats = [
                ("Meetings Attended:", str(row['meetings_attended'])),
                ("Whiskies Scored:", str(row['whiskies_scored'])),
                ("Total Price of Whiskies Scored:", f"${row['total_price']:,.2f}"),
                ("Average Score:", f"{row['avg_score']:.2f}")
            ]
            for label, value in stats:
                pdf.set_font("Arial", size=12, style='B')
                pdf.cell(pdf.get_string_width(label) + 2, 10, label)
                pdf.set_font("Arial", size=12, style='')
                pdf.cell(200 - pdf.get_string_width(label) - 2, 10, f" {value}", ln=True)
        pdf.ln(10)

        # Add trend chart
        pdf.image(trend_chart, x=10, w=190)
        pdf.ln(10)

        # 2. Distillery analysis page
        pdf.add_page()
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(200, 10, "Distillery Analysis", ln=True, align='C')
        pdf.ln(5)
        pdf.image(distillery_chart, x=10, w=190)
        pdf.ln(5)

        # Add distillery tables
        headers = [("Distillery", 60), ("Avg Score", 30), ("Count", 30)]
        left_margin = (210 - sum(w for _, w in headers)) / 2

        # Top distilleries
        pdf.set_font("Arial", size=11, style='B')
        pdf.cell(200, 10, "Top Distilleries", ln=True, align='C')
        
        pdf.set_font("Arial", size=10, style='B')
        pdf.set_fill_color(200, 220, 255)
        pdf.set_x(left_margin)
        for header, width in headers:
            pdf.cell(width, 10, header, border=1, fill=True)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for _, row in top_5.iterrows():
            pdf.set_x(left_margin)
            pdf.cell(60, 10, str(row['Whisky_Distillery'])[:30], border=1)
            pdf.cell(30, 10, f"{row['avg_score']:.2f}", border=1)
            pdf.cell(30, 10, str(int(row['whisky_count'])), border=1)
            pdf.ln()
        
        pdf.ln(10)

        # Bottom distilleries
        pdf.set_font("Arial", size=11, style='B')
        pdf.cell(200, 10, "Bottom Distilleries", ln=True, align='C')
        
        pdf.set_font("Arial", size=10, style='B')
        pdf.set_fill_color(200, 220, 255)
        pdf.set_x(left_margin)
        for header, width in headers:
            pdf.cell(width, 10, header, border=1, fill=True)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for _, row in bottom_5.iterrows():
            pdf.set_x(left_margin)
            pdf.cell(60, 10, str(row['Whisky_Distillery'])[:30], border=1)
            pdf.cell(30, 10, f"{row['avg_score']:.2f}", border=1)
            pdf.cell(30, 10, str(int(row['whisky_count'])), border=1)
            pdf.ln()

        # 3. Regional analysis page
        pdf.add_page()
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(200, 10, "Regional Analysis", ln=True, align='C')
        pdf.ln(5)
        pdf.image(region_chart, x=10, w=190)
        pdf.ln(10)

        # Add region tables
        headers = [("Region", 60), ("Avg Score", 30), ("Count", 30)]
        
        # Top regions
        pdf.set_font("Arial", size=11, style='B')
        pdf.cell(200, 10, "Top Regions", ln=True, align='C')
        
        pdf.set_font("Arial", size=10, style='B')
        pdf.set_fill_color(200, 220, 255)
        pdf.set_x(left_margin)
        for header, width in headers:
            pdf.cell(width, 10, header, border=1, fill=True)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for _, row in top_3_regions.iterrows():
            pdf.set_x(left_margin)
            pdf.cell(60, 10, str(row['Whisky_Region'])[:30], border=1)
            pdf.cell(30, 10, f"{row['avg_score']:.2f}", border=1)
            pdf.cell(30, 10, str(int(row['whisky_count'])), border=1)
            pdf.ln()
        
        pdf.ln(10)

        # Bottom regions
        pdf.set_font("Arial", size=11, style='B')
        pdf.cell(200, 10, "Bottom Regions", ln=True, align='C')
        
        pdf.set_font("Arial", size=10, style='B')
        pdf.set_fill_color(200, 220, 255)
        pdf.set_x(left_margin)
        for header, width in headers:
            pdf.cell(width, 10, header, border=1, fill=True)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for _, row in bottom_3_regions.iterrows():
            pdf.set_x(left_margin)
            pdf.cell(60, 10, str(row['Whisky_Region'])[:30], border=1)
            pdf.cell(30, 10, f"{row['avg_score']:.2f}", border=1)
            pdf.cell(30, 10, str(int(row['whisky_count'])), border=1)
            pdf.ln()

        # 4. Scoring pattern analysis page
        pdf.add_page()
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(200, 10, "Scoring Pattern Analysis", ln=True, align='C')
        pdf.ln(5)

        # Similar scorers
        pdf.set_font("Arial", size=11, style='B')
        pdf.cell(200, 10, "Most Similar Scorers", ln=True)
        
        headers = [("Attendee", 60), ("Correlation", 40), ("Common Whiskies", 40)]
        left_margin = (210 - sum(w for _, w in headers)) / 2
        
        pdf.set_font("Arial", size=10, style='B')
        pdf.set_fill_color(200, 220, 255)
        pdf.set_x(left_margin)
        for header, width in headers:
            pdf.cell(width, 10, header, border=1, fill=True)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for _, row in correlations_df.head(3).iterrows():
            pdf.set_x(left_margin)
            pdf.cell(60, 10, str(row['Attendee']), border=1)
            pdf.cell(40, 10, f"{row['Correlation']:.3f}", border=1)
            pdf.cell(40, 10, str(row['Common_Whiskies']), border=1)
            pdf.ln()
        
        pdf.ln(10)

        # Different scorers
        pdf.set_font("Arial", size=11, style='B')
        pdf.cell(200, 10, "Most Different Scorers", ln=True)
        
        pdf.set_font("Arial", size=10, style='B')
        pdf.set_x(left_margin)
        for header, width in headers:
            pdf.cell(width, 10, header, border=1, fill=True)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for _, row in correlations_df.tail(3).iterrows():
            pdf.set_x(left_margin)
            pdf.cell(60, 10, str(row['Attendee']), border=1)
            pdf.cell(40, 10, f"{row['Correlation']:.3f}", border=1)
            pdf.cell(40, 10, str(row['Common_Whiskies']), border=1)
            pdf.ln()
        
        pdf.ln(10)

        # Largest differences table
        pdf.set_font("Arial", size=11, style='B')
        pdf.cell(200, 10, "Largest Score Differences", ln=True)
        
        # Updated headers with all columns
        diff_headers = [
            ("Description", 60),
            ("Distillery", 35),
            ("Age", 15),
            ("Other Attendee", 30),
            ("Your Score", 20), 
            ("Their Score", 20), 
            ("Difference", 20)
        ]
        diff_margin = (210 - sum(w for _, w in diff_headers)) / 2
        
        pdf.set_font("Arial", size=10, style='B')
        pdf.set_x(diff_margin)
        for header, width in diff_headers:
            pdf.cell(width, 10, header, border=1, fill=True)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        for _, row in differences_df.head(5).iterrows():
            pdf.set_x(diff_margin)
            pdf.cell(60, 10, clean_text(str(row['Description']))[:30], border=1)
            pdf.cell(35, 10, clean_text(str(row['Distillery']))[:17], border=1)
            pdf.cell(15, 10, str(int(row['Age'])) if row['Age'] >= 0 else 'NAN', border=1)
            pdf.cell(30, 10, clean_text(str(row['Other_Attendee']))[:15], border=1)
            pdf.cell(20, 10, f"{row['Target_Score']:.1f}", border=1)
            pdf.cell(20, 10, f"{row['Other_Score']:.1f}", border=1)
            pdf.cell(20, 10, f"{row['Absolute_Difference']:.1f}", border=1)
            pdf.ln()

        # 5. Complete scoring history
        pdf.add_page()
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(200, 10, "Complete Scoring History", ln=True, align='C')
        pdf.ln(5)

        # Sort data by score in descending order
        sorted_data = current_focus.sort_values(['Whisky_Score'], ascending=[False])
        
        # Set up detailed scores table with smaller font and updated headers
        headers = [
            ("Meeting", 15), 
            ("Score", 15), 
            ("Description", 50),
            ("Distillery", 35),
            ("Age", 12), 
            ("Region", 25), 
            ("ABV%", 12), 
            ("Price", 20)
        ]
        detail_left_margin = (210 - sum(width for _, width in headers)) / 2
        
        pdf.set_table_header_props(
            [h[0] for h in headers],
            [h[1] for h in headers],
            detail_left_margin
        )
        pdf.is_table_header = True

        # Print header
        pdf.set_font("Arial", size=8, style='B')  # Reduced font size
        pdf.set_fill_color(200, 220, 255)
        pdf.set_x(detail_left_margin)
        for header, width in headers:
            pdf.cell(width, 10, header, border=1, fill=True)
        pdf.ln()

        # Print all scores
        pdf.set_font("Arial", size=8)  # Reduced font size
        for _, row in sorted_data.iterrows():
            if pdf.get_y() > pdf.page_break_trigger:
                pdf.add_page()
            
            pdf.set_x(detail_left_margin)
            pdf.cell(15, 10, str(int(row['Meeting_Number'])), border=1)
            pdf.cell(15, 10, f"{row['Whisky_Score']:.1f}", border=1)
            pdf.cell(50, 10, clean_text(str(row['Whisky_Description']))[:35], border=1)
            pdf.cell(35, 10, clean_text(str(row['Whisky_Distillery']))[:20], border=1)
            pdf.cell(12, 10, row['Age_Display'], border=1)
            pdf.cell(25, 10, clean_text(str(row['Whisky_Region']))[:15], border=1)
            pdf.cell(12, 10, f"{row['Whisky_ABV']:.0f}%", border=1)
            pdf.cell(20, 10, f"${row['Whisky_Price']:,.0f}", border=1)
            pdf.ln()

        # Generate output and cleanup
        output_filename = f"whisky_report_{attendee_name.replace(' ', '_').lower()}.pdf"
        pdf.output(output_filename)

        for chart_file in [distillery_chart, region_chart, trend_chart]:
            if os.path.exists(chart_file):
                os.remove(chart_file)

        return output_filename

    except Exception as e:
        print(f"Error generating report: {e}")
        return None 