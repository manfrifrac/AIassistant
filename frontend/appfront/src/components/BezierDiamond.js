export function BezierDiamond({ audioLevel, isActive }) {
  const size = 300;
  const center = size / 2;
  
  // Parametri più reattivi
  const minWidth = 40;
  const maxWidth = 120;
  const minHeight = 30;
  const maxHeight = 80;
  
  // Calcolo più sensibile delle dimensioni
  const normalizedLevel = Math.min(Math.max(audioLevel, 0), 1);  // Assicura che sia tra 0 e 1
  const scaleFactor = normalizedLevel * normalizedLevel;  // Risposta quadratica per enfatizzare i picchi
  
  // Calcolo dimensioni con maggiore reattività
  const currentWidth = maxWidth - (scaleFactor * (maxWidth - minWidth));
  const currentHeight = minHeight + (scaleFactor * (maxHeight - minHeight));
  
  // Punti di controllo più dinamici
  const leftX = center - currentWidth;
  const rightX = center + currentWidth;
  const topY = center - currentHeight * (1 + scaleFactor);    // Maggiore estensione verticale
  const bottomY = center + currentHeight * (1 + scaleFactor); // Maggiore estensione verticale
  
  // Curve di Bézier più dinamiche
  const topCurve = `
    M ${leftX} ${center}
    C ${leftX + currentWidth * 0.2} ${topY},
      ${rightX - currentWidth * 0.2} ${topY},
      ${rightX} ${center}
  `.trim();
  
  const bottomCurve = `
    M ${leftX} ${center}
    C ${leftX + currentWidth * 0.2} ${bottomY},
      ${rightX - currentWidth * 0.2} ${bottomY},
      ${rightX} ${center}
  `.trim();

  return (
    <svg 
      width={size} 
      height={size} 
      className={`audio-visualizer ${isActive ? 'active' : ''}`}
      viewBox={`0 0 ${size} ${size}`}
    >
      <path 
        d={topCurve} 
        className="curve top-curve" 
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path 
        d={bottomCurve} 
        className="curve bottom-curve" 
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
