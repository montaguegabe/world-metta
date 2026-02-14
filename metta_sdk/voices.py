"""Cultural voice mapping and ElevenLabs speech-to-speech conversion."""

import io
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

from .cache import ElevenLabsCache


@dataclass
class CulturalVoice:
    """Configuration for a cultural voice."""

    culture: str
    accent: str
    language: str
    ambiance_prompt: str
    voice_id: Optional[str] = None  # Cached voice ID after lookup


# Predefined cultural configurations
CULTURAL_VOICES = {
    # East Asian
    "japanese": CulturalVoice(
        culture="japanese",
        accent="japanese",
        language="ja",
        ambiance_prompt="serene zen garden at dawn, the hollow sound of a shishi-odoshi bamboo water fountain rhythmically striking stone, wind rustling through tall bamboo groves, distant temple bell echoing across misty mountains, koi pond water gently rippling, morning birds in a Japanese maple tree",
    ),
    "chinese": CulturalVoice(
        culture="chinese",
        accent="chinese",
        language="zh",
        ambiance_prompt="ancient Chinese garden courtyard at sunrise, melodic guzheng strings floating through the air, water trickling down ornate stone formations into a lotus pond, wind chimes tinkling from a red lacquered pagoda, morning doves cooing, silk robes rustling on stone paths",
    ),
    "korean": CulturalVoice(
        culture="korean",
        accent="korean",
        language="ko",
        ambiance_prompt="Korean Buddhist mountain temple at dawn, deep bronze temple bell resonating through pine forests, distant monks chanting, morning mist rolling through mountain valleys, wind through ancient pine trees, songbirds awakening, wooden temple wind chimes",
    ),
    # South Asian
    "indian": CulturalVoice(
        culture="indian",
        accent="indian",
        language="hi",
        ambiance_prompt="peaceful Indian ashram at golden hour, soft tanpura drone creating meditative resonance, distant temple bells ringing for evening puja, incense smoke curling through the air, Ganges river flowing gently, peacocks calling in the distance, sitar strings vibrating softly",
    ),
    # African
    "african": CulturalVoice(
        culture="african",
        accent="african",
        language="en",
        ambiance_prompt="African savanna at sunset, golden light over endless grasslands, distant djembe drums echoing from a village, elephants rumbling in the distance, acacia trees swaying in warm breeze, lion purring far away, crickets beginning their evening chorus, stars emerging over the Serengeti",
    ),
    "nigerian": CulturalVoice(
        culture="nigerian",
        accent="nigerian",
        language="en",
        ambiance_prompt="West African village at dawn, talking drums sending messages between communities, tropical birds calling from palm trees, gentle breeze carrying the scent of cooking fires, children laughing in the distance, rooster crowing, the Niger River flowing peacefully nearby",
    ),
    # Middle Eastern
    "arabic": CulturalVoice(
        culture="arabic",
        accent="arabic",
        language="ar",
        ambiance_prompt="vast Arabian desert at twilight, endless sand dunes glowing amber and rose, warm wind whispering across the sands, distant oud playing a haunting melody, a desert oasis with date palms rustling, camels breathing softly, stars emerging in an infinite sky, the muezzin's call echoing from a faraway minaret",
    ),
    # European
    "celtic": CulturalVoice(
        culture="celtic",
        accent="irish",
        language="en",
        ambiance_prompt="misty Irish countryside at dawn, rolling green hills disappearing into fog, a wooden flute playing an ancient melody, sheep bleating in distant pastures, a brook babbling over mossy stones, morning dew dripping from fern leaves, castle ruins silhouetted against grey sky",
    ),
    "scottish": CulturalVoice(
        culture="scottish",
        accent="scottish",
        language="en",
        ambiance_prompt="Scottish Highlands at dusk, purple heather covering dramatic mountain slopes, distant bagpipes echoing across a misty loch, soft rain pattering on ancient stones, red deer calling in the glen, wind howling gently through castle ruins, waves lapping at rocky shores",
    ),
    "french": CulturalVoice(
        culture="french",
        accent="french",
        language="fr",
        ambiance_prompt="Provence countryside in late afternoon, endless lavender fields swaying in warm breeze, bees humming lazily, distant accordion playing a romantic waltz, church bells ringing from a stone village, cicadas singing, wine glasses clinking at a vineyard terrace, cypress trees rustling",
    ),
    "russian": CulturalVoice(
        culture="russian",
        accent="russian",
        language="ru",
        ambiance_prompt="deep Russian forest in winter twilight, snow falling silently on endless birch trees, a balalaika playing a melancholic folk tune in the distance, wolves howling far away, frozen river cracking softly, Orthodox church bells ringing across the taiga, wind whispering through snow-laden branches",
    ),
    "greek": CulturalVoice(
        culture="greek",
        accent="greek",
        language="el",
        ambiance_prompt="Greek island village at sunset, whitewashed walls glowing golden, bouzouki music drifting from a taverna, Aegean waves gently lapping against fishing boats, olive trees rustling in Mediterranean breeze, goat bells tinkling on distant hillside, seagulls calling, wine being poured",
    ),
    # Americas
    "latin": CulturalVoice(
        culture="latin",
        accent="spanish",
        language="es",
        ambiance_prompt="Central American cloud forest at dawn, exotic birds calling through mist, howler monkeys in the distance, ancient Mayan ruins emerging from jungle, warm rain dripping from giant leaves, a wooden flute playing indigenous melodies, toucans and quetzals singing",
    ),
    "brazilian": CulturalVoice(
        culture="brazilian",
        accent="brazilian",
        language="pt",
        ambiance_prompt="Amazon rainforest at sunrise, the mighty river flowing through endless green canopy, macaws and parrots calling, soft rain pattering on giant leaves, distant berimbau playing capoeira rhythms, howler monkeys awakening, exotic frogs and insects creating a symphony of life, mist rising from the forest floor",
    ),
    # Oceania
    "australian": CulturalVoice(
        culture="australian",
        accent="australian",
        language="en",
        ambiance_prompt="Australian outback at sunset, red earth glowing under vast infinite sky, ancient didgeridoo droning a dreamtime song, kangaroos hopping through spinifex grass, kookaburras laughing as stars emerge, eucalyptus trees creaking in warm desert wind, Aboriginal fire crackling under the Southern Cross",
    ),
    # British Isles
    "british": CulturalVoice(
        culture="british",
        accent="british",
        language="en",
        ambiance_prompt="English countryside garden at twilight, roses and lavender perfuming the air, distant church bells ringing vespers, blackbirds singing their evening song, wind rustling through ancient oak trees, a gentle stream trickling past moss-covered stones, sheep bleating in distant fields",
    ),
}


class CulturalVoiceMapper:
    """Maps cultures to ElevenLabs voices and handles speech-to-speech conversion."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with ElevenLabs API key.

        Args:
            api_key: ElevenLabs API key. If not provided, looks for ELEVENLABS_API_KEY env var.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")

        if not self.api_key:
            raise ValueError(
                "ElevenLabs API key required. Set ELEVENLABS_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = ElevenLabs(api_key=self.api_key)
        self._voice_cache: dict[str, str] = {}
        self._file_cache = ElevenLabsCache()

    def get_cultural_voice(self, culture: str) -> CulturalVoice:
        """Get the CulturalVoice configuration for a culture.

        Args:
            culture: Culture name (e.g., "japanese", "indian")

        Returns:
            CulturalVoice configuration
        """
        if culture not in CULTURAL_VOICES:
            available = ", ".join(CULTURAL_VOICES.keys())
            raise ValueError(f"Unknown culture '{culture}'. Available: {available}")

        return CULTURAL_VOICES[culture]

    def find_voice_id(self, culture: str) -> str:
        """Find an ElevenLabs voice ID matching the cultural accent.

        Prioritizes user's existing voices to avoid hitting custom voice limits.

        Args:
            culture: Culture name

        Returns:
            Voice ID string
        """
        if culture in self._voice_cache:
            return self._voice_cache[culture]

        voice_config = self.get_cultural_voice(culture)

        # First, check user's existing voices (doesn't add to custom voice count)
        try:
            voices = self.client.voices.get_all()

            # Look for exact accent match in user's voices
            for voice in voices.voices:
                if voice.labels:
                    accent = voice.labels.get("accent", "").lower()
                    if voice_config.accent.lower() == accent:
                        print(
                            f"    Using existing voice: {voice.name} (accent: {accent})"
                        )
                        self._voice_cache[culture] = voice.voice_id
                        return voice.voice_id

            # Try partial match (e.g., "british" in "british-american")
            for voice in voices.voices:
                if voice.labels:
                    accent = voice.labels.get("accent", "").lower()
                    if voice_config.accent.lower() in accent:
                        print(
                            f"    Using existing voice: {voice.name} (accent: {accent})"
                        )
                        self._voice_cache[culture] = voice.voice_id
                        return voice.voice_id

        except Exception as e:
            print(f"    Warning: Could not check existing voices: {e}")

        # Fallback: search shared library (may add to custom voice count)
        try:
            print(f"    Searching shared library for {voice_config.accent} accent...")
            shared_voices = self.client.voices.get_shared(
                accent=voice_config.accent,
                language=voice_config.language,
                page_size=10,
            )

            if shared_voices.voices:
                voice = shared_voices.voices[0]
                print(f"    Found shared voice: {voice.name} (ID: {voice.voice_id})")
                self._voice_cache[culture] = voice.voice_id
                return voice.voice_id

            # Try accent only
            shared_voices = self.client.voices.get_shared(
                accent=voice_config.accent,
                page_size=10,
            )

            if shared_voices.voices:
                voice = shared_voices.voices[0]
                print(f"    Found shared voice (accent only): {voice.name}")
                self._voice_cache[culture] = voice.voice_id
                return voice.voice_id

        except Exception as e:
            print(f"    Warning: Could not search shared voices: {e}")

        raise ValueError(f"Could not find a voice for culture '{culture}'")

    def convert_speech(
        self,
        audio_data: bytes,
        culture: str,
        voice_id: Optional[str] = None,
    ) -> bytes:
        """Convert speech to a cultural voice using ElevenLabs speech-to-speech.

        Args:
            audio_data: Input audio bytes
            culture: Culture name for voice selection
            voice_id: Optional explicit voice ID (overrides culture lookup)

        Returns:
            Converted audio bytes
        """
        if voice_id is None:
            voice_id = self.find_voice_id(culture)

        # Check cache first
        audio_hash = self._file_cache.hash_audio(audio_data)
        cached = self._file_cache.get_voice_conversion(audio_hash, voice_id, culture)
        if cached is not None:
            return cached

        # Use speech-to-speech conversion
        result = self.client.speech_to_speech.convert(
            voice_id=voice_id,
            audio=io.BytesIO(audio_data),
            model_id="eleven_multilingual_sts_v2",
        )

        # Collect all chunks from generator
        audio_bytes = b"".join(chunk for chunk in result)

        # Cache the result
        self._file_cache.set_voice_conversion(
            audio_hash, voice_id, culture, audio_bytes
        )

        return audio_bytes

    def convert_speech_from_file(
        self,
        audio_path: str,
        culture: str,
        voice_id: Optional[str] = None,
    ) -> bytes:
        """Convert speech from a file to a cultural voice.

        Args:
            audio_path: Path to input audio file
            culture: Culture name for voice selection
            voice_id: Optional explicit voice ID

        Returns:
            Converted audio bytes
        """
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        return self.convert_speech(audio_data, culture, voice_id)

    def generate_ambiance(
        self,
        culture: str,
        duration_seconds: float = 60.0,
    ) -> bytes:
        """Generate culturally-appropriate ambient sound.

        Args:
            culture: Culture name
            duration_seconds: Duration of ambient sound

        Returns:
            Audio bytes
        """
        # Check cache first
        cached = self._file_cache.get_ambiance(culture, duration_seconds)
        if cached is not None:
            return cached

        voice_config = self.get_cultural_voice(culture)

        result = self.client.text_to_sound_effects.convert(
            text=voice_config.ambiance_prompt,
            duration_seconds=duration_seconds,
        )

        audio_bytes = b"".join(chunk for chunk in result)

        # Cache the result
        self._file_cache.set_ambiance(culture, duration_seconds, audio_bytes)

        return audio_bytes

    @staticmethod
    def list_cultures() -> list[str]:
        """List available cultural voices.

        Returns:
            List of culture names
        """
        return list(CULTURAL_VOICES.keys())

    @staticmethod
    def get_culture_info(culture: str) -> dict:
        """Get information about a cultural voice configuration.

        Args:
            culture: Culture name

        Returns:
            Dict with culture details
        """
        if culture not in CULTURAL_VOICES:
            available = ", ".join(CULTURAL_VOICES.keys())
            raise ValueError(f"Unknown culture '{culture}'. Available: {available}")

        config = CULTURAL_VOICES[culture]
        return {
            "culture": config.culture,
            "accent": config.accent,
            "language": config.language,
            "ambiance_prompt": config.ambiance_prompt,
        }
