# Episodio 05 — I Doubled the Workers. The Bottleneck Didn't Move.

## Revisión gamificada: 4:00 objetivo

Locución en inglés. Cada frase tiene una acción visual. Tiempos editoriales, no voz medida.
Cuenta atrás: 3 segundos, tres ticks discretos, sin narración; no se presenta un atasco como caída real.

## 00:00 — The orange pile (S01)

Trace-driven playfield: orange_stack_and_two_service_lanes -> waiting_tiles_age_while_service_advances -> fifo_release_and_stack_reflow -> moving_trace_and_worker_slot_badges

### 00:00–00:07

Stop adding workers. Look at this pile. Eight workers are holding jobs; only two jobs are getting through.

En pantalla: orange_stack_and_two_service_lanes.

### 00:07–00:14

Those orange blocks are waiting, not doing extra work. This is simulated traffic, not a live AI crash.

En pantalla: waiting_tiles_age_while_service_advances.

### 00:14–00:22

Here comes another pair. The door opens, the pile drops, and the next two squeeze through. Nobody disappears.

En pantalla: fifo_release_and_stack_reflow.

### 00:22–00:30

I'm giving you the controls next. Before we touch that worker switch, watch what this little doorway can actually clear.

En pantalla: moving_trace_and_worker_slot_badges.

## 00:30 — Beat this time (S02)

Trace-driven playfield: baseline_state_colors_in_motion -> completed_counter_and_fifo_release -> completed_receipt_then_labeled_replay -> replay_and_locked_input_badges

### 00:30–00:36

Twelve jobs. Four workers. Go. The blue blocks prepare; the white lanes process; the green blocks are finished.

En pantalla: baseline_state_colors_in_motion.

### 00:36–00:43

Follow the exits. Another pair, then another. The next pair is already waiting when a lane opens. Keep your eye on twelve.

En pantalla: completed_counter_and_fifo_release.

### 00:43–00:51

Twelve point five simulated seconds. That's our time to beat. The orange pile never held more than two waiting jobs.

En pantalla: completed_receipt_then_labeled_replay.

### 00:51–01:00

Same twelve jobs on the replay. Same half-second preparation and two-second tool service. I'm leaving those settings locked. Only the worker switch gets a turn.

En pantalla: replay_and_locked_input_badges.

## 01:00 — The empty doorway (S03)

Trace-driven playfield: prep_and_idle_slots -> idle_intervals_and_final_pair -> underfed_receipt_then_baseline_replay -> baseline_preparation_overlaps_service

### 01:00–01:07

First, take two workers away. See that empty doorway? Both workers are preparing the next pair. Nothing passes during that gap.

En pantalla: prep_and_idle_slots.

### 01:07–01:15

There it is again. Green blocks leave, blue blocks prepare, and the doorway waits. Watch the last pair crawl toward the finish.

En pantalla: idle_intervals_and_final_pair.

### 01:15–01:22

Fifteen seconds. Slower. So more workers helped us before. The four-worker run filled those gaps and finished at twelve point five.

En pantalla: underfed_receipt_then_baseline_replay.

### 01:22–01:30

Look at the doorway now: busy while the next pair gets ready. Four workers feed it. What happens when we give it eight?

En pantalla: baseline_preparation_overlaps_service.

## 01:30 — Follow the orange block (S04)

Trace-driven playfield: job4_preparing_then_waiting -> job4_service_and_ownership -> fifo_tiles_and_fixed_tool_wall -> locked_badges_and_moving_trace

### 01:30–01:37

Follow job four. Blue, then orange. Its worker is still occupied, but the job cannot enter either white lane yet.

En pantalla: job4_preparing_then_waiting.

### 01:37–01:44

Now a lane opens. Job four moves in; its worker stays attached. Watch that badge follow the job all the way out.

En pantalla: job4_service_and_ownership.

### 01:44–01:52

The other orange blocks wait their turn. More occupied worker boxes would not magically carve another opening in this wall. Here comes the replay.

En pantalla: fifo_tiles_and_fixed_tool_wall.

### 01:52–02:00

Same jobs. Same two slots. Keep that picture in your head, because you're about to bet on the next run. No changing the jobs after guessing.

En pantalla: locked_badges_and_moving_trace.

## 02:00 — Lock in your guess (S05)

Trace-driven playfield: worker_switch_and_neutral_choices -> massive_3_2_1_countdown -> double_workers_queue_impact -> double_workers_continues_to_completion -> trace_backed_result_and_answer

### 02:00–02:12

I just doubled the workers from 4 to 8. Does the processing speed double, or does the system choke? Lock in your guess.

En pantalla: worker_switch_and_neutral_choices.

### 02:12–02:15

**[3 → 2 → 1: sin voz, tres ticks, simulación congelada]**

En pantalla: massive_3_2_1_countdown.

### 02:15–02:19

Go. There they go. Six orange blocks pile up against the same two openings.

En pantalla: double_workers_queue_impact.

### 02:19–02:25

The door keeps draining pairs. No crash. Watch the final pair: the finish line has not moved.

En pantalla: double_workers_continues_to_completion.

### 02:25–02:30

Twelve point five. Traffic jam wins. More waiting at the tool, not double speed.

En pantalla: trace_backed_result_and_answer.

## 02:30 — The waiting room moved (S06)

Trace-driven playfield: input_queue_and_tool_stack -> tool_progress_and_peak_queue_receipt -> baseline_both_queues -> both_wait_counters_and_completions

### 02:30–02:37

Look left. The input queue emptied faster. Looks like an upgrade, right? Now look at the orange tower beside the tool.

En pantalla: input_queue_and_tool_stack.

### 02:37–02:45

That's where the waiting went. Six piled up at the peak. The lanes keep draining it; the service clock hasn't sped up.

En pantalla: tool_progress_and_peak_queue_receipt.

### 02:45–02:53

Replay with four workers. Smaller orange pile, more jobs waiting on the left. We didn't delete the work. We moved the waiting room again.

En pantalla: baseline_both_queues.

### 02:53–03:00

Watch both counters as the jobs move. A prettier input queue is not the finish line. The green completed jobs are.

En pantalla: both_wait_counters_and_completions.

## 03:00 — Widen the door (S07)

Trace-driven playfield: four_lane_trace_to_completion -> capacity_receipt_and_replay -> four_lane_replay_and_simulation_badge -> simulated_capacity_control_and_flow

### 03:00–03:07

Keep eight workers. Open two more slots. Four jobs pass together. Watch the green side fill. Last four coming through.

En pantalla: four_lane_trace_to_completion.

### 03:07–03:15

Six point five simulated seconds. This time the finish moved. The orange pile clears in bigger waves because the doorway actually got wider.

En pantalla: capacity_receipt_and_replay.

### 03:15–03:23

Watch again: same jobs, same service time, four slots. That capacity switch belongs to this simulator, not your provider's control panel.

En pantalla: four_lane_replay_and_simulation_badge.

### 03:23–03:30

No magic setting appeared in a real API. We widened this simulated door. Your turn to change an input.

En pantalla: simulated_capacity_control_and_flow.

## 03:30 — Rematch (S08)

Trace-driven playfield: long_prep_and_idle_slots -> long_prep_gap_then_service -> job_ids_and_editorial_log -> active_rematch_cut_on_event

### 03:30–03:38

Rematch. I'm stretching preparation from half a second to three. Watch the blue blocks hang around. Now the doorway can run out of ready jobs again.

En pantalla: long_prep_and_idle_slots.

### 03:38–03:46

There is the gap. A different input, a different race. Run this exact simulator and change that value before you add another worker.

En pantalla: long_prep_gap_then_service.

### 03:46–03:54

Keep the job numbers visible. Count what finishes, not how busy the screen looks. And yes, worker four's little comment was intentional.

En pantalla: job_ids_and_editorial_log.

### 03:54–04:00

Make your next guess with the doorway in view. Then press run. The orange pile will tell you where to look.

En pantalla: active_rematch_cut_on_event.

## Easter eggs — comentarios editoriales, no errores reales

- S01 +10–14 s: `// queue.exe has entered its stacking era`
- S04 +12–17 s: `// Worker 4 is questioning its existence`
- S06 +8–13 s: `// more_workers != wider_door`
- S08 +20–25 s: `// TODO: negotiate with the doorway`
