# SearchScience v5.0 - Robustness module
import time, threading, functools, logging, os, json, random
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, name, failure_threshold=3, recovery_timeout=60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
        self._lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        with self._lock:
            if self.state == 'OPEN':
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise RuntimeError('Circuit ' + self.name + ' OPEN')
        try:
            result = func(*args, **kwargs)
            with self._lock:
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
            return result
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'
            raise

def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=60.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        delay = delay * (0.5 + random.random())
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator

class DegradationManager:
    def __init__(self):
        self.source_health = defaultdict(lambda: dict(failures=0, degraded=False))

    def record_success(self, name):
        h = self.source_health[name]
        h['failures'] = 0
        h['degraded'] = False

    def record_failure(self, name):
        h = self.source_health[name]
        h['failures'] += 1
        if h['failures'] >= 3:
            h['degraded'] = True

    def is_degraded(self, name):
        return self.source_health[name]['degraded']

    def get_healthy(self, sources):
        return [(n, c) for n, c in sources if not self.is_degraded(n)]

class CheckpointManager:
    def __init__(self, checkpoint_dir):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)

    def save(self, name, data):
        path = os.path.join(self.checkpoint_dir, name + '.json')
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    def load(self, name):
        path = os.path.join(self.checkpoint_dir, name + '.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def list_checkpoints(self):
        if not os.path.exists(self.checkpoint_dir):
            return []
        return [f.replace('.json', '') for f in os.listdir(self.checkpoint_dir)
                if f.endswith('.json') and not f.endswith('.tmp')]
