import pandas as pd
import streamlit as st
import datetime as dt

st.set_page_config(page_icon="👮🏻‍♂️", page_title= "Check Post Dashboard" , layout= "wide")

st.header("Welcome to Police Check Post Logs")
st.sidebar.subheader("Upload old logs in '.csv' Format")
file = st.sidebar.file_uploader("Upload Here", type= ["csv"])

file_df = pd.DataFrame()

if file:
    file_df = pd.read_csv(file)
    file_df.fillna("None", inplace= True) # Changing the NAN values into "None"
    file_df['stop_date'] = pd.to_datetime(file_df['stop_date']).dt.date
    file_df['stop_time'] = pd.to_datetime(file_df['stop_time']).dt.time
    file_df.drop(columns= ["driver_age_raw"], axis= 1, inplace= True)
    st.success("File Uploaded Sucessfully! Here is a preview!")
    st.dataframe(file_df)

import mysql.connector 

def db_connect():
    return mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "4122", # Change Password Authetication type to 'standard' if error showsup
        database = "police_checkpost_logs"
    )

def df_into_db():
    conn = db_connect()
    cursor = conn.cursor()

    for _, row in file_df.iterrows():
        cursor.execute(
            """
        insert into logs(
        stop_date,
        stop_time,
        country_name,
        driver_gender,
        driver_age,
        driver_race,
        violation_raw,
        violation,
        search_conducted,
        search_type,
        stop_outcome,
        is_arrested,
        stop_duration,
        drugs_related_stop,
        vehicle_number
        )
        values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(row)
        )
    conn.commit()
    conn.close()

upload = st.sidebar.button("Click here to uplod logs to secure database!")
if upload:
    df_into_db()
    st.success("successfully uploaded into database")

with st.sidebar.form("Manual log"):
    st.subheader("Add a new entry")

    stop_date = st.date_input("Enter stop date")
    hour = st.selectbox("Hour", list(range(0, 24)))
    minute = st.selectbox("Minute", list(range(0, 60)))
    stop_time = dt.time(hour, minute)
    country_name = st.text_input("Enter country name")
    driver_gender = st.selectbox("Enter gender", ["M", "F"])
    driver_age = st.number_input("Enter driver age", min_value= 18, max_value= 120)
    driver_race = st.text_input("Enter driver race")
    violation_raw = st.text_input("Enter violation raw")
    violation = st.text_input("Enter reason of violation")
    search_conducted = st.selectbox("Whether search conducted", ["Yes", "No"])
    search_type = st.text_input("Enter search type")
    stop_outcome = st.text_input("What is the outcome of the search")
    is_arrested = st.selectbox("Is the person arrested", ["Yes", "No"])
    stop_duration = st.text_input("Enter stop duration")
    drugs_related_stop = st.selectbox("Is it related to drug", ["Yes", "No"])
    vehicle_number = st.text_input("Enter vehicle number")

    submit = st.form_submit_button("Click here to add the entry!")

if submit:
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO logs(
    stop_date, stop_time, country_name, driver_gender, driver_age,
    driver_race, violation_raw, violation, search_conducted,
    search_type, stop_outcome, is_arrested, stop_duration,
    drugs_related_stop, vehicle_number) 
    VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, 
    (
    stop_date, stop_time, country_name, driver_gender, driver_age,
    driver_race, violation_raw, violation,
    search_conducted == "Yes", search_type, stop_outcome,
    is_arrested == "Yes", stop_duration,
    drugs_related_stop == "Yes", vehicle_number
    ))
    conn.commit()
    conn.close()
    st.success("✅ New entry added successfully!")

def updated_log():
    conn = db_connect()
    df = pd.read_sql("select * from logs", conn)
    conn.close()
    return df

updated_file_df = updated_log()
st.dataframe(updated_file_df)

if submit:
    st.success("Updated one")
    updated_file_df = updated_log()
    st.dataframe(updated_file_df)

with st.form("Person Crime Check"):
    st.subheader("Crime Analysis")

    stop_date = st.date_input("Enter stop date")
    hour = st.selectbox("Hour", list(range(0, 24)))
    minute = st.selectbox("Minute", list(range(0, 60)))
    stop_time = dt.time(hour, minute)
    country_name = st.selectbox("Enter country name", updated_file_df["country_name"].unique())
    driver_gender = st.selectbox("Enter gender", ["M", "F"])
    driver_age = st.number_input("Enter driver age", min_value= 18, max_value= 120)
    driver_race = st.selectbox("Enter driver race", updated_file_df["driver_race"].unique())
    violation_raw = st.selectbox("Enter violation raw", updated_file_df["violation_raw"].unique())
    violation = st.selectbox("Enter reason of violation", updated_file_df["violation"].unique())
    search_conducted = st.selectbox("Whether search conducted", ["Yes", "No"])
    search_type = st.selectbox("Enter search type", updated_file_df["search_type"].unique())
    stop_outcome = st.selectbox("What is the outcome of the search", updated_file_df["stop_outcome"].unique())
    is_arrested = st.selectbox("Is the person arrested", ["Yes", "No"])
    stop_duration = st.selectbox("Enter stop duration", updated_file_df["stop_duration"].unique())
    drugs_related_stop = st.selectbox("Is it related to drug", ["Yes", "No"])
    vehicle_number = st.text_input("Enter vehicle number")
    submit_check = st.form_submit_button("Check this entry")

if submit_check:
    gender = "male" if driver_gender == "M" else "female"
    search = "No search was conducted" if search_conducted == "No" else f"A search was conducted ({search_type})"
    arrest = "and was arrested" if is_arrested == "Yes" else "and was not arrested"
    drug = "and was drug-related" if drugs_related_stop == "Yes" else "and was not drug-related"

    summary = (
        f"A {driver_age}-year-old {gender} driver was stopped for {violation} at {stop_time.strftime('%I:%M %p')}. "
        f"{search}, and outcome is {stop_outcome.lower()}. The stop lasted {stop_duration} {drug}."
    )

    st.markdown("### 📝 Summary of Entry")
    st.info(summary)

queries = {
    "Top 10 Vehicles in Drug-Related Stops": """
        SELECT vehicle_number, COUNT(*) AS drug_stop_count
        FROM logs
        WHERE drugs_related_stop = TRUE
        GROUP BY vehicle_number
        ORDER BY drug_stop_count DESC
        LIMIT 10;
    """,
    "Most Frequently Searched Vehicles": """
        SELECT vehicle_number, COUNT(*) AS search_count
        FROM logs
        WHERE search_conducted = TRUE
        GROUP BY vehicle_number
        ORDER BY search_count DESC
        LIMIT 10;
    """,
    "Driver age group with highest arrest rate": """
        SELECT driver_age, sum(is_arrested) as total_arrests
        from logs
        GROUP BY driver_age
        order by total_arrests desc
        limit 10;
          
    """,
    "Gender distribution of drivers stopped in each country": """
        SELECT country_name, driver_gender, COUNT(*) AS stop_count
        FROM logs
        GROUP BY country_name, driver_gender
        ORDER BY country_name, stop_count DESC;
    """,
    "Gender and Race with highest search rate": """
        SELECT driver_race, driver_gender, COUNT(*) AS search_count
        FROM logs
        GROUP BY driver_race, driver_gender
        ORDER BY search_count DESC
        LIMIT 10;
    """,
    "Time of day which sees the most traffic stops": """
        select stop_time, count(*) daytime_with_most_arrest
        from logs
        group by stop_time
        order by daytime_with_most_arrest desc
        limit 10;
     """,
     "Day/night period arrest rate": """
        select case
        when hour(stop_time) between 6 and 17 then "DAY_Time"
        else "NIGHT_Time"
        end as time_period, round(sum(is_arrested)/count(*) *100, 2) as arrest_rate
        from logs
        group by time_period
        order by arrest_rate desc;
        """,
    "Average stop time of violations": """
        select violation, round(avg(stop_time), 2)
        from logs
        group by violation
        limit 10;
    """,
    "Which violations are most associated with searches or arrests?" : """
       SELECT violation,
       COUNT(*) AS total_stops,
       SUM(search_conducted) AS total_searches,
       SUM(is_arrested) AS total_arrests,
       ROUND(SUM(search_conducted)/COUNT(*) * 100, 2) AS search_rate,
       ROUND(SUM(is_arrested)/COUNT(*) * 100, 2) AS arrest_rate
       FROM logs
       GROUP BY violation
       ORDER BY total_arrests DESC, total_searches DESC;
     """,
     "Which violations are most common among younger drivers (<25)": """
       SELECT violation, COUNT(*) AS stop_count_age_less_then_25
       FROM logs
       WHERE driver_age < 25
       GROUP BY violation
       ORDER BY stop_count_age_less_then_25 DESC;
     """, 
     "Is there a violation that rarely results in search or arrest?" : """
       SELECT violation,
       COUNT(*) AS total_stops,
       SUM(search_conducted) AS searches,
       SUM(is_arrested) AS arrests,
       ROUND(SUM(search_conducted)/COUNT(*) * 100, 2) AS search_rate,
       ROUND(SUM(is_arrested)/COUNT(*) * 100, 2) AS arrest_rate
       FROM logs
       GROUP BY violation
       ORDER BY total_stops desc;
    """,
    "Which countries report the highest rate of drug-related stops?" : """
       SELECT country_name, count(*) drug_related_stop
       from logs
       where drugs_related_stop = true
       group by country_name
       order by drug_related_stop desc
       limit 10;
     """,
     "What is the arrest rate by country and violation?": """
       SELECT country_name, violation,
       SUM(is_arrested) AS arrests,
       ROUND(SUM(is_arrested)/COUNT(*) * 100, 2) AS arrest_rate
       FROM logs
       GROUP BY country_name, violation
       ORDER BY arrest_rate DESC;
     """,
     "Which country has the most stops with search conducted?" : """
       SELECT country_name,
       count(*) most_stops,
       SUM(search_conducted) AS search_conducted
       FROM logs
       GROUP BY country_name
       ORDER BY search_conducted DESC;
     """,
     "Yearly Breakdown of Stops and Arrests by Country" : """
       SELECT country_name, YEAR(stop_date) AS year,
       COUNT(*) AS total_stops,
       SUM(is_arrested) AS total_arrests
       FROM logs
       GROUP BY country_name, year
       ORDER BY country_name, year;
     """,
     "Driver Violation Trends Based on Age and Race" : """
       SELECT driver_race, driver_age, violation, COUNT(*) AS stop_count
       FROM logs
       GROUP BY driver_race, driver_age, violation
       ORDER BY stop_count DESC;
     """,
     "Time Period Analysis of number of Stops by Year, Month, Hour of the Day" : """
       SELECT 
       YEAR(stop_date) AS year,
       MONTH(stop_date) AS month,
       HOUR(stop_time) AS hour,
       COUNT(*) AS stop_count
       FROM logs
       GROUP BY year, month, hour
       ORDER BY year, month, hour;
     """,
     "Violations with High Search and Arrest Rates" : """
       SELECT violation,
       COUNT(*) AS total_stops,
       SUM(search_conducted) AS searches,
       SUM(is_arrested) AS arrests,
       ROUND(SUM(search_conducted)/COUNT(*) * 100, 2) AS search_rate,
       ROUND(SUM(is_arrested)/COUNT(*) * 100, 2) AS arrest_rate
       FROM logs
       GROUP BY violation
       ORDER BY search_rate DESC, arrest_rate DESC
       LIMIT 10;
     """,
     "Driver Demographics by Country" : """
       SELECT country_name, driver_gender, driver_race,
       AVG(driver_age) AS avg_age,
       COUNT(*) AS total_drivers
       FROM logs
       GROUP BY country_name, driver_gender, driver_race
       ORDER BY total_drivers DESC;
     """,
     "Top 5 Violations with Highest Arrest Rates" : """
       SELECT violation,
       ROUND(SUM(is_arrested)/COUNT(*) * 100, 2) AS arrest_rate
       FROM logs
       GROUP BY violation
       ORDER BY arrest_rate DESC
       LIMIT 5;
     """
}

st.subheader("Advanced Analytics Dashboard")
select_question = st.selectbox("Choose a question to view:", list(queries.keys()))

if select_question:
    conn = db_connect()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(queries[select_question])
    data = cursor.fetchall()
    df = pd.DataFrame(data)
    st.subheader(f"🕵 {select_question}")
    st.dataframe(df)
    cursor.close()
    conn.close()
