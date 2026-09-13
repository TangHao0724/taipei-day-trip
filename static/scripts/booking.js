const btoken = localStorage.getItem("TOKEN");
main();
async function main(){
    setTitle();
    checkBooking();
}
async function checkBooking(){
    try{
        const response = await fetch("/api/booking",{
        headers:{
            "Authorization":`Bearer ${btoken}` 
        }
        });
        const result = await response.json();
        if(!response.ok){
            window.location.replace("/");
        }
        setList(result.data);
        setform(result.data);
        
    }catch(e){
        window.location.replace("/");
        throw new Error(`${e}`);
    }
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

async function setTitle(){
    const userData = await checkStatus(btoken);
    document.getElementById("title").textContent = 
        `您好，${userData.name}，待預定的行程如下：`;
    
}

function setList(bData){
    const head = document.getElementById("head");
    const list = drawList(bData);
    head.classList.add(bData ? "booking-item" : "empty-item")
    head.appendChild(list);
}

function drawList(data){
    const list = document.createElement("div");
    list.id = "booking-list";
    
    
    if(!data){
        document.querySelector("footer").classList.remove("footerbar");
        list.innerHTML=`
        <span class="body sec-c-70">
            目前沒有任何待預訂的行程。
        </span>
        `;
    }else{
        list.classList.add("booking-list");
        const timeRange = data.date === "morning" ? "早上 9 點到下午 4 點": "下午 4 點到晚上 9 點";
        list.innerHTML=`
                <div class="att-img">
                    <img src="${data.attraction.image}" alt="" srcset="">
                </div>
                <div class="att-info">
                    <button id="remove-btn"class="remove-img bg-add-c-w">
                        <img src="/static/imgs/icon_dele.png" alt="" srcset="">
                    </button>
                    <div class="info-title">
                        <span class="body-b pri-c-70">
                        ${data.attraction.name}
                        </span>
                    </div>
                    <div class="index">
                        <div class="index-content">
                            <span class="info-title body-b sec-c-70">日期：</span>
                            <span class="info-content body sec-c-70">${data.date.substring(0,10)}</span>
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
                            <span class="info-content body sec-c-70"> ${data.attraction.address}</span>
                        </div>
                    </div>
                </div>
        `
    }
    return list;

}
function setform(data){
    const main = document.querySelector("main");
    if(data){
        main.insertAdjacentHTML('beforeend',`
            <div class="hr"></div>
            <section class="booking-item">
                <span class="block-title button-b sec-c-70">您的聯絡資訊：</span>
                <div class="block">
                <div class="block-item">
                    <span class="title body sec-c-70">聯絡姓名：</span>
                    <input type="text" name="contact-name" id="contact-name" class="input body add-c-b">
                </div>
                <div class="block-item">
                    <span class="title body sec-c-70">聯絡信箱：</span>
                    <input type="text" name="contact-email" id="contact-email" class="input body add-c-b">
                </div>
                <div class="block-item">
                    <span class="title body sec-c-70">手機號碼：</span>
                    <input type="text" name="contact-phone" id="contact-phone" class="input body add-c-b">
                </div>
                <div class="block-item">
                    <span class="notice body-b sec-c-70">請保持手機暢通，準時到達，導覽人員將用手機與您聯繫，務必留下正確的聯絡方式。</span>
                </div>
            </div>
            <div class="hr"></div>
            <div class="booking-item">
                    <span class="block-title button-b sec-c-70">信用卡付款資訊：</span>
                <div class="block">
                <div class="block-item card-number-group">
                    <span class="title body sec-c-70">卡片號碼：</span>
                    <div class="tpfield" id="card-number"></div>
                </div>
                <div class="block-item expiration-date-group">
                    <span class="title body sec-c-70">過期時間：</span>
                    <div class="tpfield" id="card-expiration-date"></div>
                </div>
                <div class="block-item ccv-group">
                    <span class="title body sec-c-70">驗證密碼：</span>
                    <div class="tpfield" id="card-ccv"></div>
                </div>
            </div>
            </div>
            <div class="hr"></div>
            <section class="booking-item">
            <div class="send">
                <span class="body-b sec-c-70">總價：新台幣 2000 元</span>
                <button id="send-btn" class="send-btn bg-pri-c-70 button add-c-w">確認訂購並付款</button>
                <span id="form-alert" class="body sec-c-70">
                </span>
            </div>
            </section>
    `);
    setCard();
    form(data);
    removeBtn(btoken);
    }
}
function setCard(){
    let fields = {
        number: {
            // css selector
            element: '#card-number',
            placeholder: '**** **** **** ****'
        },
        expirationDate: {
            // DOM object
            element: document.getElementById('card-expiration-date'),
            placeholder: 'MM / YY'
        },
        ccv: {
            element: '#card-ccv',
            placeholder: 'ccv'
        },
    };
    TPDirect.card.setup({
        fields: fields,
        styles: {
            // Style all elements
            'input': {
                'color': 'gray'
            },
            // Styling ccv field
            'input.ccv': {
                'font-weight': '500',
                'font-size': '16px',
                'line-height':"16px"
            },
            // Styling expiration-date field
            'input.expiration-date': {
                'font-weight': '500',
                'font-size': '16px',
                'line-height':"16px"
            },
            // Styling card-number field
            'input.card-number': {
                'font-weight': '500',
                'font-size': '16px',
                'line-height':"16px"
            },
            // style focus state
            ':focus': {
                'color': 'black'
            },
            // style valid state
            '.valid': {
                'color': 'green'
            },
            // style invalid state
            '.invalid': {
                'color': 'red'
            },
            // Media queries
            // Note that these apply to the iframe, not the root window.
            '@media screen and (max-width: 400px)': {
                'input': {
                    'color': 'gray'
                }
            }
        },
        isMaskCreditCardNumber: true,
        maskCreditCardNumberRange: {
            beginIndex: 4,
            endIndex: 11
        }
    })
}
function form(data){
    
    document.getElementById("send-btn").addEventListener("click",(e)=>{
        e.preventDefault();
        const formElementData={
            contactName:document.getElementById("contact-name").value,
            contactEmail:document.getElementById("contact-email").value,
            contactPhone:document.getElementById("contact-phone").value,
        }
        
        if (formElementData.contactName === "" || formElementData.contactName === null){
            alertFormText("請輸入名稱")
            return;
        }

        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (formElementData.contactEmail === "" || formElementData.contactEmail === null){
            e.preventDefault();
            alertFormText("請輸入 Email");
        }
        if (!emailPattern.test(formElementData.contactEmail)){
            alertFormText("Email 格式不正確");
            return;
        }
        const phonePattern = /^09\d{8}$/;
        if (formElementData.contactPhone === "" || formElementData.contactPhone === null){
            alertFormText("請輸入電話號碼")
            return;
        }
        if (!phonePattern.test(formElementData.contactPhone)){
            alertFormText("電話號碼格式不正確,請輸入 09 開頭的 10 碼數字");
            return;
        }


        TPDirect.card.getPrime(async function(result) {
        if (result.status !== 0) {
            alertFormText(result.status);
            return;
        }
        let prime = result.card.prime
        try{
            const body = {
                prime: prime,
                order: {
                    price: data.price,
                    trip: {
                        attraction: {
                            id: data.attraction.id,
                            name: data.attraction.name,
                            address: data.attraction.address,
                            image: data.attraction.image
                        },
                        date: data.date,
                        time: data.time
                    }
                },
                contact: {
                    name: formElementData.contactName,
                    email: formElementData.contactEmail,
                    phone: formElementData.contactPhone
                }
            };

            const response = await fetch("/api/orders",{
            method:"POST",
            headers:{
                "Authorization":`Bearer ${btoken}`,
                "Content-Type": "application/json"
            },
            body:JSON.stringify(body)
            });

            let status = await response.json();
            if(!response.ok){
                alertFormText("訂單建立失敗,請稍後再試");
                return;
            }else{
                window.location.replace(`/thankyou/?number=${status.number}`);
            }
        }catch(e){
            console.error(e);
            alertFormText("發生錯誤,請稍後再試");
        }
        })
    })
}
async function removeBtn(token){    
    document.getElementById("remove-btn").addEventListener("click",async ()=>{
        try{
            const response = await fetch("/api/booking",{
                method:"DELETE",
                headers:{
                    "Authorization":`Bearer ${token}` 
                }
            });
            const data = await response.json();
            if(!response.ok){
                throw new Error(response.status);
            }
            window.location.reload();
        }catch(e){
            throw new Error(e);
            
        }
    });

}

function alertFormText(alertStr){
  const alertDom = document.getElementById("form-alert");
  alertDom.innerText = alertStr;
  alertDom.style.color = "#a43f39";
}