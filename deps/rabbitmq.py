import json, uuid, os, pika

QUEUE    = os.getenv("TTS_QUEUE", "tts_he_mms")
RMQ_HOST = os.getenv("RABBIT_HOST", "localhost")

def publish_tts_freq(freq_hz: float, *, style: str = "digits", rel_path: str | None = None) -> dict:
    file_id = uuid.uuid4().hex
    rel_path = rel_path or f"tts/{file_id}.wav"
    msg = {"type":"announce_frequency", "freq_hz": float(freq_hz), "style": style, "rel_path": rel_path}
    
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
    return {"id": file_id, "rel_path": rel_path, "url": f"/static/{rel_path}"}