export class AudioAnalyzer {
  constructor() {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048; // Modificato per ottenere un segnale grezzo nel dominio del tempo
      this.analyser.smoothingTimeConstant = 0.3;
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      this.prevLevel = 0;
      this.source = null;
      
      // Buffer circolare per smoothing avanzato
      this.bufferSize = 12;
      this.levelBuffer = new Array(this.bufferSize).fill(0);
      this.bufferIndex = 0;
      
      // Parametri di interpolazione
      this.interpolationFactor = 0.15;
      this.peakDecay = 0.92;
      this.peakLevel = 0;
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
      const timeDomainData = new Uint8Array(this.analyser.frequencyBinCount);
      this.analyser.getByteTimeDomainData(timeDomainData);

      // Calcoliamo l'RMS del segnale: media quadratica
      let sumOfSquares = 0;
      for (let i = 0; i < timeDomainData.length; i++) {
        const sample = (timeDomainData[i] - 128) / 128;
        sumOfSquares += sample * sample;
      }
      const rms = Math.sqrt(sumOfSquares / timeDomainData.length);

      let currentLevel = rms; // Valore grezzo
      // Rilevamento picco e decadimento
      this.peakLevel = Math.max(currentLevel, this.peakLevel * this.peakDecay);

      // Buffer circolare per smoothing
      this.levelBuffer[this.bufferIndex] = currentLevel;
      this.bufferIndex = (this.bufferIndex + 1) % this.bufferSize;

      // Media pesata con enfasi sui valori più recenti
      const weights = Array.from({length: this.bufferSize}, (_, i) => Math.exp(-i * 0.2));
      const weightSum = weights.reduce((a, b) => a + b);

      let smoothedLevel = 0;
      for (let i = 0; i < this.bufferSize; i++) {
        const idx = (this.bufferIndex - i + this.bufferSize) % this.bufferSize;
        smoothedLevel += this.levelBuffer[idx] * weights[i];
      }
      smoothedLevel /= weightSum;

      // Interpolazione cubica
      const t = this.interpolationFactor;
      const interpolatedLevel = this.prevLevel +
        (smoothedLevel - this.prevLevel) * (1 - Math.pow(1 - t, 3));

      this.prevLevel = interpolatedLevel;

      // Usiamo la peakLevel come base
      return 2.5 * Math.pow(Math.max(interpolatedLevel, this.peakLevel * 0.8), 1.2);
    } catch (error) {
      console.error('Error getting audio level:', error);
      return 0;
    }
  }
}
