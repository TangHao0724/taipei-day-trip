const bd = document.getElementById("black-drop");
const token = localStorage.getItem("TOKEN");
main();
async function main(){
    await checkStatus(token);
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
      return dialog(false);
    }else{
      return dialog(true);
    }
    
  }catch(e){
    return dialog(false);
  }
  
}

function dialog(isPass){
    const btn = document.getElementById("dialog-btn");
    if(isPass){
      btn.innerText="登出系統";
      btn.addEventListener('click',(e)=>{
        localStorage.removeItem("TOKEN");
        location.reload();
      })
    }else{
      btn.innerText="登入/註冊";
      btn.addEventListener('click',(e)=>{
        toogleDrop(true);
        toogleDialog(true,true);
      })
    }
}
function toogleDrop(isOpen){
    if (isOpen){
        bd.classList.remove("drop-display");
    }else{
        bd.classList.add("drop-display");
        bd.querySelector(".dialog")?.remove();
    }
}

function toogleDialog(isOpen,islogin){
  if (isOpen){
      if (!bd.querySelector(".dialog")) {
        const dialog = createDialog(islogin);
        bd.append(dialog);
        document.getElementById("dialog-exit-btn").addEventListener("click",()=>{
          toogleDialog(!isOpen);
          toogleDrop(!isOpen);
        })
        document.getElementById("footer-link").addEventListener("click",()=>{
          toogleDialog(!isOpen);
          toogleDialog(true,!islogin);
        })
        document.getElementById("dialog-form").addEventListener("submit",(e)=>{
          e.preventDefault();
          const name = document.getElementById("form-name") ? 
          document.getElementById("form-name").value
          :null ;
          const email = document.getElementById("form-email").value;
          const password = document.getElementById("form-password").value;
          if(islogin){
            if(emailVerify(email) && pwVerify(password)){
              signIn(email,password);
            }
          }else{
            if(namerify(name) && emailVerify(email) && pwVerify(password)){
              register(name,email,password);
            }
          }
        })
      }
  }else{
      bd.querySelector(".dialog")?.remove();
  }
}
async function register(name,email,pw){
  const data = {
    "name":name,
    "email":email,
    "password":pw
  };
  try{
    const response = await fetch("/api/user",{
      method:"POST",
      headers: {
        "Content-Type": "application/json",
      },
      body:JSON.stringify(data)
    });
    const errorMessage = await response.json();
    if(!response.ok){
      alertText(errorMessage["message"],"#a43f39");
    }else{
      alertText("註冊成功","#72a439")
    }
  }catch(e){  
    alertText("程式錯誤請稍後再試","#a43f39");
    console.error(e);
  }

}
async function signIn(email,pw){
  const data = {
    "email":email,
    "password":pw
  };
  try{
    const response = await fetch("/api/user/auth",{
      method:"PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body:JSON.stringify(data)
    });
    const responseData = await response.json();
    if (!response.ok) {
      alertText(responseData["message"] || "所輸入的帳號或密碼錯誤","#a43f39");
      return;
    }
    
    localStorage.setItem('TOKEN', responseData["token"]);
    location.reload();

  }catch(e){
    alertText("程式錯誤請稍後再試","#a43f39");
    console.error(e);
  }
  
}
function createDialog(islogin){
  const dialog = document.createElement('div');
  const login = `
      <input type="text" name="email" id="form-email" class="dialog-form-input" placeholder="輸入電子信箱"/>
      <input type="password" name="password" id="form-password" class="dialog-form-input" placeholder="輸入密碼"/>
  `;
  const register = `
      <input type="text" name="name" id="form-name" class="dialog-form-input" placeholder="輸入姓名"/>
      <input type="text" name="email" id="form-email" class="dialog-form-input" placeholder="輸入電子信箱"/>
      <input type="password" name="password" id="form-password" class="dialog-form-input" placeholder="輸入密碼"/>
  `;
  dialog.classList.add("dialog","bg-add-c-w")
  dialog.innerHTML = 
  `
    <div class="decorator-bar">
    </div>
    <button id="dialog-exit-btn" class="dialog-exit-btn">
      <img src="/static/imgs/dialog_exit.png" alt="" srcset="">
    </button>
    <div class="dialog-main">
        <span class="title dialog-title-b sec-c-70">
          ${islogin? "登入" : "註冊"}會員帳號
        </span>
      <form  id="dialog-form" action="" class="dialog-form">
          ${islogin? login : register}
        <button type="submit" class="dialog-form-btn bg-pri-c-70">
          <span class="add-c-w button">
            ${islogin? "登入帳戶" : "註冊新帳戶"}
          </span>
        </button>
        <div class="dialog-footer">
          <span class="footer-content body sec-c-70">
            ${islogin? "還沒有帳戶？<a id='footer-link'>點此註冊</a>" : "已經有帳戶了？<a id='footer-link'>點此登入</a>"}
          </span>
        </div>
      </form>
      <span id="dialog-alert" class="body sec-c-70">
      </span>
    </div>
  `
  
  return dialog;
}
function alertText(alertStr,color){
  const alertDom = document.getElementById("dialog-alert");
  alertDom.innerText = alertStr;
  alertDom.style.color = color;
}
// verfily
function emailVerify(str){
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if(str === ""){
    alertText("請輸入電子信箱","#a43f39");
    return false;
  }
  if(!regex.test(str)){
    alertText("請輸入正確電子信箱格式","#a43f39");
    return false;
  }
  return true;
}
function pwVerify(str){
  if(str === ""){
    alertText("請輸入密碼","#a43f39");
    return false;
  }
  return true;
}
function namerify(str){
  if(str === ""){
    alertText("請輸入姓名","#a43f39");
    return false;
  }
  return true;
}