/**
 * Earcon Engine — Web Audio API based non-verbal status sounds.
 * Provides audio feedback without conflicting with screen readers.
 *
 * Aligned with TDD Section 7 (FR-17) and PRD Section 12.7.
 * Target latency: < 15ms
 */

let audioContext: AudioContext | null = null;

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new AudioContext();
  }
  return audioContext;
}

interface EarconOptions {
  frequency: number;
  duration: number;
  type: OscillatorType;
  volume?: number;
}

function playTone({ frequency, duration, type, volume = 0.3 }: EarconOptions): void {
  const ctx = getAudioContext();
  const oscillator = ctx.createOscillator();
  const gainNode = ctx.createGain();

  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);
  gainNode.gain.setValueAtTime(volume, ctx.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

  oscillator.connect(gainNode);
  gainNode.connect(ctx.destination);

  oscillator.start(ctx.currentTime);
  oscillator.stop(ctx.currentTime + duration);
}

/** Short rising tone — recording started */
export function earconRecordStart(): void {
  playTone({ frequency: 440, duration: 0.15, type: 'sine' });
}

/** Short falling tone — recording stopped */
export function earconRecordStop(): void {
  playTone({ frequency: 330, duration: 0.15, type: 'sine' });
}

/** Double beep — response ready */
export function earconResponseReady(): void {
  playTone({ frequency: 660, duration: 0.1, type: 'sine' });
  setTimeout(() => {
    playTone({ frequency: 880, duration: 0.1, type: 'sine' });
  }, 120);
}

/** Low buzzing tone — error */
export function earconError(): void {
  playTone({ frequency: 200, duration: 0.3, type: 'sawtooth', volume: 0.2 });
}

/** Quick tick — action confirmed */
export function earconConfirm(): void {
  playTone({ frequency: 1000, duration: 0.08, type: 'sine', volume: 0.2 });
}
