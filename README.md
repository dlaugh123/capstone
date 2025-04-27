### Pleasanton Malt Whisky Circle Statistics

David Melaugh

Please see Project Presentation for more details: https://github.com/dlaugh123/capstone/blob/main/Project%20Presentation.pdf.

#### Executive summary

Started in November 2009, the Pleasanton Malt Whisky Circle is composed a group of friends that have met roughly every six weeks to connect over a shared love of whisky -- primarily Scotch whisky. 

We typically taste six whiskies per meeting, and scores are recorded for each attendee. Meetings have 10-20 attendees.

To date, we have held 125 meetings, scoring over 750 whiskies. Once collected and organized for this Capstone Project, this yielded a database of almost 12,000 whisky scores.

This project analyzes that data.


#### Rationale

Though I will acknowledge I am not curing cancer here, PMWC meetings have been an enjoyable part of my life for over ten years. This Capstone Project offers a great opportunity to give back to the group to help our members better understand our own shared tastes.

The PMWC whisky scores also happen to offer a nicely sized dataset that is amenable to many of the learnings and techniques imparted by the Machine Learning and Artificial Intelligence Certificate Course, and the dataset is large enough that other whisky enthusiasts may draw from learnings from the project outcome here.


#### Research Question

Presently, this Capstone project has four outputs:

- Member Reports, which provide PMWC with an overview of their whisky scoring history
- "Easy Grader" analysis, aiming to show whether certain members habitually score higher or lower than the group average.
- Similarity analysis, aiming to show commonalities between individual group members.
- Score Prediction analysis, aiming to predict PMWC scores given certain whisky attributes such as price, age, and region.


#### Data Sources

The collected scores of PMWC whisky tastings.


#### Methodology
The methodologies are more fully described in the Project Presentation, but included:

- Data ingestion and cleaning in Excel
- Visualization via plotly, seaborn, and pyplot
- Regression, ensemble techniques, gradient boosting, and other predictive analysis models


#### Results

The results are more fully described in the Project Presentation, but included:

- Certain members are, in fact, "easier" or "harder" graders, though some of this variance can be explained by specific tastes that differ from the group average.
- In general, the group is inter-correlated, with every individual member having a positive score correlation with every other individual member.  Some members are more strongly correlated with each other, suggesting similarities in tastes or scoring habits.
- Predictive modeling techniques are capable of moderate accuracy, topping out at R^2 0.49 / NMSE 0.51 for specific score prediction or 62% accuracy for high/medium/low score bucket prediction.


#### Next steps

The project is in near final form.  One significant addition I intend to make prior to finalization is to compare the predictions from this project to subsequent data.  Our group has held two meetings since I started this project, and that data is not part of the current dataset.  I intend to try to "predict" the score results from those meetings.

There is an external source of public whisky reviews, www.whiskybase.com, that I might try to correlate with this dataset.  It would, however, involve considerable manual effort to match specific whiskies at that site with the correct whiskies in the PMWC's dataset.

#### Outline of project

Project Presentation: https://github.com/dlaugh123/capstone/blob/main/Project%20Presentation.pdf

Data: https://github.com/dlaugh123/capstone/blob/main/Master%20Data%20File.xlsx

Data loading: https://github.com/dlaugh123/capstone/blob/main/Data_Loading.py

Initial visualizations:
https://github.com/dlaugh123/capstone/blob/main/Data%20Analysis.Visualization.ipynb

Member Report generator: 
https://github.com/dlaugh123/capstone/blob/main/whisky_report_generator.py

Sample report: https://github.com/dlaugh123/capstone/blob/main/whisky_report_david_melaugh.pdf

Easy Grader analysis: https://github.com/dlaugh123/capstone/blob/main/Data%20Analysis.Easy%20Graders.ipynb

Similarity analysis: https://github.com/dlaugh123/capstone/blob/main/Data%20Analysis.Most%20Similar.ipynb

Score Prediction analysis:
https://github.com/dlaugh123/capstone/blob/main/Data%20Analysis.Regression.ipynb


##### Contact and Further Information

David Melaugh
melaugh@gmail.com


##### AI Usage Statement

First draft of all code was written by author.  Code was subsequently improved and refined via dialog with ChatGPT Canvas code editor.

Heaviest use of AI was in the Member Report Generator, to refine PDF formatting, and in the Score Prediction analysis, to employ techniques outside scope of course materials (e.g., LightGBM, CatBoost).

