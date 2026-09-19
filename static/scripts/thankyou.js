const ttoken = localStorage.getItem("TOKEN");
main();
async function main(){

    getBooking(getParm());
    setTitle();
}
function getParm(){
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    return urlParams.get('number') ?? null;
}
async function getToken(orderNum){
    try{
        const response = await fetch(`/api/order/${orderNum}`,{
        headers:{
            "Authorization":`Bearer ${ttoken}` 
        }
        });
        const result = await response.json();
        // if(!response.ok){
        //     window.location.replace("/");
        // }
        setList(result.data);
    }catch(e){
        throw new Error(`${e}`);
    }
}
async function setTitle(){
    const userData = await checkStatus(ttoken);
    document.getElementById("title").textContent = 
        `您好，${userData.name}，已預約成功！您的訂單號碼為「${getParm()}」。詳細如下：`;
}
async function checkStatus(token){
  let status;
  try{
    const response = await fetch("/api/user/auth",{
      headers:{
        "Authorization":`Bearer ${token}` 
      }
    });

    status = await response.json();
    if(!response.ok){
        return null;
    }else{
        return status.data;
    }
  }catch(e){
    throw new Error(e);
  }
  
}

function setList(data){
    const head = document.getElementById("head");
    const list = drawList(data);
    head.classList.add(data ? "booking-item" : "empty-item")
    head.appendChild(list);
}
function drawList(data){
    const list = document.createElement("div");
    list.id = "booking-list";
    
    if(!data){
        document.querySelector("footer").classList.remove("footerbar");
        list.innerHTML=`
        <span class="body sec-c-70">
            目前沒有任何待行程！
        </span>
        `;
    }else{
        list.classList.add("booking-list");
        const timeRange = data.trip.time === "morning" ? "早上九點到下午四點": "下午四點到晚上 九點";
        list.innerHTML=`
                <div class="att-img">
                    <img src="${data.trip.attraction.image}" alt="" srcset="">
                </div>
                <div class="att-info">
                    <div class="info-title">
                        <span class="body-b pri-c-70">
                        ${data.trip.attraction.name}
                        </span>
                    </div>
                    <div class="index">
                        <div class="index-content">
                            <span class="info-title body-b sec-c-70">日期：</span>
                            <span class="info-content body sec-c-70">${data.trip.date.substring(0,10)}</span>
                        </div>
                        <div class="index-content">
                            <span class="info-title body-b sec-c-70">時間：</span>
                            <span class="info-content  body sec-c-70">${timeRange}</span>
                        </div>
                        <div class="index-content">
                            <span class="info-title body-b sec-c-70">費用：</span>
                            <span class="info-content body sec-c-70">新台幣 ${data.price} 元</span>
                            </div>
                        <div class="index-content">
                            <span class="info-title body-b sec-c-70">地點：</span>
                            <span class="info-content body sec-c-70"> ${data.trip.attraction.address}</span>
                        </div>
                    </div>
                </div>
        `;
        setContact(data);
    }
    return list;
}


function setContact(data){
    const main = document.querySelector("main");
    if(data){
        main.insertAdjacentHTML('beforeend',`
            <div class="hr"></div>
            <section class="booking-item">
                <span class="block-title button-b sec-c-70">您的聯絡資訊：</span>
                <div class="block">
                    <div class="block-item">
                        <span class="title body sec-c-70">聯絡姓名：</span>
                        <span class="title body sec-c-70">${data.contact.name}</span>
                    </div>
                    <div class="block-item">
                        <span class="title body sec-c-70">聯絡信箱：</span>
                        <span class="title body sec-c-70">${data.contact.email}</span>
                    </div>
                    <div class="block-item">
                        <span class="title body sec-c-70">手機號碼：</span>
                        <span class="title body sec-c-70">${data.contact.phone}</span>
                    </div>
                </div>
            </section>
            <div class="hr"></div>
            <section class="booking-title">
                <span id="subtitle" class="button-b sec-c-70">
                敬請準時抵達會合，屆時會以電話聯絡通知！
                </span>
            </section>
        `);
    }
}