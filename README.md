# Web Monitoring App

This application monitors a specific website section for changes and logs them.

## Prerequisites

- Python 3.9.7
- Docker and Docker Compose (for containerized setup)

## Setup Instructions

1. Ensure you have the project files in your working directory.

2. Create a `.env` file in the project root with the following content:
   ```
   USERNAME=your_username
   PASSWORD=your_password
   ```
   Replace `your_username` and `your_password` with your actual credentials.

3. Set up a Python virtual environment:
   ```
   python3.9 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Running the App Locally

1. Activate the virtual environment if not already active:
   ```
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Run the monitoring script:
   ```
   python monitor.py
   ```

3. To stop the app, press `Ctrl+C` in the terminal.


## Running with Docker

1. Build and start the Docker container:
   ```
   docker-compose build
   docker-compose up
   ```

2. The app will start running, and you'll see the logs in the console.

3. To stop the app, press `Ctrl+C` in the terminal where docker-compose is running.

## Accessing Logs

Logs will be stored in the `./logs` directory on your host machine.

## Troubleshooting

If you encounter any issues, check the following:
- Ensure Python 3.9.7 is installed (for local setup).
- For Docker setup, ensure Docker and Docker Compose are installed and running.
- Verify that the `.env` file contains the correct credentials.
- Check the logs for any error messages.