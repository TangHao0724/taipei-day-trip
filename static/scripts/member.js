const mtoken = localStorage.getItem("TOKEN");

main();
async function main(){
    const name = await loginCheck();
    setTitle(name);
    drawMcpUrl(setMcpUrl());
    drawToken(await getToken());
    setUpdateBtn();
    setSignoutBtn();
}

async function loginCheck(){
    if (mtoken === null){
     window.location.assign('/');
    };
    let result; 
    try{
        const response = await fetch('/api/user/auth',{
        method:"get",
        headers:{
            "Authorization":`Bearer ${mtoken}` 
        }
        });
        if (!response.ok){
            window.location.assign('/');
        }
        result = await response.json();
        console.log(result);
    }catch(e){
        window.location.assign('/');
        throw new Error(`${e}`);
    }
    return result.data.name;
}
async function setTitle(name){
    const title = document.getElementById("title");
    title.textContent=`您好 ${name} ，歡迎來到會員中心。`
}
async function getToken() {
    let result ;
    try{
        const response = await fetch('/api/mcptoken',{
        method:"get",
        headers:{
            "Authorization":`Bearer ${mtoken}` 
        }
        });
        result = await response.json();
        console.log(result);
    }catch(e){
        throw new Error(`${e}`);
    }
    return result.token;
}
function setMcpUrl(){
    const local = window.location.origin;
    const mcp = `${local}/mcp`;
    console.log(mcp);
    return mcp;
}
async function drawMcpUrl(url){
    const mcpEle = document.getElementById("mcp-url");
    mcpEle.textContent = url;
    
}
function drawToken(token){
    const tokenEle = document.getElementById("token");
    tokenEle.textContent = token ?? "尚未產生token";
}
async function setUpdateBtn(){
    document.getElementById("token-btn").addEventListener("click",async (e)=>{
        let result ;
        try{
            const response = await fetch('/api/mcptoken',{
            method:"PATCH",
            headers:{
                "Authorization":`Bearer ${mtoken}` 
            }
            });
            result = await response.json();
            console.log(result);
        }catch(e){
            throw new Error(`${e}`);
        }
        drawToken(result.token);
    });
}
function setSignoutBtn(){
    document.getElementById("signout-btn").addEventListener("click",async (e)=>{
        localStorage.removeItem("TOKEN");
        if(window.location.pathname === "/booking" | window.location.pathname === "/member"){
          window.location.assign('/');
        }else{
          location.reload();
        }
    });
}