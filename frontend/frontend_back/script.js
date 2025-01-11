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

const micBtn = document.getElementById("mic-btn");
const recordingStatus = document.getElementById("recording-status");
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

micBtn.addEventListener("click", async () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            await sendAudioToServer(audioBlob);
            audioChunks = [];
            
            // Stop all tracks to release microphone
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;
        micBtn.classList.add("recording");
        recordingStatus.classList.remove("hidden");
        
    } catch (error) {
        console.error("Error accessing microphone:", error);
        alert("Could not access microphone. Please check permissions.");
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        micBtn.classList.remove("recording");
        recordingStatus.classList.add("hidden");
    }
}

async function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.wav");

    try {
        const response = await fetch("http://localhost:8000/audio", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        if (response.ok) {
            console.log("Audio processed:", result);
            if (result.text) {
                commandInput.value = result.text;
            }
        } else {
            console.error("Server error:", result.message);
        }
    } catch (error) {
        console.error("Error sending audio:", error);
    }
}

// Add keyboard shortcut for microphone
document.addEventListener("keydown", (event) => {
    if (event.code === "Space" && event.ctrlKey) {
        event.preventDefault();
        micBtn.click();
    }
});
