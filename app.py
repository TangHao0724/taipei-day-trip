from typing import Annotated
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from fastapi import *
from fastapi.responses import FileResponse , JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer

import mysql.connector
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone,date
from pwdlib import PasswordHash

from backend.mcp import mcp
from backend.error import AttractionNotFoundError, DatabaseError
from backend.schema import User_data, Signin_data, Booking_data,Full_order
from backend.service import add_booking, new_mcptoken, search_attraction,get_att_list, ser_mcptoken
import requests

load_dotenv()
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/auth")

config = {
    "host":os.getenv("DB_HOST"),
    "user":os.getenv("DB_USER"),
    "password":os.getenv("DB_PASSWORD"),
    "database":os.getenv("DB_DATABASE"),
}
cnxpool = mysql.connector.pooling.MySQLConnectionPool(pool_name = "tdt",
	pool_size = 6,
	**config)

mcp_app = mcp.http_app(path="/")
app=FastAPI(lifespan=mcp_app.lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/mcp", mcp_app)

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
@app.get("/member", include_in_schema=False)
async def member(request: Request):
	return FileResponse("./static/member.html", media_type="text/html")

@app.get("/api/attractions", response_class=JSONResponse, tags=["Attraction"])
async def get_attractions_list(request: Request,page:int ,category:Annotated[str | None, Query()] = None,keyword:Annotated[str | None, Query()] = None,):
	# 取得不同分頁的旅遊景點列表資料，也可以根據標題關鍵字、或捷運站名稱篩選
	result = await get_att_list(page,category,keyword)

	return JSONResponse(result,status_code=status.HTTP_200_OK) 

@app.get("/api/attractions/{attractionId}", response_class=JSONResponse, tags=["Attraction"])
async def get_attraction(request: Request,attractionId:int):
	result = await search_attraction(attractionId)
	return JSONResponse({"data": result},status_code=status.HTTP_200_OK)

@app.get("/api/categories", response_class=JSONResponse, tags=["Attraction Category"])
async def get_categories(request: Request):
	connect = cnxpool.get_connection()
	try :
		with connect.cursor() as cursor:
			cursor.execute("SELECT name FROM categories")
			cats = [cat for (cat,) in cursor.fetchall()]
	except Exception as e:
		print(f"db error: {e}")
		return JSONResponse({"error":True,"message":"查詢時發生錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
		return JSONResponse({"error":True,"message":"查詢時發生錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()	
	return JSONResponse({"data": mrts},status_code=status.HTTP_200_OK)

# 會員系統
key = os.getenv("JWT_SECRET_KEY")
jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
if not key:
	raise RuntimeError("JWT_SECRET_KEY 尚未設定")
@app.post("/api/user",response_class=JSONResponse,tags=["User"])
async def register_user(request:Request,register_data:User_data):
	data = register_data
	if data.id is not None or data.name is None :
		return JSONResponse({"error":True,"message":"錯誤的資料格式"},status_code=status.HTTP_400_BAD_REQUEST)
	
	connect = cnxpool.get_connection()
	hash_pw = password_hash.hash(data.password)
	try:
		with connect.cursor() as cursor:
	
			query = "INSERT INTO users (name , email , password) Values (%s,%s,%s)"
			cursor.execute(query,(data.name,data.email,hash_pw,))

			connect.commit()
		return JSONResponse({"ok":True},status_code=status.HTTP_201_CREATED)
	except mysql.connector.IntegrityError:
			connect.rollback()
			return JSONResponse(
				{"error": True, "message": "註冊失敗，Email 或名稱已存在"},
				status_code=status.HTTP_400_BAD_REQUEST,
			)
	except Exception as e:
		print(f"db error: {e}")
		return JSONResponse({"error":True,"message":"查詢時發生錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()

@app.put("/api/user/auth",response_class=JSONResponse,tags=["User"])
async def sign_in(sign_data:Signin_data):
	connect = cnxpool.get_connection()

	try:
		with connect.cursor() as cur:
			cur.execute("SELECT id, name, email, password FROM users WHERE email = %s ",(sign_data.email,))
			result = cur.fetchone()

			# 比對帳號與密碼
			if result is None or not password_hash.verify(
				sign_data.password,
				result[3]
			):
				return JSONResponse(
					{"error": True, "message": "Email 或 密碼錯誤"},
					status_code=status.HTTP_400_BAD_REQUEST,
				)
			expire_at = datetime.now(timezone.utc) + timedelta(days=7)
			# 經過加密處里JWT
			encoded_jwt  = jwt.encode({"id":result[0],"name":result[1],"email":result[2],"exp":expire_at},key,algorithm=jwt_algorithm)


			return JSONResponse({"token":encoded_jwt},status_code=status.HTTP_200_OK)
	except Exception as e:
			print(f"db error: {e}")
			return JSONResponse({"error":True,"message":"查詢時發生錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
	# 傳入bearer token 解密後確認資料
	try :
		payload = jwt.decode(token,key,algorithms=[jwt_algorithm])
		print(payload)
		payload.pop("exp", None)
		return payload
	except ExpiredSignatureError:
		raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已過期，請重新登入",
            headers={"WWW-Authenticate": "Bearer"},
        )
	except InvalidTokenError:
		raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
	
@app.get("/api/user/auth",tags=["User"])
async def get_user(user: dict = Depends(get_current_user)):
	print("user",user)
	return JSONResponse(
		content={"data": user},
		status_code=status.HTTP_200_OK,
	)

# 訂單系統
@app.get("/api/booking",response_class=JSONResponse,tags=["Booking"])
async def get_booking(user:dict = Depends(get_current_user)):
	print(user)
	connect = cnxpool.get_connection()
	try:
		with connect.cursor() as cur:
			sql = """SELECT 
				att.id, 
				att.name, 
				att.address, 
				img.img_url, 
				orders.order_at, 
				orders.time_slot, 
				orders.price
			FROM orders  
			JOIN attractions AS att ON orders.attraction_id = att.id 
			LEFT JOIN att_img_urls AS img ON orders.attraction_id = img.attraction_id
			WHERE orders.user_id = %s AND orders.paid = FALSE
			ORDER BY img.id ASC LIMIT 1"""

			cur.execute(sql,(user["id"],))
			order_data = cur.fetchone()
			if order_data is None:
				return JSONResponse({"data":None},status_code=status.HTTP_200_OK)
			response = {
					"attraction":{
						"id": order_data[0],
						"name": order_data[1],
						"address":order_data[2],
						"image":order_data[3],
					},
					"date":order_data[4].isoformat() if order_data[4] else None,
					"time":order_data[5],
					"price":order_data[6],
				}
			return JSONResponse({"data":response},status_code=status.HTTP_200_OK)
	except Exception as e:
		print(f"db error: {e}")
		return JSONResponse({"error":True,"message":"查詢時發生錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()		

@app.post("/api/booking",response_class=JSONResponse,tags=["Booking"])
async def new_booking(data:Booking_data,user=Depends(get_current_user)):
	print("now_user",user)
	result = await add_booking(data,user["id"])
	if not result:
		return JSONResponse({"error":True,"message":"建立發生錯誤"},status_code=status.HTTP_201_CREATED)
	JSONResponse({"ok":True},status_code=status.HTTP_201_CREATED)


@app.delete("/api/booking",response_class=JSONResponse,tags=["Booking"])
async def dele_booking(user=Depends(get_current_user)):
	connect =cnxpool.get_connection()
	try:
		with connect.cursor() as cur:
			sql ="""
				DELETE FROM orders
				WHERE orders.user_id = %s AND orders.paid = FALSE 
			"""
			cur.execute(sql,(user["id"],))
			connect.commit()
			return JSONResponse({"ok":True},status_code=status.HTTP_200_OK)
	except Exception as e:
			connect.rollback()
			print(f"db error: {e}")
			return JSONResponse({"error":True,"message":"查詢時發生錯誤"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()		
	
# ordering

@app.post("/api/orders",response_class=JSONResponse,tags=["Order"]) 
async def new_order(data:Full_order,user=Depends(get_current_user)):
	connect =cnxpool.get_connection()
	partner_key="partner_kSxkVGCDl8l3vMuIPqaahF7rSejDoDO8qRdoiH9hULWdbmTsF5BIMMVA"
	# 檢查格式(先跳過)
	# 送出表單
	pt_url ="https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
	merchant_id="nicoth35011_TAISHIN"
	header = {
		"Content-Type": "application/json",
		"x-api-key":"partner_kSxkVGCDl8l3vMuIPqaahF7rSejDoDO8qRdoiH9hULWdbmTsF5BIMMVA"
	 }
	db_data ={}
	try:
		# 撿price
		with connect.cursor() as cur:
			
			sql = """SELECT 
				att.name, 
				orders.order_at, 
				orders.time_slot,
				orders.price,
				orders.id,
				orders.create_at
			FROM orders  
			JOIN attractions AS att ON orders.attraction_id = att.id 
			LEFT JOIN att_img_urls AS img ON orders.attraction_id = img.attraction_id
			WHERE orders.user_id = %s AND orders.paid = FALSE
			ORDER BY img.id ASC LIMIT 1"""

			cur.execute(sql,(user["id"],))
			order_data = cur.fetchone()
			if order_data is None:
				return JSONResponse({"error":True,"message":"不存在的訂單"},status_code=status.HTTP_400_BAD_REQUEST)
			db_data = {
					"name": order_data[0],
					"date":order_data[1].isoformat() if order_data[1] else None,
					"time":order_data[2],
					"price":order_data[3],
				}
		# 執行支付
		body={
			"prime":data.prime,
			"partner_key":"partner_kSxkVGCDl8l3vMuIPqaahF7rSejDoDO8qRdoiH9hULWdbmTsF5BIMMVA",
			"merchant_id":merchant_id,
			"amount":db_data["price"],
			"details":f"{db_data['name']} {db_data['date']} {db_data['time']}",
			"cardholder":{
				"phone_number":data.contact.phone,
				"name":data.contact.name,
				"email":data.contact.email,
			}
		}
		response = requests.post(pt_url,headers=header,json=body)
		if response.ok:
			payment = response.json()
			print(payment)
			if payment["status"] != 0:
				return JSONResponse({"error":True,"message":"交易失敗"},status_code=status.HTTP_400_BAD_REQUEST)
		
		# 塞入payment
		with connect.cursor() as cur:
			order_id = order_data[4]
			create_at = order_data[5]
			order_number=create_at.strftime("%Y%m%d%H%M%S")
			cur.execute("UPDATE orders SET paid = TRUE, order_number = %s,contact_name = %s,contact_email=%s,contact_phone=%s WHERE id = %s",
			   (
				order_number,
				data.contact.name,
				data.contact.email,
				data.contact.phone,
				order_id
				))
			# 將獲得的內容存入db
			sql = """
				INSERT INTO payment (
					order_id,
					rec_trade_id,
					status,
					bank_transaction_id,
					amount,
					currency,
					details,
					card_info,
					transaction_time_millis,
					bank_transaction_time
				)
				VALUES (
					%s, %s, %s, %s, %s,
					%s, %s, %s, %s, %s
				)
			"""
			values = (
				order_id,
				payment["rec_trade_id"],
				True,
				payment["bank_transaction_id"],
				payment["amount"],
				payment["currency"],
				f"{data.order.trip.attraction.name} {data.order.trip.date} {data.order.trip.time}",
				json.dumps(payment["card_info"]),
				payment["transaction_time_millis"],
				json.dumps(payment["bank_transaction_time"])
				)
			print("values",values)
			cur.execute(sql,values)
			connect.commit()
			return JSONResponse({
				"number":order_number,
				"payment":{
					"status":payment["status"],
					"msg":payment["msg"]
				}
			},status_code=status.HTTP_200_OK)
	except Exception as e:
		print(f"db error: {e}")
		return JSONResponse({"error":True,"message":"查詢時發生錯誤，請稍後再試"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		connect.close()		
	
	# 回傳結果
@app.get("/api/order/{order_number}",response_class=JSONResponse,tags=["Order"])
def get_order(order_number:str,user=Depends(get_current_user)):
	user_id = user["id"]
	connect = cnxpool.get_connection()
	try:
		with connect.cursor() as cur:
			sql="""SELECT 
				att.id, 
				att.name, 
				att.address, 
				img.img_url, 
				orders.order_at, 
				orders.time_slot, 
				orders.price,
				orders.contact_name,
				orders.contact_email,
				orders.contact_phone,
				orders.paid 
			FROM orders  
			JOIN attractions AS att ON orders.attraction_id = att.id 
			LEFT JOIN att_img_urls AS img ON orders.attraction_id = img.attraction_id
			WHERE orders.user_id = %s AND orders.order_number = %s
			ORDER BY img.id ASC LIMIT 1"""
			cur.execute(sql , (user_id, order_number))
			response  =cur.fetchone()
			if response is None:
				return JSONResponse(
					{
						"error": True,
						"message": "找不到此訂單"
					},
					status_code=status.HTTP_404_NOT_FOUND
			)
			result = {
				"data":{
					"number": order_number,
					"price": response[6],
					"trip": {
						"attraction": {
							"id": response[0],
							"name": response[1],
							"address": response[2],
							"image": response[3]
						},
						"date": response[4].date().isoformat(),
						"time": response[5]
					},
					"contact": {
					"name": response[7],
					"email": response[8],
					"phone": response[9]
					},
					"status": response[10]
				}
			}
			return JSONResponse(content=result,status_code=status.HTTP_200_OK)
	except Exception as e:
			print(e)
			return JSONResponse({
				"error":True,
				"message":f"發生查詢錯誤 {e}"
			},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)		
	finally:
		connect.close()

@app.get("/api/mcptoken",response_class=JSONResponse,)
async def get_mcptoken(user=Depends(get_current_user)):
	user_id = user["id"]
	result = ser_mcptoken(user_id)
	json_result = result.model_dump()
	return JSONResponse(json_result,status_code=status.HTTP_200_OK)

@app.patch("/api/mcptoken",response_class=JSONResponse,)
async def get_mcptoken(user=Depends(get_current_user)):
	user_id = user["id"]
	result = new_mcptoken(user_id)
	json_result = result.model_dump()
	return JSONResponse(json_result,status_code=status.HTTP_202_ACCEPTED)


# exception_handler
@app.exception_handler(AttractionNotFoundError)
async def att_no_found(request, exc):
	return JSONResponse(
            {
                "error": True,
                "message": "找不到景點"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

@app.exception_handler(DatabaseError)
async def sql_err(request, exc):
	 return JSONResponse(
            {
                "error": True,
                "message": "查詢發生錯誤"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )