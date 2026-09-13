"""Deterministic event simulation, NOT a measured AI/API/database benchmark.

All jobs arrive at t=0. A worker owns a job through preparation, FIFO tool wait,
and tool service. Only tool_slots jobs can use the tool concurrently. Logical
time is integer milliseconds; ties finish tool work before preparation.
"""
from collections import deque
import heapq


def simulate(workers=4, tool_slots=2, jobs=12, prep_ms=500, service_ms=2000):
    for name, value in locals().copy().items():
        if type(value) is not int or value <= 0:
            raise ValueError(f'{name} must be a positive integer')
    pending = deque(range(jobs))
    waiting = deque()
    free_slots = list(range(tool_slots))
    heapq.heapify(free_slots)
    events = []
    records = [{'id': j, 'arrival_ms': 0} for j in range(jobs)]
    log = []
    peak_wait = 0

    def prepare(worker, now):
        if pending:
            j = pending.popleft()
            records[j].update(worker=worker, prep_start_ms=now, prep_end_ms=now+prep_ms)
            heapq.heappush(events, (now+prep_ms, 1, j))
            log.append({'t_ms': now, 'job': j, 'event': 'prepare', 'worker': worker})

    for worker in range(min(workers, jobs)):
        prepare(worker, 0)
    while events:
        now = events[0][0]
        # Process all completions at this timestamp, then assign FIFO slots.
        while events and events[0][0] == now:
            _, kind, j = heapq.heappop(events)
            if kind == 0:
                heapq.heappush(free_slots, records[j]['slot'])
                log.append({'t_ms': now, 'job': j, 'event': 'complete'})
                prepare(records[j]['worker'], now)
            else:
                waiting.append(j)
                log.append({'t_ms': now, 'job': j, 'event': 'tool_ready'})
        while waiting and free_slots:
            j = waiting.popleft()
            slot = heapq.heappop(free_slots)
            records[j].update(slot=slot, service_start_ms=now, complete_ms=now+service_ms)
            heapq.heappush(events, (now+service_ms, 0, j))
            log.append({'t_ms': now, 'job': j, 'event': 'tool_start', 'slot': slot})
        peak_wait = max(peak_wait, len(waiting))
    for row in records:
        row['input_wait_ms'] = row['prep_start_ms']
        row['tool_wait_ms'] = row['service_start_ms']-row['prep_end_ms']
        row['end_to_end_ms'] = row['complete_ms']
    return {
        'kind': 'synthetic_discrete_event_simulation',
        'inputs': dict(workers=workers, tool_slots=tool_slots, jobs=jobs,
                       prep_ms=prep_ms, service_ms=service_ms),
        'metrics': {'batch_ms': max(r['complete_ms'] for r in records),
                    'peak_tool_queue': peak_wait,
                    'completed': len(records)},
        'jobs': records, 'events': log,
    }


def cases():
    return {name: simulate(workers=w, tool_slots=s) for name, w, s in
            [('underfed', 2, 2), ('baseline', 4, 2), ('double_workers', 8, 2),
             ('double_capacity', 8, 4)]}


def state_at(trace, t_ms):
    """Observable states use half-open intervals; no job exists twice."""
    import math
    if isinstance(t_ms, bool) or not isinstance(t_ms, (int, float)) or not math.isfinite(t_ms) or t_ms < 0:
        raise ValueError('t_ms must be finite and non-negative')
    states = {k: [] for k in ('input', 'preparing', 'waiting', 'service', 'done')}
    for job in trace['jobs']:
        if t_ms < job['prep_start_ms']:
            kind = 'input'
        elif t_ms < job['prep_end_ms']:
            kind = 'preparing'
        elif t_ms < job['service_start_ms']:
            kind = 'waiting'
        elif t_ms < job['complete_ms']:
            kind = 'service'
        else:
            kind = 'done'
        states[kind].append(job['id'])
    return states


if __name__ == '__main__':
    import json
    print(json.dumps({k: v['metrics'] for k, v in cases().items()}, indent=2))
