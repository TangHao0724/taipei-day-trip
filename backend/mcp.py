from datetime import date, datetime
from typing import Literal

from fastapi import Depends
from fastmcp import FastMCP
from fastmcp.client import Client
from fastmcp.server.dependencies import get_http_headers

from backend.schema import Booking_data
from backend.service import add_booking, auth_token, get_att_list

mcp = FastMCP("TDT Tools")

# 查詢
@mcp.tool(
		name="搜尋台北市景點", 
		description="透過關鍵字和捷運站名搜尋台北市一日旅遊的景點", )
async def get_attraction(keyword:str):
	index = 0
	data = []
	while True:
		result = await get_att_list(index,None,keyword)
		index = index + 1 
		data.append(result["data"])
		if result["nextPage"] is None:
			break
	return {"data":data}

#新增入booking

@mcp.tool(
		name="預定景點導覽行程",
		description="根據景點編號、日期、時間、價格，預定一個景點導覽行程",
)
async def add_to_cart(date:date,start_at:datetime,att_id:int,):
	headers = get_http_headers(include_all=True)

	auth = headers.get("authorization", "")
	print("header",auth)
	if not auth.startswith("Bearer "):
		return {"error": "Bearer 開頭錯誤"}

	token = auth[len("Bearer "):].strip()
	id = auth_token(token)
	if id is None:
		return {"error": True,"msg":"不存在的用戶"}
	
	hour = start_at.hour
	if 9 <= hour < 16:
		period = "morning"
		price= "2000"
	elif 16 <= hour < 21:
		period = "afternoon"
		price= "2500"
	else:
		raise {"error": True,"msg":"不在可預約時間點，請選擇早上(08-15)，或者下午(16-21)時段，謝謝！"}
	data = Booking_data(
		attractionId=att_id,
		date=date,
		time=period,
		price=price
	)
	result = await add_booking(data,id)
	if not result:
		raise {"error": True,"msg":"預約時發生錯誤。"}
	return{
		"ok":True,
		"message":"台北導覽行程，預定成功，請到 Booking Page URL 完成付款。",

	}