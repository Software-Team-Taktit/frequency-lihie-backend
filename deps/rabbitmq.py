import json, os, pika

QUEUE    = os.getenv("TTS_QUEUE", "tts_he_mms")
RMQ_HOST = os.getenv("RABBIT_HOST", "localhost")

def publish_tts_result(is_freq: bool, freq_hz: float, tx_power_dbm: float | None = None) -> None:
    msg = {
        "isFreq": bool(is_freq),
        "freq_hz": float(freq_hz),
        "tx_power_dbm": None if tx_power_dbm is None else float(tx_power_dbm),
    }

    conn = pika.BlockingConnection(pika.ConnectionParameters(RMQ_HOST))
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.basic_publish(
        exchange="",
        routing_key=QUEUE,
        body=json.dumps(msg, ensure_ascii=False).encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    conn.close()