from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Cookie, Depends, Query, WebSocketException, status
from fastapi.responses import HTMLResponse


app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat room!</title>
           <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">

    </head>
    <body>
    <div class="container mt-3">
        <h1>FastAPI Chat Room!</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" class="form-control" id="messageText" autocomplete="off"/>
            <button class="btn btn-outline-primary mt-2">Send</button>
        </form>
        <ul id='messages' class="mt-5">
        </ul>
        
    </div>
    
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        # Här är en lista av connections.
        self.active_connections: list[WebSocket] = []

    # Här skapar vi en connection och till en ny användare som den kommer ha.

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    # Här gör vi en funktion för att kunna ta bort en connection. Med remove()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    # Här är det som gör magin. Här kan vi lägga till ett personligt meddelande till vår websocket.
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    # Här kan man broadcasta det meddelande som finns inne hos vår websocket till alla connactions.

    async def broadcast(self, message: str):
        # Här väljer vi alla websockets med en for loop
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} has left the chat")
