import paho.mqtt.client as mqtt
import json
import random
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "agent/observation"
MQTT_QOS = 2

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    connection_responses = {
        0: "Connected successfully",
        1: "Incorrect protocol version",
        2: "Invalid client identifier",
        3: "Server unavailable",
        4: "Bad username or password",
        5: "Not authorized"
    }
    logger.info(connection_responses.get(rc, f"Unknown connection response: {rc}"))

def on_publish(client, userdata, mid):
    """Callback for when a message is published."""
    logger.debug(f"Message {mid} published successfully")

def generate_random_observation():
    """Generate a random observation with realistic constraints."""
    observation = {
        "T": random.uniform(200.0, 420.0),
        "Tc": random.uniform(180.0, 300.0),
        "Ca": random.uniform(5.0, 10.0),
        "Cref": random.uniform(3.0, 15.0),
        "Tref": random.uniform(250.0, 320.0),
        "Conc_Error": random.uniform(0.0, 10.0),
        "Eps_Yield": random.uniform(0.0, 50.0),
        "Cb_Prod": random.uniform(0.0, 10.0)
    }
    return {"observation": observation}

def run_producer(interval=5):
    """Run the MQTT producer with specified interval."""
    # Initialize MQTT client
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION1,
        client_id=f"producer_{datetime.now().timestamp()}",
        clean_session=True
    )
    
    # Set up callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        # Connect to MQTT broker
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start the MQTT loop in a background thread
        client.loop_start()
        
        while True:
            try:
                # Generate and publish observation
                observation = generate_random_observation()
                
                # Publish message
                result = client.publish(
                    MQTT_TOPIC,
                    json.dumps(observation),
                    qos=MQTT_QOS
                )
                
                # Check if publish was successful
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"Published observation: {observation}")
                else:
                    logger.error(f"Failed to publish message: {mqtt.error_string(result.rc)}")
                
                # Wait for the specified interval
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping producer...")
                break
            except Exception as e:
                logger.error(f"Error in producer loop: {str(e)}")
                time.sleep(1)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {str(e)}")
    finally:
        # Clean up
        client.loop_stop()
        client.disconnect()
        logger.info("Producer stopped")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MQTT Observation Generator')
    parser.add_argument(
        '-i', '--interval',
        type=float,
        default=5.0,
        help='Interval between messages in seconds (default: 5.0)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        run_producer(interval=args.interval)
    except KeyboardInterrupt:
        logger.info("Producer terminated by user")