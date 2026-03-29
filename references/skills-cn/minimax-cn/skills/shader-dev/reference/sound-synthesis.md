# 声音合成——详细参考

本文档是对[SKILL.md](SKILL.md)的完整参考补充，涵盖先决条件、每个步骤的详细解释、深入的变体描述、性能优化分析以及完整的组合代码示例。

## 先决条件

- **GLSL 基础知识**：函数、向量运算、`float`/`vec2` 类型、数学函数，如 `sin()`/`exp()`/`fract()`
- **音频基础知识**：采样率（通常为 44100Hz）、频率与音高关系、波形概念（正弦波、锯齿波、方波）
- **音乐理论基础**：MIDI 音符编号、平均律、八度关系（双频）、和弦结构
- **ShaderToy 声音模式**：`vec2 mainSound(int samp, float time)` 返回范围为 `[-1, 1]` 的 `vec2` 立体声样本值

## 实施步骤

### 步骤1：mainSound入口点和基本框架

**什么**：建立声音着色器的标准入口函数，输出立体声信号。

**为什么**：ShaderToy 需要固定签名`vec2 mainSound(int samp, float time)`，其中返回值的`.x`和`.y`分别是左声道和右声道，范围为`[-1, 1]`。 `samp` 是样本索引，`time` 是对应的时间（以秒为单位）。```glsl
// ShaderToy sound shader basic framework
#define TAU 6.28318530718
#define BPM 120.0                    // Adjustable: tempo
#define SPB (60.0 / BPM)             // Seconds per beat

vec2 mainSound(int samp, float time) {
    vec2 audio = vec2(0.0);

    // Layer instruments/tracks here
    // audio += instrument(time);

    // Master volume control + anti-click fade-in
    audio *= 0.5 * smoothstep(0.0, 0.5, time);

    return clamp(audio, -1.0, 1.0);
}
```### 步骤 2：MIDI 音符到频率转换

**什么**：将 MIDI 音符编号转换为其相应的频率值。

**为什么**：在平均律中，每升高一个半音，频率就会乘以`2^(1/12)`。 MIDI 69 = A4 = 440Hz 是标准参考点。这是所有旋律合成的基础。```glsl
// MIDI note number to frequency
// 69 = A4 = 440Hz, every +12 is one octave (frequency doubles)
float noteFreq(float note) {
    return 440.0 * pow(2.0, (note - 69.0) / 12.0);
}
```### 第 3 步：基本振荡器

**内容**：实现四种标准波形发生器 - 正弦波、锯齿波、方波和三角波。

**为什么**：不同的波形有不同的谐波特性。正弦波是纯净的（仅基波），锯齿波富含所有谐波（明亮），方波仅包含奇次谐波（空心），三角波具有更快的谐波衰减（柔和）。这四个是所有音色合成的构建块。```glsl
// Sine wave - pure tone, fundamental only
float osc_sin(float t) {
    return sin(TAU * t);
}

// Sawtooth wave - contains all harmonics, bright and sharp
float osc_saw(float t) {
    return fract(t) * 2.0 - 1.0;
}

// Square wave - odd harmonics only, hollow texture
float osc_sqr(float t) {
    return step(fract(t), 0.5) * 2.0 - 1.0;
}

// Triangle wave - fast harmonic decay, soft and warm
float osc_tri(float t) {
    return abs(fract(t) - 0.5) * 4.0 - 1.0;
}
```### 步骤 4：加成合成仪器

**什么**：通过分层多个谐波（基波的整数倍）构建音色，每个谐波具有独立的幅度和衰减率。

**为什么**：真实乐器的音色是由其谐波含量（频谱）决定的。将 3-8 个谐波分层，较高谐波的衰减速度更快，可以模拟钢琴、铃声和其他音色。这是加法音色合成的核心技术。```glsl
// Additive synthesis instrument
// freq: fundamental frequency, t: time within note
// Additive synthesis with harmonic layering
float instrument_additive(float freq, float t) {
    float y = 0.0;

    // Layer harmonics: fundamental × 1, 2, 4
    // Decreasing amplitude + frequency-dependent decay (higher harmonics decay faster)
    y += 0.50 * sin(TAU * 1.00 * freq * t) * exp(-0.0015 * 1.0 * freq * t);
    y += 0.30 * sin(TAU * 2.01 * freq * t) * exp(-0.0015 * 2.0 * freq * t);
    y += 0.20 * sin(TAU * 4.01 * freq * t) * exp(-0.0015 * 4.0 * freq * t);

    // Nonlinear waveshaping to enrich harmonics
    y += 0.1 * y * y * y;                          // Adjustable: 0.0-0.35, higher = more distortion

    // Tremolo
    y *= 0.9 + 0.1 * cos(40.0 * t);                // Adjustable: 40.0 = tremolo frequency

    // Smooth attack to avoid clicks
    y *= smoothstep(0.0, 0.01, t);                  // Adjustable: 0.01 = attack time

    return y;
}
```### 步骤 5：FM 合成仪器

**什么**：使用一个振荡器（调制器）的输出作为另一个振荡器（载波）的相位偏移来产生丰富的谐波。

**为什么**：FM 合成可以用很少的振荡器产生极其丰富的音色。随着时间的推移改变调制深度可以模拟仪器的“亮→暗”衰减特性。电钢琴和类似西塔琴的音色都是基于这个原理。```glsl
// FM synthesis electric piano
// FM electric piano synthesis
vec2 fm_epiano(float freq, float t) {
    // Stereo micro-detuning for chorus effect
    vec2 f0 = vec2(freq * 0.998, freq * 1.002);    // Adjustable: detune amount

    // "Glass" layer - high-frequency FM, fast decay → metallic attack quality
    vec2 glass = sin(TAU * (f0 + 3.0) * t
        + sin(TAU * 14.0 * f0 * t) * exp(-30.0 * t)  // Adjustable: 14.0=mod ratio, -30.0=mod decay
    ) * exp(-4.0 * t);                                 // Adjustable: -4.0 = glass layer decay
    glass = sin(glass);                                 // Second-order nonlinearity

    // "Body" layer - low-frequency FM, slow decay → sustained warm tone
    vec2 body = sin(TAU * f0 * t
        + sin(TAU * f0 * t) * exp(-0.5 * t) * pow(440.0 / f0.x, 0.5)  // Low-frequency compensation
    ) * exp(-t);                                        // Adjustable: -1.0 = body decay

    return (glass + body) * smoothstep(0.0, 0.001, t) * 0.1;
}

// FM synthesis generic instrument (struct-parameterized)
// FM synthesis generic instrument (struct-parameterized)
struct Instr {
    float att;      // Attack speed (higher = faster)
    float fo;       // Decay rate
    float vibe;     // Vibrato speed
    float vphas;    // Vibrato phase
    float phas;     // FM modulation depth
    float dtun;     // Detune amount
};

float fm_instrument(float freq, float t, float beatTime, Instr ins) {
    float f = freq - beatTime * ins.dtun;
    float phase = f * t * TAU;
    float vibrato = cos(beatTime * ins.vibe * 3.14159 / 8.0 + ins.vphas * 1.5708);
    float fm = sin(phase + vibrato * sin(phase * ins.phas));
    float env = exp(-beatTime * ins.fo) * (1.0 - exp(-beatTime * ins.att));
    return fm * env * (1.0 - beatTime * 0.125);
}
```### 步骤 6：打击乐合成

**内容**：合成底鼓、军鼓/拍手和踩镲打击乐器。

**为什么**：打击乐通常由具有快速包络的音高扫频（底鼓）或噪声脉冲（踩镲/拍手）组成。底鼓的核心是从高频到低频的正弦扫描；踩镲是指数衰减的噪音。几乎所有完整的音乐着色器都需要这些。```glsl
// Pseudo-random hash (replaces noise texture)
float hash(float p) {
    p = fract(p * 0.1031);
    p *= p + 33.33;
    p *= p + p;
    return fract(p);
}

// 909-style kick drum
// 909-style kick drum synthesis
float kick(float t) {
    float df = 512.0;                               // Adjustable: frequency sweep depth
    float dftime = 0.01;                             // Adjustable: sweep time constant
    float freq = 60.0;                               // Adjustable: base frequency

    // Exponential frequency sweep: rapidly slides from high to base frequency
    float phase = TAU * (freq * t - df * dftime * exp(-t / dftime));
    float body = sin(phase) * smoothstep(0.3, 0.0, t) * 1.5;

    // Transient noise click
    float click = sin(TAU * 8000.0 * fract(t)) * hash(t * 2000.0)
                * smoothstep(0.007, 0.0, t);

    return body + click;
}

// Hi-hat (open / closed)
// Hi-hat synthesis (open / closed)
float hihat(float t, float decay) {
    // decay: 5.0 = open hat (long decay), 15.0 = closed hat (short decay)
    float noise = hash(floor(t * 44100.0)) * 2.0 - 1.0;
    return noise * exp(-decay * t) * smoothstep(0.0, 0.02, t);
}

// Clap / snare
float clap(float t) {
    float noise = hash(floor(t * 44100.0)) * 2.0 - 1.0;
    return noise * smoothstep(0.1, 0.0, t);
}
```### 步骤 7：音符顺序排列

**内容**：实现旋律/和弦时间安排，确定每个时刻应播放哪个音符。

**为什么**：音乐=音色×时机。 ShaderToy 具有三种主流编排方式：(A) D()宏累加用于手写旋律，(B) 数组查找用于复杂编排，(C) 哈希伪随机用于算法编排。```glsl
// === Approach A: D() Macro Accumulation ===
// Usage: D(duration, MIDI note number) arranged sequentially
// b = accumulated time, x = current note start time, n = current note
#define D(duration, note) b += float(duration); if(t > b) { x = b; n = float(note); }

float melody_macro(float time) {
    float t = time / 0.18;                          // Adjustable: 0.18 = seconds per unit duration
    float n = 0.0, b = 0.0, x = 0.0;

    D(10,71) D(2,76) D(3,79) D(1,78) D(2,76) D(4,83) D(2,81) D(6,78)
    // ... continue arranging notes ...

    float freq = noteFreq(n);
    float noteTime = 0.18 * (t - x);
    return instrument_additive(freq, noteTime);
}

// === Approach B: Array Lookup ===
const float NOTES[16] = float[16](
    60., 62., 64., 65., 67., 69., 71., 72.,         // Adjustable: note sequence
    60., 64., 67., 72., 65., 69., 64., 60.
);

float melody_array(float time, float bpm) {
    float beat = time * bpm / 60.0;
    int idx = int(mod(beat, 16.0));
    float noteTime = fract(beat);
    float freq = noteFreq(NOTES[idx]);
    return instrument_additive(freq, noteTime * 60.0 / bpm);
}

// === Approach C: Hash Pseudo-Random ===
float nse(float x) {
    return fract(sin(x * 110.082) * 19871.8972);
}

// Scale quantization: filter out dissonant notes
float scale_filter(float note) {
    float n2 = mod(note, 12.0);
    // Major scale: filter out semitones 1,3,6,8,10
    if (n2==1.||n2==3.||n2==6.||n2==8.||n2==10.) return -100.0;
    return note;
}

float melody_random(float time, float bpm) {
    float beat = time * bpm / 60.0;
    float seqn = nse(floor(beat));
    float note = 48.0 + floor(seqn * 24.0);         // Adjustable: 48.0=lowest note, 24.0=range
    note = scale_filter(note);
    float freq = noteFreq(note);
    float noteTime = fract(beat) * 60.0 / bpm;
    return instrument_additive(freq, noteTime);
}
```### 步骤 8：和弦构造

**什么**：根据和弦关系分层多个音符以形成和声。

**为什么**：和弦是同时发声的多个音高的组合。常见的结构是根音+三度+五度（三和弦），并添加了爵士和弦的七度和九度。爵士乐和弦进行可以通过这种方式构建。```glsl
// Chord construction
vec2 chord(float time, float root, float isMinor) {
    vec2 result = vec2(0.0);
    float bass = root - 24.0;                        // Root two octaves lower

    // Root (bass)
    result += fm_epiano(noteFreq(bass), time, 2.0);
    // Root
    result += fm_epiano(noteFreq(root), time - SPB * 0.5, 1.25);
    // Third (major third = 4 semitones, minor third = 3 semitones)
    result += fm_epiano(noteFreq(root + 4.0 - isMinor), time - SPB, 1.5);
    // Fifth
    result += fm_epiano(noteFreq(root + 7.0), time - SPB * 0.5, 1.25);
    // Seventh
    result += fm_epiano(noteFreq(root + 11.0 - isMinor), time - SPB, 1.5);
    // Ninth
    result += fm_epiano(noteFreq(root + 14.0), time - SPB, 1.5);

    return result;
}
```### 步骤 9：延迟和混响效果

**内容**：通过分层音频信号的时间偏移副本来模拟空间回声和混响效果。

**为什么**：干燥的音频听起来“平淡”。多次抽头延迟通过以不同延迟和衰减量分层信号副本来创建空间深度。乒乓延迟在左右声道之间交替弹跳，增强立体声宽度。```glsl
// Multi-tap echo/reverb
// Multi-tap echo/reverb
// NOTE: in GLSL ES 3.00, "sample" is a reserved word — use "samp" instead
vec2 echo_reverb(float time) {
    vec2 tot = vec2(0.0);
    float hh = 1.0;
    for (int i = 0; i < 6; i++) {                   // Adjustable: 6 = echo count
        float h = float(i) / 5.0;
        float delayedTime = time - 0.7 * h;         // Adjustable: 0.7 = echo interval

        // Call your instrument function to get audio at that time point
        float samp = get_instrument_sample(delayedTime);

        // Stereo spread: each echo has different L/R ratio
        tot += samp * vec2(0.5 + 0.1 * h, 0.5 - 0.1 * h) * hh;
        hh *= 0.5;                                   // Adjustable: 0.5 = decay per echo
    }
    return tot;
}

// Ping-pong stereo delay
// Ping-pong stereo delay
vec2 pingpong_delay(float time) {
    vec2 mx = get_stereo_sample(time) * 0.5;
    float ec = 0.4;                                  // Adjustable: initial echo volume
    float fb = 0.6;                                  // Adjustable: feedback decay coefficient
    float delay_time = 0.222;                        // Adjustable: delay time (seconds)
    float et = delay_time;

    // 4 alternating left/right ping-pong taps
    mx += get_stereo_sample(time - et) * ec * vec2(1.0, 0.5); ec *= fb; et += delay_time;
    mx += get_stereo_sample(time - et) * ec * vec2(0.5, 1.0); ec *= fb; et += delay_time;
    mx += get_stereo_sample(time - et) * ec * vec2(1.0, 0.5); ec *= fb; et += delay_time;
    mx += get_stereo_sample(time - et) * ec * vec2(0.5, 1.0); ec *= fb; et += delay_time;

    return mx;
}
```### 步骤 10：节拍和编曲结构

**内容**：使用 BPM 定义时间网格，将不同的乐器安排在不同的节拍位置，并控制整体歌曲结构（前奏、主歌、间奏等）。

**为什么**：音乐的节奏骨架建立在统一的节拍网格上。使用“floor(time * BPM / 60)”获取当前节拍编号，使用“fract()”获取节拍内的位置。 “smoothstep”选通控制仪器在特定部分的进入和退出。```glsl
vec2 mainSound(int samp, float time) {
    vec2 audio = vec2(0.0);

    float beat = time * BPM / 60.0;                  // Current beat count
    float bar = beat / 4.0;                           // Current bar (4/4 time)
    float beatInBar = mod(beat, 4.0);                 // Beat position within bar

    // --- Rhythm layer ---
    // Kick: trigger every beat
    float kickTime = mod(time, SPB);
    audio += vec2(kick(kickTime) * 0.5);

    // Hi-hat: trigger every half beat
    float hatTime = mod(time, SPB * 0.5);
    audio += vec2(hihat(hatTime, 15.0) * 0.15);

    // --- Melody layer ---
    audio += vec2(melody_array(time, BPM)) * 0.3;

    // --- Arrangement automation ---
    // Use smoothstep to control instrument entry/exit
    float introFade = smoothstep(0.0, 4.0, bar);     // Fade in over first 4 bars
    float dropGate = smoothstep(16.0, 16.1, bar);    // Drop at bar 16

    audio *= introFade;

    // Master volume + anti-click
    audio *= 0.35 * smoothstep(0.0, 0.5, time);
    return clamp(audio, -1.0, 1.0);
}
```## 变体详细信息

### 变体 1：减法合成/TB-303 酸合成仪

**与基本版本的区别**：不是通过分层谐波来构建音色，而是生成谐波丰富的波形（锯齿波），然后使用谐振低通滤波器对其进行雕刻以消除高频。滤波器截止频率由包络调制，产生经典的“哇”声。

**关键修改代码**：```glsl
#define NSPC 128                                    // Adjustable: synthesis harmonic count (higher = better quality)

// Resonant low-pass frequency response
float lpf_response(float h, float cutoff, float reso) {
    cutoff -= 20.0;
    float df = max(h - cutoff, 0.0);
    float df2 = abs(h - cutoff);
    return exp(-0.005 * df * df) * 0.5              // Adjustable: -0.005 = rolloff slope
         + exp(df2 * df2 * -0.1) * reso;            // Adjustable: resonance peak
}

// TB-303 acid synthesizer
vec2 acid_synth(float freq, float noteTime) {
    vec2 v = vec2(0.0);
    // Envelope-driven filter cutoff frequency
    float cutoff = exp(noteTime * -1.5) * 50.0      // Adjustable: -1.5=envelope speed, 50.0=sweep range
                 + 10.0;                             // Adjustable: minimum cutoff
    float sqr = step(0.5, fract(noteTime * 4.5));   // Sawtooth/square switching

    for (int i = 0; i < NSPC; i++) {
        float h = float(i + 1);
        float inten = 1.0 / h;                      // Sawtooth spectrum
        inten = mix(inten, inten * mod(h, 2.0), sqr); // Square wave variant
        inten *= lpf_response(h, cutoff, 2.2);
        v.x += inten * sin((TAU + 0.01) * noteTime * freq * h);
        v.y += inten * sin(TAU * noteTime * freq * h);
    }
    float amp = smoothstep(0.05, 0.0, abs(noteTime - 0.31) - 0.26)
              * exp(noteTime * -1.0);
    return clamp(v * amp * 2.0, -1.0, 1.0);
}
```### 变体 2：IIR 双二阶滤波器

**与基本版本的区别**：使用基于 Audio EQ Cookbook 的时域 IIR 滤波器，而不是频域方法。支持 7 种滤波器类型，包括低通、高通、带通、陷波、峰值和搁架，更接近真实硬件。需要维护过去的样本状态。

**关键修改代码**：```glsl
// Sawtooth oscillator (sample-domain, anti-aliasing friendly)
float waveSaw(float freq, int samp) {
    return fract(freq * float(samp) / iSampleRate) * 2.0 - 1.0;
}

// Stereo widening
vec2 widerSaw(float freq, int samp) {
    int offset = int(freq) * 64;                    // Adjustable: 64 = width factor
    return vec2(waveSaw(freq, samp - offset), waveSaw(freq, samp + offset));
}

// Biquad low-pass filter coefficient calculation
void biquadLPF(float freq, float Q, float sr,
    out float b0, out float b1, out float b2,
    out float a0, out float a1, out float a2) {
    float omega = TAU * freq / sr;
    float sn = sin(omega), cs = cos(omega);
    float alpha = sn / (2.0 * Q);                   // Adjustable: Q = resonance (0.5-20)
    b0 = (1.0 - cs) * 0.5;
    b1 = 1.0 - cs;
    b2 = (1.0 - cs) * 0.5;
    a0 = 1.0 + alpha;
    a1 = -2.0 * cs;
    a2 = 1.0 - alpha;
}
```### 变体 3：人声/共振峰合成

**与基础版的区别**：使用正弦波模型来模拟人声。通过设置不同频率的共振峰及其带宽，可以合成元音。辅音是通过摩擦音实现的。

**关键修改代码**：```glsl
// Vocal tract formant model
float tract(float x, float formantFreq, float bandwidth) {
    return sin(TAU * formantFreq * x)
         * exp(-bandwidth * 3.14159 * x);
}

// "Ah" vowel synthesis
float vowel_aah(float t, float pitch) {
    float period = 1.0 / pitch;
    float x = mod(t, period);
    // Formant frequencies and bandwidths (Hz) — adjustable to simulate different vowels
    float aud = tract(x, 710.0, 70.0) * 0.5         // F1: 710Hz ('a' vowel)
              + tract(x, 1000.0, 90.0) * 0.6         // F2: 1000Hz
              + tract(x, 2450.0, 140.0) * 0.4;       // F3: 2450Hz
    return aud;
}

// Fricative consonant noise
float fricative(float t, float formantFreq) {
    return (hash11(floor(formantFreq * t) * 20.0) - 0.5) * 3.0;
}
```### 变体 4：算法作曲（生成音乐）

**与基本版本的区别**：不使用手写笔记序列；相反，使用哈希函数生成伪随机旋律，并通过音阶量化来确保和声一致性。多级节奏细分（1拍/2拍/4拍）产生分形般的音乐结构。

**关键修改代码**：```glsl
// 8-note pseudo-random loop
vec2 noteRing(float n) {
    float r = 0.5 + 0.5 * fract(sin(mod(floor(n), 32.123) * 32.123) * 41.123);
    n = mod(n, 8.0);
    // Adjustable: modify these intervals to change the melodic character
    float note = n<1.?0. : n<2.?5. : n<3.?-2. : n<4.?4. : n<5.?7. : n<6.?4. : n<7.?2. : 0.;
    return vec2(note, r);                            // (interval, volume)
}

// FBM-style layered note generation
vec2 generativeNote(float beat) {
    float b0 = floor(beat);
    float b1 = floor(beat * 0.5);
    float b2 = floor(beat * 0.25);
    // Large-scale + medium-scale + small-scale layering
    vec2 note = noteRing(b2 * 0.0625)
              + noteRing(b2 * 0.25)
              + noteRing(b2);
    return note;
}
```### 变体 5：和弦进行系统（五度圈）

**与基本版本的区别**：根据五度音程自动生成和声进行。每 4 个节拍前进五分之一（+7 个半音），自动将大/小和弦与爵士和弦扩展（第七、第九）交替。

**关键修改代码**：```glsl
vec2 mainSound(int samp, float time) {
    float id = floor(time / SPB / 4.0);             // Current chord number
    float offset = id * 7.0;                         // Circle of fifths: +7 semitones per step
    float minor = mod(id, 4.0) >= 3.0 ? 1.0 : 0.0; // Every 4th chord is minor
    float t = mod(time, SPB * 4.0);

    float root = 57.0 + mod(offset, 12.0);           // Adjustable: 57.0 = starting root (A3)
    vec2 result = chord(t, root, minor);

    // Two-tap ping-pong delay
    result += vec2(0.5, 0.2) * chord(t - SPB * 0.5, root, minor);
    result += vec2(0.05, 0.1) * chord(t - SPB, root, minor);

    return result;
}
```## 性能优化详情

1. **减少谐波计数**：在加法合成和频域滤波器中，谐波计数（`NUM_HARMONICS`/`NSPC`）是最大的性能瓶颈。从 4-8 个和声开始，一旦声音令人满意就不再添加。使用 256 个谐波是一种极端情况。

2. **避免循环中的样本历史**：IIR 滤波器需要处理 128 个历史样本，这意味着每个输出样本需要 128 次循环迭代。首选频域方法或减少“PAST_SAMPLES”。

3. **简化回声/延迟**：每个延迟抽头都需要重新计算完整的信号链。 4 次点击意味着 5 倍计算。考虑降低延迟信号的复杂性（更少的谐波）。

4. **使用 `fract()` 代替 `mod()`**：当除数为 1.0 时，`fract(x)` 比 `mod(x, 1.0)` 更快。

5. **预计算常量**：将循环不变表达式（例如“TAU * freq”）移到循环之外。

6. **使用Common Pass**：将常量定义和共享函数放在ShaderToy的Common选项卡中，声音和图像都可以访问，避免BPM/SPB等的冗余计算。

## 组合建议

### 1. 与音频可视化相结合

声音着色器输出可以通过“iChannel0”在图像着色器中读取（设置为此着色器的声音输出）。使用`texture(iChannel0, vec2(freq, 0.0))`获取频谱数据来驱动视觉效果（波形、频谱条形图等）。

### 2. 与 Raymarching 场景结合

可以通过共享时间线/提示事件来实现声音-视觉同步。在公共通道中定义共享时间线/提示事件，由声音和图像着色器同时引用，确保视音频同步。

### 3. 与粒子系统结合

使用节拍事件（踢触发时刻）来驱动粒子发射。在图像着色器中，使用相同的 BPM/SPB 来计算当前节拍位置，并增加踢动触发时刻的粒子计数或速度。

### 4.与后处理效果结合

通过 Common Pass 与图像着色器共享声音着色器包络值（例如，侧链压缩系数），驱动光晕强度、色移、屏幕抖动和其他效果。

### 5. 与文本/图形叠加相结合

使用图像着色器中的“message()”函数来渲染文本提示、参数显示或交互指令，以帮助用户了解正在播放的内容。