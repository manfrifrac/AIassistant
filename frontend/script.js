const statusText = document.getElementById("status-text");
const sendBtn = document.getElementById("send-btn");
const commandInput = document.getElementById("command-input");

const ws = new WebSocket("ws://localhost:8000/ws");

ws.onopen = () => {
    console.log("WebSocket connection opened.");
};

ws.onclose = () => {
    console.warn("WebSocket connection closed. Attempting to reconnect...");
    setTimeout(() => {
        window.location.reload();
    }, 3000);
};

ws.onerror = (error) => {
    console.error("WebSocket error:", error);
};

ws.onmessage = (event) => {
    try {
        const state = JSON.parse(event.data);
        statusText.textContent = state.status.charAt(0).toUpperCase() + state.status.slice(1);
    } catch (error) {
        console.error("Error processing WebSocket message:", error);
    }
};

sendBtn.addEventListener("click", async () => {
    const command = commandInput.value.trim();
    if (!command) return;

    sendBtn.disabled = true;
    try {
        const response = await fetch("http://localhost:8000/command", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ command }),
        });
        

        const result = await response.json();
        if (response.ok) {
            console.log("Command sent:", result);
        } else {
            console.error("Server error:", result.message);
        }
    } catch (error) {
        console.error("Error sending command:", error);
    } finally {
        sendBtn.disabled = false;
        commandInput.value = "";
    }
});
