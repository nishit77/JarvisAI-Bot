    # -------------------------
    # PYTORCH SAFE GLOBALS FIX (REQUIRED FOR PYTORCH 2.6+)
    # -------------------------
    import torch

    import TTS.tts.configs.xtts_config
    import TTS.tts.models.xtts
    import TTS.config.shared_configs

    torch.serialization.add_safe_globals([
        TTS.tts.configs.xtts_config.XttsConfig,
        TTS.tts.models.xtts.XttsAudioConfig,
        TTS.tts.models.xtts.XttsArgs,
        TTS.config.shared_configs.BaseDatasetConfig
    ])

    # -------------------------
    # IMPORTS
    # -------------------------
    import os
    from TTS.api import TTS

    # -------------------------
    # PATHS
    # -------------------------
    speaker_wav = r"C:\python\MegaProject - JARVIS\JarvisAI-Bot\voices\my_voice_xtts.wav"
    output_file = r"C:\python\MegaProject - JARVIS\JarvisAI-Bot\output.wav"

    # -------------------------
    # CHECK VOICE FILE
    # -------------------------
    if not os.path.exists(speaker_wav):
        raise FileNotFoundError(f"Speaker WAV not found: {speaker_wav}")

    # -------------------------
    # LOAD XTTS MODEL (CPU)
    # -------------------------
    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        gpu=False
    )

    # -------------------------
    # TEXT TO SPEAK
    # -------------------------
    text = "Hello, this is Jarvis speaking in Nishit's voice."

    # -------------------------
    # GENERATE AUDIO
    # -------------------------
    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wav,
        language="en",
        file_path=output_file
    )

    print(f"Audio generated successfully: {output_file}")
