import "server-only"
import {
  type BaseEvent,
  EventType,
  type RunErrorEvent,
  type RunStartedEvent,
} from "@ag-ui/client"
import {
  AgentRunner,
  type AgentRunnerConnectRequest,
  type AgentRunnerIsRunningRequest,
  type AgentRunnerRunRequest,
  type AgentRunnerStopRequest,
  createRunEventFinalizer,
} from "@copilotkit/runtime/v2"
import { EMPTY, Observable } from "rxjs"
import { chatErrorMessage, isRejection } from "@/lib/chat"

type ActiveRun = { runId: string; stopped: boolean; abort: () => void }

// Returns the event that tells the user why a run failed; a refusal carries its HTTP status as the code.
function failureEvent(error: unknown): RunErrorEvent {
  return {
    type: EventType.RUN_ERROR,
    message: chatErrorMessage(error),
    ...(isRejection(error) && {
      code: String((error as { status: number }).status),
    }),
  }
}

// Runs an agent for a thread and keeps nothing; the transcript lives in the API.
export class ChatRunner extends AgentRunner {
  private readonly active = new Map<string, ActiveRun>()

  run({ threadId, agent, input }: AgentRunnerRunRequest) {
    return new Observable<BaseEvent>((subscriber) => {
      const finalizer = createRunEventFinalizer()
      const run: ActiveRun = {
        runId: input.runId,
        stopped: false,
        abort: () => agent.abortRun(),
      }
      let started = false
      this.active.set(threadId, run)

      const emit = (event: BaseEvent) => {
        started ||= event.type === EventType.RUN_STARTED
        finalizer.observe(event)
        subscriber.next(event)
      }
      const ensureStarted = () => {
        if (started) return
        emit({
          type: EventType.RUN_STARTED,
          threadId,
          runId: input.runId,
        } satisfies RunStartedEvent)
      }

      agent
        .runAgent(input, { onEvent: ({ event }) => emit(event) })
        .catch((error: unknown) => {
          if (run.stopped) return
          ensureStarted()
          emit(failureEvent(error))
        })
        .then(() => {
          ensureStarted()
          const closing = finalizer.finalize({
            stopRequested: run.stopped,
            protocolVersion: input.protocolVersion,
          })
          for (const event of closing) subscriber.next(event)
          subscriber.complete()
        })

      return () => {
        if (this.active.get(threadId) === run) this.active.delete(threadId)
        run.abort()
      }
    })
  }

  connect(_request: AgentRunnerConnectRequest) {
    return EMPTY
  }

  isRunning({ threadId }: AgentRunnerIsRunningRequest) {
    return Promise.resolve(this.active.has(threadId))
  }

  stop({ threadId, runId }: AgentRunnerStopRequest) {
    const run = this.active.get(threadId)
    if (!run || (runId !== undefined && run.runId !== runId)) {
      return Promise.resolve(false)
    }
    run.stopped = true
    run.abort()
    return Promise.resolve(true)
  }
}
