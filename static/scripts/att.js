let attData = null;
let nowimglist = 0;
const attoken = localStorage.getItem("TOKEN");

start();
async function start() {
    const id = get_id();
    const userData = await checkStatus(attoken);
    attData = await getAttData(id);
    setImgList(attData);
    setInfo();
    setAttProf();
    setTimePicker();
    bindRadio();
    formSub(userData);

    //  監聽size切換
    const resizeObserver = new ResizeObserver(() => {
        requestAnimationFrame(syncCurrentImage);
    });

    resizeObserver.observe(imgWindow);
    
}
async function checkStatus(token){
  try{
    const response = await fetch("/api/user/auth",{
      headers:{
        "Authorization":`Bearer ${token}` 
      }
    });

    const data = await response.json();

    if (!response.ok) {
      console.log(data.detail);
      return null;
    }

    console.log(data);
    return data; 
  }catch(e){
    throw new Error(e);
  }
}

function get_id() {
    const nowURL = window.location.pathname;
    const id = nowURL.trim().split("/")[2];
    return id;
}
// load data
async function getAttData(id) {
    const attUrl = new URL(`/api/attractions/${decodeURIComponent(id)}`, window.location.origin);
    try{
        const response = await fetch(attUrl);
        if(!response.ok){
            throw new Error(`${response.status}`);
        }
        const data = await response.json();
        return data.data ;
    }catch(e){
        throw new Error(`HTTP Error Status :${e}`);
    }
}
// imglist
function drawImg(url){
    const img = document.createElement("img");
    img.src=url;
    img.classList.add("img-item");
    return img;
}
function setImgList(attData){
    const imglist = attData.images.map(img => drawImg(img));
    const target = document.getElementById("img-list");
    target.append(...imglist);
    const listLen  = attData.images.length;
    nowimglist = 0;
    setIndeBar(listLen);
    setImgBtn(listLen);

}
function setIndeBar(imgs){
    
    let indis = [];
    for(let i = 0 ;i < imgs;i++){
        const indi = document.createElement("div");
        if (i <1 ){
            indi.classList.add("indi-on");
        }
        indi.classList.add("indi-item");
        indi.id = `indi-item-${i}`;
        indis.push(indi);
    }
    const list = document.getElementById("indi-bar");
    list.append(...indis);
}

const imgWindow = document.getElementById("img-window");
function setImgBtn(imgs){
    const lBtn = document.getElementById("l-btn");
    const rBtn = document.getElementById("r-btn");
    lBtn.addEventListener("click",()=>{
        if(nowimglist > 0){
            document.getElementById(`indi-item-${nowimglist}`).classList.remove("indi-on");
            nowimglist -= 1;
            document.getElementById(`indi-item-${nowimglist}`).classList.add("indi-on");
        
            imgWindow.scrollTo({
            left: nowimglist * getItemWidth(),
            behavior:"smooth"
        })
        }
        
    });
    rBtn.addEventListener("click",()=>{

        if(nowimglist < imgs-1 ){
            document.getElementById(`indi-item-${nowimglist}`).classList.remove("indi-on");
            nowimglist += 1;
            document.getElementById(`indi-item-${nowimglist}`).classList.add("indi-on");
            
            imgWindow.scrollTo({
                left: nowimglist * getItemWidth(),
                behavior:"smooth"
            })
        }
        
    });
}
function getItemWidth(){
    const item = document.querySelector(".img-item");
    return item?.getBoundingClientRect().width  ?? 0;
}
function syncCurrentImage() {
  const itemWidth = getItemWidth();
  imgWindow.scrollLeft = nowimglist * itemWidth;
}

// prof
function setAttProf(){
    const title = document.getElementById("att-title")
    const tags = document.getElementById("att-tags");
    title.innerText = attData.name;
    tags.textContent = `${attData.category} ${"at "+attData.mrt ?? ""}`;
}
// info
function setInfo(){
    const section = document.createElement("section");
    section.classList.add("att-info");
    section.innerHTML=`
    <article class="att-art">
        <span class="att-des content sec-c-70">${attData.description}</span>
    </article>
    <article class="att-art">
        <span class="info-title body-b sec-c-70">
        景觀地址：
        </span>
        <span class="att-des content sec-c-70">${attData.address}</span>
    </article>
    <article class="att-art">
        <span class="info-title body-b sec-c-70">
        交通方式：
        </span>
        <span class="att-des content sec-c-70">${attData.transport}</span>
    </article>
    `;
    const getMain = document.querySelector("main");
    getMain.appendChild(section);
}   
// form
function bindRadio(){

    const radio = document.querySelectorAll(".time-radio");
    radio.forEach(i =>{
        i.addEventListener("change",(e)=>{
            if (e.target.checked) {
                setPrice(Number(e.target.value));
            }
        });
    });
    
}
function setPrice(time){
    const price = document.getElementById("order-price");
    price.innerText = `新臺幣 ${time == "0"?2000:2500} 元`

}
async function formSub(userData){
    document.getElementById("booking-form").addEventListener('submit',async (event)=>{
        event.preventDefault();
        if (!userData){
            toogleDrop(true);
            toogleDialog(true,true);
        }else{
            const date = document.getElementById("date-picker");
            const time = document.querySelector(
            'input[name="order-time"]:checked'
            );
            const formData = {
                "attractionId": attData.id,
                "date": date.value || null,
                "time": time.value == "0" ? "morning":"afternoon",
                "price": time.value == "0"? 2000:2500
            }
            try{
                const response = await fetch("/api/booking",{
                method:"POST",
                headers:{
                    "Authorization":`Bearer ${attoken}` ,
                    "Content-Type": "application/json",
                },
                body:JSON.stringify(formData)
                });

                const result = await response.json();
                if(!response.ok){
                alertText(result.message,"#a43f39");
                }else{
                    window.location.assign("/booking");
                }
                
                
            }catch(e){
                throw new Error(e);
            }
        }


    });

}
function alertText(alertStr,color){
  const alertDom = document.getElementById("dialog-alert");
  alertDom.innerText = alertStr;
  alertDom.style.color = color;
}
function setTimePicker(){
    const input = document.getElementById("date-picker");
    const today = new Date();
    today.setDate(today.getDate() + 1);

    input.min = today.toISOString().split('T')[0];
}