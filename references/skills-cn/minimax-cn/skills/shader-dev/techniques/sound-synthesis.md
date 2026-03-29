**重要 - GLSL ES 3.00 关键规则**：
1. **类型严格**：`int`和`float`不能直接混合；数组索引必须是“int”类型
2. **保留字**：`sample`是GLSL ES 3.00中的保留字；它不能用作变量名
3. **常量数组**：声明时必须显式指定大小，例如 `const float ARR[4] = float[4](1.,2.,3.,4.);`
4. **整数除法**：在 GLSL ES 3.00 中，`1/2` 计算结果为 0（整数除法）；必须使用 `1.0/2.0` 或 `float(1)/float(2)`

# 声音合成（程序音频）

## 用例
- 在 ShaderToy 中使用“mainSound()”生成程序音频
- 合成旋律、和弦、节奏模式和完整的音乐
- 合成乐器音色：钢琴、贝斯、酸合成器、打击乐
- 实现音频效果：延迟、混响、失真、滤波器
- 纯数学音频生成，无需外部样本

## 核心原则

ShaderToy声音着色器四层架构：

1. **振荡器层**：`sin(2π·f·t)`，分层谐波或FM调制来构建音色
2. **包络层**：`exp(-rate·t)` + `smoothstep`攻击，模拟打击→衰变
3. **音序器层**：用于安排旋律的宏定义/数组查找/散列伪随机
4. **效果层**：混响、延迟、失真、滤波器等后处理

关键公式：
- MIDI → 频率：`f = 440.0 × 2^((n - 69) / 12)`
- 正弦振荡器：`y = sin(2π × freq × time)`
- 指数衰减：`env = exp(-decay_rate × time)`
- FM 调制：`y = sin(2π × f_c × t + 深度 × sin(2π × f_m × t))`

## 实施步骤

### 步骤1：mainSound入口框架```glsl
#define TAU 6.28318530718
#define BPM 120.0
#define SPB (60.0 / BPM)

vec2 mainSound(int samp, float time) {
    vec2 audio = vec2(0.0);
    // Layer each instrument/track
    audio *= 0.5 * smoothstep(0.0, 0.5, time);  // Master volume + pop prevention
    return clamp(audio, -1.0, 1.0);
}
```### 步骤 2：MIDI 频率音符```glsl
float noteFreq(float note) {
    return 440.0 * pow(2.0, (note - 69.0) / 12.0);
}
```### 第 3 步：基本振荡器```glsl
float osc_sin(float t) { return sin(TAU * t); }
float osc_saw(float t) { return fract(t) * 2.0 - 1.0; }
float osc_sqr(float t) { return step(fract(t), 0.5) * 2.0 - 1.0; }
float osc_tri(float t) { return abs(fract(t) - 0.5) * 4.0 - 1.0; }
```### 步骤 4：加成合成仪器```glsl
// Layer harmonics to build timbre; higher harmonics decay faster
float instrument_additive(float freq, float t) {
    float y = 0.0;
    y += 0.50 * sin(TAU * 1.00 * freq * t) * exp(-0.0015 * 1.0 * freq * t);
    y += 0.30 * sin(TAU * 2.01 * freq * t) * exp(-0.0015 * 2.0 * freq * t);
    y += 0.20 * sin(TAU * 4.01 * freq * t) * exp(-0.0015 * 4.0 * freq * t);
    y += 0.1 * y * y * y;                          // Nonlinear waveshaping
    y *= 0.9 + 0.1 * cos(40.0 * t);                // Tremolo
    y *= smoothstep(0.0, 0.01, t);                  // Smooth attack
    return y;
}
```### 步骤 5：FM 合成仪器```glsl
// FM electric piano (stereo)
vec2 fm_epiano(float freq, float t) {
    vec2 f0 = vec2(freq * 0.998, freq * 1.002);    // Stereo micro-detuning
    // "Glass" layer - high-frequency FM, metallic attack
    vec2 glass = sin(TAU * (f0 + 3.0) * t
        + sin(TAU * 14.0 * f0 * t) * exp(-30.0 * t)
    ) * exp(-4.0 * t);
    glass = sin(glass);
    // "Body" layer - low-frequency FM, warm sustained tone
    vec2 body = sin(TAU * f0 * t
        + sin(TAU * f0 * t) * exp(-0.5 * t) * pow(440.0 / f0.x, 0.5)
    ) * exp(-t);
    return (glass + body) * smoothstep(0.0, 0.001, t) * 0.1;
}

// FM generic instrument (struct parameterized)
struct Instr {
    float att, fo, vibe, vphas, phas, dtun;
};

float fm_instrument(float freq, float t, float beatTime, Instr ins) {
    float f = freq - beatTime * ins.dtun;
    float phase = f * t * TAU;
    float vibrato = cos(beatTime * ins.vibe * 3.14159 / 8.0 + ins.vphas * 1.5708);
    float fm = sin(phase + vibrato * sin(phase * ins.phas));
    float env = exp(-beatTime * ins.fo) * (1.0 - exp(-beatTime * ins.att));
    return fm * env * (1.0 - beatTime * 0.125);
}
```### 步骤 6：打击乐合成```glsl
float hash(float p) {
    p = fract(p * 0.1031); p *= p + 33.33; p *= p + p; return fract(p);
}

// 909 kick drum: frequency sweep + noise click
float kick(float t) {
    float phase = TAU * (60.0 * t - 512.0 * 0.01 * exp(-t / 0.01));
    float body = sin(phase) * smoothstep(0.3, 0.0, t) * 1.5;
    float click = sin(TAU * 8000.0 * fract(t)) * hash(t * 2000.0)
                * smoothstep(0.007, 0.0, t);
    return body + click;
}

// Hi-hat: noise + exponential decay. decay: 5.0=open, 15.0=closed
float hihat(float t, float decay) {
    float noise = hash(floor(t * 44100.0)) * 2.0 - 1.0;
    return noise * exp(-decay * t) * smoothstep(0.0, 0.02, t);
}

// Clap/snare
float clap(float t) {
    float noise = hash(floor(t * 44100.0)) * 2.0 - 1.0;
    return noise * smoothstep(0.1, 0.0, t);
}
```### 步骤 7：音符顺序排列```glsl
// === Method A: D() macro accumulation (good for handwritten melodies) ===
#define D(duration, note) b += float(duration); if(t > b) { x = b; n = float(note); }

float melody_macro(float time) {
    float t = time / 0.18;
    float n = 0.0, b = 0.0, x = 0.0;
    D(10,71) D(2,76) D(3,79) D(1,78) D(2,76) D(4,83) D(2,81) D(6,78)
    float freq = noteFreq(n);
    float noteTime = 0.18 * (t - x);
    return instrument_additive(freq, noteTime);
}

// === Method B: Array lookup (good for complex arrangements) ===
// NOTE: Array indices must be int type in GLSL ES 3.00
const float NOTES[16] = float[16](
    60., 62., 64., 65., 67., 69., 71., 72.,
    60., 64., 67., 72., 65., 69., 64., 60.
);

float melody_array(float time, float bpm) {
    float beat = time * bpm / 60.0;
    int idx = int(mod(beat, 16.0));  // IMPORTANT: Must use int() conversion
    float noteTime = fract(beat);
    float freq = noteFreq(NOTES[idx]);
    return instrument_additive(freq, noteTime * 60.0 / bpm);
}

// === Method C: Hash pseudo-random (good for algorithmic composition) ===
float nse(float x) { return fract(sin(x * 110.082) * 19871.8972); }

float scale_filter(float note) {
    float n2 = mod(note, 12.0);
    if (n2==1.||n2==3.||n2==6.||n2==8.||n2==10.) return -100.0;
    return note;
}

float melody_random(float time, float bpm) {
    float beat = time * bpm / 60.0;
    float note = 48.0 + floor(nse(floor(beat)) * 24.0);
    note = scale_filter(note);
    return instrument_additive(noteFreq(note), fract(beat) * 60.0 / bpm);
}
```### 步骤 8：和弦构造```glsl
vec2 chord(float time, float root, float isMinor) {
    vec2 result = vec2(0.0);
    float bass = root - 24.0;
    result += fm_epiano(noteFreq(bass), time, 2.0);
    result += fm_epiano(noteFreq(root), time - SPB * 0.5, 1.25);
    result += fm_epiano(noteFreq(root + 4.0 - isMinor), time - SPB, 1.5);  // Third
    result += fm_epiano(noteFreq(root + 7.0), time - SPB * 0.5, 1.25);     // Fifth
    result += fm_epiano(noteFreq(root + 11.0 - isMinor), time - SPB, 1.5); // Seventh
    result += fm_epiano(noteFreq(root + 14.0), time - SPB, 1.5);           // Ninth
    return result;
}
```### 步骤 9：延迟和混响```glsl
// Multi-tap echo
// NOTE: "sample" is a reserved word in GLSL ES 3.00; use "samp" instead
vec2 echo_reverb(float time) {
    vec2 tot = vec2(0.0);
    float hh = 1.0;
    for (int i = 0; i < 6; i++) {
        float h = float(i) / 5.0;
        float samp = get_instrument_sample(time - 0.7 * h);
        tot += samp * vec2(0.5 + 0.1 * h, 0.5 - 0.1 * h) * hh;
        hh *= 0.5;
    }
    return tot;
}

// Ping-pong stereo delay
vec2 pingpong_delay(float time) {
    vec2 mx = get_stereo_sample(time) * 0.5;
    float ec = 0.4, fb = 0.6, dt = 0.222;
    float et = dt;
    mx += get_stereo_sample(time - et) * ec * vec2(1.0, 0.5); ec *= fb; et += dt;
    mx += get_stereo_sample(time - et) * ec * vec2(0.5, 1.0); ec *= fb; et += dt;
    mx += get_stereo_sample(time - et) * ec * vec2(1.0, 0.5); ec *= fb; et += dt;
    mx += get_stereo_sample(time - et) * ec * vec2(0.5, 1.0); ec *= fb; et += dt;
    return mx;
}
```### 步骤 10：节拍和编曲结构```glsl
vec2 mainSound(int samp, float time) {
    vec2 audio = vec2(0.0);
    float beat = time * BPM / 60.0;
    float bar = beat / 4.0;

    // Kick (every beat) + hi-hat (every half beat) + melody
    float kickTime = mod(time, SPB);
    audio += vec2(kick(kickTime) * 0.5);
    float hatTime = mod(time, SPB * 0.5);
    audio += vec2(hihat(hatTime, 15.0) * 0.15);
    audio += vec2(melody_array(time, BPM)) * 0.3;

    // Arrangement: smoothstep controls intro/outro
    audio *= smoothstep(0.0, 4.0, bar);              // Fade in over first 4 bars
    audio *= 0.35 * smoothstep(0.0, 0.5, time);
    // IMPORTANT: Array indices must be int type
    // float idx = mod(beat, 16.0);        // WRONG: float cannot be used as index
    int idx = int(mod(beat, 16.0));       // CORRECT: int(mod(...)) conversion
    return clamp(audio, -1.0, 1.0);
}
```## 完整的代码模板

可以直接粘贴到ShaderToy Sound选项卡中运行。包括 FM 钢琴旋律、底鼓节奏和乒乓延迟。```glsl
// === Sound Synthesis Complete Template ===
#define TAU 6.28318530718
#define BPM 130.0
#define SPB (60.0 / BPM)
#define NUM_HARMONICS 4
#define ECHO_TAPS 4
#define ECHO_DELAY 0.18
#define ECHO_DECAY 0.45

float noteFreq(float note) {
    return 440.0 * pow(2.0, (note - 69.0) / 12.0);
}

float hash11(float p) {
    p = fract(p * 0.1031); p *= p + 33.33; p *= p + p; return fract(p);
}

float osc_tri(float t) { return abs(fract(t) - 0.5) * 4.0 - 1.0; }

float instrument(float freq, float t) {
    float y = 0.0;
    for (int i = 1; i <= NUM_HARMONICS; i++) {
        float h = float(i);
        float amp = 0.6 / h;
        float decay = 0.002 * h * freq;
        y += amp * sin(TAU * h * 1.003 * freq * t) * exp(-decay * t);
    }
    y += 0.15 * y * y * y;
    y *= 0.9 + 0.1 * cos(35.0 * t);
    y *= smoothstep(0.0, 0.008, t);
    return y;
}

vec2 epiano(float freq, float t) {
    vec2 f0 = vec2(freq * 0.998, freq * 1.002);
    vec2 glass = sin(TAU * (f0 + 3.0) * t
        + sin(TAU * 14.0 * f0 * t) * exp(-30.0 * t)
    ) * exp(-4.0 * t);
    glass = sin(glass);
    vec2 body = sin(TAU * f0 * t
        + sin(TAU * f0 * t) * exp(-0.5 * t) * pow(440.0 / max(f0.x, 1.0), 0.5)
    ) * exp(-t);
    return (glass + body) * smoothstep(0.0, 0.001, t) * 0.12;
}

float kick(float t) {
    float df = 512.0, dftime = 0.01, freq = 60.0;
    float phase = TAU * (freq * t - df * dftime * exp(-t / dftime));
    float body = sin(phase) * smoothstep(0.3, 0.0, t) * 1.5;
    float click = sin(TAU * 8000.0 * fract(t)) * hash11(t * 2048.0)
                * smoothstep(0.007, 0.0, t);
    return body + click;
}

float hihat(float t) {
    float noise = hash11(floor(t * 44100.0)) * 2.0 - 1.0;
    return noise * exp(-15.0 * t) * smoothstep(0.0, 0.002, t);
}

const float MELODY[16] = float[16](
    67., 67., 72., 71.,  69., 67., 64., 64.,
    65., 65., 69., 67.,  67., 65., 64., 62.
);

const float BASS[4] = float[4](43., 48., 45., 41.);

vec2 mainSound(int samp, float time) {
    time = mod(time, 32.0 * SPB * 4.0);
    vec2 audio = vec2(0.0);
    float beat = time / SPB;
    float bar = beat / 4.0;

    // Melody
    { int idx = int(mod(beat, 16.0));
      float noteTime = fract(beat) * SPB;
      audio += vec2(instrument(noteFreq(MELODY[idx]), noteTime) * 0.25); }

    // Bass
    { int idx = int(mod(bar, 4.0));
      float noteTime = fract(bar) * SPB * 4.0;
      float freq = noteFreq(BASS[idx]);
      audio += vec2(osc_tri(freq * noteTime) * exp(-1.5 * noteTime)
                   * smoothstep(0.0, 0.01, noteTime) * 0.3); }

    // Kick (every beat) + sidechain compression
    { float kt = mod(time, SPB);
      float k = kick(kt) * 0.4;
      audio *= min(1.0, kt * 6.0 / SPB);
      audio += vec2(k); }

    // Hi-hat (every half beat, panned right)
    { float ht = mod(time, SPB * 0.5);
      audio += vec2(0.4, 0.6) * hihat(ht) * 0.12; }

    // Ping-pong delay (melody)
    { float ec = 0.3;
      for (int i = 1; i <= ECHO_TAPS; i++) {
        float dt = ECHO_DELAY * float(i);
        int idx = int(mod((time - dt) / SPB, 16.0));
        float nt = fract((time - dt) / SPB) * SPB;
        float echoed = instrument(noteFreq(MELODY[idx]), nt) * 0.25 * ec;
        if (i % 2 == 0) audio += vec2(0.3, 1.0) * echoed;
        else             audio += vec2(1.0, 0.3) * echoed;
        ec *= ECHO_DECAY;
      } }

    audio *= 0.4 * smoothstep(0.0, 2.0, time);
    return clamp(audio, -1.0, 1.0);
}
```## 常见变体

### 变体 1：减法合成 / TB-303 酸合成
锯齿波通过谐振低通滤波器，截止频率经包络调制，产生“哇”的声音。```glsl
#define NSPC 128
float lpf_response(float h, float cutoff, float reso) {
    cutoff -= 20.0;
    float df = max(h - cutoff, 0.0);
    float df2 = abs(h - cutoff);
    return exp(-0.005 * df * df) * 0.5 + exp(df2 * df2 * -0.1) * reso;
}

vec2 acid_synth(float freq, float noteTime) {
    vec2 v = vec2(0.0);
    float cutoff = exp(noteTime * -1.5) * 50.0 + 10.0;
    float sqr = step(0.5, fract(noteTime * 4.5));
    for (int i = 0; i < NSPC; i++) {
        float h = float(i + 1);
        float inten = 1.0 / h;
        inten = mix(inten, inten * mod(h, 2.0), sqr);
        inten *= lpf_response(h, cutoff, 2.2);
        v.x += inten * sin((TAU + 0.01) * noteTime * freq * h);
        v.y += inten * sin(TAU * noteTime * freq * h);
    }
    float amp = smoothstep(0.05, 0.0, abs(noteTime - 0.31) - 0.26) * exp(noteTime * -1.0);
    return clamp(v * amp * 2.0, -1.0, 1.0);
}
```### 变体 2：IIR 双二阶滤波器
基于Audio EQ Cookbook的时域IIR滤波器，支持低通/高通/带通等7种类型。```glsl
float waveSaw(float freq, int samp) {
    return fract(freq * float(samp) / iSampleRate) * 2.0 - 1.0;
}

vec2 widerSaw(float freq, int samp) {
    int offset = int(freq) * 64;
    return vec2(waveSaw(freq, samp - offset), waveSaw(freq, samp + offset));
}

void biquadLPF(float freq, float Q, float sr,
    out float b0, out float b1, out float b2,
    out float a0, out float a1, out float a2) {
    float omega = TAU * freq / sr;
    float sn = sin(omega), cs = cos(omega);
    float alpha = sn / (2.0 * Q);
    b0 = (1.0 - cs) * 0.5; b1 = 1.0 - cs; b2 = (1.0 - cs) * 0.5;
    a0 = 1.0 + alpha; a1 = -2.0 * cs; a2 = 1.0 - alpha;
}
```### 变体 3：人声/共振峰合成
通过共振峰频率和带宽合成元音来模拟人声的声道模型。```glsl
float tract(float x, float formantFreq, float bandwidth) {
    return sin(TAU * formantFreq * x) * exp(-bandwidth * 3.14159 * x);
}

float vowel_aah(float t, float pitch) {
    float x = mod(t, 1.0 / pitch);
    float aud = tract(x, 710.0, 70.0) * 0.5     // F1
              + tract(x, 1000.0, 90.0) * 0.6     // F2
              + tract(x, 2450.0, 140.0) * 0.4;   // F3
    return aud;
}

float fricative(float t, float formantFreq) {
    return (hash11(floor(formantFreq * t) * 20.0) - 0.5) * 3.0;
}
```### 变体 4：算法组合
哈希伪随机旋律+音阶量化，多层节奏细分产生分形音乐结构。```glsl
vec2 noteRing(float n) {
    float r = 0.5 + 0.5 * fract(sin(mod(floor(n), 32.123) * 32.123) * 41.123);
    n = mod(n, 8.0);
    float note = n<1.?0. : n<2.?5. : n<3.?-2. : n<4.?4. : n<5.?7. : n<6.?4. : n<7.?2. : 0.;
    return vec2(note, r);
}

vec2 generativeNote(float beat) {
    float b2 = floor(beat * 0.25);
    return noteRing(b2 * 0.0625) + noteRing(b2 * 0.25) + noteRing(b2);
}
```### 变体 5：五度圈和弦进行
根据五度音圈自动生成和声，每 4 个节拍前进 +7 个半音，交替大/小和弦。```glsl
vec2 mainSound(int samp, float time) {
    float id = floor(time / SPB / 4.0);
    float offset = id * 7.0;
    float minor = mod(id, 4.0) >= 3.0 ? 1.0 : 0.0;
    float t = mod(time, SPB * 4.0);
    float root = 57.0 + mod(offset, 12.0);
    vec2 result = chord(t, root, minor);
    result += vec2(0.5, 0.2) * chord(t - SPB * 0.5, root, minor);
    result += vec2(0.05, 0.1) * chord(t - SPB, root, minor);
    return result;
}
```## 表演与作曲

**性能提示：**
- 谐波计数（`NUM_HARMONICS`/`NSPC`）是最大的瓶颈；从4-8开始，足够时停止
- IIR 滤波器需要循环遍历每个输出样本的样本历史记录；更喜欢频域方法
- 每个延迟抽头都需要重新计算整个信号链； 4 次点击 = 5 倍计算
- `fract(x)` 比 `mod(x, 1.0)` 更快；将常量提升出循环
- 使用Common Pass共享常量；避免声音和图像之间的冗余计算

**构图技巧：**
- **音频可视化**：通过图像着色器中的“iChannel0”读取声音输出以进行频谱显示
- **Raymarching 同步**：Common Pass 定义共享时间线；声音/图像同步引用
- **粒子系统**：使用踢触发器来驱动粒子发射；共享 BPM/SPB 以进行节拍位置计算
- **后处理联动**：侧链压缩系数通过 Common Pass 驱动光晕/色差/抖动
- **文本叠加**：图像着色器中的`message()`渲染参数显示或交互指令

## 进一步阅读

有关完整的分步教程、数学推导和高级用法，请参阅 [参考](../reference/sound-synthesis.md)