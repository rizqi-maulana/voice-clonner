# Voice Clonner

Clone any voice from a short audio recording. Load or record a reference voice, type the text you want spoken, and generate speech that sounds like the original speaker.

[![Join Discord](https://img.shields.io/badge/Join%20Community-Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/FEXhA3cQjP)

## Features

- Clone voices from audio files or microphone recordings
- Support for **18 languages**: Indonesian, English, Spanish, French, German, Italian, Portuguese, Polish, Turkish, Russian, Dutch, Czech, Arabic, Chinese, Hungarian, Korean, Japanese, Hindi
- Auto-detect speaking speed and expressiveness from reference audio
- Long text is automatically split into natural chunks
- Indonesian abbreviation expansion for better pronunciation
- Sample texts provided for each language to help with recording

## Demo

[![Watch Demo](https://img.shields.io/badge/Watch%20Demo-YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/uQ0TEMTE4T4)

## Before You Start

Make sure you have the following ready before running the app:

### 1. FFmpeg (Required)

FFmpeg is needed for audio processing. Install it using one of these methods:

**Option A — Using winget (recommended):**
```
winget install Gyan.FFmpeg
```

**Option B — Manual download:**
1. Go to https://www.gyan.dev/ffmpeg/builds/
2. Download **ffmpeg-release-essentials.zip**
3. Extract the zip to a folder (e.g. `C:\ffmpeg`)
4. Add the `bin` folder to your system PATH:
   - Search "Environment Variables" in Start menu
   - Click "Environment Variables..."
   - Under "System variables", find `Path`, click "Edit"
   - Click "New" and add `C:\ffmpeg\bin`
   - Click OK on all windows

To verify FFmpeg is installed, open a terminal and type:
```
ffmpeg -version
```

### 2. System Requirements

- **Windows** 10 or later
- **Internet connection** — required for first-time setup (downloads voice models automatically)
- **Disk space** — ~2 GB for the main voice model, ~5 GB additional for Indonesian language (downloaded on first use)
- **RAM** — 8 GB minimum, 16 GB recommended
- **Microphone** — only needed if you want to record your own voice as reference (you can also load audio files)

> Everything else (Python, packages, dependencies) is installed automatically when you first run the app. No manual setup needed.

## How to Run

1. **Download** this repository — click the green **Code** button, then **Download ZIP**, and extract it to any folder.

2. **Run the app** — double-click `run.bat`. On first launch, it will automatically install the required tools and dependencies. This may take a few minutes.

3. That's it! The app will open and guide you through initial setup.

## How to Use

1. **Load a reference voice** — Click "Load Audio File" to use an existing recording, or click "Record from Mic" to record your own voice. A 5-15 second clip works best.

2. **Choose a language** — Select the language you want to generate speech in from the dropdown menu.

3. **Type your text** — Enter the text you want spoken in the cloned voice. You can use the provided sample texts for quick testing.

4. **Generate** — Click the "Generate Cloned Voice" button and wait for the result.

5. **Listen & Save** — Play the generated audio, and save it as a WAV file if you're satisfied.

## Tips for Best Results

- Use a clear, noise-free reference recording
- 5-15 seconds of speech gives the best voice quality
- Shorter references (<3 seconds) may produce lower quality
- Very long references (>30 seconds) — only the first 30 seconds are used
- WAV files work best for reference audio

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `run.bat` closes immediately | Right-click `run.bat` → "Run as administrator" |
| "FFmpeg not found" error | Install FFmpeg (see "Before You Start" above) |
| Download fails on first launch | Check your internet connection and try again — the app will resume where it left off |
| Audio doesn't play | Make sure your speakers/headphones are connected |
| App is slow to generate | This is normal on CPU. Generation takes 30-60 seconds depending on text length |

## Community

Join our Discord community for help, updates, and sharing your creations:

[![Join Discord](https://img.shields.io/badge/Join%20Community-Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/FEXhA3cQjP)

## License

This project is provided as-is for personal and educational use.
