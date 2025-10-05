from deps.heb_freq_phrase import _digits_to_hebrew, freq_to_phrase_he
import os, json, sys, pika, soundfile as sf, torch
from transformers import AutoProcessor, VitsModel

QUEUE = os.getenv("TTS_QUEUE", "tts_he_mms")
RMQ_HOST = os.getenv("RABBIT_HOST", "localhost")
MODEL_ID = "facebook/mms-tts-heb"
STATIC_DIR = os.getenv("STATIC_DIR","static")

def ensure_dirs(path:str): os.makedirs(os.path.dirname(path), exist_ok=True)

def main():
    print("Loading MMS Hebrew model (CPU)...")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = VitsModel.from_pretrained(MODEL_ID)
    
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RMQ_HOST))
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.basic_qos(prefetch_count=1)
    print(" [*] Waiting for messages. CTRL+C to exit")
    
    def handle(ch_, method, props, body):
        try:
            msg = json.loads(body.decode("utf-8"))
            if msg.get("type") != "announce_frequency":
                ch_.basic_ack(delivery_tag=method.delivery_tag); return
            freq_hz = float(msg["freq_hz"])
            style = msg.get("style", "digits")
            rel = msg["rel_path"]
            text = freq_to_phrase_he(freq_hz, style)
            
            out_path = os.path.join(STATIC_DIR, rel)
            ensure_dirs(out_path)
            
            inputs = processor(text=text, return_tensors="pt")
            with torch.no_grad():
                wav = model(**inputs).waveform.squeeze().cpu().numpy()
            sf.write(out_path, wav, 16000)
            
            print(f" [✓] {text} -> {out_path}")
            ch_.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(" [x] Error:", e, file=sys.stderr)
            ch_.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
    ch.basic_consume(queue=QUEUE, on_message_callback=handle)
    ch.start_consuming()

if __name__ == "__main__":
    main()