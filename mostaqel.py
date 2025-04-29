import sqlite3
import requests
import pandas as pd
from M_db import save_jobs_to_db
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import random
import time
from urllib.parse import quote
import pytz
# from transformers import pipeline
import sys
sys.stdout.reconfigure(encoding='utf-8')



session = requests.Session()

def set_new_proxy():
    port = 9150 
    credentials = f"{random.randint(10000, 99999)}:pass"
    proxy_url = f"socks5h://{credentials}@127.0.0.1:{port}"
    session.proxies = {'http': proxy_url,
                       'https': proxy_url}
    
def check_tor_ip():
    response = session.get("http://httpbin.org/ip", timeout=10)
    print("Tor IP:", response.text)
check_tor_ip()

def generate_url(keyword):
    encoded_keyword = quote(keyword)
    url = f"https://mostaql.com/projects?keyword={encoded_keyword}&budget_max=1000&sort=latest"
    return url

def get_job_data(url, max_retries=5):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'X-Requested-With': 'XMLHttpRequest'}
    for attempt in range(max_retries):
        try:
            set_new_proxy()
            check_tor_ip()
            response = session.get(url, headers=headers, timeout=15)
            data = response.json()
            time.sleep(random.uniform(3, 6))
            return data['collection']
        except Exception as e:
            print(f"محاولة {attempt+1} فشلت: {e}")
            time.sleep(5)
    return []

def parse_job_details(project):
    html = project['rendered']
    soup = BeautifulSoup(html, 'html.parser')

    project_id = project['id']

    title_tag = soup.find('a')
    title = title_tag.text.strip() if title_tag else 'غير متوفر'
    
    description_tag = soup.find('p')
    description = description_tag.text.strip() if description_tag else 'غير متوفر'
    
    date_tag = soup.find('time')
    if date_tag and 'datetime' in date_tag.attrs:
        utc_time_str = date_tag['datetime']
        utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
        utc_time = utc_time.replace(tzinfo=pytz.utc)
        local_time = utc_time.astimezone(pytz.timezone('Africa/Cairo'))
        date = local_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        date = 'غير متوفر'

    link = title_tag['href'] if title_tag else '#'
    
    return {
        'id': project_id,
        'title': title,
        'description': description,
        'date': date,
        'link': link
    }
    
def extract_additional_details(project_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = session.get(project_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        budget_tag = soup.find('span', dir='rtl')
        budget = budget_tag.text.strip() if budget_tag else 'غير متوفر'

        skills_list = []
        skills_section = soup.find('ul', class_='skills')
        if skills_section:
            for li in skills_section.find_all('li'):
                skill = li.get_text(strip=True)
                skills_list.append(skill)

        return {
            'budget': budget,
            'skills': ', '.join(skills_list)
        }

    except Exception as e:
        print(f"فشل في جلب التفاصيل من {project_url}: {e}")
        return {
            'budget': 'غير متوفر',
            'skills': 'غير متوفر'
        }
        
def scrape_jobs(keyword):
    url = generate_url(keyword)
    projects = get_job_data(url)

    if projects:
        job_list = []
        for project in projects:
            job_details = parse_job_details(project)
            extra_details = extract_additional_details(job_details['link'])
            job_details.update(extra_details)
            job_list.append(job_details)
        
        df = pd.DataFrame(job_list)
        # print(df.head())
        save_jobs_to_db(df)
        return df
    
import sqlite3

conn = sqlite3.connect("MostaqelJobs.db")
query = "SELECT description FROM jobs"

db_data = pd.read_sql_query(query, conn)

# for line in range( len(db_data)) :
    # print(f' line number {line}   has length : { len(db_data['description'][line]) } ')

con=sqlite3.connect('MostaqelJobs.db')
cursor=con.cursor()
def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return column_name in [row[1] for row in cursor.fetchall()]

if not column_exists(cursor, "jobs", "summary"):
    cursor.execute('ALTER TABLE jobs ADD COLUMN summary TEXT')

conn.commit()


conn = sqlite3.connect('MostaqelJobs.db')
cursor = conn.cursor()


cursor.execute("SELECT rowid, description, summary FROM jobs LIMIT 5")
rows = cursor.fetchall()


# for row in rows:
    # print(f'Row ID: {row[0]} \n , Description: {row[1]} , \n Summary: {row[2]} \n ')

conn.close()

# summarizer = pipeline('summarization', model="google/pegasus-xsum", framework="pt")

# summaries = []


# for line in db_data["description"].tolist():
#     i=0
#     if len(line) > 512:
#         line = line[:512]  

    
#     try:
#         summary = summarizer(line, max_length=60, min_length=10, do_sample=False)
#         summaries.append(summary[0]['summary_text'])
#         print(f' t {i}')
#         print(summaries)
#         i=i+1
#     except Exception as e:
#         summaries.append("")  
#         print(f' e {i}')
#         print(summaries)
#         i=i+1
        

# conn = sqlite3.connect('MostaqelJobs.db')
# cursor = conn.cursor()

# for i, summary in enumerate(summaries):
#     cursor.execute('''
#         UPDATE jobs
#         SET summary = ?
#         WHERE rowid = ?''', (summary, i + 1))  


# conn.commit()

