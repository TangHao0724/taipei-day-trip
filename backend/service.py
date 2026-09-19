from datetime import date

from backend.error import AttractionNotFoundError, DatabaseError, WrongTimeError
from backend.schema import Mcp_data, User_data, Signin_data, Booking_data,Full_order
import mysql.connector
import mysql.connector.cursor
import hashlib
import secrets
import os
from dotenv import load_dotenv

load_dotenv()
config = {
    "host":os.getenv("DB_HOST"),
    "user":os.getenv("DB_USER"),
    "password":os.getenv("DB_PASSWORD"),
    "database":os.getenv("DB_DATABASE"),
}

cnxpool = mysql.connector.pooling.MySQLConnectionPool(pool_name = "tdt",
	pool_size = 6,
	**config)

async def search_attraction(id:int) -> dict :
    connect = cnxpool.get_connection()
    try:
        with connect.cursor() as cursor:
            select = "SELECT a.id,a.name,c.name AS category,a.description,a.address,a.transport,m.name AS mrt,longitude,latitude FROM attractions a " \
                    "JOIN categories c ON a.category_id = c.id LEFT JOIN mrts m ON a.mrt_id = m.id WHERE a.id = %s " 
            cursor.execute(select,(id,))
            ans = cursor.fetchone()
            if ans is None:
                 raise AttractionNotFoundError()
            cursor.execute("SELECT img_url FROM att_img_urls WHERE attraction_id = %s",(id,))
            images =  cursor.fetchall()
            return_json = {
                    "id" : ans[0],
                    "name" : ans[1],
                    "category":ans[2],
                    "description":ans[3],
                    "address":ans[4],
                    "transport":ans[5],
                    "mrt":ans[6],
                    "lat":float(ans[8]),
                    "lng":float(ans[7]),
                    "images" : [url for (url,) in images]
            }
            return return_json
    except Exception as e:
            print(f"db error: {e}")
            raise DatabaseError()
    finally:
        connect.close()	

async def get_att_list(page:int,category:str|None, keyword:str|None)-> dict:
    connect = cnxpool.get_connection()
    try:
        with connect.cursor() as cursor:
            # 主要景點查詢
            select = """
            SELECT 
            a.id,
            a.name,
            c.name AS category,
            a.description,
            a.address,
            a.transport,
            m.name AS mrt,
            longitude,
            latitude 
            FROM attractions AS a 
            JOIN categories AS c ON a.category_id = c.id 
            LEFT JOIN mrts AS m ON a.mrt_id = m.id 
            """ 
            # 條件添加
            cond = []
            params = []
            if category :	
                cat = "c.name = %s"
                cond.append(cat)
                params.append(category)
            if keyword :
                mrt = "( a.name LIKE %s OR m.name = %s)"
                cond.append(mrt)
                params.extend([f"%{keyword}%", keyword])
            if cond:	
                select += " WHERE " + " AND ".join(cond)
            # 範圍查詢 
            PAGE_SIZE = 8
            limit = PAGE_SIZE+1
            offset = page * PAGE_SIZE
            select += " ORDER BY a.id LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            cursor.execute(select,params)
            print(select)
            print(params)
            ans = cursor.fetchall()

            # 如果無資料提前跳開api
            if not ans:
                return {"nextPage": None,"data": []}
            
            # nextpage 推算 用>8下去查，如果9代表後續有資料
            if len(ans) > 8:
                nextpage = page+1
            else:
                nextpage = None
            
            # 查詢獲得資料的圖片
            attraction_ids = [row[0] for row in ans[:8]]
            if attraction_ids:
                print( attraction_ids)
                holder = ','.join(["%s"] * len(attraction_ids)) 
                img_query = f"SELECT attraction_id,img_url FROM att_img_urls WHERE attraction_id IN ({holder}) "
                print("img_query : "+ img_query)
                cursor.execute(img_query,attraction_ids)
                img_rows = cursor.fetchall()
            else:
                img_rows =[]
            images = {}
            for attraction_id, img_url in img_rows:

                if attraction_id not in images:
                    images[attraction_id] = []

                images[attraction_id].append(img_url)
            # 組裝
            data = []
            for i in ans[:8]:
                a = {
                    "id" : i[0],
                    "name" : i[1],
                    "category":i[2],
                    "description":i[3],
                    "address":i[4],
                    "transport":i[5],
                    "mrt":i[6],
                    "lat":float(i[8]),
                    "lng":float(i[7]),
                    "images" : images.get(i[0], [])
                }
                data.append(a)
            return {"nextpage":nextpage,"data":data}
    except Exception as e:
        print(f"db error: {e}")
        raise DatabaseError()
    finally:
        connect.close()

async def add_booking(data:Booking_data ,user_id:int) -> bool:
     
	if data.date < date.today():
		raise WrongTimeError()
	connect = cnxpool.get_connection()
	try:
		with connect.cursor() as cur:
			cur.execute(
				"SELECT id FROM attractions WHERE id = %s",
				(data.attractionId,)
			)

			if cur.fetchone() is None:
				raise AttractionNotFoundError()
			
			dele_sql ="""
				DELETE FROM orders
				WHERE orders.user_id = %s AND orders.paid = FALSE 
			"""
			cur.execute(dele_sql,(user_id,))
			sql ="""
                INSERT INTO orders (user_id, attraction_id, order_at, time_slot, price)
                VALUES (%s, %s, %s, %s, %s)
            """
			cur.execute(
				sql,
				(user_id, data.attractionId, data.date, data.time.value, data.price)
			)
		connect.commit()
		return True
            
	except Exception as e:
		connect.rollback()
		print(f"db error: {e}")
		return DatabaseError()
	finally:
		connect.close()

def new_mcptoken(id:int) -> Mcp_data:
    # 無條件建立一個新的TOKEN 
    # UPDATE欄位
    connect = cnxpool.get_connection()
    token = secrets.token_urlsafe(32)
    try:
        with connect.cursor() as cur:
            cur.execute("UPDATE users SET mcp_token = %s WHERE id = %s",(token,id))
            connect.commit()
            if cur.rowcount != 1:
                raise DatabaseError()
    except Exception as e:
            connect.rollback()
            print(f"{e}")
            raise DatabaseError()
    finally:
         connect.close()
    return Mcp_data(id=id,token=token)

def ser_mcptoken(id:int) -> Mcp_data :
    connect = cnxpool.get_connection()
    try:
        with connect.cursor() as cur:
            cur.execute("SELECT mcp_token FROM users WHERE id = %s",(id,))
            result = cur.fetchone()
            if result is None:
                raise DatabaseError()
    except Exception as e:
                print(f"{e}")
                raise DatabaseError()
    finally:
            connect.close()

    if result[0] is None:
        return Mcp_data(id=id,token=None)

    return Mcp_data(id=id,token=result[0])

async def auth_token(token:str) -> int | None:
    connect = cnxpool.get_connection()
    try:
        with connect.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE mcp_token = %s",(token,))
            result = cur.fetchone()
    except Exception as e:
        print(f"{e}")
        raise DatabaseError()
    finally:
        connect.close()
    if result is None:
        return None
    return result[0]