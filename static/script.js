let userId=null, currentChat=null, currentType=null;

function register(){
    fetch("/register",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            username:document.getElementById("username_input").value,
            phone:document.getElementById("phone_input").value,
            password:document.getElementById("password_input").value
        })
    }).then(r=>r.json()).then(d=>console.log(d));
}

function login(){
    fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            login:document.getElementById("login_input").value,
            password:document.getElementById("password_input").value
        })
    }).then(r=>r.json()).then(d=>{
        if(d.user_id){
            userId=d.user_id;
            document.getElementById("login_register").style.display="none";
            document.getElementById("chat").style.display="flex";
            document.getElementById("profile_info").innerText=`${d.username} (${d.phone})`;
            loadUsers(); loadGroups();
        } else document.getElementById("login_error").innerText="Invalid login";
    });
}

function searchUsers(){
    let q=document.getElementById("search_user").value;
    fetch("/search?q="+q).then(r=>r.json()).then(users=>{
        let div=document.getElementById("user_list"); div.innerHTML="";
        users.forEach(u=>{let b=document.createElement("button"); b.innerText=u.username; b.onclick=()=>{currentChat=u.id; currentType="dm"; loadMessages();}; div.appendChild(b);});
    });
}

function loadUsers(){ searchUsers(); }
function loadGroups(){ /* можно добавить получение списка групп */ }

function sendMessage(){
    let msg=document.getElementById("message_input").value; if(!msg) return;
    if(currentType=="dm"){
        fetch("/dm/send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({from:userId,to:currentChat,msg:msg})}).then(loadMessages);
    } else if(currentType=="group"){
        fetch("/group/send",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({from:userId,group:currentChat,msg:msg})}).then(loadMessages);
    }
    document.getElementById("message_input").value="";
}

function loadMessages(){
    if(!currentChat) return;
    if(currentType=="dm"){
        fetch(`/dm/history?a=${userId}&b=${currentChat}`).then(r=>r.json()).then(d=>{
            let div=document.getElementById("messages"); div.innerHTML=""; d.forEach(m=>{let p=document.createElement("p"); p.innerText=`${m.sender_id}: ${m.message}`; div.appendChild(p);}); div.scrollTop=div.scrollHeight;
        });
    } else if(currentType=="group"){
        fetch(`/group/history?group=${currentChat}`).then(r=>r.json()).then(d=>{
            let div=document.getElementById("messages"); div.innerHTML=""; d.forEach(m=>{let p=document.createElement("p"); p.innerText=`${m.sender_id}: ${m.message}`; div.appendChild(p);}); div.scrollTop=div.scrollHeight;
        });
    }
}

function createGroup(){
    let name=document.getElementById("new_group").value; if(!name) return;
    fetch("/group/create",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:name,owner:userId})}).then(r=>r.json()).then(d=>{console.log(d); loadGroups();});
}

// автообновление
setInterval(()=>{if(userId){ loadMessages(); loadUsers(); }},2000);
