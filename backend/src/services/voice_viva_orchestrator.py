"""
Voice Infrastructure Pipeline — Stage 6

Deterministic, turn-based voice viva system that:
1. Plays questions via TTS
2. Records student responses via microphone
3. Transcribes speech to text
4. Normalizes technical terminology
5. Detects silence to finalize responses
6. Delivers finalized transcript to MAIN Agent

IMPORTANT: Voice system is infrastructure-only.
MAIN Agent remains the viva examiner brain.
"""

import json
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum


class VoicePhase(str, Enum):
    """Phases of voice interaction in a turn."""

    IDLE = "IDLE"
    PLAYING_QUESTION = "PLAYING_QUESTION"
    QUESTION_PLAYED = "QUESTION_PLAYED"
    LISTENING = "LISTENING"
    RECORDING = "RECORDING"
    SILENCE_DETECTED = "SILENCE_DETECTED"
    TRANSCRIBING = "TRANSCRIBING"
    TRANSCRIPT_READY = "TRANSCRIPT_READY"


class TranscriptNormalizer:
    """
    Normalizes technical terminology in transcribed speech.

    Examples:
    - "redis" → "Redis"
    - "jay pee off" → "JPG"
    - "async" → "async/await"
    - "cache invalidation" → "cache invalidation"
    """

    # Technical term corrections
    TECHNICAL_CORRECTIONS = {
        # Databases
        "postgres": "PostgreSQL",
        "postgre sql": "PostgreSQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        # Languages
        "python": "Python",
        "javascript": "JavaScript",
        "type script": "TypeScript",
        "go": "Go",
        # Frameworks
        "fast api": "FastAPI",
        "django": "Django",
        "react": "React",
        "next dot js": "Next.js",
        # Protocols
        "jay son": "JSON",
        "rest": "REST",
        "graphql": "GraphQL",
        "soap": "SOAP",
        # Common terms
        "async": "async/await",
        "cache invalidation": "cache invalidation",
        "race condition": "race condition",
        "dead lock": "deadlock",
        "jwt": "JWT",
        # Acronyms
        "oh auth": "OAuth",
        "s s l": "SSL",
        "h t t p s": "HTTPS",
        "c r u d": "CRUD",
        "acid": "ACID",
        "solid": "SOLID",
    }

    @staticmethod
    def normalize(transcript: str) -> str:
        """
        Normalize technical terminology in transcript.

        Performs deterministic corrections for common speech-to-text errors
        with technical terms.
        """

        normalized = transcript.lower()

        # Apply technical corrections
        for wrong, correct in TranscriptNormalizer.TECHNICAL_CORRECTIONS.items():
            normalized = normalized.replace(wrong.lower(), correct)

        return normalized

    @staticmethod
    def extract_technical_terms(transcript: str) -> List[str]:
        """Extract identified technical terms from normalized transcript."""

        terms = []

        for term in TranscriptNormalizer.TECHNICAL_CORRECTIONS.values():
            if term.lower() in transcript.lower():
                terms.append(term)

        return list(set(terms))


class SilenceDetector:
    """
    Detects silence in audio stream to determine response finalization.

    Parameters:
    - silence_threshold_ms: Milliseconds of silence to trigger finalization
    - min_response_duration_ms: Minimum response duration before silence ends session
    """

    def __init__(
        self,
        silence_threshold_ms: int = 3000,
        min_response_duration_ms: int = 1000,
        max_response_duration_seconds: int = 120,
    ):
        self.silence_threshold_ms = silence_threshold_ms
        self.min_response_duration_ms = min_response_duration_ms
        self.max_response_duration_seconds = max_response_duration_seconds
        self.recording_start_time: Optional[float] = None
        self.last_sound_time: Optional[float] = None

    def start_recording(self) -> None:
        """Mark recording start."""

        self.recording_start_time = time.time()
        self.last_sound_time = self.recording_start_time

    def should_finalize(self, is_sound_present: bool) -> bool:
        """
        Determine if recording should be finalized.

        Returns True if:
        - Silence exceeded threshold after minimum response duration
        - Maximum response duration exceeded
        """

        if not self.recording_start_time:
            return False

        current_time = time.time()
        elapsed_ms = (current_time - self.recording_start_time) * 1000

        # Max response duration exceeded
        if elapsed_ms > self.max_response_duration_seconds * 1000:
            return True

        # Update last sound time
        if is_sound_present:
            self.last_sound_time = current_time

        # Check silence duration
        if self.last_sound_time:
            silence_duration_ms = (current_time - self.last_sound_time) * 1000

            # If minimum response given and silence exceeded
            if elapsed_ms >= self.min_response_duration_ms and silence_duration_ms >= self.silence_threshold_ms:
                return True

        return False


class TTSProvider:
    """
    Text-to-Speech provider interface.

    Implementations: SystemTTS, GoogleTTS, AzureTTS, etc.
    """

    async def speak(self, text: str, language: str = "en-US") -> Dict[str, Any]:
        """
        Play text as speech.

        Returns:
            {"success": bool, "duration_seconds": float, "audio_path": str}
        """

        raise NotImplementedError()


class SystemTTSProvider(TTSProvider):
    """System TTS using platform-native speech synthesis (say on macOS, etc.)."""

    async def speak(self, text: str, language: str = "en-US") -> Dict[str, Any]:
        """
        Use system TTS to play question.

        On macOS: uses `say` command
        On Linux: uses `espeak` or `festival`
        On Windows: uses SAPI
        """

        import subprocess
        import sys

        try:
            start_time = time.time()

            # Platform-specific TTS command
            if sys.platform == "darwin":  # macOS
                subprocess.run(["say", "-r", "150", text], check=True)
            elif sys.platform == "linux":
                # Try espeak first, fallback to festival
                try:
                    subprocess.run(["espeak", text], check=True)
                except FileNotFoundError:
                    subprocess.run(["festival", "--tts"], input=text.encode(), check=True)
            elif sys.platform == "win32":
                # Windows SAPI
                import pyttsx3

                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()

            duration = time.time() - start_time

            return {
                "success": True,
                "duration_seconds": duration,
                "audio_path": None,
                "provider": "system_tts",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "system_tts",
            }


class STTProvider:
    """
    Speech-to-Text provider interface.

    Implementations: Deepgram, Google Speech-to-Text, Azure, etc.
    """

    async def transcribe(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Transcribe audio to text.

        Returns:
            {"success": bool, "transcript": str, "confidence": float}
        """

        raise NotImplementedError()


class MockSTTProvider(STTProvider):
    """Mock STT for testing (returns pre-configured responses)."""

    def __init__(self):
        self.mock_responses = []
        self.response_index = 0

    def add_mock_response(self, transcript: str, confidence: float = 0.95):
        """Add a mock response for testing."""

        self.mock_responses.append({"transcript": transcript, "confidence": confidence})

    async def transcribe(self, audio_data: bytes) -> Dict[str, Any]:
        """Return next mock response."""

        if self.response_index < len(self.mock_responses):
            response = self.mock_responses[self.response_index]
            self.response_index += 1
            return {
                "success": True,
                "transcript": response["transcript"],
                "confidence": response["confidence"],
                "provider": "mock_stt",
            }

        return {
            "success": False,
            "error": "No more mock responses",
            "provider": "mock_stt",
        }


class VoiceSessionOrchestrator:
    """
    Orchestrates a single voice turn: question → playback → listen → transcribe.

    Deterministic and turn-based.
    """

    def __init__(
        self,
        tts_provider: TTSProvider,
        stt_provider: STTProvider,
        silence_detector: Optional[SilenceDetector] = None,
    ):
        self.tts_provider = tts_provider
        self.stt_provider = stt_provider
        self.silence_detector = silence_detector or SilenceDetector()
        self.phase = VoicePhase.IDLE

    async def conduct_turn(
        self,
        question: str,
        turn_number: int,
        max_response_duration_seconds: int = 120,
    ) -> Dict[str, Any]:
        """
        Conduct a single voice turn: play question → listen → transcribe.

        Returns:
            {
                "success": bool,
                "turn_number": int,
                "question": str,
                "transcript": str,
                "transcript_normalized": str,
                "confidence": float,
                "duration_seconds": float,
                "technical_terms": List[str],
                "timestamp": str
            }
        """

        turn_start = time.time()
        result = {
            "turn_number": turn_number,
            "question": question,
            "success": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            # Step 1: Play question
            self.phase = VoicePhase.PLAYING_QUESTION
            play_result = await self.tts_provider.speak(question)

            if not play_result.get("success"):
                result["error"] = f"TTS failed: {play_result.get('error')}"
                return result

            self.phase = VoicePhase.QUESTION_PLAYED
            result["question_playback_duration_seconds"] = play_result.get("duration_seconds", 0)

            # Step 2: Listen for response
            self.phase = VoicePhase.LISTENING
            self.silence_detector.start_recording()

            # Simulate recording (in real implementation, would use actual audio device)
            # For now, this is a placeholder that returns after timeout
            recording_start = time.time()
            while (time.time() - recording_start) < 5:  # Simulate 5 second recording window
                # In real implementation, would check audio device for sound
                # and update silence detector
                if self.silence_detector.should_finalize(is_sound_present=False):
                    break
                await self._async_sleep(0.1)

            self.phase = VoicePhase.SILENCE_DETECTED

            # Step 3: Transcribe (mock audio for now)
            self.phase = VoicePhase.TRANSCRIBING
            mock_audio = b"mock_audio_data"  # In real impl: actual audio bytes
            transcribe_result = await self.stt_provider.transcribe(mock_audio)

            if not transcribe_result.get("success"):
                result["error"] = f"STT failed: {transcribe_result.get('error')}"
                return result

            # Step 4: Normalize transcript
            raw_transcript = transcribe_result.get("transcript", "")
            normalized_transcript = TranscriptNormalizer.normalize(raw_transcript)
            technical_terms = TranscriptNormalizer.extract_technical_terms(normalized_transcript)

            self.phase = VoicePhase.TRANSCRIPT_READY

            # Step 5: Build result
            turn_duration = time.time() - turn_start
            result.update(
                {
                    "success": True,
                    "transcript": raw_transcript,
                    "transcript_normalized": normalized_transcript,
                    "confidence": transcribe_result.get("confidence", 0.0),
                    "duration_seconds": turn_duration,
                    "technical_terms": technical_terms,
                    "phase_final": self.phase.value,
                }
            )

        except Exception as e:
            result["error"] = str(e)
            result["phase_error"] = self.phase.value

        return result

    async def _async_sleep(self, duration: float) -> None:
        """Async sleep utility."""

        import asyncio

        await asyncio.sleep(duration)


class VoiceVivaSession:
    """
    Complete voice-based viva session from start to finish.

    Coordinates:
    - Question selection from MAIN Agent
    - Voice turn orchestration
    - Transcript collection
    - Session persistence
    """

    def __init__(
        self,
        session_id: str,
        main_agent_orchestrator,
        tts_provider: TTSProvider,
        stt_provider: STTProvider,
    ):
        self.session_id = session_id
        self.main_agent_orchestrator = main_agent_orchestrator
        self.voice_turn_orchestrator = VoiceSessionOrchestrator(tts_provider, stt_provider)
        self.turns: List[Dict[str, Any]] = []
        self.session_start_time = datetime.utcnow()

    async def conduct_viva(self, max_turns: int = 15) -> Dict[str, Any]:
        """
        Conduct full voice-based viva.

        Returns session transcript and final state.
        """

        for turn_num in range(1, max_turns + 1):
            # Get next question from MAIN Agent
            target, question_text = self.main_agent_orchestrator.get_next_question()

            if not target:
                # All questions done
                break

            # Conduct voice turn
            voice_turn_result = await self.voice_turn_orchestrator.conduct_turn(question_text, turn_num)

            if not voice_turn_result.get("success"):
                # Continue despite STT error
                continue

            # Extract normalized transcript
            student_response = voice_turn_result.get("transcript_normalized", "")

            # Evaluate response
            evaluation = self.main_agent_orchestrator.evaluate_answer(student_response, target)

            # Generate follow-up
            follow_up = self.main_agent_orchestrator.generate_follow_up(evaluation, target)

            # Store turn
            turn_record = {
                "turn_number": turn_num,
                "question": question_text,
                "target_id": target.target_id,
                "voice_turn": voice_turn_result,
                "evaluation": evaluation,
                "follow_up": follow_up,
            }

            self.turns.append(turn_record)

            # If strong follow-up needed, ask it before moving to next question
            if follow_up:
                # This would be asked as next voice turn
                pass

        # Generate session summary
        session_summary = self.main_agent_orchestrator.get_session_summary()
        session_summary["voice_turns"] = len(self.turns)
        session_summary["session_duration_seconds"] = (
            datetime.utcnow() - self.session_start_time
        ).total_seconds()

        return {
            "session_id": self.session_id,
            "success": len(self.turns) > 0,
            "turns": self.turns,
            "summary": session_summary,
        }
