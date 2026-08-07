import mysql.connector
import json
import os
from dotenv import load_dotenv
from pathlib import Path

current_path =Path(__file__).resolve().parent
env_path = current_path / '.env'

load_dotenv(dotenv_path=env_path)

config = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_DATABASE")
)

with open("data/taipei-attractions.json",encoding="utf-8") as f:
    data = f.read()
    jd = json.loads(data)
    img_base = "https://padax.github.io/taipei-day-trip-resources"
    # 先把景點的寫入，再額外寫兩個mrt與cat的分類
    with config.cursor() as cursor:
        for  i in jd["list"]:
            cursor.execute("INSERT IGNORE categories(name) VALUES (%s)",(i["CAT"],))
            cursor.execute("SELECT id FROM categories WHERE name = %s",(i["CAT"],))
            cat_id = cursor.fetchone()[0]

            if i["MRT"] is None:
                mrt_id = None
            else :
                cursor.execute("INSERT IGNORE mrts(name) VALUES (%s)",(i["MRT"],))
                cursor.execute("SELECT id FROM mrts WHERE name = %s",(i["MRT"],))
                mrt_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT attractions (name,category_id,description,address,transport,mrt_id,longitude,latitude,price) " \
                "VALUES  (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(
                    i["name"],
                    cat_id,
                    i["description"],
                    i["address"],
                    i["direction"],
                    mrt_id,
                    i["longitude"],
                    i["latitude"],
                    2000 #暫時都用2000計價
                ))
            att_id = cursor.lastrowid
            titles = i["imgurls"].split("/imgs")

            for j in filter(None, titles):
                url = img_base +'/imgs'+j
                cursor.execute(
                    "INSERT IGNORE att_img_urls(attraction_id,img_url) VALUES(%s,%s) ",(
                        att_id,
                        url
                    )
                )

        config.commit()
    
        
