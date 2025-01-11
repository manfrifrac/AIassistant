export class AudioAnalyzer {
  constructor() {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 1024;
      this.analyser.smoothingTimeConstant = 0.7;
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      this.prevLevel = 0;
      this.source = null;
      
      // Buffer per smoothing
      this.levelHistory = new Array(5).fill(0);
      this.historyIndex = 0;
      console.log('AudioAnalyzer initialized successfully');
    } catch (error) {
      console.error('Error initializing AudioAnalyzer:', error);
    }
  }

  connectSource(audioElement) {
    try {
      if (this.source) {
        this.source.disconnect();
      }
      
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }
      
      this.source = this.audioContext.createMediaElementSource(audioElement);
      this.source.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);
      console.log('Audio source connected successfully');
    } catch (error) {
      console.error('Error connecting audio source:', error);
    }
  }

  getLevel() {
    try {
      this.analyser.getByteFrequencyData(this.dataArray);
      
      // Focus sulle frequenze medio-basse (dove è più presente la voce)
      const relevantFreqs = this.dataArray.slice(1, 50);
      const currentLevel = Math.max(...relevantFreqs) / 255;
      
      // Media mobile per smoothing
      this.levelHistory[this.historyIndex] = currentLevel;
      this.historyIndex = (this.historyIndex + 1) % this.levelHistory.length;
      
      const averageLevel = this.levelHistory.reduce((a, b) => a + b) / this.levelHistory.length;
      
      // Smoothing aggiuntivo
      const smoothingFactor = 0.3;
      const smoothedLevel = this.prevLevel + (averageLevel - this.prevLevel) * smoothingFactor;
      this.prevLevel = smoothedLevel;
      
      // Enfatizza i picchi ma mantieni un movimento fluido
      return Math.pow(smoothedLevel, 1.5);
    } catch (error) {
      console.error('Error getting audio level:', error);
      return 0;
    }
  }
}
