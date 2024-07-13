# Ayase
## Description
An open-source recreation of the Karuta discord bot's card system.
## Dependencies
Python 3.10 or higher is required: https://www.python.org/downloads/
## Installation
To install the required dependencies for this project you can run the following:
```bash
# Clone the repository
git clone https://github.com/Keerran/ayase

# Navigate to the project directory
cd ayase

# Install dependencies
pip install .
```
If you are forking the project and would like to use the pre-commit hooks you can instead use:
```bash
pip install .[dev]
```
## Usage
Once installed you must provide a `.env` file in the format shown in `.env.example`.
Then you can simply run:
```bash
ayase
```

## Features
Currently the project has the following features:
- Anime character card dropping
- Card collection viewing
- Admin commands for reloading modules or refreshing cooldowns
