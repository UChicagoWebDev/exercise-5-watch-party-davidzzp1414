const API_KEY = 'z220NmV1MRNLR3SKQRu4d5VgJNtojDo';


/* For index.html */

// TODO: If a user clicks to create a chat, create an auth key for them
// and save it. Redirect the user to /chat/<chat_id>
function createChat() {  //???
  return;
}


/* For updating username or password */
function updateID(name_or_password) {
    var route;
    if (name_or_password.localeCompare('name') == 0) {
        route = `/api/user/name`;
    } else {
        route = `api/user/password`;
    }
    const messageData = {username: document.getElementById('username').value,
                         password: document.getElementById('password').value};
    fetch(route, {
        method: 'POST',
        headers: {
            'x-api-key': API_KEY,
            "Content-Type": "application/json"
          },
        body: JSON.stringify(messageData)
    })

    .then(response => response.text())
    .catch(error => {
        console.error(error);
    });
}

if ((new URL(window.location.href).pathname.split('/')[1]).localeCompare('profile') == 0){
    document.querySelector("#username_button").addEventListener('click', (e) => {
        e.preventDefault();
        updateID('name');
    });
    document.querySelector("#password_button").addEventListener('click', (e) => {
        e.preventDefault();
        updateID('password');
    });
}


/* For updating room name */
function updateRoomName() {
    const roomId = new URL(window.location.href).pathname.split('/')[2];
    const new_name = document.querySelector('#input_field').value;
    const messageData = {name: new_name};
    fetch(`/api/room/${roomId}`, {
        method: 'POST',
        headers: {
            'x-api-key': API_KEY,
            "Content-Type": "application/json"
          },
        body: JSON.stringify(messageData)
    })
    .then(response =>  response.json())
    .then(data => {
      document.querySelector('.roomName').innerHTML = new_name;
      console.log('Room name changed:', data);
    })
    .catch(error => {
        console.error(error);
    });
}

if ((new URL(window.location.href).pathname.split('/')[1]).localeCompare('rooms') == 0){
    document.querySelector("#edit_button").addEventListener('click', (e) => {
        //console.log('clicked edit');
        const e1 = document.querySelector('.display');
        e1.setAttribute('class', 'display hide')
        const e2 = document.querySelector('.edit.hide');
        e2.setAttribute('class', 'edit');
    });
}

if ((new URL(window.location.href).pathname.split('/')[1]).localeCompare('rooms') == 0){
    document.querySelector("#display_button").addEventListener('click', (e) => {
        //console.log('clicked save');
        const e1 = document.querySelector('.display.hide');
        e1.setAttribute('class', 'display')
        const e2 = document.querySelector('.edit');
        e2.setAttribute('class', 'edit hide');
        
        updateRoomName();
    });
}


/* For room.html */

// TODO: Fetch the list of existing room messages.
// POST to the API when the user posts a new message.
// Automatically poll for new messages on a regular interval.
function postMessage() {
    const roomId = new URL(window.location.href).pathname.split('/')[2];
    const msg = document.getElementById('comment_content').value;
    const messageData = { room_id: roomId, comment: msg }; // Adjust according to your API expectations
    
    fetch(`/api/post_message/rooms/${roomId}`, {
        method: 'POST',
        headers: {
            'x-api-key': API_KEY,
            "Content-Type": "application/json"
          },
        body: JSON.stringify(messageData)
    })
    .then(response =>  response.json())
    .then(data => {
      console.log('Message posted:', data);
      //getMessages(roomId);
    })
    .catch(error => {
      console.error('Error posting message:', error);
    });
}


function getMessages() {
    const roomId = new URL(window.location.href).pathname.split('/')[2];
    fetch(`/api/get_messages/rooms/${roomId}`, {
        method: 'GET',
        headers: {
            'x-api-key': API_KEY,
            "Content-Type": "application/json"
        },
    })
      .then(response => response.json())
      .then(messages => {
        displayMessages(messages);
      })
      .catch(error => console.error('Error:', error));
}

function displayMessages(messages) {
    const messagesContainer = document.querySelector('.messages');
    messagesContainer.innerHTML = '';
    if (typeof messages == 'string' || messages instanceof String) {
        const messageElement = document.createElement('div');
        messageElement.innerHTML = `${messages}`;
        messagesContainer.appendChild(messageElement);
    } else {
        messages.forEach(message => {
        const messageElement = document.createElement('message');
        messageElement.innerHTML = `
            <author>${message.author}</author>
            <content>${message.body}</content>
        `;
        messagesContainer.appendChild(messageElement);
        });
    }
}
  

if ((new URL(window.location.href).pathname.split('/')[1]).localeCompare('rooms') == 0){
    document.addEventListener('DOMContentLoaded', () => {
        getMessages();
    });
}

if ((new URL(window.location.href).pathname.split('/')[1]).localeCompare('rooms') == 0){
  document.addEventListener('submit', (e) => {
      e.preventDefault();
      postMessage();
  });
}


function startMessagePolling() {
    if ((new URL(window.location.href).pathname.split('/')[1]).localeCompare('rooms') == 0){
      getMessages();
    }
}
setInterval(startMessagePolling, 100);