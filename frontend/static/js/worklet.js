class Recorder extends AudioWorkletProcessor {
    constructor() {
        super();
        // Constraints: 16000 Hz, Mono, 32ms frames (512 samples)
        // This perfectly matches Silero VAD requirements
        this.buffer = new Int16Array(512);
        this.offset = 0;
    }

    process(inputs) {
        const input = inputs[0][0]; // Mono stream
        if (input) {
            for (let i = 0; i < input.length; i++) {
                // Constraints: Float32 -> Int16 PCM Conversion
                const s = Math.max(-1, Math.min(1, input[i]));
                this.buffer[this.offset++] = s < 0 ? s * 0x8000 : s * 0x7FFF;

                if (this.offset >= 512) {
                    // Send 32ms frame to Backend
                    this.port.postMessage(this.buffer.buffer);
                    this.buffer = new Int16Array(512);
                    this.offset = 0;
                }
            }
        }
        return true;
    }
}

registerProcessor('recorder', Recorder);
