import asyncio
import os
from composabl import Agent, Trainer
import numpy as np
import paho.mqtt.client as mqtt
from threading import Thread
import json
import logging
from datetime import datetime
import traceback
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global objects
trainer = None
trained_agent = None
mqtt_client = None
license_key = os.environ["COMPOSABL_LICENSE"]

PATH = os.path.dirname(os.path.realpath(__file__))
PATH_CHECKPOINTS = f"{PATH}/model/agent.json"

# MQTT settings
MQTT_BROKER = os.environ.get("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_TOPIC_OBSERVATION = "agent/observation"
MQTT_TOPIC_ACTION = "agent/action"
MQTT_QOS = 2
MQTT_KEEPALIVE = 60

def on_connect(client, userdata, flags, rc):
    """Callback for when the client receives a CONNECT response from the server."""
    connection_responses = {
        0: "Connected successfully",
        1: "Incorrect protocol version",
        2: "Invalid client identifier",
        3: "Server unavailable",
        4: "Bad username or password",
        5: "Not authorized"
    }
    
    if rc == 0:
        logger.info(connection_responses[rc])
        client.subscribe(MQTT_TOPIC_OBSERVATION, qos=MQTT_QOS)
        logger.info(f"Subscribed to {MQTT_TOPIC_OBSERVATION}")
    else:
        logger.error(f"Connection failed: {connection_responses.get(rc, f'Unknown error ({rc})')}")

def on_disconnect(client, userdata, rc):
    """Callback for client disconnection."""
    if rc != 0:
        logger.warning("Unexpected disconnection. Attempting to reconnect...")
    else:
        logger.info("Client disconnected successfully")

async def process_observation(observation: Dict[str, float]) -> Optional[Any]:
    """Process an observation through the trained agent and return an action."""
    global trained_agent
    
    try:
        if not trained_agent:
            raise ValueError("Agent not initialized")
        
        # Try processing as numpy array
        obs = np.array([float(observation[key]) for key in [
            "T", "Tc", "Ca", "Cref", "Tref", "Conc_Error", "Eps_Yield", "Cb_Prod"
        ]])
        
        action = await trained_agent._execute(obs)
        logger.debug(f"Generated action: {action}")
        
        return action.tolist() if isinstance(action, np.ndarray) else action
        
    except Exception as e:
        logger.error(f"Error processing observation: {str(e)}")
        return None

def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    try:
        logger.info(f"Received message on topic {msg.topic}")
        
        # Parse the observation from the MQTT message
        payload = msg.payload.decode()
        logger.debug(f"Received payload: {payload}")
        
        observation_data = json.loads(payload)
        observation = observation_data.get("observation")
        
        if not observation:
            logger.error("No observation field in message")
            return
            
        # Create new event loop for async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Process the observation and get action
        action = loop.run_until_complete(process_observation(observation))
        
        # Publish the action back to MQTT
        if action is not None:
            response = json.dumps({"action": action})
            logger.info(f"Publishing action: {response}")
            client.publish(MQTT_TOPIC_ACTION, response, qos=MQTT_QOS)
        
        loop.close()
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error(traceback.format_exc())

async def init_runtime():
    """Initialize the trainer and agent."""
    global trainer, trained_agent, mqtt_client
    
    try:
        logger.info("Initializing Composabl trainer...")
        
        # Initialize Composabl trainer
        config = {
            "license": license_key,
            "target": {
                "local": {"address": "localhost:1337"}
            },
            "env": {
                "name": "sim-deploy",
            },
            "trainer": {
                "workers": 1
            }
        }
        
        trainer = Trainer(config)
        agent = Agent.load(PATH_CHECKPOINTS)
        trained_agent = await trainer._package(agent)
        logger.info("Agent loaded successfully")
        
        # Initialize MQTT client with VERSION1 API
        mqtt_client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1,
            client_id=f"agent_server_{datetime.now().timestamp()}",
            clean_session=True
        )
        
        # Set up callbacks
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_disconnect = on_disconnect
        
        # Connect to MQTT broker
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
        
        # Start MQTT loop in a separate thread
        mqtt_thread = Thread(target=mqtt_client.loop_forever)
        mqtt_thread.daemon = True
        mqtt_thread.start()
        logger.info("MQTT client started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize runtime: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        # Initialize runtime
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init_runtime())
        
        # Keep the main thread running
        try:
            while True:
                asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}")
        logger.critical(traceback.format_exc())
        exit(1)