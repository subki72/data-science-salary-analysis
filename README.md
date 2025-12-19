# Data Science Salary Analysis (2020-2022)

![Language](https://img.shields.io/badge/Language-Python%20%7C%20SQL-blue)
![Tools](https://img.shields.io/badge/Tools-Jupyter%20%7C%20Pandas%20%7C%20Seaborn-green)
![Status](https://img.shields.io/badge/Status-Completed-success)

## Project Overview
This project aims to analyze the trends in Data Science salaries globally from 2020 to 2022. By utilizing a dataset of real-world salaries, this analysis provides insights into how factors such as **experience level**, **employment type**, **remote work ratio**, and **job titles** influence compensation in the tech industry.

The project demonstrates a hybrid workflow, executing **SQL queries** directly within a Python environment to bridge the gap between database management and data visualization.

## Business Questions
To guide the analysis, the following strategic questions were formulated:
1.  **Salary Trend:** Is there a significant increase in salaries for data roles over the years?
2.  **Experience Impact:** How does the salary scale progress from Entry-level to Executive roles?
3.  **Remote Work Analysis:** Does working remotely (WFH) negatively or positively affect salary compared to office-based roles?
4.  **Top Paying Roles:** Which specific job titles command the highest average salaries in the industry?

## Tech Stack
* **Language:** Python 3.9+
* **Query Language:** SQL (SQLite)
* **Libraries:**
    * `pandas` (Data Manipulation)
    * `sqlite3` (Database Connection)
    * `matplotlib` & `seaborn` (Data Visualization)
* **Environment:** Jupyter Notebook

## Dataset
The dataset used (`ds_salaries.csv`) contains the following key columns:
* `work_year`: The year the salary was paid.
* `experience_level`: EN (Entry), MI (Mid), SE (Senior), EX (Executive).
* `job_title`: The role of the employee (e.g., Data Scientist, Data Engineer).
* `salary_in_usd`: Salary converted to USD for uniform comparison.
* `remote_ratio`: The amount of work done remotely (0, 50, 100).

## Key Findings
Based on the SQL analysis and visualizations, here are the key takeaways:

* **Positive Market Trend:** There was a significant surge in average salaries in **2022**, indicating high demand for data professionals.
* **Seniority Pays:** Moving from a Mid-level (MI) to a Senior-level (SE) role offers the most significant salary jump.
* **Remote Work is Lucrative:** Surprisingly, fully remote positions (100% remote) tend to have a **higher average salary** compared to hybrid or on-site roles, likely due to competition from global tech companies.
* **Top Roles:** Specialized roles such as *Principal Data Engineer* and *Data Architect* are among the highest-paid positions, outearning generalist roles.

## How to Run This Project
1.  Clone this repository:
    ```bash
    git clone [https://github.com/yourusername/data-science-salary-analysis.git](https://github.com/yourusername/data-science-salary-analysis.git)
    ```
2.  Install the required libraries:
    ```bash
    pip install pandas matplotlib seaborn
    ```
3.  Open the Jupyter Notebook:
    ```bash
    jupyter notebook "Portfolio_Project_DS_Salaries.ipynb"
    ```

##  Author
**Muhammad Syafii Assubki**

---
*This project was created as part of my Data Science Portfolio to demonstrate proficiency in SQL and Python for Data Analysis.*
