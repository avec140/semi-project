from elasticsearch import Elasticsearch, helpers
import mysql.connector
import urllib3
from datetime import datetime
import pycountry
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import re
import traceback

# 🔧 SSL 경고 무시
urllib3.disable_warnings()

# ✅ Elasticsearch 설정
es = Elasticsearch(
    hosts=["http://localhost:9200"],
    basic_auth=("elastic", "1234"),
    verify_certs=False
)

posts_index = "darkweb_posts_with_geo"
emails_index = "darkweb_email_domains"

# ✅ 인덱스 삭제 함수
def delete_index(index_name):
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"🗑️ 인덱스 '{index_name}' 삭제 완료")
    else:
        print(f"ℹ️ 인덱스 '{index_name}' 없음")

delete_index(posts_index)
delete_index(emails_index)

# ✅ 인덱스 생성
es.indices.create(index=posts_index, body={
    "mappings": {
        "properties": {
            "title": {"type": "text"},
            "author": {"type": "keyword"},
            "post_date": {"type": "date"},
            "keywords": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
            },
            "raw_body": {"type": "text"},
            "created_at": {"type": "date"},
            "country": {"type": "keyword"},
            "location": {"type": "geo_point"}
        }
    }
})
print(f"📁 인덱스 '{posts_index}' 생성 완료")

es.indices.create(index=emails_index, body={
    "mappings": {
        "properties": {
            "email": {"type": "keyword"},
            "domain": {"type": "keyword"}
        }
    }
})
print(f"📁 인덱스 '{emails_index}' 생성 완료")

# ✅ MariaDB 연결
config = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "bcw",
    "port": 3306
}

try:
    conn = mysql.connector.connect(**config)
    cur = conn.cursor(dictionary=True)
    print("✅ MariaDB 연결 성공")
except Exception as e:
    print("❌ MariaDB 연결 실패:", e)
    exit(1)

# ✅ 도움메 함수들
def parse_datetime_field(dt):
    if isinstance(dt, datetime):
        return dt.isoformat()
    try:
        return datetime.strptime(dt, "%a %b %d, %Y %I:%M %p").isoformat()
    except:
        return None

country_names = set(c.name for c in pycountry.countries)
geolocator = Nominatim(user_agent="geo-extractor")
coordinates_cache = {}

def extract_country(text):
    if not text:
        return None
    for country in country_names:
        if re.search(rf"\\b{re.escape(country)}\\b", text, re.IGNORECASE):
            return country
    return None

def get_coordinates(country):
    if country in coordinates_cache:
        return coordinates_cache[country]
    try:
        location = geolocator.geocode(country, language="en", timeout=10)
        if location:
            coordinates_cache[country] = {"lat": location.latitude, "lon": location.longitude}
            return coordinates_cache[country]
    except GeocoderTimedOut:
        return None
    except Exception:
        return None
    return None

def extract_domain(email):
    if email and isinstance(email, str):
        match = re.search(r"@([\w.-]+)$", email)
        return match.group(1).lower() if match else None
    return None

# ✅ 게시곸 생성
posts_actions = []
try:
    cur.execute("SELECT * FROM parsed_posts")
    for row in cur.fetchall():
        created_at = parse_datetime_field(row.get("created_at"))
        post_date = parse_datetime_field(row.get("post_date"))
        raw_body = row.get("raw_body") or ""
        country = extract_country(raw_body)
        location = get_coordinates(country) if country else None

        doc = {
            "title": row.get("title", ""),
            "author": row.get("author", ""),
            "post_date": post_date,
            "keywords": row.get("keywords", ""),
            "raw_body": raw_body,
            "created_at": created_at,
            "country": country or "",
            "location": location
        }

        posts_actions.append({
            "_index": posts_index,
            "_id": row["id"],
            "_source": doc
        })
    helpers.bulk(es, posts_actions)
    print(f"✅ 게시물 {len(posts_actions)}개 생성 완료")
except Exception as e:
    print("❌ 게시물 생성 오류:", e)
    traceback.print_exc()

# ✅ 이메일 생성
emails_actions = []
try:
    cur.execute("SELECT email FROM parsed_emails WHERE email IS NOT NULL AND email != ''")
    for row in cur.fetchall():
        email = row.get("email")
        domain = extract_domain(email)
        if domain:
            emails_actions.append({
                "_index": emails_index,
                "_id": email.lower(),
                "_source": {"email": email.lower(), "domain": domain}
            })
    helpers.bulk(es, emails_actions)
    print(f"✅ 이메일 {len(emails_actions)}개 생성 완료")
except Exception as e:
    print("❌ 이메일 생성 오류:", e)
    traceback.print_exc()

cur.close()
conn.close()