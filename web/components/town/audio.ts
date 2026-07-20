// Tiny synthesized sound module — no asset files (CSP-safe). Everything is
// gated behind `enabled` (default OFF); toggle() must be called from a user
// gesture (the mute button) so the browser's autoplay policy lets audio start.
class TownAudio {
  enabled = false;
  private ctx?: AudioContext;
  private ambient?: () => void;   // stops the ambient pad
  private lastStep = 0;

  private ensure(): AudioContext {
    if (!this.ctx) this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    return this.ctx;
  }

  /** Flip mute. Returns the new enabled state. Call from a click handler. */
  toggle(): boolean {
    this.enabled = !this.enabled;
    if (this.enabled) { this.ensure().resume(); this.startAmbient(); }
    else this.stopAmbient();
    return this.enabled;
  }

  private blip(freq: number, dur: number, type: OscillatorType, gain: number) {
    if (!this.enabled || !this.ctx) return;
    const c = this.ctx, t = c.currentTime;
    const o = c.createOscillator(), g = c.createGain();
    o.type = type; o.frequency.value = freq;
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(c.destination); o.start(t); o.stop(t + dur);
  }

  click() { this.blip(620, 0.06, "square", 0.05); }
  chime() { this.blip(880, 0.16, "triangle", 0.06); setTimeout(() => this.blip(1180, 0.2, "triangle", 0.05), 90); }

  /** Footsteps self-throttle: call every frame while someone walks. */
  step(now: number) {
    if (!this.enabled || now - this.lastStep < 260) return;
    this.lastStep = now;
    this.blip(150 + Math.random() * 30, 0.05, "triangle", 0.03);
  }

  private startAmbient() {
    const c = this.ensure();
    const g = c.createGain(); g.gain.value = 0.018; g.connect(c.destination);
    const lp = c.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 700; lp.connect(g);
    const oscs = [110, 164.8, 220].map((f, i) => {
      const o = c.createOscillator(); o.type = "sine"; o.frequency.value = f;
      o.detune.value = i * 4; o.connect(lp); o.start(); return o;
    });
    // slow breathing on the pad
    const lfo = c.createOscillator(), lg = c.createGain();
    lfo.frequency.value = 0.06; lg.gain.value = 0.01; lfo.connect(lg).connect(g.gain); lfo.start();
    this.ambient = () => { oscs.forEach((o) => o.stop()); lfo.stop(); };
  }
  private stopAmbient() { this.ambient?.(); this.ambient = undefined; }
}

export const audio = new TownAudio();
