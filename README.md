# AI Agent MQTT Integration
This application demonstrates real-time AI agent inference using MQTT messaging. It consists of a message producer that generates simulated data, an MQTT broker that handles message routing, and an AI agent that processes the data and returns predictions.

## Features
- MQTT-based messaging system for real-time data processing
- Dockerized setup with multiple services
- Automated message generation for testing
- Real-time agent predictions
- Support for MQTT monitoring tools

## Project Structure
```bash
├── Dockerfile                # Dockerfile for the agent service
├── Dockerfile.producer       # Dockerfile for the message producer
├── model/                    # Directory for the trained model
│   └── agent.json            # Trained model file
├── agent_inference.py        # Main agent service that processes MQTT messages
├── mqtt_producer.py         # Script that generates test messages
├── docker-compose.yml       # Docker compose configuration
├── mosquitto/               # Mosquitto broker configuration
│   ├── config/             
│   │   └── mosquitto.conf   # MQTT broker configuration
│   ├── data/               # Persistent storage for MQTT messages
│   └── log/                # Broker logs
├── .env                    # Environment file (for license key)
├── requirements.txt        # Python dependencies for agent service
├── producer_requirements.txt # Python dependencies for producer
└── README.md              
```

## Requirements
- Docker
- Docker Compose
- Python 3.10.x
- MQTT Explorer (optional, for monitoring)

## Getting Started

1. Clone the Repository
```bash
git clone https://github.com/composabl/agent-mqtt-app.git
cd agent-mqtt-app
```

2. Set up Mosquitto Configuration
Create the necessary directories and configuration:
```bash
mkdir -p mosquitto/config mosquitto/data mosquitto/log
```

Create `mosquitto/config/mosquitto.conf` with:
```
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_type all
```

3. Start the Services
```bash
docker-compose up --build
```

This will start:
- MQTT Broker (Mosquitto)
- Agent Service
- Message Producer

4. Environment Variables
Make sure to add your COMPOSABL_LICENSE key in the `.env` file:
```
COMPOSABL_LICENSE=your_license_key_here
```

## Testing the Application

### Using MQTT Explorer
1. Download and install MQTT Explorer from [mqtt-explorer.com](http://mqtt-explorer.com/)
2. Connect to broker:
   - Host: localhost
   - Port: 1883
3. Subscribe to topics:
   - agent/observation (input data)
   - agent/action (agent predictions)

### Manual Testing
You can publish test messages using mosquitto_pub:
```bash
mosquitto_pub -h localhost -t "agent/observation" -m '{
  "observation": {
    "T": 311.0,
    "Tc": 292.0,
    "Ca": 8.56,
    "Cref": 8.56,
    "Tref": 311.0,
    "Conc_Error": 0.0,
    "Eps_Yield": 0.0,
    "Cb_Prod": 0.0
  }
}'
```

Subscribe to responses:
```bash
mosquitto_sub -h localhost -t "agent/action" -v
```

## Message Format

### Input Message (agent/observation)
```json
{
  "observation": {
    "T": 311.0,
    "Tc": 292.0,
    "Ca": 8.56,
    "Cref": 8.56,
    "Tref": 311.0,
    "Conc_Error": 0.0,
    "Eps_Yield": 0.0,
    "Cb_Prod": 0.0
  }
}
```

### Output Message (agent/action)
```json
{
  "action": [10.0]
}
```

## Development Setup (Without Docker)

If you prefer to run the services locally:

1. Install Mosquitto broker:
```bash
# Ubuntu/Debian
sudo apt-get install mosquitto

# MacOS
brew install mosquitto
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
pip install -r producer_requirements.txt
```

3. Start the services:
```bash
# Terminal 1: Start Mosquitto
mosquitto -c mosquitto/config/mosquitto.conf

# Terminal 2: Start the agent
python agent_inference.py

# Terminal 3: Start the producer
python mqtt_producer.py
```

## Monitoring and Debugging

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f composabl-mqtt-broker
docker-compose logs -f composabl-agent-mqtt
docker-compose logs -f composabl-mqtt-producer
```

### Message Producer Options
The message producer supports several command-line arguments:
```bash
# Custom interval (e.g., 2 seconds between messages)
python mqtt_producer.py -i 2

# Verbose logging
python mqtt_producer.py -v
```

## Notes
- The MQTT broker is configured for development use. Additional security measures should be implemented for production.
- The message producer generates random data within realistic ranges for testing.
- MQTT QoS level 2 is used for guaranteed message delivery.

## License
Make sure you have a valid license for the AI agent (COMPOSABL_LICENSE), as this is required for the app to work.

## Contributions
Feel free to contribute by submitting pull requests or opening issues!