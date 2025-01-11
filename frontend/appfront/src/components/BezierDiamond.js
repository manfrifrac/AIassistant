import React, { useState, useEffect, useMemo, useRef } from 'react';

export function BezierDiamond({ audioLevel, isActive }) {
  const size = 300;
  const centerX = size / 2;
  const centerY = size / 2;
  const maxWidth = 120; // Massima distanza orizzontale
  const maxHeight = 60;

  // Calcoliamo l’apertura orizzontale:
  const horizontal = maxWidth * (1 - Math.min(Math.max(audioLevel, 0), 1));
  const leftX = centerX - horizontal;
  const rightX = centerX + horizontal;

  // L’altezza varia inversamente con l’apertura orizzontale
  const vertical = maxHeight * Math.min(Math.max(audioLevel, 0), 1);
  const topY = centerY - vertical;
  const bottomY = centerY + vertical;

  // Aggiunta di punti di controllo extra per asintoti
  const controlOffset = horizontal * 0.3;

  const pathData = useMemo(() => `
    M ${centerX - horizontal} ${centerY}
    C ${centerX - horizontal} ${centerY - vertical},
      ${centerX + horizontal} ${centerY - vertical},
      ${centerX + horizontal} ${centerY}
    C ${centerX + horizontal} ${centerY + vertical},
      ${centerX - horizontal} ${centerY + vertical},
      ${centerX - horizontal} ${centerY}
    Z
  `.trim(), [audioLevel]);

  return (
    <svg
      width={size}
      height={size}
      className={`audio-visualizer ${isActive ? 'active' : ''}`}
      viewBox={`0 0 ${size} ${size}`}
    >
      <path
        d={pathData}
        className="wave-path"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
