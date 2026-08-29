from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Protocol


class Publisher(Protocol):
    def publish(self, topic: str, event: dict[str, Any], qos: int) -> None: ...

    def close(self) -> None: ...


class DryRunPublisher:
    def publish(self, topic: str, event: dict[str, Any], qos: int) -> None:
        print(f"MQTT dry-run topic={topic} qos={qos}")
        print(json.dumps(event, separators=(",", ":")))

    def close(self) -> None:
        return None


class MqttPublisher:
    def __init__(
        self,
        *,
        endpoint: str,
        port: int,
        client_id: str,
        ca_path: str | Path,
        cert_path: str | Path,
        key_path: str | Path,
        connect_timeout: float = 10,
    ) -> None:
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError(
                "MQTT support is not installed. Install with: pip install -e '.[mqtt]'"
            ) from exc

        self._mqtt = mqtt
        self._connected = threading.Event()
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.tls_set(
            ca_certs=str(ca_path),
            certfile=str(cert_path),
            keyfile=str(key_path),
        )
        self._client.connect(endpoint, port=port, keepalive=60)
        self._client.loop_start()
        if not self._connected.wait(connect_timeout):
            self.close()
            raise ConnectionError(f"MQTT connection timed out after {connect_timeout}s")

    def _on_connect(self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any) -> None:
        del client, userdata, flags, properties
        if int(reason_code) == 0:
            self._connected.set()

    def _on_disconnect(
        self,
        client: Any,
        userdata: Any,
        disconnect_flags: Any,
        reason_code: Any,
        properties: Any,
    ) -> None:
        del client, userdata, disconnect_flags, reason_code, properties
        self._connected.clear()

    def publish(self, topic: str, event: dict[str, Any], qos: int) -> None:
        if not self._connected.is_set():
            raise ConnectionError("MQTT client is disconnected")
        payload = json.dumps(event, separators=(",", ":"))
        result = self._client.publish(topic, payload=payload, qos=qos, retain=False)
        result.wait_for_publish(timeout=10)
        if result.rc != self._mqtt.MQTT_ERR_SUCCESS or not result.is_published():
            raise ConnectionError(f"MQTT publish failed with result code {result.rc}")

    def close(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
