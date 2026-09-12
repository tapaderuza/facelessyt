# Episodio 04 — Your AI Model Fits. Your Conversation Doesn't.

Guion de locución en inglés. Timestamps objetivo; ajustar al audio real.
Ejemplo matemático ejecutado; no se ha ejecutado ni medido un LLM.

## 00:00 — The budget goes red (S01)

Four gibibytes of model weights. Eight available. This budget still goes red. The weights did not change. The conversation did. Watch the blue section: a longer context pushes this example from six to nine. This is a calculated budget, not a crash recording. I'm going to build the calculation, change one input at a time, and show you why a model that fits is not the same thing as a workload that fits.

## 00:30 — The three-part bill (S02)

Our bill has three lines: resident weights, conversation cache, and a reserve for everything this simplified calculation does not model. We're budgeting one memory pool. If you have separate system RAM and GPU memory, don't add them together and pretend the result is one device. Four for weights and one for reserve are assumptions in this example. They are not measurements of your machine.

## 00:55 — The conversation leaves a footprint (S03)

The blue section is the key-value cache. During generation, an attention model can keep intermediate keys and values from earlier tokens and reuse them. In the full-context setup we're illustrating, a longer sequence means more cached values. The weights can stay fixed while this separate allocation grows. That's the mechanism, not a claim about every model on the market. Sliding windows, different architectures and cache compression change the accounting. Our calculator has a narrow job: make one common layout explicit enough that we can inspect every multiplication.

## 01:35 — Build the calculation (S04)

Here's the entire cache calculation. Two, for keys and values. Times layers. Times key-value heads, not necessarily the number of attention heads. Times head dimension. Times bytes per cached value. Our chosen inputs give one hundred and twenty-eight kibibytes per token, per sequence. Multiply by the token count and the number of sequences. Then add weights and reserve. That's it. These exact inputs and outputs come from the Python file, so the animation doesn't get to improvise the answer.

## 02:10 — The first case fits the budget (S05)

Start at eight thousand one hundred and ninety-two tokens. The cache is one gibibyte. Four of weights, one of cache, one of reserve: six against an eight-gibibyte budget. Two remain. Notice the verdict. It says under budget, not verified. It does not say the model has loaded. It does not tell us the generation speed, and it does not tell us whether the output is useful. A budget can rule out an assumption. It cannot replace a runtime test. Now leave everything else alone.

## 02:50 — Change one input (S06)

Raise the context to thirty-two thousand seven hundred and sixty-eight tokens. In this calculation, that's four times the tokens and four times the cache. The blue block reaches four gibibytes. The total is now nine. We are one over budget, even though the weights are still four. Nothing here proves that a particular computer crashed. It proves that these inputs don't fit this budget under these assumptions. That's enough to reject the plan before treating it as a working configuration. And we can change the plan without changing the model weights.

## 03:30 — The first lever (S07)

Cut the context to sixteen thousand three hundred and eighty-four tokens. The cache becomes two gibibytes. Total: seven. One left in the budget. The tradeoff is visible: a smaller context allowance, not a free improvement. And changing how weights are stored is not the same switch as changing cache precision. Check what your runtime actually supports. This example is back under budget. But one more input can send it straight back over.

## 04:00 — The second conversation (S08)

Keep that reduced context, but budget two sequences at once. We're assuming separate full caches, without shared prefixes. Two gibibytes for the first sequence. Two for the second. The weights are shared once in this example, not loaded twice. Yet the total is back to nine. So asking whether a model fits misses two questions: how much context, and how many simultaneous sequences? Four cases. Same weights. Different budgets. Those are the inputs I would write down before calling a local setup ready.

## 04:35 — Where the calculator stops (S09)

Here's where this calculator stops. Our reserve is a chosen allowance, not a universal overhead figure. A downloaded file is not automatically the same size as its resident representation. Backend behavior, buffers and allocation choices still need inspection. Offloading can move work between memory pools; our single-pool sum does not model that arrangement. Don't paste these example inputs into a different architecture and call the result a compatibility certificate. Use the right cache layout, then compare the estimate with the runtime you actually intend to use.

## 05:10 — The workload checklist (S10)

For a real trial, record the model revision, weight format and backend. Set the context you need and the concurrency you expect. Budget the memory pool you plan to use. Then load the real configuration and measure its peak during your target workload. Check latency and useful output separately. If you change the context, concurrency or backend, repeat the test. That's the handoff: arithmetic first, measurement next. Neither a promising download size nor an under-budget label is the finish line.

## 05:45 — The payoff (S11)

Here's the whole result. Short context: six. Long context: nine. Reduced context: seven. Two sequences at that reduced context: nine again. All calculated, all with the same assumed weights and reserve. We didn't discover a magic model. We made the hidden inputs visible. The question isn't just, does the model fit? It's, does this workload fit, and have I measured it?

## 06:10 — Run the calculation (S12)

Run the calculator and change the context input first. Watch which line moves. The reproducible version has no model download and makes no speed claims. If you want the next step, the previous episode shows how I make an agent check its evidence before accepting an answer. Same principle here: expose the assumptions before trusting the result.
