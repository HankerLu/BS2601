import asyncio
import aiohttp
import json
import struct
import gzip
import uuid
import logging
import time
import queue
import threading
import wave
from typing import Optional, List, Dict, Any, Callable
import pyaudio

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ASR_Engine")

# --- 1. 协议定义 (保持原样，纯逻辑) ---

class ProtocolVersion:
    V1 = 0b0001

class MessageType:
    CLIENT_FULL_REQUEST = 0b0001
    CLIENT_AUDIO_ONLY_REQUEST = 0b0010
    SERVER_FULL_RESPONSE = 0b1001
    SERVER_ERROR_RESPONSE = 0b1111

class MessageTypeSpecificFlags:
    NO_SEQUENCE = 0b0000
    POS_SEQUENCE = 0b0001
    NEG_SEQUENCE = 0b0010
    NEG_WITH_SEQUENCE = 0b0011

class SerializationType:
    NO_SERIALIZATION = 0b0000
    JSON = 0b0001

class CompressionType:
    GZIP = 0b0001

class CommonUtils:
    @staticmethod
    def gzip_compress(data: bytes) -> bytes:
        return gzip.compress(data)

    @staticmethod
    def gzip_decompress(data: bytes) -> bytes:
        return gzip.decompress(data)

class AsrRequestHeader:
    def __init__(self):
        self.message_type = MessageType.CLIENT_FULL_REQUEST
        self.message_type_specific_flags = MessageTypeSpecificFlags.POS_SEQUENCE
        self.serialization_type = SerializationType.JSON
        self.compression_type = CompressionType.GZIP
        self.reserved_data = bytes([0x00])

    def with_message_type(self, message_type: int) -> 'AsrRequestHeader':
        self.message_type = message_type
        return self

    def with_message_type_specific_flags(self, flags: int) -> 'AsrRequestHeader':
        self.message_type_specific_flags = flags
        return self

    def with_serialization_type(self, serialization_type: int) -> 'AsrRequestHeader':
        self.serialization_type = serialization_type
        return self

    def with_compression_type(self, compression_type: int) -> 'AsrRequestHeader':
        self.compression_type = compression_type
        return self

    def to_bytes(self) -> bytes:
        header = bytearray()
        header.append((ProtocolVersion.V1 << 4) | 1)
        header.append((self.message_type << 4) | self.message_type_specific_flags)
        header.append((self.serialization_type << 4) | self.compression_type)
        header.extend(self.reserved_data)
        return bytes(header)

    @staticmethod
    def default_header() -> 'AsrRequestHeader':
        return AsrRequestHeader()

class AsrResponse:
    def __init__(self):
        self.code = 0
        self.event = 0
        self.is_last_package = False
        self.payload_sequence = 0
        self.payload_size = 0
        self.payload_msg = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "event": self.event,
            "is_last_package": self.is_last_package,
            "payload_sequence": self.payload_sequence,
            "payload_size": self.payload_size,
            "payload_msg": self.payload_msg
        }

class ResponseParser:
    @staticmethod
    def parse_response(msg: bytes) -> AsrResponse:
        response = AsrResponse()
        if len(msg) < 4:
            return response
            
        header_size = msg[0] & 0x0f
        message_type = msg[1] >> 4
        message_type_specific_flags = msg[1] & 0x0f
        serialization_method = msg[2] >> 4
        message_compression = msg[2] & 0x0f
        
        payload = msg[header_size*4:]
        
        if message_type_specific_flags & 0x01:
            response.payload_sequence = struct.unpack('>i', payload[:4])[0]
            payload = payload[4:]
        if message_type_specific_flags & 0x02:
            response.is_last_package = True
        if message_type_specific_flags & 0x04:
            response.event = struct.unpack('>i', payload[:4])[0]
            payload = payload[4:]
            
        if message_type == MessageType.SERVER_FULL_RESPONSE:
            response.payload_size = struct.unpack('>I', payload[:4])[0]
            payload = payload[4:]
        elif message_type == MessageType.SERVER_ERROR_RESPONSE:
            response.code = struct.unpack('>i', payload[:4])[0]
            response.payload_size = struct.unpack('>I', payload[4:8])[0]
            payload = payload[8:]
            
        if not payload:
            return response
            
        if message_compression == CompressionType.GZIP:
            try:
                payload = CommonUtils.gzip_decompress(payload)
            except Exception as e:
                logger.error(f"Failed to decompress: {e}")
                return response
                
        try:
            if serialization_method == SerializationType.JSON:
                response.payload_msg = json.loads(payload.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to parse payload: {e}")
            
        return response

class RequestBuilder:
    def __init__(self, app_key: str, access_key: str):
        self.app_key = app_key
        self.access_key = access_key

    def new_auth_headers(self) -> Dict[str, str]:
        reqid = str(uuid.uuid4())
        return {
            "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
            "X-Api-Request-Id": reqid,
            "X-Api-Access-Key": self.access_key,
            "X-Api-App-Key": self.app_key
        }

    @staticmethod
    def new_full_client_request(seq: int) -> bytes:
        header = AsrRequestHeader.default_header() \
            .with_message_type_specific_flags(MessageTypeSpecificFlags.POS_SEQUENCE)
        
        payload = {
            "user": {
                "uid": "python_demo_uid"
            },
            "audio": {
                "format": "pcm",
                "codec": "raw",
                "rate": 16000,
                "bits": 16,
                "channel": 1
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "enable_ddc": True,
                "show_utterances": True,
                "enable_nonstream": False
            }
        }
        
        payload_bytes = json.dumps(payload).encode('utf-8')
        compressed_payload = CommonUtils.gzip_compress(payload_bytes)
        payload_size = len(compressed_payload)
        
        request = bytearray()
        request.extend(header.to_bytes())
        request.extend(struct.pack('>i', seq))
        request.extend(struct.pack('>I', payload_size))
        request.extend(compressed_payload)
        
        return bytes(request)

    @staticmethod
    def new_audio_only_request(seq: int, segment: bytes, is_last: bool = False) -> bytes:
        header = AsrRequestHeader.default_header()
        if is_last:
            header.with_message_type_specific_flags(MessageTypeSpecificFlags.NEG_WITH_SEQUENCE)
            seq = -seq
        else:
            header.with_message_type_specific_flags(MessageTypeSpecificFlags.POS_SEQUENCE)
        header.with_message_type(MessageType.CLIENT_AUDIO_ONLY_REQUEST)
        
        request = bytearray()
        request.extend(header.to_bytes())
        request.extend(struct.pack('>i', seq))
        
        compressed_segment = CommonUtils.gzip_compress(segment)
        request.extend(struct.pack('>I', len(compressed_segment)))
        request.extend(compressed_segment)
        
        return bytes(request)

# --- 2. 核心客户端逻辑 (移除 QT) ---

class VolcASRClient:
    """
    火山引擎实时语音识别客户端
    """
    def __init__(self, 
                 app_key: str, 
                 access_key: str, 
                 on_result_callback: Callable[[str, bool], None] = None,
                 on_error_callback: Callable[[str], None] = None,
                 url: str = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"):
        """
        初始化客户端
        :param app_key: 应用 ID
        :param access_key: 访问 Token
        :param on_result_callback: 接收到识别结果的回调函数 func(text, is_final)
        :param on_error_callback: 接收错误信息的回调函数 func(error_msg)
        :param url: WebSocket 地址
        """
        self.url = url
        self.request_builder = RequestBuilder(app_key, access_key)
        self.on_result = on_result_callback
        self.on_error = on_error_callback
        
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.stop_event = threading.Event()
        self.thread = None

    def push_audio(self, data: bytes):
        """外部调用此方法传入音频数据"""
        if self.is_running:
            self.audio_queue.put(data)

    def start(self):
        """启动后台线程处理网络请求"""
        if self.is_running:
            logger.warning("Client is already running.")
            return

        self.is_running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        logger.info("ASR Client started.")

    def stop(self):
        """停止处理"""
        if not self.is_running:
            return
        
        logger.info("Stopping ASR Client...")
        self.is_running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("ASR Client stopped.")

    def _run_async_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_asr())
        finally:
            loop.close()

    async def _process_asr(self):
        headers = self.request_builder.new_auth_headers()
        seq = 1
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.url, headers=headers, ssl=False) as ws:
                    logger.info("WebSocket Connected.")
                    
                    # 1. Send Handshake (Full Request)
                    request = RequestBuilder.new_full_client_request(seq)
                    seq += 1
                    await ws.send_bytes(request)
                    
                    # 2. Wait for Handshake Response
                    msg = await ws.receive()
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        resp = ResponseParser.parse_response(msg.data)
                        logger.info(f"Handshake response code: {resp.code}")
                        if resp.code != 1000: # 1000 usually means success/ready
                             logger.warning(f"Handshake might have failed: {resp.to_dict()}")

                    # 3. Define Sender (Reads from Queue -> Sends to WS)
                    async def sender():
                        nonlocal seq
                        while not self.stop_event.is_set():
                            try:
                                try:
                                    # Non-blocking get
                                    data = self.audio_queue.get(block=False)
                                    req = RequestBuilder.new_audio_only_request(seq, data, is_last=False)
                                    await ws.send_bytes(req)
                                    seq += 1
                                except queue.Empty:
                                    await asyncio.sleep(0.01)
                            except Exception as e:
                                logger.error(f"Sender error: {e}")
                                break
                        
                        # Send last packet when stopping
                        try:
                            req = RequestBuilder.new_audio_only_request(seq, b'', is_last=True)
                            await ws.send_bytes(req)
                            logger.info("Sent stop packet.")
                        except Exception as e:
                            logger.error(f"Error sending last packet: {e}")

                    # 4. Define Receiver (Reads from WS -> Calls Callback)
                    async def receiver():
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.BINARY:
                                response = ResponseParser.parse_response(msg.data)
                                
                                if response.code != 1000 and response.code != 0:
                                    err_msg = f"Server Error Code: {response.code}"
                                    logger.error(err_msg)
                                    if self.on_error:
                                        self.on_error(err_msg)

                                if response.payload_msg and 'result' in response.payload_msg:
                                    res_data = response.payload_msg
                                    text = res_data.get('result', {}).get('text', '')
                                    is_final = res_data.get('result', {}).get('is_final', False)
                                    if text:
                                        if self.on_result:
                                            self.on_result(text, is_final)
                                
                                if response.is_last_package:
                                    logger.info("Received last package from server.")
                                    break
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                break

                    # Run both tasks
                    sender_task = asyncio.create_task(sender())
                    receiver_task = asyncio.create_task(receiver())
                    
                    await asyncio.wait([sender_task, receiver_task], return_when=asyncio.FIRST_COMPLETED)
                    
                    if not sender_task.done(): sender_task.cancel()
                    # receiver usually finishes by itself when socket closes

        except Exception as e:
            err_msg = f"Connection Loop Error: {str(e)}"
            logger.error(err_msg)
            if self.on_error:
                self.on_error(err_msg)

# --- 3. 音频采集辅助类 (可选使用) ---

class AudioRecorder:
    def __init__(self, on_audio_data: Callable[[bytes], None], chunk_size=3200, sample_rate=16000):
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.on_audio_data = on_audio_data
        self.running = False
        self.thread = None
        self.pa = pyaudio.PyAudio()

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _record_loop(self):
        stream = self.pa.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=self.sample_rate,
                              input=True,
                              frames_per_buffer=self.chunk_size)
        logger.info("Microphone started.")
        try:
            while self.running:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                if self.on_audio_data:
                    self.on_audio_data(data)
        finally:
            stream.stop_stream()
            stream.close()
            logger.info("Microphone stopped.")

    def __del__(self):
        self.pa.terminate()

# --- 4. 使用示例 ---

if __name__ == "__main__":
    # 配置你的 Key (这里使用原来的 Demo Key，实际使用请替换)
    APP_KEY = "8180401519"
    ACCESS_KEY = "1-5OBFksmAWNMb99_1RIvxGR8JBWbdmX"
    
    # 定义回调函数
    def handle_result(text, is_final):
        status = "[Final]" if is_final else "[Partial]"
        print(f"\r{status} {text}", end="" if not is_final else "\n")

    def handle_error(msg):
        print(f"\nError: {msg}")

    # 1. 初始化 ASR 客户端
    client = VolcASRClient(APP_KEY, ACCESS_KEY, handle_result, handle_error)
    
    # 2. 初始化录音机，将数据推送到 client.push_audio
    recorder = AudioRecorder(client.push_audio)

    try:
        print("Starting... (Press Ctrl+C to stop)")
        client.start()   # 启动网络线程
        recorder.start() # 启动录音线程
        
        # 主线程保持运行
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        recorder.stop()
        client.stop()
        print("Exited.")

