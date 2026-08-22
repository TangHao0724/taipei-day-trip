from typing import Annotated

from fastapi import *
from fastapi.responses import FileResponse , JSONResponse
from fastapi.staticfiles import StaticFiles

import mysql.connector
import json
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

app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")

@app.get("/api/attractions", response_class=JSONResponse, tags=["Attraction"])
async def get_attractions_list(request: Request,page:int ,category:Annotated[str | None, Query()] = None,keyword:Annotated[str | None, Query()] = None,):
	# 取得不同分頁的旅遊景點列表資料，也可以根據標題關鍵字、或捷運站名稱篩選

	connect = cnxpool.get_connection()
	try:
		with connect.cursor() as cursor:
			# 主要景點查詢
			select = "SELECT a.id,a.name,c.name AS category,a.description,a.address,a.transport,m.name AS mrt,longitude,latitude FROM attractions a " \
				"JOIN categories c ON a.category_id = c.id LEFT JOIN mrts m ON a.mrt_id = m.id " 
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
				return JSONResponse(
					{
						"nextPage": None,
						"data": []
					},
					status_code=status.HTTP_200_OK
				)

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
			datas = []
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
				datas.append(a)
			print(len(datas))
	except Exception as e:
		print(f"db error: {e}")
		return JSONResponse({"error":True,"message":"查詢錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()

	return JSONResponse({"nextpage":nextpage,"data":datas},status_code=status.HTTP_200_OK) 

@app.get("/api/attractions/{attractionId}", response_class=JSONResponse, tags=["Attraction"])
async def get_attractions(request: Request,attractionId:int):
	connect = cnxpool.get_connection()
	try:
		with connect.cursor() as cursor:
			select = "SELECT a.id,a.name,c.name AS category,a.description,a.address,a.transport,m.name AS mrt,longitude,latitude FROM attractions a " \
					"JOIN categories c ON a.category_id = c.id LEFT JOIN mrts m ON a.mrt_id = m.id WHERE a.id = %s " 
			cursor.execute(select,(attractionId,))
			ans = cursor.fetchone()
			cursor.execute("SELECT img_url FROM att_img_urls WHERE attraction_id = %s",(attractionId,))
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
	except Exception as e:
			print(f"db error: {e}")
			return JSONResponse({"error":True,"message":"查詢錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()	
	return JSONResponse({"data": return_json},status_code=status.HTTP_200_OK)

@app.get("/api/categories", response_class=JSONResponse, tags=["Attraction Category"])
async def get_categories(request: Request):
	connect = cnxpool.get_connection()
	try :
		with connect.cursor() as cursor:
			cursor.execute("SELECT name FROM categories")
			cats = [cat for (cat,) in cursor.fetchall()]
	except Exception as e:
		print(f"db error: {e}")
		return JSONResponse({"error":True,"message":"查詢錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()	
	return JSONResponse({"data": cats},status_code=status.HTTP_200_OK)
@app.get("/api/mrts", response_class=JSONResponse, tags=["MRT Station"])
async def get_mrts(request: Request):
	connect = cnxpool.get_connection()
	try :
		with connect.cursor() as cursor:
			select = "SELECT m.name AS mrt,COUNT(*) AS times FROM attractions a  LEFT JOIN mrts m ON a.mrt_id = m.id GROUP BY m.name ORDER BY times DESC" 
			cursor.execute(select)
			data= cursor.fetchall()
			mrts = [name for name, _ in data if name is not None]
			print(mrts)
	except Exception as e:
		print(f"db error: {e}")
		return JSONResponse({"error":True,"message":"查詢錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()	
	return JSONResponse({"data": mrts},status_code=status.HTTP_200_OK)