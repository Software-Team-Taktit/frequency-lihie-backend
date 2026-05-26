import shlex
import uuid
from workers.number_he import number_to_heb_string
import os, json, sys, time, pika, soundfile as sf, torch
import paramiko
from pathlib import Path
from transformers import AutoProcessor, VitsModel
import traceback
import requests
from services.utils.helpers import tx_power_level_from_dbm

QUEUE = os.getenv("TTS_QUEUE", "tts_he_mms")
RMQ_HOST = os.getenv("RABBIT_HOST", "localhost")
MODEL_ID = os.getenv("MODEL_PATH", "./local_mms_model")
STATIC_DIR = os.getenv("STATIC_DIR","static")
RPI_HOST = os.getenv("RPI_HOST", "raspberrypi4.local")
RPI_USER = os.getenv("RPI_USER", "rpi")
RPI_PASSWORD = os.getenv("RPI_PASSWORD", "")
RPI_REMOTE_DIR = os.getenv("RPI_REMOTE_DIR", "/home/rpi/mk_transmit/received_wavs")
RPI_PLAY_AFTER_UPLOAD = os.getenv("RPI_PLAY_AFTER_UPLOAD", "true").lower() == "true"
RPI_RECEIVER_URL = os.getenv(
    "RPI_RECEIVER_URL",
    f"http://{RPI_HOST}:8001/receive-transmission"
)

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

    tx_power_dbm = float(tx_power_dbm)
    is_negative = tx_power_dbm < 0

    rounded_abs = int(round(abs(tx_power_dbm)))  # עיגול מלא
    spoken = number_to_heb_string(str(rounded_abs))

    if is_negative:
        return f"בעוצמת שידור מינוס {spoken} די בי אם"
    return f"בעוצמת שידור {spoken} די בי אם"


def synthesize(text: str, out_path: str):
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = VitsModel.from_pretrained(MODEL_ID)

    inputs = processor(text=text, return_tensors="pt")

    with torch.no_grad():
        wav = model(**inputs).waveform.squeeze().cpu().numpy()

    # Remove tiny DC offset
    wav = wav - wav.mean()

    # Increase perceived loudness using RMS normalization
    target_rms = 0.75
    current_rms = float((wav ** 2).mean() ** 0.5)

    if current_rms > 0:
        wav = wav * (target_rms / current_rms)

    # Safety limiter to avoid broken/distorted WAV values
    wav = wav.clip(-0.98, 0.98)

    ensure_dirs(out_path)

    sf.write(out_path, wav, 16000, subtype="PCM_16")
    
def connect_to_rabbitmq(max_retries: int = 30, delay_seconds: int = 2):
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f" [*] Connecting to RabbitMQ at '{RMQ_HOST}'... attempt {attempt}/{max_retries}")

            conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RMQ_HOST,
                    port=5672,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )

            print(" [✓] Connected to RabbitMQ")
            return conn

        except pika.exceptions.AMQPConnectionError as e:
            last_error = e
            print(
                f" [!] RabbitMQ is not ready yet. Retrying in {delay_seconds} seconds...",
                file=sys.stderr
            )
            time.sleep(delay_seconds)

    raise RuntimeError(
        f"Could not connect to RabbitMQ after {max_retries} attempts"
    ) from last_error    

def send_wav_to_rpi(local_wav_path: str) -> str:
    local_path = Path(local_wav_path)
    
    if not local_path.exists():
        raise FileNotFoundError(f"Local WAV file not found: {local_wav_path}")
    
    if local_path.suffix.lower() != ".wav":
        raise ValueError(f"File must be a WAV file: {local_wav_path}")
    
    remote_path = f"{RPI_REMOTE_DIR}/{local_path.name}"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(
            hostname=RPI_HOST,
            username=RPI_USER,
            password=RPI_PASSWORD if RPI_PASSWORD else None,
            timeout=10
        )
        
        ssh.exec_command(f"mkdir -p {shlex.quote(RPI_REMOTE_DIR)}")
        
        sftp = ssh.open_sftp()
        sftp.put(str(local_path), remote_path)
        sftp.close()
        
        print(f" [✓] Uploaded WAV to RPI: {remote_path}")
        
        if RPI_PLAY_AFTER_UPLOAD:
            command = f"nohup aplay {shlex.quote(remote_path)} > /tmp/tts_play.log 2>&1 &"
            ssh.exec_command(command)
            print(f" [✓] Sent play command to RPI for: {remote_path}")
        
        return remote_path
    
    finally:
        ssh.close()

def format_freq_for_mk(freq_hz: float) -> str:
    freq_khz = int(round(float(freq_hz) / 1000.0))

    if freq_khz < 0 or freq_khz > 99999:
        raise ValueError(f"Frequency does not fit MMKKK format: {freq_khz}")

    return f"{freq_khz:05d}"

def send_transmission_json_to_rpi(freq_hz: float, tx_power_dbm: float | None, remote_wav_path: str):
    tx_power_level = tx_power_level_from_dbm(tx_power_dbm) if tx_power_dbm is not None else None
    
    payload = {
        "freq": format_freq_for_mk(freq_hz),
        "tx_power": tx_power_level,
        "wav_path": remote_wav_path
    }
    
    response = requests.post(
        RPI_RECEIVER_URL,
        json=payload,
        timeout=10
    )
    
    if response.status_code >= 400:
        raise RuntimeError(f"RPI receiver failed: {response.status_code} {response.text}")
    
    print(f" [✓] Sent JSON to RPI: {payload}")
    return response.json()

def main():
    conn = connect_to_rabbitmq()
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
            
            remote_path = send_wav_to_rpi(out_path)
            
            rpi_response = send_transmission_json_to_rpi(
                freq_hz=freq_hz,
                tx_power_dbm=tx_power_dbm,
                remote_wav_path=remote_path
            )
            
            print(f" [✓] {text} -> {out_path}")
            print(f" [✓] Uploaded to RPI at: {remote_path}")
            print(f" [✓] RPI response: {rpi_response}")
            
            ch_.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(" [x] Error:", repr(e), file=sys.stderr)
            traceback.print_exc()
            ch_.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
    ch.basic_consume(queue=QUEUE, on_message_callback=handle)
    ch.start_consuming()

if __name__ == "__main__":
    main()