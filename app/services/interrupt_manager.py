import time

class InterruptManager:
    def __init__(self):
        self.cancel_current_tts = False
        self.user_active = False
        self.immune_until = 0

    def on_user_speech(self):
        """Called when Sensory Layer validates user speech."""
        now = time.time()
        # Constraints: 600ms immunity window after AI starts speaking
        if now < self.immune_until:
            return False
            
        if not self.user_active:
            print(" USER BARGE-IN: ABORT SIGNAL SENT")
            self.user_active = True
            # Constraints: Abort Gemini generation safely and stop synthesis
            self.cancel_current_tts = True
            return True
        return False

    def on_silence(self):
        """Called when sustained silence is detected to reset state."""
        if self.user_active:
            self.user_active = False

    def reset_interrupt(self):
        """Called at the start of every AI response turn."""
        self.cancel_current_tts = False
        # Constraints: Set immunity window to prevent self-interruption (echo)
        self.immune_until = time.time() + 0.6
        print(f" IMMUNITY ACTIVE (600ms)")

# Single Global Instance for Stage W4
interrupt_manager = InterruptManager()
