import uuid
from .number_he import number_to_heb_string
import os, json, sys, pika, soundfile as sf, torch
from transformers import AutoProcessor, VitsModel

QUEUE = os.getenv("TTS_QUEUE", "tts_he_mms")
RMQ_HOST = os.getenv("RABBIT_HOST", "localhost")
MODEL_ID = "facebook/mms-tts-heb"
STATIC_DIR = os.getenv("STATIC_DIR","static")

def ensure_dirs(path:str): os.makedirs(os.path.dirname(path), exist_ok=True)

def format_freq_phrase(has_freq: bool, freq_hz: float) -> str:
    if (not has_freq) or (freq_hz <=0):
        return "לא אושר עבורך תדר"
    
    if freq_hz >= 1e6:
        val = round(freq_hz / 1e6, 3); unit = "מגה־הרץ"
    elif freq_hz >= 1e3:
        val = round(freq_hz / 1e3, 1); unit = "קילו־הרץ"
    else:
        val = int(round(freq_hz));     unit = "הרץ"
    
    s = f"{val}".rstrip('0').rstrip('.') if isinstance(val, float) else f"{val}"
    spoken = number_to_heb_string(s)
    return f"עברו לתדר {spoken} {unit}"
        
def format_power_phrase(tx_power_dbm: float | None) -> str:
    if tx_power_dbm is None:
        return ""
    s = f"{tx_power_dbm}".rstrip('0').rstrip('.')
    spoken = number_to_heb_string(s)
    return f"בעוצמת שידור {spoken} די בי אם"        

def synthesize(text: str, out_path: str):
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = VitsModel.from_pretrained(MODEL_ID)
    inputs = processor(text = text, return_tensors = "pt")
    with torch.no_grad():
        wav = model(**inputs).waveform.squeeze().cpu().numpy()
    ensure_dirs(out_path)
    sf.write(out_path, wav, 16000)
    
def main():
    conn = pika.BlockingConnection(pika.ConnectionParameters(host=RMQ_HOST))
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.basic_qos(prefetch_count=1)
    print(f" [*] Waiting on '{QUEUE}'. CTRL+C to exit")
    
    def handle(ch_, method, props, body):
        try:
            msg = json.loads(body.decode("utf-8"))
            has_freq = bool(msg.get("isFreq", False))
            freq_hz = float(msg.get("freq_hz", 0))
            if freq_hz < 0:
                raise ValueError(f"freq_hz must be >= 0, got {freq_hz}")
            
            tx_power_dbm = msg.get("tx_power_dbm", None)
            tx_power_dbm = None if tx_power_dbm is None else float(tx_power_dbm)
            
            freq_text = format_freq_phrase(has_freq, freq_hz)
            power_text = format_power_phrase(tx_power_dbm)
            
            text = freq_text if power_text == "" else f"{freq_text}. {power_text}"
            
            rel = f"tts/freq_{uuid.uuid4().hex}.wav"
            out_path = os.path.join(STATIC_DIR, rel)
            
            synthesize(text, out_path)
            
            print(f" [✓] {text} -> {out_path}")
            ch_.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(" [x] Error:", e, file=sys.stderr)
            ch_.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    ch.basic_consume(queue=QUEUE, on_message_callback=handle)
    ch.start_consuming()

if __name__ == "__main__":
    main()