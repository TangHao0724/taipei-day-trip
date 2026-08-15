let nextpage = null;
let category = "";
let keyword = "";
let loading = false;
function logState(){
    console.log(`nextpage : ${nextpage} ,category : ${category},keyword :${keyword},loading : ${loading} `)
}
// start At
start();
async function start(){
    await setMrtTagList();
    await setCatTagGrid();
    await setCards(0);
    
    // 滾動更新
    const obs = new IntersectionObserver(async (entries, observer) =>  {
        for(const entry of entries) {
            if (!entry.isIntersecting) continue;
            await rollLoading();
        }
    },{
        root:null,
        rootMargin: '200px 0px',
        threshold: 0
    });
    const target = document.getElementById("load-more");
    obs.observe(target);

    // 綁定按鈕功能
    const searchBtn = document.getElementById("search-btn");

    searchBtn.addEventListener("click",async()=>{
        nextpage = null;

        const word = document.getElementById("search-input").value;
        keyword = word;

        const attGrid = document.getElementById("att-grid");
        attGrid.innerHTML= "";
        logState();
        await setCards(0,category,keyword);
        await rollLoading();

    })

    const catListBtn = document.getElementById('cat-select');
    const catGrid = document.getElementById("cat-grid");
    catListBtn.addEventListener("click",()=>{
        catGrid.classList.toggle("cat-grid-off");
    })
}
// roll
async function rollLoading(){
    if (loading) return;
    if (nextpage === null) return;
    loading = true;
    try{
        await setCards(nextpage,category,keyword);
    }finally{
        loading = false;
    }
}
// att
// 獲取資料
async function getAtt(page,category= "",keyword= "") {
    if ((typeof page !== 'number')) {
        throw new TypeError('page必須是 number 型別，並且必填');
    }
    if (typeof category !== 'string') {
        throw new TypeError('category必須是 string 型別');
    }
    if (typeof keyword !== 'string') {
        throw new TypeError('keyword    必須是 string 型別');
    }
    let base_url = new URL('/api/attractions', window.location.origin);

    base_url.searchParams.append("page",page);
    if(category!= ""){
        base_url.searchParams.append("category",category);
    }
    if(keyword!= ""){
        base_url.searchParams.append("keyword",keyword);
    }
    console.log("base_url : "+ base_url.toString());
    let datas;
    try {
        const response = await fetch(base_url);
        
        if (!response.ok) {
            throw new Error(`HTTP error status: ${response.status}`);
        }
        
        datas = await response.json(); 
        
    } catch (error) {
        throw new Error("fetch error"+error);
    }
    console.log(datas);
    return datas;
}
// 繪製card
function drawCard(attData){
    const card = document.createElement("article");
    card.classList.add("att-card","bg-add-c-w");
    card.innerHTML = `
        <div class="att-photo">
            <!-- 圖片 -->
              <img src="${attData.images[0]}" alt="${attData.name}" class="att-img">
              <div class="att-img-name">
                <div class="att-img-name-info">
                  <span class="body-b add-c-w">
                    ${attData.name}
                  </span>
                </div>
              </div>
            </div>
            <div class="att-detail">
            <!-- details -->
              <div class="att-detail-info">
                <span class="body sec-c-50 att-s-dh">
                  ${attData.mrt}
                </span>
                <span class="body sec-c-50 att-s-dh">
                  ${attData.category}
                </span>
              </div>
            </div>
    `;
    return card;
}
// 添加att至網頁 set nextpage, cards
async function setCards(page,category ="",keyword=""){
    let cat = category;
    if(category.includes("全部分類")){
        cat = "";
    }
    const data = await getAtt(page,cat,keyword);
    nextpage = data.nextpage;
    if (data.data.length < 1){
        return null;
    }
    const cards = data.data.map(i =>{
        return drawCard(i);
    });
    const attGrid = document.getElementById("att-grid");
    logState(); 
    attGrid.append(...cards);
}   

// mrts
async function getMrts(){
    const url = new URL('/api/mrts', window.location.origin);
    let data ; 

    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error status: ${response.status}`);
        }
        
        data = await response.json(); 
        
    } catch (error) {
        throw new Error("fetch error"+error);
    }
    return data;
}
function drawMrtTag(mrtName){
    const mrtTag = document.createElement("li");
    mrtTag.innerHTML=`
        <button class="list-btn-item">
            <span class=" body sec-c-70 list-ih">
                ${mrtName}
            </span>
          </button>
    `;
    return mrtTag;
}
async function setMrtTagList() {
    const data = await getMrts();
    const mrtTags = data.data.map(i =>{ 
        const tag = drawMrtTag(i);
        return tag;

    });
    const ul = document.getElementById("mrt-list");
    ul.append(...mrtTags);

    mrtBtn();
    mrtLi();
}
// mrtlist 
function mrtBtn(){
    const lBtn = document.getElementById("list-btn-l")
    const rBtn = document.getElementById("list-btn-r");
    const ulList = document.getElementById("mrt-list");

    lBtn.addEventListener("click",()=>{
        ulList.scrollBy({
            left: -200,
            behavior:"smooth"
        })
    })
    rBtn.addEventListener("click",()=>{
        ulList.scrollBy({
            left: 200,
            behavior:"smooth"
        })
    })
}
function mrtLi() {
    const buttons = document.querySelectorAll("#mrt-list > li > button");
    console.log("buttons" + buttons.length);
    buttons.forEach(button => {
        button.addEventListener("click", async event => {
            const name = event.currentTarget.querySelector("span").innerText;
            document.getElementById("search-input").value = name;
            const attGrid = document.getElementById("att-grid");
            attGrid.innerHTML= "";
            nextpage = null;
            keyword = name;
            await setCards(0,category,keyword);

        });
    });
}
 
// cat
async function getCats() {
    const url = new URL('/api/categories', window.location.origin);
    let data ; 

    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error status: ${response.status}`);
        }
        
        data = await response.json(); 
        
    } catch (error) {
        throw new Error("fetch error"+error);
    }
    return data;
}
function drawCatTag(catName){
    const catTag = document.createElement("button");
    catTag.classList.add("cat-item","bg-add-c-w")
    catTag.innerHTML=`
            <span class="category-lis add-c-bt">
                ${catName}
            </span>
    `;
    return catTag;
}
async function setCatTagGrid() {
    const data = await getCats();
    const catTags = ["全部分類",...data.data,"",""].map(i =>{ 
        const tag = drawCatTag(i);
        return tag;

    });
    const grid = document.getElementById("cat-grid");
    grid.append(...catTags);
    catBtn();
}
function catBtn() {
    const buttons = document.querySelectorAll("#cat-grid > button");
    console.log("buttons" + buttons.length);
    buttons.forEach(button => {
        button.addEventListener("click", async event => {
            const name = event.currentTarget.querySelector("span").innerText;
            document.getElementById("cat-select").querySelector("span").innerText = `${name} ▼`;
            category = name;
            document.getElementById("cat-grid").classList.toggle("cat-grid-off");
            document.getElementById("att-grid").innerHTML = "";
            nextpage = null;
            await setCards(0, category,keyword);
        });
    });
}