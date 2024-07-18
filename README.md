# AudioPilot
An automatic flight control system based on LLM and CV

## Voice Control Module
The Voice is located in the folder called "VoiceControl" it used Gemma 2 LLM friendly provided by [GaiaNet](gaianet.ai) 
We use Python as developing language and openai whisper as voice to text model.
IP/Socket is used to communicate between different modules.

### Usage
Use spacebar to start the recording use the word forward, backward, move right/left and takeoff/landing to control the drone 
