import {
  HttpAgent,
  type HttpAgentConfig,
  type RunAgentInput,
} from "@ag-ui/client"

// Agent that runs a conversation against the chat endpoint.
export class ChatAgent extends HttpAgent {
  constructor(config: HttpAgentConfig) {
    super(config)
    this.subscribe({
      onMessagesSnapshotEvent: () => ({ stopPropagation: true }),
      onRunFailed: () => {
        this.pendingInterrupts = []
      },
    })
  }

  protected override requestInit(input: RunAgentInput) {
    return super.requestInit({
      ...input,
      messages: input.messages.slice(-1),
      state: {},
    })
  }
}
