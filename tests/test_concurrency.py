import sys
sys.path.insert(0, '.')

# Test 1: EventBus
from core.event_bus import EventBus, Event, PRIORITY_HIGH
bus = EventBus(persist=False)
received = []
bus.subscribe('test.*', lambda e: received.append(e.topic))
bus.subscribe('test.specific', lambda e: received.append('SPECIFIC'))
n = bus.emit('test.specific', {'data': 1}, PRIORITY_HIGH, 'test')
assert n == 2, f'Expected 2 handlers, got {n}'
assert 'test.specific' in received
assert 'SPECIFIC' in received
print('[PASS] EventBus pub/sub + wildcard')

# Test 2: Event serialization
e = Event('sensor.file.modified', {'path': '/test'})
d = e.to_dict()
e2 = Event.from_dict(d)
assert e2.topic == e.topic
assert e2.payload == e.payload
print('[PASS] Event serialization')

# Test 3: Queue
bus2 = EventBus(persist=False)
bus2.enqueue(Event('queued.test', {'x': 1}))
events = bus2.drain_queue()
assert len(events) >= 1
assert events[0].topic == 'queued.test'
events2 = bus2.drain_queue()
assert len(events2) == 0
print('[PASS] EventBus queue')

# Test 4: Sensors
from core.sensors import SystemHealth
sh = SystemHealth()
metrics = sh.scan()
assert 'disk_c_pct' in metrics or 'memory_pct' in metrics
print('[PASS] SystemHealth:', metrics)

# Test 5: Dispatcher
from core.dispatcher import dispatch
result = dispatch(run_sensors=True)
assert 'sensor_results' in result
assert 'system_health' in result['sensor_results']
assert 'network' in result['sensor_results']
health = result['sensor_results']['system_health']
network = result['sensor_results']['network']
print('[PASS] Dispatcher:', health, '| Network:', len(network), 'targets')

print()
print('All 5 tests passed!')

# Test 6: Cooldown
from core.sensors import _load_state, _is_cooled_down, _mark_fired, _save_state
state = _load_state()
# 刚 mark 过的应该在冷却中
_mark_fired(state, "sensor.file.modified", "/test/file.py")
_save_state(state)
assert not _is_cooled_down(state, "sensor.file.modified", "/test/file.py"), "Should be in cooldown"
# 不存在的 key 应该不在冷却中
assert _is_cooled_down(state, "sensor.file.modified", "/nonexistent"), "Should not be in cooldown"
print('[PASS] Sensor cooldown')

# Test 7: Dispatcher trace_id
from core.dispatcher import dispatch
r1 = dispatch(run_sensors=False)
r2 = dispatch(run_sensors=False)
assert 'trace_id' in r1
assert 'trace_id' in r2
assert len(r1['trace_id']) == 12
assert r1['trace_id'] != r2['trace_id'], "Each dispatch should have unique trace_id"
print('[PASS] Dispatcher trace_id')

print()
print('All 7 tests passed!')
