import { useState, useEffect, useRef } from 'react';
import { BezierDiamond } from './components/BezierDiamond';
import { AudioAnalyzer } from './components/AudioAnalyzer';
import './App.css';

// URLs e endpoints
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const ENDPOINTS = {
  CHAT_STATUS: `${API_URL}/api/chat`,
  CHAT_MESSAGE: `${API_URL}/api/chat`,
  AUDIO_UPLOAD: `${API_URL}/audio`,
  WEBSOCKET: `ws://localhost:8000/ws`
};

function App() {
  const [status, setStatus] = useState('Idle');
  const [command, setCommand] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioRef = useRef(null);
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false);
  const audioAnalyzer = useRef(null);

  useEffect(() => {
    // Initial connection check
    fetch(ENDPOINTS.CHAT_STATUS)  // Verifica che sia /api/chat
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        setStatus(data.message);
        console.log('Connection status:', data);  // Updated log message
      })
      .catch(error => {
        setStatus('Connection Error');
        console.error('Error:', error);
      });
  }, []);

  const handleSend = async () => {
    if (!command.trim()) return;
    
    setStatus('Sending...');
    try {
      const response = await fetch(ENDPOINTS.CHAT_MESSAGE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: command.trim() })  // Verifica che questo corrisponda al backend
      });
      
      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();
      console.log('Response received:', data);
      setStatus(data.message);

      if (data.audio_response) {  // Cambiato da data.audio a data.audio_response
        console.log('Audio response received, attempting to play...');
        const audioData = `data:audio/wav;base64,${data.audio_response}`;
        const audio = setupAssistantAudioAnalyser(audioData);
        if (audio) {
          try {
            await audio.play();
            console.log('Audio playback started');
          } catch (e) {
            console.error('Error playing audio:', e);
          }
        }
      } else {
        console.log('No audio response in data');
      }
    } catch (error) {
      setStatus('Error: ' + error.message);
      console.error('Error:', error);
    }
  };

  const setupAudioAnalyser = (stream) => {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioCtx.createAnalyser();
    const source = audioCtx.createMediaStreamSource(stream);
    
    analyser.fftSize = 32;
    source.connect(analyser);
    analyserRef.current = analyser;
    
    const updateAudioLevel = () => {
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      analyser.getByteFrequencyData(dataArray);
      
      // Calcola una media pesata delle frequenze
      const weights = dataArray.map((value, i) => value * (i + 1));
      const weightedAverage = weights.reduce((a, b) => a + b, 0) / weights.length;
      
      setAudioLevel(weightedAverage / 128);
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    };
    
    updateAudioLevel();
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      // Inizializza l'analizzatore audio quando inizia la registrazione
      setupAudioAnalyser(stream);

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await sendAudioToBackend(audioBlob);
        setAudioLevel(0); // Resetta il livello audio quando si ferma
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setStatus('Recording...');
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setStatus('Error: ' + error.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      setStatus('Processing audio...');
    }
  };

  const setupResponseAudioAnalyser = (audioElement) => {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioCtx.createAnalyser();
    const source = audioCtx.createMediaElementSource(audioElement);
    
    analyser.fftSize = 32;
    source.connect(analyser);
    analyser.connect(audioCtx.destination);
    analyserRef.current = analyser;
    
    const updateAudioLevel = () => {
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      analyser.getByteFrequencyData(dataArray);
      
      const weights = dataArray.map((value, i) => value * (i + 1));
      const weightedAverage = weights.reduce((a, b) => a + b, 0) / weights.length;
      
      setAudioLevel(weightedAverage / 128);
      if (audioElement.paused) {
        setAudioLevel(0);
        setIsAssistantSpeaking(false);
        return;
      }
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    };
    
    audioElement.addEventListener('play', () => {
      setIsAssistantSpeaking(true);
      updateAudioLevel();
    });
    
    audioElement.addEventListener('pause', () => {
      setIsAssistantSpeaking(false);
      setAudioLevel(0);
    });
    
    audioElement.addEventListener('ended', () => {
      setIsAssistantSpeaking(false);
      setAudioLevel(0);
    });
  };

  const setupAssistantAudioAnalyser = (audioData) => {
    try {
      const audio = new Audio(audioData);
      audioRef.current = audio;
      
      // Connetti l'analizzatore audio
      if (audioAnalyzer.current) {
        audioAnalyzer.current.connectSource(audio);
      }

      audio.addEventListener('play', () => {
        setIsAssistantSpeaking(true);
        console.log('Audio started playing');
      });

      audio.addEventListener('pause', () => {
        setIsAssistantSpeaking(false);
        setAudioLevel(0);
        console.log('Audio paused');
      });

      audio.addEventListener('ended', () => {
        setIsAssistantSpeaking(false);
        setAudioLevel(0);
        console.log('Audio ended');
      });

      return audio;
    } catch (error) {
      console.error('Error setting up audio:', error);
      return null;
    }
  };

  const sendAudioToBackend = async (audioBlob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    try {
      const response = await fetch(ENDPOINTS.AUDIO_UPLOAD, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();
      console.log('Received response:', data); // Debug log
      
      setStatus(data.text || 'Audio processed');
      if (data.text) setCommand(data.text);
      
      // Gestione della risposta audio
      if (data.audio_response) {
        const audioData = `data:audio/wav;base64,${data.audio_response}`;
        console.log('Playing audio response'); // Debug log
        const audio = setupAssistantAudioAnalyser(audioData);
        await audio.play().catch(e => console.error('Error playing audio:', e));
      } else {
        console.log('No audio response received'); // Debug log
      }
    } catch (error) {
      setStatus('Error: ' + error.message);
      console.error('Error sending audio:', error);
    }
  };

  const handleMic = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && command.trim()) {
      handleSend();
    }
  };

  useEffect(() => {
    // Inizializza AudioAnalyzer una sola volta
    audioAnalyzer.current = new AudioAnalyzer();
    
    const updateLevel = () => {
      if (audioRef.current && !audioRef.current.paused) {
        setAudioLevel(audioAnalyzer.current.getLevel());
      }
      animationFrameRef.current = requestAnimationFrame(updateLevel);
    };
    updateLevel();
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

// Rimuovi o commenta il secondo useEffect duplicato che inizializza AudioAnalyzer:
// useEffect(() => {
//   audioAnalyzer.current = new AudioAnalyzer();
//   const updateLevel = () => {
//     if (audioRef.current && !audioRef.current.paused) {
//       const level = audioAnalyzer.current.getLevel();
//       setAudioLevel(level);
//     }
//     animationFrameRef.current = requestAnimationFrame(updateLevel);
//   };
//   updateLevel();
//   return () => {
//     if (animationFrameRef.current) {
//       cancelAnimationFrame(animationFrameRef.current);
//     }
//   };
// }, []);

  return (
    <div className="App">
      <div className="content-container">
        <div className="visualizer-container">
          <BezierDiamond 
            audioLevel={audioLevel} 
            isActive={isAssistantSpeaking}
          />
        </div>
        <div className="controls-container">
          <input
            type="text"
            id="command-input"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter a command"
          />
          <button 
            id="mic-btn" 
            onClick={handleMic} 
            title="Record voice command"
            className={isRecording ? 'recording' : ''}
          >
            <i className="fas fa-microphone"></i>
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
